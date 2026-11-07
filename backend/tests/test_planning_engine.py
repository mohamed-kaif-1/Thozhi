import pytest
from datetime import date, datetime, time, timezone
from uuid import uuid4

from backend.app.modules.planning.engine import PlanningEngine
from backend.app.schemas.task import TaskResponse
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent
from backend.app.schemas.intent import PriorityEnum
from backend.app.core.errors import SchedulingCycleException

def make_task(title: str, duration: int, priority: PriorityEnum = PriorityEnum.P2_MEDIUM) -> TaskResponse:
    now = datetime.now(timezone.utc)
    return TaskResponse(
        id=uuid4(),
        user_id=uuid4(),
        title=title,
        priority=priority,
        estimated_duration_min=duration,
        scheduled_date=date.today(),
        created_at=now,
        updated_at=now
    )

def test_topological_sort_linear_dependency():
    t1 = make_task("Step 1: Draft Outline", 30)
    t2 = make_task("Step 2: Write Code", 60)
    t3 = make_task("Step 3: Run Tests", 20)
    
    # t1 -> t2 -> t3
    dependencies = [(t1.id, t2.id), (t2.id, t3.id)]
    
    # Provide tasks in reverse order
    tasks = [t3, t2, t1]
    sorted_tasks = PlanningEngine.topological_sort(tasks, dependencies)
    
    order = [t.title for t in sorted_tasks]
    assert order == ["Step 1: Draft Outline", "Step 2: Write Code", "Step 3: Run Tests"]

def test_topological_sort_cycle_detection():
    t1 = make_task("Task A", 30)
    t2 = make_task("Task B", 30)
    
    # Cycle: A depends on B and B depends on A
    dependencies = [(t1.id, t2.id), (t2.id, t1.id)]
    
    with pytest.raises(SchedulingCycleException) as exc_info:
        PlanningEngine.topological_sort([t1, t2], dependencies)
        
    assert "Cyclic dependency detected" in str(exc_info.value)

def test_interval_arithmetic_busy_block_subtraction():
    target_date = date(2026, 11, 10) # Tuesday (weekday 1)
    
    # Work window: 09:00 to 18:00 (540 minutes)
    windows = [
        AvailabilityWindow(day_of_week=1, start_time=time(9, 0), end_time=time(18, 0))
    ]
    
    # Busy blocks:
    # 1. 10:30 to 11:30 (Team Standup & Sync)
    # 2. 13:00 to 14:00 (Lunch)
    busy = [
        BusyEvent(
            title="Team Standup",
            start_time=datetime(2026, 11, 10, 10, 30),
            end_time=datetime(2026, 11, 10, 11, 30)
        ),
        BusyEvent(
            title="Lunch",
            start_time=datetime(2026, 11, 10, 13, 0),
            end_time=datetime(2026, 11, 10, 14, 0)
        )
    ]
    
    free_slots = PlanningEngine.calculate_free_intervals(target_date, windows, busy)
    
    # Expected free slots:
    # 1. 09:00 - 10:30 (90 min)
    # 2. 11:30 - 13:00 (90 min)
    # 3. 14:00 - 18:00 (240 min)
    # Total = 420 minutes
    assert len(free_slots) == 3
    assert free_slots[0] == (datetime(2026, 11, 10, 9, 0), datetime(2026, 11, 10, 10, 30))
    assert free_slots[1] == (datetime(2026, 11, 10, 11, 30), datetime(2026, 11, 10, 13, 0))
    assert free_slots[2] == (datetime(2026, 11, 10, 14, 0), datetime(2026, 11, 10, 18, 0))
    
    total_minutes = sum((s[1] - s[0]).total_seconds() // 60 for s in free_slots)
    assert total_minutes == 420

def test_schedule_day_placement_and_capacity():
    target_date = date(2026, 11, 10)
    windows = [
        AvailabilityWindow(day_of_week=1, start_time=time(9, 0), end_time=time(13, 0)) # 240 min window
    ]
    busy = []
    
    t1 = make_task("Deep Focus Coding", 120, PriorityEnum.P1_CRITICAL)
    t2 = make_task("Code Review", 60, PriorityEnum.P2_MEDIUM)
    t3 = make_task("Documentation", 90, PriorityEnum.P3_LOW) # Total = 270 min > 240 min
    
    plan = PlanningEngine.schedule_day(
        target_date=target_date,
        tasks=[t1, t2, t3],
        dependencies=[],
        windows=windows,
        busy_events=busy
    )
    
    assert plan.total_available_minutes == 240
    assert len(plan.slots) == 2 # t1 (120m) and t2 (60m) fit (total 180m); t3 (90m) cannot fit in remaining 60m
    assert plan.total_scheduled_minutes == 180
    assert t3.id in plan.unassigned_task_ids
    assert any(c.code == "OVERCAPACITY" for c in plan.conflicts)

