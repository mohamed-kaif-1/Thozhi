import httpx
from backend.app.providers.asr.base import BaseASRProvider, ASRTranscriptionResult
from backend.app.core.config import settings
from backend.app.core.errors import ASRProviderException

class SarvamSaarasProvider(BaseASRProvider):
    """
    Failover ASR provider: Sarvam AI Saaras v3.
    Target endpoint: https://api.sarvam.ai/speech-to-text
    Auth header: api-subscription-key
    """
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = (base_url or settings.SARVAM_API_URL).rstrip("/")

    async def transcribe(self, audio_bytes: bytes, content_type: str = "audio/wav") -> ASRTranscriptionResult:
        if not self.api_key:
            raise ASRProviderException("SARVAM_API_KEY is not configured", provider="sarvam")

        headers = {
            "api-subscription-key": self.api_key
        }
        files = {
            "file": ("recording.wav", audio_bytes, content_type)
        }
        data = {
            "model": "saaras:v3",
            "language_code": "ta-IN",
            "with_diarization": "false"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/speech-to-text",
                    headers=headers,
                    files=files,
                    data=data
                )
                if response.status_code != 200:
                    raise ASRProviderException(
                        f"Sarvam API returned status {response.status_code}: {response.text}",
                        provider="sarvam",
                        status_code=response.status_code
                    )

                payload = response.json()
                transcript = payload.get("transcript", "")
                
                return ASRTranscriptionResult(
                    transcript_text=transcript.strip(),
                    detected_language=payload.get("language_code", "ta-IN"),
                    confidence_score=0.92,
                    provider_name="Sarvam Saaras v3"
                )
        except httpx.RequestError as exc:
            raise ASRProviderException(f"Network error connecting to Sarvam Saaras: {str(exc)}", provider="sarvam")

