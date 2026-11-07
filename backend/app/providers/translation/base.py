from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, List

class TranslationResult(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    provider_name: str
    is_fallback: bool = False

class BaseTranslationProvider(ABC):
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str = "auto",
        target_language: str = "en"
    ) -> TranslationResult:
        """
        Translates text from source_language to target_language.
        Preserves numbers, punctuation, and structural invariants.
        """
        pass

    @abstractmethod
    async def translate_batch(
        self,
        texts: List[str],
        source_language: str = "auto",
        target_language: str = "en"
    ) -> List[TranslationResult]:
        """
        Translates multiple texts concurrently or in batch.
        """
        pass
