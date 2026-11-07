from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ItemTypeEnum(str, Enum):
    TASK = "TASK"
    COMMITMENT = "COMMITMENT"
    IDEA = "IDEA"
    WISH = "WISH"
    CONDITIONAL_INTENTION = "CONDITIONAL_INTENTION"
    QUESTION = "QUESTION"
    REMINDER = "REMINDER"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    INFORMATIONAL = "INFORMATIONAL"

class PriorityEnum(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"
    BACKBURNER = "BACKBURNER"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val = value.strip().upper()
            mapping = {
                "P1": cls.P1_CRITICAL,
                "CRITICAL": cls.P1_CRITICAL,
                "P1_CRITICAL": cls.P1_CRITICAL,
                "P2": cls.P2_MEDIUM,
                "MEDIUM": cls.P2_MEDIUM,
                "P2_MEDIUM": cls.P2_MEDIUM,
                "P3": cls.P3_LOW,
                "LOW": cls.P3_LOW,
                "P3_LOW": cls.P3_LOW,
                "P4": cls.BACKBURNER,
                "BACKBURNER": cls.BACKBURNER,
            }
            if val in mapping:
                return mapping[val]
        return None

class ClarificationQuestion(BaseModel):
    id: str = Field(description="Unique question id e.g. 'clar_1'")
    target_item_temp_id: Optional[str] = Field(default=None, description="temp_id of item requiring clarification")
    question_text: str = Field(description="Natural conversational clarification prompt in user's language")
    suggested_options: List[str] = Field(default_factory=list, description="Quick tap options")
    field_to_update: Optional[str] = Field(default=None, description="e.g. 'estimated_duration_min', 'priority'")

class ProposedItemExtraction(BaseModel):
    temp_id: str = Field(description="Unique incremental string id (e.g., 'item_1')")
    item_type: ItemTypeEnum = Field(description="Classification of the sentence intention")
    proposed_title: str = Field(description="Clear, actionable imperative task title in English")
    description: Optional[str] = Field(default=None, description="Additional context or notes")
    source_expression: str = Field(description="Exact substring from input corresponding to this item")
    deadline_expression: Optional[str] = Field(default=None, description="Raw temporal expression extracted from text")
    normalized_deadline_iso: Optional[str] = Field(default=None, description="ISO-8601 timestamp anchored to the current system date")
    estimated_duration_min: Optional[int] = Field(default=None, description="Estimated duration in minutes, or null if unknown")
    duration_source: str = Field(default="MODEL_ESTIMATE", description="'USER_EXPLICIT', 'MODEL_ESTIMATE', or 'UNKNOWN'")
    priority: PriorityEnum = Field(default=PriorityEnum.P2_MEDIUM)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    uncertainty_flags: List[str] = Field(default_factory=list, description="Flags like 'UNKNOWN_DEADLINE', 'AMBIGUOUS_TIME'")
    dependencies: List[str] = Field(default_factory=list, description="List of temp_ids that must complete before this task")
    condition_trigger: Optional[str] = Field(default=None, description="Trigger condition if item_type is CONDITIONAL_INTENTION")

class ExtractionResponse(BaseModel):
    intent_summary: str = Field(description="One-sentence English summary of the user's mental monologue")
    detected_language: str = Field(default="Tanglish", description="e.g. 'Tanglish', 'English', 'Tamil'")
    transcript_text: Optional[str] = Field(default=None, description="The raw transcribed speech text or input text")
    extracted_items: List[ProposedItemExtraction] = Field(default_factory=list)
    clarifications: List[ClarificationQuestion] = Field(default_factory=list)
