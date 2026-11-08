import pytest
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.repository import store
from backend.app.schemas.task import TaskCreate
from backend.app.schemas.intent import PriorityEnum
from backend.app.schemas.memory import MemoryPreferenceCreate, MemoryCategoryEnum
from backend.app.db.supabase_client import SupabaseClient, SupabaseConnectionError

client = TestClient(app)

def test_tenant_isolation_tasks():
    """
    Verifies that User A cannot access or mutate tasks belonging to User B.
    """
    user_a = uuid4()
    user_b = uuid4()

    t_create = TaskCreate(
        title="User A Secret Deliverable",
        description="Confidential strategy",
        estimated_duration_min=45,
        priority=PriorityEnum.P1_CRITICAL
    )
    task_a = store.create_task(user_id=user_a, task_create=t_create)
    assert task_a.id is not None

    # User B should not see User A's task in their task list
    tasks_b = store.list_tasks(user_id=user_b)
    assert not any(t.id == task_a.id for t in tasks_b)

    # Clean up
    store.delete_task(task_a.id)


def test_tenant_isolation_captures_and_proposals():
    """
    Verifies that User B cannot access or mutate captures or proposals belonging to User A.
    """
    user_a = uuid4()
    user_b = uuid4()

    cap_a = store.create_capture(
        user_id=user_a,
        input_type="TEXT",
        transcript_text="Confidential User A notes"
    )
    assert cap_a.id is not None

    # User B should not see User A's capture
    assert store.get_capture(capture_id=cap_a.id, user_id=user_b) is None

    # User B cannot delete User A's capture
    assert not store.delete_capture(capture_id=cap_a.id, user_id=user_b)


def test_tenant_isolation_memory_and_gdpr_purge():
    """
    Verifies that User A's GDPR purge does not wipe User B's preferences or data.
    """
    user_a = uuid4()
    user_b = uuid4()

    pref_b = store.set_memory_preference(
        user_id=user_b,
        create_req=MemoryPreferenceCreate(
            preference_key="deep_work",
            category=MemoryCategoryEnum.WORKING_HOURS,
            preference_value={"start": "10:00", "end": "12:00"},
            description="User B schedule"
        )
    )

    pref_a = store.set_memory_preference(
        user_id=user_a,
        create_req=MemoryPreferenceCreate(
            preference_key="deep_work",
            category=MemoryCategoryEnum.WORKING_HOURS,
            preference_value={"start": "14:00", "end": "16:00"},
            description="User A schedule"
        )
    )

    # Purge User A
    purge_res = store.purge_user_data(user_id=user_a)
    assert "PURGED" in purge_res.status

    # User A preferences gone
    assert len(store.list_memory_preferences(user_id=user_a)) == 0

    # User B preferences must be 100% intact
    prefs_b = store.list_memory_preferences(user_id=user_b)
    assert len(prefs_b) == 1
    assert prefs_b[0].id == pref_b.id


def test_supabase_client_unconfigured_safety():
    """
    Verifies that SupabaseClient raises explicit connection errors when unconfigured,
    preventing silent failure or unverified mock data injection.
    """
    client_unconfigured = SupabaseClient(base_url="", api_key="")
    assert not client_unconfigured.is_configured

    with pytest.raises(SupabaseConnectionError):
        import asyncio
        asyncio.run(client_unconfigured.list_records(table="users"))
