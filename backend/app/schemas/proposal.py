from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from backend.app.schemas.intent import ItemTypeEnum, PriorityEnum, ProposedItemExtraction, ClarificationQuestion

class ProposalClarificationAnswer(BaseModel):
    question_id: str
    answer: str
    selected_option: Optional[str] = None
    resolved_deadline_iso: Optional[str] = None
    resolved_duration_min: Optional[int] = None
    resolved_item_type: Optional[ItemTypeEnum] = None

class ProposalClarificationRequest(BaseModel):
    answers: List[ProposalClarificationAnswer]

class ProposalItemPatch(BaseModel):
    proposed_title: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[ItemTypeEnum] = None
    estimated_duration_min: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    normalized_deadline: Optional[datetime] = None

class ProposalItemUpdate(BaseModel):
    id: UUID
    proposed_title: Optional[str] = None
    estimated_duration_min: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    normalized_deadline_iso: Optional[str] = None
    scheduled_date: Optional[str] = None
    is_approved: bool = True
    rejection_reason: Optional[str] = None

ProposalItemDecision = ProposalItemUpdate

class ProposalApproveRequest(BaseModel):
    idempotency_key: str = Field(description="Client-generated UUID or hash for replay protection")
    items: List[ProposalItemUpdate] = Field(description="List of decisions for each item")

class ProposalItemResponse(BaseModel):
    id: UUID
    proposal_id: UUID
    temp_id: str
    item_type: ItemTypeEnum
    proposed_title: str
    description: Optional[str] = None
    source_expression: str
    deadline_expression: Optional[str] = None
    normalized_deadline: Optional[datetime] = None
    estimated_duration_min: Optional[int] = None
    duration_source: str
    priority: PriorityEnum
    confidence_score: float
    uncertainty_flags: List[str] = Field(default_factory=list)
    condition_trigger: Optional[str] = None
    decision_state: str = "PENDING"
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProposalResponse(BaseModel):
    id: UUID
    user_id: UUID
    capture_id: Optional[UUID] = None
    transcript_text: Optional[str] = None
    intent_summary: str
    detected_language: str
    status: str
    created_at: datetime
    expires_at: datetime
    items: List[ProposalItemResponse] = Field(default_factory=list)
    clarifications: List[ClarificationQuestion] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ProposalApproveResponse(BaseModel):
    proposal_id: UUID
    approved_tasks_count: int
    rejected_items_count: int
    created_task_ids: List[UUID]
    message: str = "Decision recorded successfully. Tasks committed to schedule."
