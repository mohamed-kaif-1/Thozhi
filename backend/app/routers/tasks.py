from fastapi import APIRouter, Query, status, Depends
from typing import List, Optional
from uuid import UUID
from datetime import date

from backend.app.db.repository import store
from backend.app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from backend.app.schemas.intent import PriorityEnum
from backend.app.core.auth import get_current_user, AuthenticatedUser
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    current_user: AuthenticatedUser = Depends(get_current_user),
    target_date: Optional[date] = Query(None),
    task_status: Optional[str] = Query(None, alias="status"),
    priority: Optional[PriorityEnum] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Returns tasks for the authenticated user with filtering by date, status, priority, and text search.
    """
    tasks = store.list_tasks(user_id=current_user.id, target_date=target_date, user_token=current_user.token)

    if task_status:
        tasks = [t for t in tasks if t.status.upper() == task_status.upper()]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if search and search.strip():
        q = search.strip().lower()
        tasks = [t for t in tasks if q in t.title.lower() or (t.description and q in t.description.lower())]

    return tasks

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Direct user task creation for the authenticated user with duplicate title prevention on same scheduled date.
    """
    return store.create_task(user_id=current_user.id, task_create=task_create, user_token=current_user.token)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    task = store.get_task(task_id=task_id, user_id=current_user.id, user_token=current_user.token)
    if not task:
        raise ResourceNotFoundException(detail=f"Task {task_id} not found", resource_type="task", resource_id=str(task_id))
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update: TaskUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return store.update_task(task_id=task_id, task_update=update, user_id=current_user.id, user_token=current_user.token)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    store.delete_task(task_id=task_id, user_id=current_user.id, user_token=current_user.token)
    return None

@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return store.complete_task(task_id=task_id, user_id=current_user.id, user_token=current_user.token)

@router.post("/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(
    task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return store.reopen_task(task_id=task_id, user_id=current_user.id, user_token=current_user.token)

@router.post("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_201_CREATED)
async def add_dependency(
    task_id: UUID,
    depends_on_task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Enforces prerequisite constraint with automatic DAG cycle detection for the authenticated user.
    """
    return store.add_task_dependency(task_id=task_id, depends_on_task_id=depends_on_task_id, user_id=current_user.id, user_token=current_user.token)

@router.delete("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    task_id: UUID,
    depends_on_task_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    store.delete_task_dependency(task_id=task_id, depends_on_task_id=depends_on_task_id, user_id=current_user.id, user_token=current_user.token)
    return None
