import pytest
from datetime import datetime, date, time, timedelta, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.repository import store
from backend.app.schemas.intent import PriorityEnum, ItemTypeEnum, ExtractionResponse, ProposedItemExtraction, ClarificationQuestion
from backend.app.schemas.plan import AvailabilityWindow, BusyEvent

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    store.proposals.clear()
    store.proposal_items.clear()
    store.tasks.clear()
    store.task_dependencies.clear()
    store.idempotency_keys.clear()
    yield

def test_task_proposal_editing_before_approval():
    """
    Phase 5.1: Verify user can edit proposed item before approving it.
    """
    now = datetime.now(timezone.utc)
    extraction = ExtractionResponse(
        detected_language="ta-IN",
        intent_summary="Client meeting proposal",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-1",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Draft Client Sync Notes",
                description="Original description",
                source_expression="client meeting notes podanum",
                estimated_duration_min=30,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P3_LOW,
                confidence=0.88,
                uncertainty_flags=[]
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    item_id = prop.items[0].id

    # 1. Human modifies title, duration, and priority
    patch_res = client.patch(
        f"/api/v1/proposals/{prop.id}/items/{item_id}",
        json={
            "proposed_title": "Executive Client Sync & Strategy Deck",
            "estimated_duration_min": 60,
            "priority": "P1"
        }
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["proposed_title"] == "Executive Client Sync & Strategy Deck"
    assert patched["estimated_duration_min"] == 60
    assert patched["priority"] in ["P1", "P1_CRITICAL"]

    # 2. Approve the edited proposal
    approve_res = client.post(
        f"/api/v1/proposals/{prop.id}/approve",
        json={
            "idempotency_key": str(uuid4()),
            "items": [
                {
                    "id": str(item_id),
                    "is_approved": True,
                    "proposed_title": "Executive Client Sync & Strategy Deck",
                    "estimated_duration_min": 60,
                    "priority": "P1"
                }
            ]
        }
    )
    assert approve_res.status_code == 200
    created_id = approve_res.json()["created_task_ids"][0]

    # 3. Verify task entity has the edited values
    task_res = client.get(f"/api/v1/tasks/{created_id}")
    assert task_res.status_code == 200
    task_data = task_res.json()
    assert task_data["title"] == "Executive Client Sync & Strategy Deck"
    assert task_data["estimated_duration_min"] == 60
    assert task_data["priority"] in ["P1", "P1_CRITICAL"]

def test_clarification_loop_updates_proposal():
    """
    Phase 5.3: User answers a clarification question to resolve an uncertain deadline.
    """
    extraction = ExtractionResponse(
        detected_language="ta-IN",
        intent_summary="Assignment with uncertain deadline",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-assign",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Submit Math Assignment",
                description="Math paper",
                source_expression="assignment submit pannanum",
                estimated_duration_min=45,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P2_MEDIUM,
                confidence=0.7,
                uncertainty_flags=["UNCERTAIN_DEADLINE"]
            )
        ],
        clarifications=[
            ClarificationQuestion(
                id="q-deadline-1",
                target_item_temp_id="item-assign",
                question_text="When is this assignment due?",
                suggested_options=["Today 5 PM", "Tomorrow 9 AM"]
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)

    # Submit clarification answer
    resolved_iso = "2026-11-08T17:00:00Z"
    clarify_res = client.post(
        f"/api/v1/proposals/{prop.id}/clarify",
        json={
            "answers": [
                {
                    "question_id": "q-deadline-1",
                    "answer": "Today 5 PM",
                    "resolved_deadline_iso": resolved_iso,
                    "resolved_duration_min": 50
                }
            ]
        }
    )
    assert clarify_res.status_code == 200
    updated_prop = clarify_res.json()
    updated_item = updated_prop["items"][0]
    assert updated_item["estimated_duration_min"] == 50
    assert "UNCERTAIN_DEADLINE" not in updated_item["uncertainty_flags"]

def test_task_duplicate_prevention():
    """
    Phase 5.4: Attempting to create duplicate active task on the same date is rejected.
    """
    task_payload = {
        "title": "Complete Architecture Audit",
        "description": "First version",
        "priority": "P1",
        "estimated_duration_min": 45,
        "scheduled_date": str(date.today())
    }
    # 1. Create first
    res1 = client.post("/api/v1/tasks", json=task_payload)
    assert res1.status_code == 201

    # 2. Duplicate attempt
    res2 = client.post("/api/v1/tasks", json=task_payload)
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "DUPLICATE_TASK"

def test_task_crud_lifecycle_and_filtering():
    """
    Phase 5.4: Test full task CRUD, completion, and querying.
    """
    # 1. Create task
    create_res = client.post(
        "/api/v1/tasks",
        json={
            "title": "Deploy Microservice to Production",
            "description": "Render cloud backend",
            "priority": "P1",
            "estimated_duration_min": 60,
            "scheduled_date": str(date.today())
        }
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    # 2. Filter tasks
    list_res = client.get("/api/v1/tasks?priority=P1&search=Deploy")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == task_id

    # 3. Complete task
    comp_res = client.post(f"/api/v1/tasks/{task_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"
    assert comp_res.json()["completed_at"] is not None

    # 4. Reopen task
    reopen_res = client.post(f"/api/v1/tasks/{task_id}/reopen")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "PENDING"
    assert reopen_res.json()["completed_at"] is None

    # 5. Delete task
    del_res = client.delete(f"/api/v1/tasks/{task_id}")
    assert del_res.status_code == 204

    # 6. Verify deleted
    get_res = client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404

def test_dependency_dag_and_cycle_rejection():
    """
    Phase 5.2: Kahn's DAG cycle detection prevents circular task dependencies.
    """
    # Create Task A, Task B, Task C
    res_a = client.post("/api/v1/tasks", json={"title": "Task A Database Schema", "priority": "P1"})
    res_b = client.post("/api/v1/tasks", json={"title": "Task B Backend API", "priority": "P1"})
    res_c = client.post("/api/v1/tasks", json={"title": "Task C Frontend Integration", "priority": "P1"})
    id_a = res_a.json()["id"]
    id_b = res_b.json()["id"]
    id_c = res_c.json()["id"]

    # Task B depends on Task A (A -> B)
    dep1 = client.post(f"/api/v1/tasks/{id_b}/dependencies/{id_a}")
    assert dep1.status_code == 201

    # Task C depends on Task B (B -> C)
    dep2 = client.post(f"/api/v1/tasks/{id_c}/dependencies/{id_b}")
    assert dep2.status_code == 201

    # Attempt circular: Task A depends on Task C (C -> A creates cycle A -> B -> C -> A)
    dep_cycle = client.post(f"/api/v1/tasks/{id_a}/dependencies/{id_c}")
    assert dep_cycle.status_code == 422
    assert dep_cycle.json()["error_code"] == "CIRCULAR_DEPENDENCY"

    # Self dependency rejected
    dep_self = client.post(f"/api/v1/tasks/{id_a}/dependencies/{id_a}")
    assert dep_self.status_code == 422

def test_planning_engine_deadline_exceeded_warning():
    """
    Phase 5.2: Detect when a task cannot meet its specified deadline.
    """
    today = date.today()
    # Configure availability window: 09:00 to 12:00
    store.availability_windows[store.default_user_id] = [
        AvailabilityWindow(day_of_week=today.weekday(), start_time=time(9, 0), end_time=time(12, 0))
    ]

    # Task 1: 09:00 to 11:00 (120 mins)
    client.post("/api/v1/tasks", json={
        "title": "Long Morning Task",
        "estimated_duration_min": 120,
        "priority": "P1",
        "scheduled_date": str(today)
    })

    # Task 2: 60 mins, but deadline is 10:30 AM
    deadline_1030 = datetime.combine(today, time(10, 30))
    client.post("/api/v1/tasks", json={
        "title": "Urgent Review",
        "estimated_duration_min": 60,
        "priority": "P2",
        "deadline": deadline_1030.isoformat(),
        "scheduled_date": str(today)
    })

    plan_res = client.post("/api/v1/plans/generate", json={"target_date": str(today)})
    assert plan_res.status_code == 200
    plan = plan_res.json()
    
    # Task 2 cannot finish by 10:30 because Task 1 occupies 09:00-11:00
    deadline_conflicts = [c for c in plan["conflicts"] if c["code"] == "DEADLINE_EXCEEDED"]
    assert len(deadline_conflicts) > 0
    assert "Urgent Review" in deadline_conflicts[0]["message"]

def test_planning_engine_overcapacity_and_reschedule_flow():
    """
    Phase 5.2: Overloaded schedule produces reschedule suggestions that user can apply.
    """
    today = date.today()
    # 2 hours capacity: 09:00 to 11:00 (120 mins)
    store.availability_windows[store.default_user_id] = [
        AvailabilityWindow(day_of_week=today.weekday(), start_time=time(9, 0), end_time=time(11, 0))
    ]

    # Create 3 tasks of 60 mins each = 180 mins total (exceeds 120 mins available)
    r1 = client.post("/api/v1/tasks", json={"title": "Sprint Planning", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    r2 = client.post("/api/v1/tasks", json={"title": "Client Call", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    r3 = client.post("/api/v1/tasks", json={"title": "Documentation Cleanup", "estimated_duration_min": 60, "priority": "P3", "scheduled_date": str(today)})
    
    plan_res = client.post("/api/v1/plans/generate", json={"target_date": str(today)})
    assert plan_res.status_code == 200
    plan = plan_res.json()

    assert len(plan["slots"]) == 2
    assert len(plan["unassigned_task_ids"]) == 1
    assert len(plan["reschedule_suggestions"]) == 1
    
    sugg = plan["reschedule_suggestions"][0]
    assert sugg["title"] == "Documentation Cleanup"

    # Human applies the reschedule suggestion
    apply_res = client.post(
        "/api/v1/plans/reschedule/apply",
        json={"reschedules": [sugg]}
    )
    assert apply_res.status_code == 200
    new_plan = apply_res.json()
    # Now origin day has exactly 2 tasks and 0 overcapacity!
    assert len(new_plan["slots"]) == 2
    assert len(new_plan["unassigned_task_ids"]) == 0

def test_batch_approval_partial_rejection_zero_silent_tasks():
    """
    Phase 5.1: Batch approval where user approves 2 items and rejects 1.
    Verifies that unapproved items are never silently committed.
    """
    extraction = ExtractionResponse(
        detected_language="ta-IN",
        intent_summary="Three tasks extracted",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-a",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Approved Task A",
                source_expression="task a seiyanum",
                estimated_duration_min=30,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P1_CRITICAL,
                confidence=0.9
            ),
            ProposedItemExtraction(
                temp_id="item-b",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Approved Task B",
                source_expression="task b seiyanum",
                estimated_duration_min=45,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P2_MEDIUM,
                confidence=0.85
            ),
            ProposedItemExtraction(
                temp_id="item-c",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Unwanted / Rejected Idea C",
                source_expression="maybe ideava pannalam",
                estimated_duration_min=60,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P3_LOW,
                confidence=0.65
            ),
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    id_a = prop.items[0].id
    id_b = prop.items[1].id
    id_c = prop.items[2].id

    # User explicitly approves A and B, and rejects C with a rationale
    approve_res = client.post(
        f"/api/v1/proposals/{prop.id}/approve",
        json={
            "idempotency_key": str(uuid4()),
            "items": [
                {"id": str(id_a), "is_approved": True},
                {"id": str(id_b), "is_approved": True},
                {"id": str(id_c), "is_approved": False, "rejection_reason": "Not a commitment, just a passing idea."}
            ]
        }
    )
    assert approve_res.status_code == 200
    data = approve_res.json()
    assert data["approved_tasks_count"] == 2
    assert data["rejected_items_count"] == 1
    assert len(data["created_task_ids"]) == 2

    # Verify active tasks in the store
    tasks_res = client.get("/api/v1/tasks")
    assert tasks_res.status_code == 200
    tasks = tasks_res.json()
    task_titles = [t["title"] for t in tasks]
    assert "Approved Task A" in task_titles
    assert "Approved Task B" in task_titles
    assert "Unwanted / Rejected Idea C" not in task_titles

def test_expired_proposal_rejection():
    """
    Phase 5.1: Expired proposal cannot be approved.
    """
    extraction = ExtractionResponse(
        detected_language="en",
        intent_summary="Expired proposal",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-exp",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Expired Task",
                source_expression="do this",
                estimated_duration_min=30,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P2_MEDIUM,
                confidence=0.8
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    
    # Manually expire the proposal
    store.proposals[prop.id]["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)

    res = client.post(
        f"/api/v1/proposals/{prop.id}/approve",
        json={
            "idempotency_key": str(uuid4()),
            "items": [{"id": str(prop.items[0].id), "is_approved": True}]
        }
    )
    assert res.status_code == 410
    assert res.json()["error_code"] == "PROPOSAL_EXPIRED"
    assert len(store.tasks) == 0

def test_idempotent_approval_prevents_duplicate_commit():
    """
    Phase 5.1: Re-submitting approval with same idempotency key returns previous result without creating duplicate tasks.
    """
    extraction = ExtractionResponse(
        detected_language="ta-IN",
        intent_summary="Idempotency test",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-idemp",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Idempotent Task Commit",
                source_expression="do task",
                estimated_duration_min=40,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P1_CRITICAL,
                confidence=0.9
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    idemp_key = f"test-idemp-{uuid4()}"
    payload = {
        "idempotency_key": idemp_key,
        "items": [{"id": str(prop.items[0].id), "is_approved": True}]
    }

    # First attempt
    res1 = client.post(f"/api/v1/proposals/{prop.id}/approve", json=payload)
    assert res1.status_code == 200
    assert res1.json()["approved_tasks_count"] == 1
    assert len(store.tasks) == 1

    # Second identical attempt
    res2 = client.post(f"/api/v1/proposals/{prop.id}/approve", json=payload)
    assert res2.status_code == 200
    assert res2.json()["approved_tasks_count"] == 1
    # Store should still have exactly 1 task, not 2
    assert len(store.tasks) == 1

def test_multi_interval_scheduling_with_calendar_events():
    """
    Phase 5.2: Calendar busy events (lunch break & meetings) subtract from availability windows.
    Tasks are placed in contiguous free blocks.
    """
    today = date.today()
    # User works 09:00 to 17:00 (8 hours = 480 mins)
    store.availability_windows[store.default_user_id] = [
        AvailabilityWindow(day_of_week=today.weekday(), start_time=time(9, 0), end_time=time(17, 0))
    ]
    # Protected lunch 13:00 to 14:00 (60 mins) and sync 15:00 to 15:30 (30 mins)
    store.busy_events[store.default_user_id] = [
        BusyEvent(
            id=uuid4(),
            user_id=store.default_user_id,
            title="Protected Lunch Break",
            start_time=datetime.combine(today, time(13, 0)),
            end_time=datetime.combine(today, time(14, 0)),
            is_blocking=True
        ),
        BusyEvent(
            id=uuid4(),
            user_id=store.default_user_id,
            title="Stakeholder Sync Meeting",
            start_time=datetime.combine(today, time(15, 0)),
            end_time=datetime.combine(today, time(15, 30)),
            is_blocking=True
        )
    ]

    # Task 1: 120 mins (should fit 09:00 - 11:00)
    client.post("/api/v1/tasks", json={"title": "Morning Focus", "estimated_duration_min": 120, "priority": "P1", "scheduled_date": str(today)})
    # Task 2: 120 mins (should fit 11:00 - 13:00)
    client.post("/api/v1/tasks", json={"title": "Pre-Lunch Deep Work", "estimated_duration_min": 120, "priority": "P1", "scheduled_date": str(today)})
    # Task 3: 60 mins (must NOT overlap 13:00-14:00 lunch! Should schedule 14:00 - 15:00)
    client.post("/api/v1/tasks", json={"title": "Post-Lunch Code Review", "estimated_duration_min": 60, "priority": "P2", "scheduled_date": str(today)})

    plan_res = client.post("/api/v1/plans/generate", json={"target_date": str(today)})
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert len(plan["slots"]) == 3
    
    slot_3 = [s for s in plan["slots"] if s["title"] == "Post-Lunch Code Review"][0]
    start_dt = datetime.fromisoformat(slot_3["start_time"])
    end_dt = datetime.fromisoformat(slot_3["end_time"])
    # Strictly starts at 14:00 or later, after lunch finishes
    assert start_dt.hour >= 14
    assert end_dt.hour <= 15

def test_multi_level_dag_dependency_chain():
    """
    Phase 5.2: Sequential 4-stage dependency pipeline: Design -> Frontend -> Backend -> QA.
    """
    today = date.today()
    store.availability_windows[store.default_user_id] = [
        AvailabilityWindow(day_of_week=today.weekday(), start_time=time(9, 0), end_time=time(18, 0))
    ]
    
    r_d = client.post("/api/v1/tasks", json={"title": "Stage 1 Design", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    r_f = client.post("/api/v1/tasks", json={"title": "Stage 2 Frontend", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    r_b = client.post("/api/v1/tasks", json={"title": "Stage 3 Backend", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    r_q = client.post("/api/v1/tasks", json={"title": "Stage 4 QA", "estimated_duration_min": 60, "priority": "P1", "scheduled_date": str(today)})
    
    id_d = r_d.json()["id"]
    id_f = r_f.json()["id"]
    id_b = r_b.json()["id"]
    id_q = r_q.json()["id"]

    # Dependencies: F depends on D, B depends on F, Q depends on B
    client.post(f"/api/v1/tasks/{id_f}/dependencies/{id_d}")
    client.post(f"/api/v1/tasks/{id_b}/dependencies/{id_f}")
    client.post(f"/api/v1/tasks/{id_q}/dependencies/{id_b}")

    plan_res = client.post("/api/v1/plans/generate", json={"target_date": str(today)})
    assert plan_res.status_code == 200
    slots = plan_res.json()["slots"]
    assert len(slots) == 4
    
    # Verify strict temporal sequence
    times = [(s["title"], datetime.fromisoformat(s["start_time"]), datetime.fromisoformat(s["end_time"])) for s in slots]
    assert times[0][0] == "Stage 1 Design"
    assert times[1][0] == "Stage 2 Frontend"
    assert times[2][0] == "Stage 3 Backend"
    assert times[3][0] == "Stage 4 QA"
    assert times[0][2] <= times[1][1]
    assert times[1][2] <= times[2][1]
    assert times[2][2] <= times[3][1]
