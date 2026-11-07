from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from backend.app.providers.asr.dispatcher import ASRDispatcher
from backend.app.providers.nlu.mock import MockNLUProvider
from backend.app.providers.nlu.gemini import GeminiNLUProvider
from backend.app.core.config import settings
from backend.app.db.repository import store
from backend.app.schemas.proposal import ProposalResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/captures", tags=["Capture & Intent"])

asr_dispatcher = ASRDispatcher()

def get_nlu_provider():
    if settings.GEMINI_API_KEY:
        return GeminiNLUProvider()
    return MockNLUProvider()

async def safe_extract_intent(text: str, user_timezone: str):
    provider = get_nlu_provider()
    try:
        return await provider.extract_intent(
            transcript_text=text,
            user_timezone=user_timezone
        )
    except Exception as exc:
        logger.warning(f"Primary NLU provider error ({exc}); using fallback rule-based parser.")
        fallback = MockNLUProvider()
        return await fallback.extract_intent(
            transcript_text=text,
            user_timezone=user_timezone
        )

async def apply_user_display_language_preference(user_id: UUID, proposal: ProposalResponse) -> ProposalResponse:
    for pref in store.memory_preferences.values():
        if pref.get("user_id") == user_id and pref.get("preference_key") == "preferred_display_language":
            val = pref.get("preference_value", {})
            target_lang = val.get("display_language")
            if target_lang and target_lang in ["en", "ta"]:
                return await store.translate_proposal(proposal.id, target_lang)
    return proposal

class TextCaptureRequest(BaseModel):
    user_id: Optional[UUID] = None
    text: str
    user_timezone: str = "Asia/Kolkata"

@router.post("/text", response_model=ProposalResponse)
async def capture_text(request: TextCaptureRequest):
    """
    Submits raw unstructured text monologue.
    NLU extracts actionable items and generates a pending proposal.
    Zero tasks are created until the user explicitly reviews and approves.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="Text payload cannot be empty")

    user_id = request.user_id or store.default_user_id
    extraction = await safe_extract_intent(
        text=request.text,
        user_timezone=request.user_timezone
    )
    extraction.transcript_text = request.text
    
    proposal = store.create_proposal_from_extraction(
        user_id=user_id,
        extraction=extraction
    )
    proposal = await apply_user_display_language_preference(user_id, proposal)
    return proposal

@router.post("/audio", response_model=ProposalResponse)
async def capture_audio(
    file: UploadFile = File(...),
    user_timezone: str = Form("Asia/Kolkata"),
    language: Optional[str] = Form(None),
    mock_text: Optional[str] = Form(None)
):
    """
    Receives recorded audio, transcribes via ASR (Gnani Prisma with Sarvam Saaras failover),
    extracts structured intent, and creates a pending proposal.
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
    
    proposal = store.create_proposal_from_extraction(
        user_id=store.default_user_id,
        extraction=extraction
    )
    proposal = await apply_user_display_language_preference(store.default_user_id, proposal)
    return proposal

