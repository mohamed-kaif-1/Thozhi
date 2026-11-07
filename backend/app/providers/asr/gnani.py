import httpx
import logging
from typing import Optional
from backend.app.providers.asr.base import BaseASRProvider, ASRTranscriptionResult
from backend.app.core.config import settings
from backend.app.core.errors import ASRProviderException

logger = logging.getLogger(__name__)

class GnaniPrismaProvider(BaseASRProvider):
    """
    Core Primary ASR Provider: Gnani AI Prisma v3.
    Target endpoint: https://api.vachana.ai/stt/v3
    Primary Auth Header: X-API-Key-ID
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.GNANI_API_KEY
        self.base_url = (base_url or settings.GNANI_API_URL).rstrip("/")

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        language: Optional[str] = None
    ) -> ASRTranscriptionResult:
        if not self.api_key:
            raise ASRProviderException(
                detail="GNANI_API_KEY is not set in .env. Gnani Prisma v3 is the primary speech recognition engine for THOZHI.",
                provider="gnani"
            )

        # Normalize language to Gnani Prisma supported codes:
        # Supported: as-IN, bn-IN, en-IN, gu-IN, hi-IN, indic-auto, kn-IN, ml-IN, mr-IN, pa-IN, ta-IN, te-IN
        lang_lower = (language or "").lower()
        if lang_lower in ("en", "en-in", "en-us", "english"):
            language_code = "en-IN"
        elif lang_lower in ("ta", "ta-in", "tamil"):
            language_code = "ta-IN"
        else:
            language_code = "indic-auto"

        # Determine file extension and encoding
        file_ext = "wav"
        encoding = "LINEAR16"
        if "ogg" in content_type:
            file_ext = "ogg"
            encoding = "OGG"
        elif "flac" in content_type:
            file_ext = "flac"
            encoding = "FLAC"
        elif "mp3" in content_type:
            file_ext = "mp3"
            encoding = "MP3"
        elif "mp4" in content_type or "m4a" in content_type or "aac" in content_type:
            file_ext = "m4a"
            encoding = "AAC"

        headers = {
            "X-API-Key-ID": self.api_key,
            "token": self.api_key, # Secondary compatibility header
        }
        
        # Gnani Prisma v3 STT requires 'audio_file' as the multipart field name
        files = {
            "audio_file": (f"recording.{file_ext}", audio_bytes, content_type)
        }
        
        data = {
            "model": "prisma-v3.0",
            "language_code": language_code,
            "encoding": encoding,
            "sampling_rate": 16000
        }

        logger.info(f"Submitting audio ({len(audio_bytes)} bytes, {content_type}, lang={language_code}) to Gnani Prisma v3 STT...")

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    f"{self.base_url}/stt/v3",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    logger.error(f"Gnani Prisma returned HTTP {response.status_code}: {response.text}")
                    raise ASRProviderException(
                        f"Gnani Prisma API returned {response.status_code}: {response.text}",
                        provider="gnani",
                        status_code=response.status_code
                    )

                payload = response.json()
                transcript = ""
                if isinstance(payload, dict):
                    transcript = payload.get("transcript") or payload.get("text") or ""
                    data_val = payload.get("data")
                    if not transcript and isinstance(data_val, dict):
                        transcript = data_val.get("transcript") or data_val.get("text") or ""
                    elif not transcript and isinstance(data_val, str):
                        transcript = data_val
                    elif not transcript and isinstance(payload.get("results"), list) and len(payload["results"]) > 0:
                        first_res = payload["results"][0]
                        if isinstance(first_res, dict):
                            transcript = first_res.get("transcript") or first_res.get("text") or ""
                elif isinstance(payload, str):
                    transcript = payload
                
                confidence = float(payload.get("confidence", 0.95)) if isinstance(payload, dict) else 0.95
                detected_lang = payload.get("detected_language_code") or payload.get("language_code") or language_code
                
                logger.info(f"Gnani Prisma v3 transcription succeeded: '{transcript[:60]}...'")

                return ASRTranscriptionResult(
                    transcript_text=transcript.strip(),
                    detected_language=detected_lang,
                    confidence_score=confidence,
                    provider_name="Gnani AI Prisma v3"
                )
        except httpx.RequestError as exc:
            logger.error(f"Network failure connecting to Gnani Prisma v3 at {self.base_url}: {exc}")
            raise ASRProviderException(
                f"Failed to connect to Gnani Prisma v3: {str(exc)}",
                provider="gnani"
            )
