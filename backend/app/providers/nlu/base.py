from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from backend.app.schemas.intent import ExtractionResponse

class BaseNLUProvider(ABC):
    @abstractmethod
    async def extract_intent(
        self,
        transcript_text: str,
        reference_date: Optional[date] = None,
        user_timezone: str = "Asia/Kolkata"
    ) -> ExtractionResponse:
        """
        Parses raw multilingual transcript into structured task/commitment proposals.
        """
        pass

