from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from backend.app.schemas.proposal import ProposalResponse

class CaptureCreate(BaseModel):
    user_id: Optional[UUID] = None
    input_type: str = Field(default="TEXT", description="'VOICE' or 'TEXT'")
    transcript_text: str
    original_transcript: Optional[str] = None
    translated_transcript: Optional[str] = None
    detected_language: str = "Tanglish"
    processing_status: str = "PROCESSED"
    provider_metadata: Optional[dict] = Field(default_factory=dict)

class CaptureResponse(BaseModel):
    id: UUID
    user_id: UUID
    input_type: str
    transcript_text: str
    original_transcript: Optional[str] = None
    translated_transcript: Optional[str] = None
    detected_language: str = "Tanglish"
    processing_status: str = "PROCESSED"
    lifecycle_status: str = "PENDING_REVIEW"
    created_at: datetime
    proposal_ids: List[UUID] = Field(default_factory=list)
    proposals: List[ProposalResponse] = Field(default_factory=list)
    proposal_count: int = 0
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
