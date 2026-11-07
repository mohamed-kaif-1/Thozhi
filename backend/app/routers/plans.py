from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from backend.app.modules.planning.engine import PlanningEngine
from backend.app.db.repository import store
from backend.app.schemas.plan import PlanGenerateRequest, PlanResponse, RescheduleSuggestion

router = APIRouter(prefix="/plans", tags=["Planning & Capacity Engine"])

class RescheduleApplyRequest(BaseModel):
    reschedules: List[RescheduleSuggestion]

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanGenerateRequest):
    """
    Executes Kahn's DAG topological sort and interval capacity bin-packing
    to build a realistic daily schedule without non-deterministic hallucinations.
    """
    user_id = store.default_user_id
    tasks = store.list_tasks(user_id=user_id, target_date=request.target_date)
    
    dependencies = [
        (UUID(str(d["depends_on_task_id"])), UUID(str(d["task_id"])))
        for d in store.task_dependencies
    ]
    windows = store.get_user_windows(user_id)
    busy_events = store.get_user_busy_events(user_id, request.target_date)
    
    plan = PlanningEngine.schedule_day(
        target_date=request.target_date,
        tasks=tasks,
        dependencies=dependencies,
        windows=windows,
        busy_events=busy_events
    )
    return plan

@router.get("/today", response_model=PlanResponse)
async def get_today_plan():
    """
    Quick helper for today's active schedule.
    """
    today = date.today()
    req = PlanGenerateRequest(target_date=today)
    return await generate_plan(req)

@router.get("/date/{target_date}", response_model=PlanResponse)
async def get_plan_for_date(target_date: date):
    """
    Helper for a specific target date schedule.
    """
    req = PlanGenerateRequest(target_date=target_date)
    return await generate_plan(req)

@router.post("/reschedule/apply", response_model=PlanResponse)
async def apply_reschedule(request: RescheduleApplyRequest):
    """
    Applies human-approved reschedule suggestions by updating task scheduled dates,
    then recalculates the plan for the origin date.
    """
    origin_date = None
    for sugg in request.reschedules:
        task = store.tasks.get(sugg.task_id)
        if task:
            origin_date = sugg.current_date
            task["scheduled_date"] = sugg.suggested_date
            from backend.app.db.repository import get_utc_now
            task["updated_at"] = get_utc_now()
            
    target = origin_date or date.today()
    return await generate_plan(PlanGenerateRequest(target_date=target))

