from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional

class ASRTranscriptionResult(BaseModel):
    transcript_text: str
    detected_language: str
    confidence_score: float = 1.0
    audio_duration_seconds: float = 0.0
    provider_name: str

class BaseASRProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, content_type: str = "audio/wav") -> ASRTranscriptionResult:
        """
        Transcribes audio bytes to text.
        Zero disk storage requirement: operates strictly in-memory.
        """
        pass

