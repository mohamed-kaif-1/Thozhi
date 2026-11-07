import pytest
from datetime import datetime, date, timezone
from uuid import uuid4, UUID
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.repository import store
from backend.app.schemas.task import TaskCreate

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    store.proposals.clear()
    store.proposal_items.clear()
    store.tasks.clear()
    store.task_dependencies.clear()
    store.idempotency_keys.clear()
    store.memory_preferences.clear()
    store.availability_windows.clear()
    store.busy_events.clear()
    store._seed_default_memory()
    yield

def test_user_controlled_preferences_crud():
    """
    Phase 6.2: Personal memory CRUD with explicit user consent.
    """
    # 1. Create a personal planning preference
    create_payload = {
        "preference_key": "evening_winddown_hour",
        "category": "WORKING_HOURS",
        "preference_value": {"cutoff_hour": 20, "allow_emergencies": False},
        "description": "Never schedule work tasks after 8:00 PM.",
        "consent_level": "EXPLICIT_CONSENT"
    }
    res = client.post("/api/v1/memory/preferences", json=create_payload)
    assert res.status_code == 200
    pref = res.json()
    pref_id = pref["id"]
    assert pref["preference_key"] == "evening_winddown_hour"
    assert pref["is_active"] is True

    # 2. Patch preference
    patch_res = client.patch(
        f"/api/v1/memory/preferences/{pref_id}",
        json={"preference_value": {"cutoff_hour": 21, "allow_emergencies": True}}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["preference_value"]["cutoff_hour"] == 21

    # 3. Toggle preference
    toggle_res = client.post(f"/api/v1/memory/preferences/{pref_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # 4. List preferences (filtered by active_only)
    list_active = client.get("/api/v1/memory/preferences?active_only=true")
    assert list_active.status_code == 200
    assert not any(p["id"] == pref_id for p in list_active.json())

    # 5. Delete preference
    del_res = client.delete(f"/api/v1/memory/preferences/{pref_id}")
    assert del_res.status_code == 200

    # 6. Verify gone
    get_res = client.get(f"/api/v1/memory/preferences/{pref_id}")
    assert get_res.status_code == 404

def test_duration_learning_engine():
    """
    Phase 6.3: Duration Learning analyzes completed tasks to propose priors without hallucinating.
    """
    # Simulate user having completed 3 technical report tasks that took longer than estimated
    today = date.today()
    # Task 1: estimated 30m, actual 60m
    t1 = store.create_task(
        user_id=store.default_user_id,
        task_create=TaskCreate(title="Annual Technical Report Part 1", estimated_duration_min=30, scheduled_date=today)
    )
    store.complete_task(t1.id, actual_duration_min=60)

    # Task 2: estimated 45m, actual 75m
    t2 = store.create_task(
        user_id=store.default_user_id,
        task_create=TaskCreate(title="Annual Technical Report Part 2", estimated_duration_min=45, scheduled_date=today)
    )
    store.complete_task(t2.id, actual_duration_min=75)

    # Fetch duration prior suggestions
    res = client.get("/api/v1/memory/duration-priors/suggestions")
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) > 0

    report_sugg = next((s for s in suggestions if s["task_pattern"] == "report"), None)
    assert report_sugg is not None
    # Average actual = (60 + 75) // 2 = 67m
    assert report_sugg["suggested_duration_min"] == 67
    assert report_sugg["historical_samples"] == 2
    assert "report" in report_sugg["rationale"].lower()

def test_sovereign_data_portability_export():
    """
    Phase 6.4: Full personal data bundle export for user sovereignty.
    """
    # Create a task and proposal
    store.create_task(
        user_id=store.default_user_id,
        task_create=TaskCreate(title="Client Deliverable Review", estimated_duration_min=45)
    )

    export_res = client.post("/api/v1/memory/export")
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["user_id"] == str(store.default_user_id)
    assert export_data["tasks_count"] >= 1
    assert export_data["preferences_count"] >= 1
    assert export_data["data"]["export_metadata"]["zero_audio_retention_verified"] is True

def test_sovereign_right_to_be_forgotten_purge():
    """
    Phase 6.4: Sovereign Right to be Forgotten wipes all tenant records.
    """
    store.create_task(
        user_id=store.default_user_id,
        task_create=TaskCreate(title="Private Task To Delete", estimated_duration_min=30)
    )

    purge_res = client.delete("/api/v1/memory/purge")
    assert purge_res.status_code == 200
    purge_info = purge_res.json()
    assert purge_info["status"] == "PURGED_SOVEREIGN"
    assert purge_info["records_deleted"]["tasks"] >= 1

    # Verify task list is empty
    tasks_res = client.get("/api/v1/tasks")
    assert len(tasks_res.json()) == 0

    # Verify memory preferences are empty
    prefs_res = client.get("/api/v1/memory/preferences")
    assert len(prefs_res.json()) == 0

def test_multi_tenant_memory_isolation():
    """
    Phase 6.4: Verify complete isolation between tenant memories.
    """
    user_a = store.default_user_id
    user_b = uuid4()
    store.users[user_b] = {"id": user_b, "email": "tenant_b@thozhi.ai"}

    # Tenant A sets a preference
    from backend.app.schemas.memory import MemoryPreferenceCreate
    pref_a = store.set_memory_preference(
        user_id=user_a,
        create_req=MemoryPreferenceCreate(
            preference_key="tenant_a_secret",
            preference_value={"key": "val"},
            consent_level="EXPLICIT_CONSENT"
        )
    )

    # Attempting to fetch Tenant A's preference with Tenant B id raises 404
    with pytest.raises(Exception):
        store.get_memory_preference(user_id=user_b, pref_id=pref_a.id)

    # Attempting to delete Tenant A's preference as Tenant B raises 404
    with pytest.raises(Exception):
        store.delete_memory_preference(user_id=user_b, identifier=str(pref_a.id))

def test_learned_duration_prior_calibrates_proposal_item():
    """
    Phase 6.3: Contextual memory calibrates default heuristic durations using learned priors.
    """
    from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction, ItemTypeEnum, PriorityEnum
    
    # Store default memory has seeded 'technical_report_duration_prior' with suggested_min=75
    extraction = ExtractionResponse(
        detected_language="en",
        intent_summary="Report task",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item-rep",
                item_type=ItemTypeEnum.TASK,
                proposed_title="Q4 Financial Report Audit",
                source_expression="do financial report",
                estimated_duration_min=30,
                duration_source="DEFAULT_HEURISTIC",
                priority=PriorityEnum.P1_CRITICAL,
                confidence=0.88
            )
        ]
    )
    prop = store.create_proposal_from_extraction(store.default_user_id, extraction)
    item = prop.items[0]
    
    # Learned prior was automatically applied!
    assert item.estimated_duration_min == 75
    assert item.duration_source == "LEARNED_PRIOR"

def test_personal_working_hours_memory_alters_schedule_windows():
    """
    Phase 6.2: Working hours stored in memory automatically configure schedule availability.
    """
    # Set customized working hours: 10:00 to 16:00 (6 hours = 360 mins)
    client.post(
        "/api/v1/memory/preferences",
        json={
            "preference_key": "user_working_hours",
            "category": "WORKING_HOURS",
            "preference_value": {"startTime": "10:00", "endTime": "16:00"},
            "consent_level": "EXPLICIT_CONSENT"
        }
    )

    windows = store.get_user_windows(store.default_user_id)
    assert len(windows) == 5
    assert windows[0].start_time.hour == 10
    assert windows[0].end_time.hour == 16

def test_protected_break_memory_creates_blocking_interval():
    """
    Phase 6.2: Protected break preference (e.g. lunch 13:00 to 14:00) automatically injects blocking event.
    """
    today = date.today()
    busy_events = store.get_user_busy_events(store.default_user_id, today)
    lunch = next((e for e in busy_events if "lunch" in e.title.lower()), None)
    assert lunch is not None
    assert lunch.is_blocking is True
    assert lunch.start_time.hour == 13
    assert lunch.end_time.hour == 14

def test_preference_upsert_preserves_single_record():
    """
    Phase 6.2: Re-submitting preference with same key updates value without duplicating records.
    """
    client.post(
        "/api/v1/memory/preferences",
        json={
            "preference_key": "auto_buffer",
            "category": "PLANNING_STYLE",
            "preference_value": {"pct": 10},
            "consent_level": "EXPLICIT_CONSENT"
        }
    )
    client.post(
        "/api/v1/memory/preferences",
        json={
            "preference_key": "auto_buffer",
            "category": "PLANNING_STYLE",
            "preference_value": {"pct": 20},
            "consent_level": "EXPLICIT_CONSENT"
        }
    )
    prefs = client.get("/api/v1/memory/preferences").json()
    buffer_prefs = [p for p in prefs if p["preference_key"] == "auto_buffer"]
    assert len(buffer_prefs) == 1
    assert buffer_prefs[0]["preference_value"]["pct"] == 20
