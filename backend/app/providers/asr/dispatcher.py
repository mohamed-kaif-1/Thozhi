import logging
from typing import Optional
from backend.app.providers.asr.base import BaseASRProvider, ASRTranscriptionResult
from backend.app.providers.asr.gnani import GnaniPrismaProvider
from backend.app.providers.asr.sarvam import SarvamSaarasProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class ASRDispatcher:
    """
    Dispatcher managing automatic failover between Gnani Prisma v3 and Sarvam Saaras v3.
    Includes mock fallback for offline development and local automated test suites.
    """
    def __init__(self):
        self.gnani = GnaniPrismaProvider()
        self.sarvam = SarvamSaarasProvider()

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        mock_fallback_text: Optional[str] = None
    ) -> ASRTranscriptionResult:
        # 1. Try Gnani Prisma if key configured
        if settings.GNANI_API_KEY:
            try:
                logger.info("Attempting transcription via Gnani Prisma v3...")
                return await self.gnani.transcribe(audio_bytes, content_type)
            except Exception as e:
                logger.warning(f"Gnani Prisma failed: {e}. Initiating failover to Sarvam Saaras v3...")

        # 2. Try Sarvam Saaras failover if key configured
        if settings.SARVAM_API_KEY:
            try:
                logger.info("Attempting transcription via Sarvam Saaras v3 failover...")
                return await self.sarvam.transcribe(audio_bytes, content_type)
            except Exception as e:
                logger.error(f"Sarvam Saaras failed: {e}.")

        # 3. Development / Test Mock Fallback
        if mock_fallback_text or settings.ENVIRONMENT in ("development", "test"):
            logger.info("Returning development mock transcription result.")
            return ASRTranscriptionResult(
                transcript_text=mock_fallback_text or "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum.",
                detected_language="Tanglish",
                confidence_score=0.95,
                provider_name="Mock Development Fallback ASR"
            )

        raise RuntimeError("No ASR provider succeeded and no mock text was provided.")

