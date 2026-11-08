import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from backend.app.core.auth import get_current_user, AuthenticatedUser
from backend.app.core.errors import NLUProviderException
from backend.app.providers.asr.dispatcher import ASRDispatcher
from backend.app.providers.nlu.mock import MockNLUProvider
from backend.app.providers.nlu.gemini import GeminiNLUProvider
from backend.app.core.config import settings
from backend.app.db.repository import store
from backend.app.schemas.proposal import ProposalResponse
from backend.app.schemas.capture import CaptureResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/captures", tags=["Capture & Intent"])

asr_dispatcher = ASRDispatcher()

def get_nlu_provider():
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if settings.GEMINI_API_KEY:
        return GeminiNLUProvider()
    if env == "production":
        raise NLUProviderException(
            detail="Production environment requires GEMINI_API_KEY to be configured; mock NLU provider is forbidden in production.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="NLU_CREDENTIALS_MISSING"
        )
    return MockNLUProvider()

async def safe_extract_intent(text: str, user_timezone: str):
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    provider = get_nlu_provider()
    try:
        return await provider.extract_intent(
            transcript_text=text,
            user_timezone=user_timezone
        )
    except NLUProviderException:
        raise
    except httpx.TimeoutException as exc:
        logger.error(f"Gemini API request timed out: {exc}")
        if env == "production":
            raise NLUProviderException(
                detail="AI intent extraction timed out. Please try again.",
                provider="gemini",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                error_code="NLU_TIMEOUT"
            )
        logger.warning("Development/test fallback to MockNLUProvider due to Gemini timeout.")
        fallback = MockNLUProvider()
        return await fallback.extract_intent(transcript_text=text, user_timezone=user_timezone)
    except Exception as exc:
        exc_str = str(exc)
        logger.error(f"Primary NLU provider error ({exc})")
        if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
            if env == "production":
                raise NLUProviderException(
                    detail="AI intent extraction is currently unavailable due to provider rate limits (HTTP 429). Please retry shortly.",
                    provider="gemini",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    error_code="NLU_RATE_LIMITED"
                )
            logger.warning("Development/test fallback to MockNLUProvider due to Gemini rate limit (429).")
            fallback = MockNLUProvider()
            return await fallback.extract_intent(transcript_text=text, user_timezone=user_timezone)

        if env == "production":
            raise NLUProviderException(
                detail=f"AI intent extraction failed: {exc}",
                provider="gemini",
                status_code=status.HTTP_502_BAD_GATEWAY,
                error_code="NLU_PROVIDER_ERROR"
            )
        logger.warning(f"Development/test fallback to MockNLUProvider due to provider error ({exc}).")
        fallback = MockNLUProvider()
        return await fallback.extract_intent(transcript_text=text, user_timezone=user_timezone)

async def apply_user_display_language_preference(user_id: UUID, proposal: ProposalResponse, user_token: Optional[str] = None) -> ProposalResponse:
    prefs = store.list_memory_preferences(user_id=user_id, user_token=user_token)
    for pref in prefs:
        if pref.preference_key == "preferred_display_language":
            val = pref.preference_value or {}
            target_lang = val.get("display_language")
            if target_lang and target_lang in ["en", "ta"]:
                return await store.translate_proposal(proposal.id, target_lang, user_id=user_id, user_token=user_token)
    return proposal

class TextCaptureRequest(BaseModel):
    text: str
    user_timezone: str = "Asia/Kolkata"

@router.get("", response_model=List[CaptureResponse])
async def list_captures(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Retrieves chronological capture stream for the authenticated user.
    Each capture record includes its associated proposals and lifecycle status.
    """
    return store.list_captures(user_id=current_user.id, user_token=current_user.token)

@router.get("/{capture_id}", response_model=CaptureResponse)
async def get_capture(capture_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Retrieves an individual capture and all its associated proposals scoped to the authenticated user.
    """
    cap = store.get_capture(capture_id=capture_id, user_id=current_user.id, user_token=current_user.token)
    if not cap:
        raise HTTPException(status_code=404, detail=f"Capture {capture_id} not found")
    return cap

@router.delete("/{capture_id}")
async def delete_capture(capture_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Deletes an individual capture from history for the authenticated user.
    Committed tasks remain strictly preserved.
    """
    deleted = store.delete_capture(capture_id=capture_id, user_id=current_user.id, user_token=current_user.token)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Capture {capture_id} not found")
    return {"message": f"Capture {capture_id} deleted successfully."}

@router.post("/clear")
async def clear_captures(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Clears visible capture stream for the authenticated user without deleting committed tasks or pending proposals.
    """
    count = store.clear_captures(user_id=current_user.id, user_token=current_user.token)
    return {"message": f"Cleared {count} capture records. Committed tasks and pending proposals remain preserved."}

@router.post("/text", response_model=ProposalResponse)
async def capture_text(
    request: TextCaptureRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Submits raw unstructured text monologue.
    Creates persistent capture record, runs NLU to extract items,
    and returns the created pending proposal for the authenticated user.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="Text payload cannot be empty")

    user_id = current_user.id
    token = current_user.token
    extraction = await safe_extract_intent(
        text=request.text,
        user_timezone=request.user_timezone
    )
    extraction.transcript_text = request.text

    # 1. Create persistent capture record
    capture = store.create_capture(
        user_id=user_id,
        input_type="TEXT",
        transcript_text=request.text,
        detected_language=extraction.detected_language,
        original_transcript=request.text,
        user_token=token
    )

    # 2. Create proposal linked to capture
    proposal = store.create_proposal_from_extraction(
        user_id=user_id,
        extraction=extraction,
        capture_id=capture.id,
        model_provider=extraction.model_provider,
        model_version=extraction.model_version,
        user_token=token
    )
    proposal = await apply_user_display_language_preference(user_id, proposal, user_token=token)
    return proposal

@router.post("/audio", response_model=ProposalResponse)
async def capture_audio(
    file: UploadFile = File(...),
    user_timezone: str = Form("Asia/Kolkata"),
    language: Optional[str] = Form(None),
    mock_text: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Receives recorded audio, transcribes via ASR (Gnani Prisma with Sarvam Saaras failover),
    creates persistent capture record, extracts structured intent, and creates a pending proposal.
    Audio bytes are destroyed immediately after transcription (Zero raw audio retention).
    """
    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio payload received")

    transcription = await asr_dispatcher.transcribe(
        audio_bytes=audio_bytes,
        content_type=file.content_type or "audio/wav",
        language=language,
        mock_fallback_text=mock_text
    )

    if not transcription.transcript_text or not transcription.transcript_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Speech recognition did not detect any spoken words. Please speak clearly into the microphone."
        )

    extraction = await safe_extract_intent(
        text=transcription.transcript_text,
        user_timezone=user_timezone
    )
    extraction.transcript_text = transcription.transcript_text

    user_id = current_user.id
    token = current_user.token

    # 1. Create persistent capture record
    capture = store.create_capture(
        user_id=user_id,
        input_type="VOICE",
        transcript_text=transcription.transcript_text,
        detected_language=extraction.detected_language,
        original_transcript=transcription.transcript_text,
        provider_metadata={"language_hint": language},
        user_token=token
    )

    # 2. Create proposal linked to capture
    proposal = store.create_proposal_from_extraction(
        user_id=user_id,
        extraction=extraction,
        capture_id=capture.id,
        model_provider=extraction.model_provider,
        model_version=extraction.model_version,
        user_token=token
    )
    proposal = await apply_user_display_language_preference(user_id, proposal, user_token=token)
    return proposal
