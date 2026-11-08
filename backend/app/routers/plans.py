from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from backend.app.modules.planning.engine import PlanningEngine
from backend.app.db.repository import store
from backend.app.schemas.plan import PlanGenerateRequest, PlanResponse, RescheduleSuggestion
from backend.app.core.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/plans", tags=["Planning & Capacity Engine"])

class RescheduleApplyRequest(BaseModel):
    reschedules: List[RescheduleSuggestion]

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(
    request: PlanGenerateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Executes Kahn's DAG topological sort and interval capacity bin-packing
    to build a realistic daily schedule without non-deterministic hallucinations.
    Scoped strictly to the authenticated user.
    """
    user_id = current_user.id
    token = current_user.token
    tasks = store.list_tasks(user_id=user_id, target_date=request.target_date, user_token=token)

    deps_records = store.get_task_dependencies(user_id=user_id, user_token=token)
    dependencies = [
        (UUID(str(d["depends_on_task_id"])), UUID(str(d["task_id"])))
        for d in deps_records
    ]
    windows = store.get_user_windows(user_id, user_token=token)
    busy_events = store.get_user_busy_events(user_id, request.target_date, user_token=token)

    plan = PlanningEngine.schedule_day(
        target_date=request.target_date,
        tasks=tasks,
        dependencies=dependencies,
        windows=windows,
        busy_events=busy_events
    )
    return plan

@router.get("/today", response_model=PlanResponse)
async def get_today_plan(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Quick helper for today's active schedule for the authenticated user.
    """
    today = date.today()
    req = PlanGenerateRequest(target_date=today)
    return await generate_plan(req, current_user=current_user)

@router.get("/date/{target_date}", response_model=PlanResponse)
async def get_plan_for_date(
    target_date: date,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Helper for a specific target date schedule for the authenticated user.
    """
    req = PlanGenerateRequest(target_date=target_date)
    return await generate_plan(req, current_user=current_user)

@router.post("/reschedule/apply", response_model=PlanResponse)
async def apply_reschedule(
    request: RescheduleApplyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Applies human-approved reschedule suggestions by updating task scheduled dates,
    then recalculates the plan for the origin date.
    """
    from backend.app.schemas.task import TaskUpdate
    origin_date = None
    token = current_user.token
    for sugg in request.reschedules:
        task = store.get_task(task_id=sugg.task_id, user_id=current_user.id, user_token=token)
        if task:
            origin_date = sugg.current_date
            store.update_task(
                task_id=sugg.task_id,
                task_update=TaskUpdate(scheduled_date=sugg.suggested_date),
                user_id=current_user.id,
                user_token=token
            )

    target = origin_date or date.today()
    return await generate_plan(PlanGenerateRequest(target_date=target), current_user=current_user)
