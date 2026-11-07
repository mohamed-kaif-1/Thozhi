import pytest
from datetime import datetime, date, time, timezone
from uuid import uuid4, UUID
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.repository import store
from backend.app.schemas.intent import PriorityEnum, ItemTypeEnum, ExtractionResponse, ProposedItemExtraction, ClarificationQuestion
from backend.app.schemas.plan import AvailabilityWindow

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    store.proposals.clear()
    store.proposal_items.clear()
    store.tasks.clear()
    store.task_dependencies.clear()
    store.idempotency_keys.clear()
    store.memory_preferences.clear()
    store._seed_default_memory()
    yield

def test_stage7_complete_end_to_end_thozhi_pipeline():
    """
    Stage 7 Core Verification:
    Full journey from Multilingual Thought Capture -> Clarification -> Human Approval ->
    Deterministic Topological Scheduling -> Task Execution -> Duration Learning -> Sovereign Export.
    """
    today = date.today()
    # Configure 8-hour workday 09:00 - 17:00
    store.availability_windows[store.default_user_id] = [
        AvailabilityWindow(day_of_week=today.weekday(), start_time=time(9, 0), end_time=time(17, 0))
    ]

    # 1. Thought Capture & Extraction (Tanglish monologue)
    # "Inaiku kaalaila client review irukku, adhellam prepare pannanum. Also lab report submit pannanum but timing therila."
    extraction = ExtractionResponse(
        detected_language="ta-IN",
        intent_summary="Client review prep and lab report submission",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-review",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Prepare Client Review Slides",
                description="Finalize metrics and presentation deck",
                source_expression="client review irukku, adhellam prepare pannanum",
                estimated_duration_min=45,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P2_MEDIUM,
                confidence=0.92,
                uncertainty_flags=[]
            ),
            ProposedItemExtraction(
                temp_id="item-lab",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Submit Lab Record",
                description="Upload final record PDF",
                source_expression="lab report submit pannanum but timing therila",
                estimated_duration_min=30,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P3_LOW,
                confidence=0.75,
                uncertainty_flags=["UNCERTAIN_DEADLINE"]
            )
        ],
        clarifications=[
            ClarificationQuestion(
                id="q-lab-deadline",
                target_item_temp_id="item-lab",
                question_text="When is the lab record due?",
                suggested_options=["Today 4 PM", "Tomorrow 10 AM"]
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    assert prop.status == "PENDING_REVIEW"
    assert len(prop.items) == 2
    item_review = next(it for it in prop.items if it.temp_id == "item-review")
    item_lab = next(it for it in prop.items if it.temp_id == "item-lab")

    # 2. Strict Invariant Check: ZERO silent task creation
    initial_tasks = client.get("/api/v1/tasks")
    assert len(initial_tasks.json()) == 0

    # 3. Clarification Question Loop
    # User resolves the lab deadline: "Today 4 PM"
    clarify_res = client.post(
        f"/api/v1/proposals/{prop.id}/clarify",
        json={
            "answers": [
                {
                    "question_id": "q-lab-deadline",
                    "answer": "Today 4 PM",
                    "resolved_deadline_iso": f"{today}T16:00:00Z",
                    "resolved_duration_min": 45
                }
            ]
        }
    )
    assert clarify_res.status_code == 200
    clarified_lab = next(it for it in clarify_res.json()["items"] if it["temp_id"] == "item-lab")
    assert clarified_lab["estimated_duration_min"] == 45
    assert "UNCERTAIN_DEADLINE" not in clarified_lab["uncertainty_flags"]

    # 4. Pre-Approval Human Editing
    # User bumps client review to P1 Urgent and updates title
    patch_res = client.patch(
        f"/api/v1/proposals/{prop.id}/items/{item_review.id}",
        json={
            "proposed_title": "Executive Client Review & Demo Prep",
            "priority": "P1",
            "estimated_duration_min": 60
        }
    )
    assert patch_res.status_code == 200

    # 5. Human Decision Gate: Approve both items
    idemp_key = str(uuid4())
    approve_res = client.post(
        f"/api/v1/proposals/{prop.id}/approve",
        json={
            "idempotency_key": idemp_key,
            "items": [
                {
                    "id": str(item_review.id),
                    "is_approved": True,
                    "proposed_title": "Executive Client Review & Demo Prep",
                    "priority": "P1",
                    "estimated_duration_min": 60,
                    "scheduled_date": str(today)
                },
                {
                    "id": str(item_lab.id),
                    "is_approved": True,
                    "proposed_title": "Submit Lab Record",
                    "priority": "P2",
                    "estimated_duration_min": 45,
                    "scheduled_date": str(today)
                }
            ]
        }
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["approved_tasks_count"] == 2
    task_ids = approve_data["created_task_ids"]

    # 6. Replay Protection Idempotency Check
    replay_res = client.post(
        f"/api/v1/proposals/{prop.id}/approve",
        json={"idempotency_key": idemp_key, "items": []}
    )
    assert replay_res.status_code == 200
    assert replay_res.json()["approved_tasks_count"] == 2

    # 7. Add Sequential Dependency: Lab submission requires Client Review to finish first
    task_review_id = task_ids[0]
    task_lab_id = task_ids[1]
    dep_res = client.post(f"/api/v1/tasks/{task_lab_id}/dependencies/{task_review_id}")
    assert dep_res.status_code == 201

    # 8. Deterministic Schedule Generation
    plan_res = client.post("/api/v1/plans/generate", json={"target_date": str(today)})
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert len(plan["slots"]) == 2
    assert plan["capacity_percentage"] > 0
    # Slot 1 must be Client Review, Slot 2 must be Lab Record (strictly ordered by dependency)
    assert plan["slots"][0]["title"] == "Executive Client Review & Demo Prep"
    assert plan["slots"][1]["title"] == "Submit Lab Record"
    slot1_end = datetime.fromisoformat(plan["slots"][0]["end_time"])
    slot2_start = datetime.fromisoformat(plan["slots"][1]["start_time"])
    assert slot2_start >= slot1_end

    # 9. Task Execution & Actual Duration Logging
    # Task 1 completes in 75m (exceeding 60m estimate)
    comp_res = client.post(f"/api/v1/tasks/{task_review_id}/complete")
    assert comp_res.status_code == 200
    store.tasks[UUID(task_review_id)]["actual_duration_min"] = 75

    # 10. Duration Learning Engine: Learns client review pattern
    priors_res = client.get("/api/v1/memory/duration-priors/suggestions")
    assert priors_res.status_code == 200
    priors = priors_res.json()
    review_prior = next((p for p in priors if p["task_pattern"] == "review"), None)
    assert review_prior is not None
    assert review_prior["suggested_duration_min"] == 75

    # 11. Sovereign Data Portability Export
    export_res = client.post("/api/v1/memory/export")
    assert export_res.status_code == 200
    export_bundle = export_res.json()
    assert export_bundle["tasks_count"] == 2
    assert export_bundle["proposals_count"] == 1
    assert export_bundle["data"]["export_metadata"]["zero_audio_retention_verified"] is True
