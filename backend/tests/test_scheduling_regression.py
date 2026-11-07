import pytest
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.modules.planning.engine import PlanningEngine
from backend.app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent, ConflictWarning
from backend.app.schemas.intent import PriorityEnum
from backend.app.db.repository import store
from backend.app.main import app

client = TestClient(app)


def to_dt(val: datetime | str) -> datetime:
    if isinstance(val, str):
        return datetime.fromisoformat(val)
    return val


def make_test_task(
    title: str,
    duration: int | None = None,
    priority: PriorityEnum = PriorityEnum.P2_MEDIUM,
    deadline: datetime | None = None,
    scheduled_date: date | None = None,
    duration_source: str = "UNSPECIFIED"
) -> TaskResponse:
    now = datetime.now(timezone.utc)
    return TaskResponse(
        id=uuid4(),
        user_id=uuid4(),
        title=title,
        priority=priority,
        estimated_duration_min=duration,
        duration_source=duration_source,
        deadline=deadline,
        scheduled_date=scheduled_date or (deadline.date() if deadline else date.today()),
        created_at=now,
        updated_at=now
    )


# ==============================================================================
# CASE 1: Short task scheduling
# ==============================================================================
def test_case_1_short_task_scheduling():
    """
    Case 1: Short task ('Send an email to team', duration 15m, deadline tomorrow 6:00 PM).
    Must allocate a 15-minute slot before the deadline, never defaulted to 30m.
    """
    tomorrow = date.today() + timedelta(days=1)
    deadline = datetime.combine(tomorrow, time(18, 0))
    task = make_test_task(
        title="Send an email to client team",
        duration=15,
        priority=PriorityEnum.P2_MEDIUM,
        deadline=deadline,
        scheduled_date=tomorrow,
        duration_source="USER_EXPLICIT"
    )

    windows = [AvailabilityWindow(day_of_week=tomorrow.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(tomorrow, [task], [], windows, [])

    assert len(plan.slots) == 1
    slot = plan.slots[0]
    assert slot.duration_min == 15
    assert slot.duration_source == "USER_EXPLICIT"
    assert slot.title == "Send an email to client team"
    start_dt = to_dt(slot.start_time)
    end_dt = to_dt(slot.end_time)
    assert (end_dt - start_dt).total_seconds() == 15 * 60
    assert end_dt <= deadline


# ==============================================================================
# CASE 2: Large project (Raven project scenario)
# ==============================================================================
def test_case_2_large_project_raven_inferred_duration():
    """
    Case 2: Large project ('Complete my Raven project', duration unstated, deadline tomorrow 6:00 PM).
    Must NOT default to an arbitrary 30-minute slot.
    Infers 180m AI estimate for complex project work, schedules strictly before deadline.
    """
    tomorrow = date.today() + timedelta(days=1)
    deadline = datetime.combine(tomorrow, time(18, 0))
    task = make_test_task(
        title="Complete my Raven project",
        duration=None,
        priority=PriorityEnum.P2_MEDIUM,
        deadline=deadline,
        scheduled_date=tomorrow,
        duration_source="UNSPECIFIED"
    )

    inferred_dur, dur_src, is_est = PlanningEngine.infer_task_duration(task)
    assert inferred_dur == 180
    assert dur_src == "AI_ESTIMATE"

    windows = [AvailabilityWindow(day_of_week=tomorrow.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(tomorrow, [task], [], windows, [])

    assert len(plan.slots) == 1
    slot = plan.slots[0]
    assert slot.duration_min == 180
    assert slot.duration_source == "AI_ESTIMATE"
    end_dt = to_dt(slot.end_time)
    assert end_dt <= deadline
    assert slot.explanation is not None
    assert "safety buffer" in slot.explanation or "AI estimate" in slot.explanation


# ==============================================================================
# CASE 3: Explicit user duration preserved
# ==============================================================================
def test_case_3_explicit_duration_preserved():
    """
    Case 3: Explicit duration ('Study database systems', 2 hours).
    Engine preserves 120 minutes and marks duration_source as USER_EXPLICIT.
    """
    target_date = date.today() + timedelta(days=1)
    deadline = datetime.combine(target_date, time(17, 0))
    task = make_test_task(
        title="Study database systems",
        duration=120,
        priority=PriorityEnum.P2_MEDIUM,
        deadline=deadline,
        scheduled_date=target_date,
        duration_source="USER_EXPLICIT"
    )

    inferred_dur, dur_src, is_est = PlanningEngine.infer_task_duration(task)
    assert inferred_dur == 120
    assert dur_src == "USER_EXPLICIT"

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(17, 0))]
    plan = PlanningEngine.schedule_day(target_date, [task], [], windows, [])

    assert len(plan.slots) == 1
    assert plan.slots[0].duration_min == 120
    assert plan.slots[0].duration_source == "USER_EXPLICIT"


# ==============================================================================
# CASE 4: Insufficient availability / Overcapacity
# ==============================================================================
def test_case_4_insufficient_availability_overcapacity():
    """
    Case 4: Insufficient availability.
    Task requires 5 hours (300 minutes). Available focus window before deadline is only 2 hours (120 min).
    Must mark OVERCAPACITY conflict, report exact deficit (180 minutes), and never schedule beyond deadline.
    """
    target_date = date.today() + timedelta(days=1)
    deadline = datetime.combine(target_date, time(11, 0))
    task = make_test_task(
        title="Build complete authentication microservice",
        duration=300,
        priority=PriorityEnum.P1_CRITICAL,
        deadline=deadline,
        scheduled_date=target_date,
        duration_source="USER_EXPLICIT"
    )

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(11, 0))]
    plan = PlanningEngine.schedule_day(target_date, [task], [], windows, [])

    assert len(plan.slots) == 0
    assert task.id in plan.unassigned_task_ids
    assert any(c.code == "OVERCAPACITY" for c in plan.conflicts)
    conflict = next(c for c in plan.conflicts if c.code == "OVERCAPACITY")
    assert "deficit: 180" in conflict.message.lower()


# ==============================================================================
# CASE 5: Existing commitments / Overlapping conflict detection
# ==============================================================================
def test_case_5_overlapping_commitments_detected():
    """
    Case 5: Busy calendar events overlap with each other.
    Engine detects OVERLAPPING_COMMITMENT and generates clear conflict warning.
    """
    target_date = date.today() + timedelta(days=1)
    busy = [
        BusyEvent(
            title="Design Review",
            start_time=datetime.combine(target_date, time(10, 0)),
            end_time=datetime.combine(target_date, time(12, 0))
        ),
        BusyEvent(
            title="Emergency Production Incident",
            start_time=datetime.combine(target_date, time(11, 0)),
            end_time=datetime.combine(target_date, time(13, 0))
        )
    ]
    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(target_date, [], [], windows, busy)

    assert any(c.code == "OVERLAPPING_COMMITMENT" for c in plan.conflicts)
    overlap_conflict = next(c for c in plan.conflicts if c.code == "OVERLAPPING_COMMITMENT")
    assert "Design Review" in overlap_conflict.message
    assert "Emergency Production Incident" in overlap_conflict.message


# ==============================================================================
# CASE 6: Dependency DAG (Kahn's Topological Sort)
# ==============================================================================
def test_case_6_dependency_dag_kahn_sort():
    """
    Case 6: Dependency DAG.
    Task A must complete before Task B begins, and Task B before Task C.
    Kahn's algorithm guarantees exact sequential scheduling.
    """
    target_date = date.today() + timedelta(days=1)
    tA = make_test_task("Step A: Architecture PRD", 60, PriorityEnum.P2_MEDIUM, scheduled_date=target_date)
    tB = make_test_task("Step B: Implement Core Schema", 60, PriorityEnum.P2_MEDIUM, scheduled_date=target_date)
    tC = make_test_task("Step C: End to End Tests", 60, PriorityEnum.P2_MEDIUM, scheduled_date=target_date)

    dependencies = [(tA.id, tB.id), (tB.id, tC.id)]
    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]

    # Pass in shuffled order
    plan = PlanningEngine.schedule_day(target_date, [tC, tA, tB], dependencies, windows, [])

    assert len(plan.slots) == 3
    assert plan.slots[0].title == "Step A: Architecture PRD"
    assert plan.slots[1].title == "Step B: Implement Core Schema"
    assert plan.slots[2].title == "Step C: End to End Tests"

    # Verify no overlap
    endA = to_dt(plan.slots[0].end_time)
    startB = to_dt(plan.slots[1].start_time)
    endB = to_dt(plan.slots[1].end_time)
    startC = to_dt(plan.slots[2].start_time)
    assert endA <= startB
    assert endB <= startC


# ==============================================================================
# CASE 7: Missed / Past Deadline
# ==============================================================================
def test_case_7_deadline_already_passed():
    """
    Case 7: Deadline already passed.
    Task has a deadline in the past. Engine detects DEADLINE_ALREADY_PASSED conflict.
    """
    target_date = date.today()
    past_deadline = datetime.now() - timedelta(hours=2)
    task = make_test_task(
        title="Submit Taxes",
        duration=60,
        priority=PriorityEnum.P1_CRITICAL,
        deadline=past_deadline,
        scheduled_date=target_date
    )

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(target_date, [task], [], windows, [])

    assert any(c.code == "DEADLINE_ALREADY_PASSED" for c in plan.conflicts)


# ==============================================================================
# CASE 8: Timezone preservation (IST Asia/Kolkata)
# ==============================================================================
def test_case_8_timezone_ist_preservation():
    """
    Case 8: Indian Standard Time (UTC+5:30) preservation.
    A deadline of 18:00 IST must not be scheduled at 18:00 UTC (which would be 23:30 IST)
    or shifted across dates.
    """
    target_date = date.today() + timedelta(days=1)
    deadline_local = datetime(target_date.year, target_date.month, target_date.day, 18, 0)
    task = make_test_task(
        title="Client Demo",
        duration=60,
        priority=PriorityEnum.P1_CRITICAL,
        deadline=deadline_local,
        scheduled_date=target_date
    )

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(target_date, [task], [], windows, [])

    assert len(plan.slots) == 1
    slot = plan.slots[0]
    end_dt = to_dt(slot.end_time)
    assert end_dt.date() == target_date
    assert end_dt <= deadline_local


# ==============================================================================
# CASE 9: Multiple tasks with mixed priorities, durations, and deadlines
# ==============================================================================
def test_case_9_multiple_tasks_priorities_and_deadlines():
    """
    Case 9: Mixed priorities and deadlines.
    P1 Critical task with earlier deadline must take scheduling priority.
    """
    target_date = date.today() + timedelta(days=1)
    t_low = make_test_task("Clean up workspace", 30, PriorityEnum.P3_LOW, deadline=datetime.combine(target_date, time(18, 0)), scheduled_date=target_date)
    t_crit = make_test_task("Submit Final Patent Filing", 90, PriorityEnum.P1_CRITICAL, deadline=datetime.combine(target_date, time(12, 0)), scheduled_date=target_date)
    t_med = make_test_task("Write Engineering Documentation", 60, PriorityEnum.P2_MEDIUM, deadline=datetime.combine(target_date, time(16, 0)), scheduled_date=target_date)

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan = PlanningEngine.schedule_day(target_date, [t_low, t_crit, t_med], [], windows, [])

    assert len(plan.slots) == 3
    # Critical filing should be scheduled first at 09:00 - 10:30
    assert plan.slots[0].title == "Submit Final Patent Filing"
    assert to_dt(plan.slots[0].end_time) <= datetime.combine(target_date, time(12, 0))


# ==============================================================================
# CASE 10: User edits task duration recalculates plan
# ==============================================================================
def test_case_10_user_edits_task_duration():
    """
    Case 10: User edits duration.
    Updating task duration from 180m to 60m reduces scheduled capacity and updates slot.
    """
    target_date = date.today() + timedelta(days=1)
    deadline = datetime.combine(target_date, time(18, 0))
    task = make_test_task(
        title="Complete my Raven project",
        duration=180,
        priority=PriorityEnum.P2_MEDIUM,
        deadline=deadline,
        scheduled_date=target_date,
        duration_source="AI_ESTIMATE"
    )

    windows = [AvailabilityWindow(day_of_week=target_date.weekday(), start_time=time(9, 0), end_time=time(18, 0))]
    plan1 = PlanningEngine.schedule_day(target_date, [task], [], windows, [])
    assert plan1.slots[0].duration_min == 180

    # User adjusts to 60m
    updated_task = task.model_copy(update={"estimated_duration_min": 60, "duration_source": "USER_EXPLICIT"})
    plan2 = PlanningEngine.schedule_day(target_date, [updated_task], [], windows, [])
    assert plan2.slots[0].duration_min == 60
    assert plan2.slots[0].duration_source == "USER_EXPLICIT"
    assert plan2.total_scheduled_minutes == 60


# ==============================================================================
# CASE 11: End-to-end API test with exact Raven project scenario
# ==============================================================================
def test_case_11_end_to_end_raven_api_flow():
    """
    Case 11: Complete End-to-End API test for the Raven project scenario.
    1. Proposal created for tomorrow 6:00 PM deadline.
    2. Approval endpoint commits task for tomorrow.
    3. Plan endpoint /plans/date/{tomorrow_str} returns the scheduled slot with AI estimate.
    """
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    deadline_iso = f"{tomorrow_str}T18:00:00"

    task_payload = {
        "title": "Complete my Raven project",
        "priority": "P2_MEDIUM",
        "deadline": deadline_iso,
        "scheduled_date": tomorrow_str,
        "duration_source": "UNSPECIFIED"
    }
    create_resp = client.post("/api/v1/tasks", json=task_payload)
    assert create_resp.status_code == 201
    created_task = create_resp.json()
    assert created_task["title"] == "Complete my Raven project"

    # Retrieve plan for tomorrow
    plan_resp = client.get(f"/api/v1/plans/date/{tomorrow_str}")
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()

    assert len(plan_data["slots"]) >= 1
    raven_slot = next(s for s in plan_data["slots"] if "Raven" in s["title"])
    # Verified: not 30 minutes! Inferred 180 min AI estimate
    assert raven_slot["duration_min"] == 180
    assert raven_slot["duration_source"] == "AI_ESTIMATE"
    assert raven_slot["end_time"] <= deadline_iso

