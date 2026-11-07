from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class MemoryCategoryEnum(str, Enum):
    WORKING_HOURS = "WORKING_HOURS"
    PLANNING_STYLE = "PLANNING_STYLE"
    LANGUAGE = "LANGUAGE"
    DURATION_PRIOR = "DURATION_PRIOR"
    CONTEXTUAL = "CONTEXTUAL"
    USER_PROFILE = "USER_PROFILE"

class MemoryPreferenceCreate(BaseModel):
    preference_key: str = Field(description="e.g., 'preferred_focus_start_time', 'technical_report_duration_prior'")
    category: MemoryCategoryEnum = Field(default=MemoryCategoryEnum.PLANNING_STYLE)
    preference_value: Dict[str, Any] = Field(description="JSON value containing preference rules")
    description: Optional[str] = Field(default=None, description="Human readable explanation of what is remembered")
    consent_level: str = Field(default="EXPLICIT_CONSENT", description="'EXPLICIT_CONSENT', 'USER_APPROVED'")

class MemoryPreferencePatch(BaseModel):
    preference_value: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class MemoryPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    category: MemoryCategoryEnum = MemoryCategoryEnum.PLANNING_STYLE
    preference_key: str
    preference_value: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True
    consent_level: str = "EXPLICIT_CONSENT"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DurationPriorSuggestion(BaseModel):
    task_pattern: str
    suggested_duration_min: int
    historical_samples: int
    confidence: float
    rationale: str

class UserDataExportResponse(BaseModel):
    user_id: UUID
    exported_at: datetime
    tasks_count: int
    proposals_count: int
    preferences_count: int
    data: Dict[str, Any]

class DataPurgeResponse(BaseModel):
    user_id: UUID
    purged_at: datetime
    records_deleted: Dict[str, int]
    status: str = "PURGED_SOVEREIGN"

