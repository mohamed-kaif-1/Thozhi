from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, time
from uuid import UUID

class AvailabilityWindow(BaseModel):
    id: Optional[UUID] = None
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    label: str = "Focus Work"

class BusyEvent(BaseModel):
    id: Optional[UUID] = None
    title: str
    start_time: datetime
    end_time: datetime
    is_blocking: bool = True

class ScheduleSlot(BaseModel):
    task_id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    duration_min: int

class ConflictWarning(BaseModel):
    code: str
    severity: str = "WARNING"  # INFO, WARNING, CRITICAL
    message: str
    task_ids: List[UUID] = Field(default_factory=list)

class RescheduleSuggestion(BaseModel):
    task_id: UUID
    title: str
    current_date: date
    suggested_date: date
    reason: str

class PlanGenerateRequest(BaseModel):
    target_date: date
    task_ids: Optional[List[UUID]] = None  # None means all unscheduled/pending tasks for user
    allow_overtime: bool = False

class PlanResponse(BaseModel):
    id: Optional[UUID] = None
    plan_date: date
    status: str = "PROPOSED"
    total_available_minutes: int
    total_scheduled_minutes: int
    capacity_percentage: float
    summary_explanation: str = ""
    slots: List[ScheduleSlot] = Field(default_factory=list)
    conflicts: List[ConflictWarning] = Field(default_factory=list)
    unassigned_task_ids: List[UUID] = Field(default_factory=list)
    reschedule_suggestions: List[RescheduleSuggestion] = Field(default_factory=list)

