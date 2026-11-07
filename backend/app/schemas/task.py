from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from backend.app.schemas.intent import PriorityEnum

class TaskDependencyResponse(BaseModel):
    id: UUID
    task_id: UUID
    depends_on_task_id: UUID

    model_config = ConfigDict(from_attributes=True)

class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    estimated_duration_min: Optional[int] = None
    duration_source: str = "UNSPECIFIED"
    actual_duration_min: Optional[int] = None
    deadline: Optional[datetime] = None
    scheduled_date: Optional[date] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: str = "PENDING"
    origin_proposal_item_id: Optional[UUID] = None
    source_language: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    dependencies: List[UUID] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    estimated_duration_min: Optional[int] = None
    duration_source: str = "UNSPECIFIED"
    deadline: Optional[datetime] = None
    scheduled_date: Optional[date] = None
    origin_proposal_item_id: Optional[UUID] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    estimated_duration_min: Optional[int] = None
    duration_source: Optional[str] = None
    deadline: Optional[datetime] = None
    scheduled_date: Optional[date] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: Optional[str] = None
