from fastapi import APIRouter, Query, status
from typing import List, Optional
from uuid import UUID
from datetime import date

from backend.app.db.repository import store
from backend.app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from backend.app.schemas.intent import PriorityEnum
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    target_date: Optional[date] = Query(None),
    task_status: Optional[str] = Query(None, alias="status"),
    priority: Optional[PriorityEnum] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Returns tasks for the authenticated user with filtering by date, status, priority, and text search.
    """
    user_id = store.default_user_id
    tasks = store.list_tasks(user_id=user_id, target_date=target_date)
    
    if task_status:
        tasks = [t for t in tasks if t.status.upper() == task_status.upper()]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if search and search.strip():
        q = search.strip().lower()
        tasks = [t for t in tasks if q in t.title.lower() or (t.description and q in t.description.lower())]
        
    return tasks

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_create: TaskCreate):
    """
    Direct user task creation with duplicate title prevention on same scheduled date.
    """
    return store.create_task(user_id=store.default_user_id, task_create=task_create)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID):
    task = store.tasks.get(task_id)
    if not task:
        raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
    deps = [d["depends_on_task_id"] for d in store.task_dependencies if d["task_id"] == task_id]
    return TaskResponse(**task, dependencies=deps)

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, update: TaskUpdate):
    task = store.tasks.get(task_id)
    if not task:
        raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
        
    update_data = update.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        task[key] = val
        
    from backend.app.db.repository import get_utc_now
    task["updated_at"] = get_utc_now()
    deps = [d["depends_on_task_id"] for d in store.task_dependencies if d["task_id"] == task_id]
    return TaskResponse(**task, dependencies=deps)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID):
    store.delete_task(task_id)
    return None

@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: UUID):
    return store.complete_task(task_id)

@router.post("/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: UUID):
    return store.reopen_task(task_id)

@router.post("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_201_CREATED)
async def add_dependency(task_id: UUID, depends_on_task_id: UUID):
    """
    Enforces prerequisite constraint with automatic DAG cycle detection.
    """
    return store.add_task_dependency(task_id, depends_on_task_id)

@router.delete("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(task_id: UUID, depends_on_task_id: UUID):
    store.delete_task_dependency(task_id, depends_on_task_id)
    return None

