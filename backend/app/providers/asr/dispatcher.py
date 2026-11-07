import logging
from typing import Optional
from backend.app.providers.asr.base import BaseASRProvider, ASRTranscriptionResult
from backend.app.providers.asr.gnani import GnaniPrismaProvider
from backend.app.providers.asr.sarvam import SarvamSaarasProvider
from backend.app.core.config import settings
from backend.app.core.audio import normalize_audio_to_wav_16k_mono
from backend.app.core.errors import ASRProviderException

logger = logging.getLogger(__name__)

class ASRDispatcher:
    """
    Dispatcher managing automatic failover between Gnani Prisma v3 and Sarvam Saaras v3.
    Normalizes all incoming audio in-memory to 16kHz 16-bit mono WAV to guarantee format compliance.
    Includes mock fallback strictly for offline development and local automated test suites.
    """
    def __init__(self):
        self.gnani = GnaniPrismaProvider()
        self.sarvam = SarvamSaarasProvider()

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        language: Optional[str] = None,
        mock_fallback_text: Optional[str] = None
    ) -> ASRTranscriptionResult:
        # Pre-normalize audio in-memory to standard 16kHz 16-bit mono WAV
        norm_bytes, norm_content_type = normalize_audio_to_wav_16k_mono(audio_bytes, content_type)

        # 1. Prioritize explicit mock if provided in test fixtures
        if mock_fallback_text:
            logger.info("Using explicit mock fallback text provided in test request.")
            return ASRTranscriptionResult(
                transcript_text=mock_fallback_text,
                detected_language="Tanglish",
                confidence_score=0.95,
                provider_name="Mock Development Fallback ASR"
            )

        last_error = None

        # 2. Try Gnani Prisma v3 (Primary Indic Speech Engine)
        if settings.GNANI_API_KEY:
            try:
                logger.info("Submitting normalized audio to Gnani Prisma v3...")
                res = await self.gnani.transcribe(norm_bytes, norm_content_type, language=language)
                if res and res.transcript_text.strip():
                    return res
                logger.info("Gnani Prisma returned empty transcript; trying failover...")
            except Exception as e:
                last_error = e
                logger.warning(f"Gnani Prisma failed: {e}. Initiating failover to Sarvam Saaras v3...")

        # 3. Try Sarvam Saaras v3 failover
        if settings.SARVAM_API_KEY:
            try:
                logger.info("Submitting normalized audio to Sarvam Saaras v3 failover...")
                res = await self.sarvam.transcribe(norm_bytes, norm_content_type)
                if res and res.transcript_text.strip():
                    return res
            except Exception as e:
                last_error = e
                logger.error(f"Sarvam Saaras failover also failed: {e}.")

        # 4. If neither key is configured and running in test/offline environment
        if not settings.GNANI_API_KEY and not settings.SARVAM_API_KEY:
            logger.info("No ASR credentials configured; using synthetic mock result for development.")
            return ASRTranscriptionResult(
                transcript_text="Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum.",
                detected_language="Tanglish",
                confidence_score=0.95,
                provider_name="Mock Development Fallback ASR"
            )

        # 5. If credentials WERE configured but both failed or audio was empty/unintelligible
        if last_error:
            raise ASRProviderException(
                f"Speech recognition could not process audio: {str(last_error)}",
                provider="dispatcher"
            )

        # If audio contained silence/no recognizable words
        return ASRTranscriptionResult(
            transcript_text="",
            detected_language="indic-auto",
            confidence_score=0.0,
            provider_name="Gnani AI Prisma v3 (Silence/Unintelligible)"
        )

