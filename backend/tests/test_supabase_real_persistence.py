"""
================================================================================
THOZHI — SUPABASE REAL PERSISTENCE IMPLEMENTATION UNIT TESTS (MOCKED TRANSPORT)
================================================================================
CRITICAL NOTICE:
These unit tests mock the HTTP transport boundary (httpx) to verify correct PostgREST
query construction, table routing, parameter encoding, error propagation, factory selection,
and the strict absence of RAM delegation in SupabaseRepository.
These tests DO NOT verify live Supabase network persistence. Live verification requires
a provisioned PostgreSQL instance and is verified in staging/production environments.
================================================================================
"""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone, date, time
import httpx

from backend.app.core.config import settings
from backend.app.db.supabase_client import (
    SupabaseClient,
    SupabaseConnectionError,
    SupabaseQueryError,
    SupabaseAuthError,
)
from backend.app.db.repositories.base import BaseRepository
from backend.app.db.repositories.memory import InMemoryRepository
from backend.app.db.repositories.supabase import SupabaseRepository
from backend.app.db.repositories.factory import get_repository, reset_repository
from backend.app.schemas.task import TaskCreate, TaskUpdate
from backend.app.schemas.intent import PriorityEnum, ExtractionResponse, ProposedItemExtraction, ItemTypeEnum
from backend.app.schemas.proposal import ProposalApproveRequest, ProposalItemUpdate, ProposalItemPatch
from backend.app.schemas.memory import MemoryPreferenceCreate, MemoryPreferencePatch, MemoryCategoryEnum
from backend.app.schemas.plan import PlanResponse, ScheduleSlot


# ==============================================================================
# 1. HTTP REQUEST CONSTRUCTION & TRANSPORT BOUNDARY TESTS
# ==============================================================================

def test_supabase_client_request_construction_headers_and_urls():
    """
    [MOCKED TRANSPORT] Verifies that SupabaseClient constructs the correct PostgREST URL,
    headers (apikey, Authorization, Prefer), and parameter encodings.
    """
    client = SupabaseClient(
        base_url="https://testproject.supabase.co/rest/v1",
        api_key="test-anon-key",
        jwt_secret="test-secret"
    )

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = '[{"id": "1", "title": "Test Task"}]'
    mock_response.json.return_value = [{"id": "1", "title": "Test Task"}]

    with patch("httpx.Client.request", return_value=mock_response) as mock_req:
        result = client.list_records_sync(
            table="tasks",
            filters={"user_id": "eq.00000000-0000-0000-0000-000000000001", "limit": "10"},
            allow_service_role=True
        )

        assert mock_req.called
        method, url = mock_req.call_args[0][:2]
        kwargs = mock_req.call_args[1]

        assert method == "GET"
        assert url == "https://testproject.supabase.co/rest/v1/tasks"
        assert kwargs["headers"]["apikey"] == "test-anon-key"
        assert kwargs["headers"]["Authorization"] == "Bearer test-anon-key"
        assert kwargs["headers"]["Prefer"] == "return=representation"
        assert kwargs["params"]["user_id"] == "eq.00000000-0000-0000-0000-000000000001"
        assert kwargs["params"]["limit"] == "10"
        assert result == [{"id": "1", "title": "Test Task"}]


def test_supabase_client_user_jwt_forwarding():
    """
    [MOCKED TRANSPORT] Verifies that when an authenticated user token is passed,
    SupabaseClient forwards it in the Authorization header instead of the anon key.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    mock_res = MagicMock(spec=httpx.Response)
    mock_res.status_code = 200
    mock_res.text = "[]"
    mock_res.json.return_value = []

    with patch("httpx.Client.request", return_value=mock_res) as mock_req:
        client.list_records_sync("captures", user_token="user-jwt-xyz")
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer user-jwt-xyz"
        assert headers["apikey"] == "anon-key"


# ==============================================================================
# 2. STRICT ABSENCE OF RAM DELEGATION IN SUPABASENREPOSITORY
# ==============================================================================

def test_supabase_repository_does_not_delegate_to_in_memory_repository():
    """
    [MOCKED TRANSPORT] Verifies that SupabaseRepository does NOT maintain or delegate
    to an InMemoryRepository instance (_fallback_memory).
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)

    # Must NOT have _fallback_memory
    assert not hasattr(repo, "_fallback_memory"), "VIOLATION: SupabaseRepository contains RAM fallback attribute!"

    # Must be an instance of BaseRepository
    assert isinstance(repo, BaseRepository)


# ==============================================================================
# 3. REAL SUPABASE CRUD OPERATIONS WITH MOCKED POSTGREST RESPONSES
# ==============================================================================

def test_supabase_repository_create_and_get_capture():
    """
    [MOCKED TRANSPORT] Verifies capture creation and retrieval through PostgREST.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    cap_id = uuid4()

    fake_row = {
        "id": str(cap_id),
        "user_id": str(user_id),
        "input_type": "TEXT",
        "transcript_text": "Meeting with advisor tomorrow at 10am",
        "detected_language": "Tanglish",
        "processing_status": "PROCESSED",
        "lifecycle_status": "PENDING_REVIEW",
        "proposal_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    with patch.object(client, "insert_record_sync", return_value=fake_row) as mock_ins, \
         patch.object(client, "get_record_sync", return_value=fake_row) as mock_get:

        # Create
        created = repo.create_capture(
            user_id=user_id,
            input_type="TEXT",
            transcript_text="Meeting with advisor tomorrow at 10am"
        )
        assert mock_ins.called
        assert mock_ins.call_args[0][0] == "captures"
        assert created.transcript_text == "Meeting with advisor tomorrow at 10am"

        # Get
        fetched = repo.get_capture(capture_id=cap_id, user_id=user_id)
        assert mock_get.called
        assert mock_get.call_args[0][0] == "captures"
        assert fetched is not None
        assert fetched.id == cap_id


def test_supabase_repository_create_task_and_list_with_filters():
    """
    [MOCKED TRANSPORT] Verifies task creation, listing, and dependency resolution.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    task_id = uuid4()

    fake_task = {
        "id": str(task_id),
        "user_id": str(user_id),
        "title": "Complete Raven App",
        "description": "Production deliverables",
        "priority": "P1_CRITICAL",
        "estimated_duration_min": 90,
        "duration_source": "USER_EXPLICIT",
        "deadline": "2026-11-09T18:00:00+00:00",
        "status": "PENDING",
        "created_at": "2026-11-08T10:00:00+00:00",
        "updated_at": "2026-11-08T10:00:00+00:00"
    }

    with patch.object(client, "list_records_sync") as mock_list, \
         patch.object(client, "insert_record_sync", return_value=fake_task) as mock_ins:

        mock_list.side_effect = [
            [], # check existing for duplicates: tasks
            [], # check existing for duplicates: task_dependencies
            [fake_task], # list_tasks: tasks
            [] # list_tasks: task_dependencies
        ]

        # Create
        created = repo.create_task(
            user_id=user_id,
            task_create=TaskCreate(
                title="Complete Raven App",
                estimated_duration_min=90,
                priority=PriorityEnum.P1_CRITICAL
            )
        )
        assert mock_ins.called
        assert mock_ins.call_args[0][0] == "tasks"
        assert created.title == "Complete Raven App"

        # List
        tasks = repo.list_tasks(user_id=user_id)
        assert len(tasks) == 1
        assert tasks[0].id == task_id


def test_supabase_repository_approve_proposal_creates_tasks_and_audit():
    """
    [MOCKED TRANSPORT] Verifies that proposal approval calls commit_proposal_atomic RPC
    in a single atomic transaction and returns a typed ProposalApproveResponse.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    prop_id = uuid4()
    item_id = uuid4()
    task_id = uuid4()

    fake_prop_row = {
        "id": str(prop_id),
        "user_id": str(user_id),
        "capture_id": None,
        "status": "PENDING_REVIEW",
        "model_provider": "gemini-2.5-flash",
        "model_version": "v1",
        "intent_summary": "Complete project",
        "display_language": "original",
        "translation_status": "ORIGINAL",
        "detected_language": "Tanglish",
        "created_at": "2026-11-08T10:00:00+00:00",
        "expires_at": "2026-11-15T10:00:00+00:00"
    }
    fake_item_row = {
        "id": str(item_id),
        "proposal_id": str(prop_id),
        "user_id": str(user_id),
        "item_type": "TASK",
        "proposed_title": "Finish report",
        "estimated_duration_min": 45,
        "priority": "P2_MEDIUM",
        "confidence": 0.95,
        "source_reference": "RAW_EXTRACT",
        "decision_state": "PENDING",
        "created_at": "2026-11-08T10:00:00+00:00"
    }

    mock_rpc_response = {
        "proposal_id": str(prop_id),
        "approved_tasks_count": 1,
        "rejected_items_count": 0,
        "created_task_ids": [str(task_id)],
        "message": "Human decision recorded atomically. Tasks explicitly committed to schedule."
    }

    with patch.object(client, "get_record_sync") as mock_get, \
         patch.object(client, "list_records_sync") as mock_list, \
         patch.object(client, "rpc_sync", return_value=mock_rpc_response) as mock_rpc:

        # 1. idempotency check -> None
        # 2. get_proposal -> fake_prop_row
        mock_get.side_effect = [None, fake_prop_row]
        # list items -> [fake_item_row]
        mock_list.return_value = [fake_item_row]

        req = ProposalApproveRequest(
            idempotency_key="key-12345",
            items=[ProposalItemUpdate(id=item_id, is_approved=True)]
        )

        res = repo.approve_proposal(prop_id, user_id, req)

        assert res.approved_tasks_count == 1
        assert len(res.created_task_ids) == 1
        assert res.created_task_ids[0] == task_id

        # Verify atomic RPC was invoked with complete 100% item coverage payload
        assert mock_rpc.called
        assert mock_rpc.call_args[0][0] == "commit_proposal_atomic"
        rpc_params = mock_rpc.call_args[0][1]
        assert rpc_params["p_user_id"] == str(user_id)
        assert rpc_params["p_proposal_id"] == str(prop_id)
        assert rpc_params["p_idempotency_key"] == "key-12345"
        assert len(rpc_params["p_item_decisions"]) == 1
        assert rpc_params["p_item_decisions"][0]["id"] == str(item_id)
        assert rpc_params["p_item_decisions"][0]["is_approved"] is True


def test_supabase_repository_atomic_approval_error_mapping():
    """
    [MOCKED TRANSPORT] Verifies that PostgreSQL SQLSTATE errors returned from PostgREST
    are mapped to domain exceptions:
    - P0002 -> ResourceNotFoundException
    - 23505 -> IdempotencyConflictException
    - 42501 -> PermissionDeniedException
    """
    from backend.app.core.errors import (
        ResourceNotFoundException,
        IdempotencyConflictException,
        PermissionDeniedException,
    )

    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    prop_id = uuid4()
    item_id = uuid4()

    fake_prop_row = {
        "id": str(prop_id),
        "user_id": str(user_id),
        "status": "PENDING_REVIEW",
        "intent_summary": "Task",
        "created_at": "2026-11-08T10:00:00+00:00"
    }
    fake_item_row = {
        "id": str(item_id),
        "proposal_id": str(prop_id),
        "proposed_title": "Item 1",
        "created_at": "2026-11-08T10:00:00+00:00"
    }

    req = ProposalApproveRequest(idempotency_key="key-err", items=[ProposalItemUpdate(id=item_id, is_approved=True)])

    # Test P0002 -> ResourceNotFoundException
    with patch.object(client, "get_record_sync", side_effect=[None, fake_prop_row]), \
         patch.object(client, "list_records_sync", return_value=[fake_item_row]), \
         patch.object(client, "rpc_sync", side_effect=SupabaseQueryError(400, "P0002: Proposal item not found")):
        with pytest.raises(ResourceNotFoundException):
            repo.approve_proposal(prop_id, user_id, req)

    # Test 23505 -> IdempotencyConflictException
    with patch.object(client, "get_record_sync", side_effect=[None, fake_prop_row]), \
         patch.object(client, "list_records_sync", return_value=[fake_item_row]), \
         patch.object(client, "rpc_sync", side_effect=SupabaseQueryError(409, "23505: Proposal has already been committed")):
        with pytest.raises(IdempotencyConflictException):
            repo.approve_proposal(prop_id, user_id, req)

    # Test 42501 -> PermissionDeniedException
    with patch.object(client, "get_record_sync", side_effect=[None, fake_prop_row]), \
         patch.object(client, "list_records_sync", return_value=[fake_item_row]), \
         patch.object(client, "rpc_sync", side_effect=SupabaseQueryError(403, "42501: Access denied: caller does not match user_id")):
        with pytest.raises(PermissionDeniedException):
            repo.approve_proposal(prop_id, user_id, req)


def test_supabase_repository_task_completion_persists_actual_duration():
    """
    [MOCKED TRANSPORT] Verifies that complete_task correctly persists actual_duration_min
    and returns it in the TaskResponse.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    task_id = uuid4()

    existing_task = {
        "id": str(task_id),
        "user_id": str(user_id),
        "title": "Build Architecture",
        "status": "PENDING",
        "estimated_duration_min": 60,
        "created_at": "2026-11-08T10:00:00+00:00"
    }
    updated_task = {
        **existing_task,
        "status": "COMPLETED",
        "actual_duration_min": 75,
        "completed_at": "2026-11-08T11:15:00+00:00",
        "updated_at": "2026-11-08T11:15:00+00:00"
    }

    with patch.object(client, "get_record_sync", return_value=existing_task), \
         patch.object(client, "update_record_sync", return_value=[updated_task]) as mock_up, \
         patch.object(repo, "get_task_dependencies", return_value=[]):

        completed = repo.complete_task(task_id=task_id, user_id=user_id, actual_duration_min=75)

        assert mock_up.called
        update_payload = mock_up.call_args[0][2]
        assert update_payload["status"] == "COMPLETED"
        assert update_payload["actual_duration_min"] == 75
        assert completed.actual_duration_min == 75
        assert completed.status == "COMPLETED"


def test_supabase_repository_clarification_persistence_roundtrip():
    """
    [MOCKED TRANSPORT] Verifies that clarification questions from extraction are persisted
    in proposals table and restored upon get_proposal.
    """
    from backend.app.schemas.intent import ClarificationQuestion

    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    prop_id = uuid4()

    extraction = ExtractionResponse(
        intent_summary="Do task",
        extracted_items=[],
        clarifications=[
            ClarificationQuestion(
                id="clar_1",
                question_text="When should this task be scheduled?",
                suggested_options=["Morning", "Afternoon", "Evening"],
                field_to_update="deadline"
            )
        ]
    )

    with patch.object(client, "insert_record_sync") as mock_ins, \
         patch.object(client, "get_record_sync") as mock_get, \
         patch.object(client, "list_records_sync", return_value=[]):

        # 1. Create proposal from extraction
        created_prop = repo.create_proposal_from_extraction(user_id=user_id, extraction=extraction)
        assert mock_ins.called
        prop_payload = mock_ins.call_args_list[0][0][1]
        assert "clarifications" in prop_payload
        assert len(prop_payload["clarifications"]) == 1
        assert prop_payload["clarifications"][0]["question_text"] == "When should this task be scheduled?"

        # 2. Get proposal restores clarifications
        mock_get.return_value = {
            "id": str(prop_id),
            "user_id": str(user_id),
            "intent_summary": "Do task",
            "clarifications": [
                {
                    "id": "clar_1",
                    "question_text": "When should this task be scheduled?",
                    "suggested_options": ["Morning", "Afternoon", "Evening"],
                    "field_to_update": "deadline"
                }
            ],
            "created_at": "2026-11-08T10:00:00+00:00"
        }
        retrieved = repo.get_proposal(prop_id, user_id=user_id)
        assert retrieved is not None
        assert len(retrieved.clarifications) == 1
        assert retrieved.clarifications[0].question_text == "When should this task be scheduled?"
        assert retrieved.clarifications[0].suggested_options == ["Morning", "Afternoon", "Evening"]


def test_supabase_repository_sovereign_purge():
    """
    [MOCKED TRANSPORT] Verifies sovereign purge executes DELETE across all 11 user-scoped tables
    and writes an audit log.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()

    with patch.object(client, "delete_record_sync", return_value=3) as mock_del, \
         patch.object(client, "insert_record_sync") as mock_ins:

        purge_res = repo.purge_user_data(user_id=user_id)

        assert purge_res.status == "PURGED_SOVEREIGN"
        # Must delete across all 11 user tables:
        # task_dependencies, tasks, proposal_items, proposals, captures, plans, busy_events,
        # availability_windows, contextual_summaries, memory_preferences, approval_idempotency
        assert mock_del.call_count >= 11
        assert mock_ins.called
        assert mock_ins.call_args[0][0] == "audit_logs"
        assert mock_ins.call_args[0][1]["event_type"] == "SOVEREIGN_PURGE"


def test_supabase_repository_priority_lifecycle_representation():
    """
    [MOCKED TRANSPORT] Verifies SEC-02 resolution:
    - Every Python PriorityEnum value maps deterministically to its database representation.
    - PriorityEnum.UNSPECIFIED maps to SQL NULL (not fabricated P2_MEDIUM).
    - Database NULL or UNSPECIFIED deserializes cleanly to None in TaskResponse.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()

    # 1. Test insertion payloads for each PriorityEnum value
    priority_expectations = [
        (PriorityEnum.P1_CRITICAL, "P1_CRITICAL"),
        (PriorityEnum.P2_MEDIUM, "P2_MEDIUM"),
        (PriorityEnum.P3_LOW, "P3_LOW"),
        (PriorityEnum.BACKBURNER, "BACKBURNER"),
        (PriorityEnum.UNSPECIFIED, None),
        (None, None),
    ]

    for py_prio, expected_db in priority_expectations:
        t_create = TaskCreate(
            title=f"Test Priority {py_prio}",
            priority=py_prio,
            estimated_duration_min=30
        )
        with patch.object(client, "insert_record_sync") as mock_ins, \
             patch.object(repo, "list_tasks", return_value=[]):
            repo.create_task(user_id=user_id, task_create=t_create)
            assert mock_ins.called
            insert_payload = mock_ins.call_args[0][1]
            assert insert_payload["priority"] == expected_db, f"Expected {expected_db} for {py_prio}, got {insert_payload['priority']}"

    # 2. Test deserialization via _row_to_task
    row_deserialization_cases = [
        ({"priority": "P1_CRITICAL"}, PriorityEnum.P1_CRITICAL),
        ({"priority": "P2_MEDIUM"}, PriorityEnum.P2_MEDIUM),
        ({"priority": "P3_LOW"}, PriorityEnum.P3_LOW),
        ({"priority": "BACKBURNER"}, PriorityEnum.BACKBURNER),
        ({"priority": None}, None),
        ({"priority": "UNSPECIFIED"}, None),
    ]

    for row_input, expected_resp in row_deserialization_cases:
        row = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "title": "Sample Task",
            "created_at": "2026-11-08T10:00:00+00:00",
            **row_input
        }
        resp = repo._row_to_task(row, [])
        assert resp.priority == expected_resp, f"Expected {expected_resp} for row {row_input}, got {resp.priority}"


def test_supabase_repository_scheduled_date_roundtrip():
    """
    [MOCKED TRANSPORT] Verifies SEC-03 resolution:
    - create_task persists scheduled_date into the database record payload.
    - _row_to_task reads scheduled_date directly from the database row, distinct from deadline.
    - Absence of scheduled_date correctly falls back to deadline/created_at date.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()

    # 1. Explicit scheduled_date persisted in insert payload
    target_date = date(2026, 12, 1)
    deadline_dt = datetime(2026, 12, 15, 18, 0, tzinfo=timezone.utc)
    t_create = TaskCreate(
        title="Scheduled Deliverable",
        deadline=deadline_dt,
        scheduled_date=target_date,
        estimated_duration_min=45
    )

    with patch.object(client, "insert_record_sync") as mock_ins, \
         patch.object(repo, "list_tasks", return_value=[]):
        repo.create_task(user_id=user_id, task_create=t_create)
        assert mock_ins.called
        payload = mock_ins.call_args[0][1]
        assert payload["scheduled_date"] == "2026-12-01"
        assert payload["deadline"] == deadline_dt.isoformat()

    # 2. _row_to_task preserves explicit scheduled_date from DB row
    row_with_sched = {
        "id": str(uuid4()),
        "user_id": str(user_id),
        "title": "Dec 1 Focus",
        "scheduled_date": "2026-12-01",
        "deadline": deadline_dt.isoformat(),
        "created_at": "2026-11-08T10:00:00+00:00"
    }
    task_resp = repo._row_to_task(row_with_sched, [])
    assert task_resp.scheduled_date == date(2026, 12, 1)
    assert task_resp.deadline == deadline_dt

    # 3. Fallback when scheduled_date is absent in DB row
    row_without_sched = {
        "id": str(uuid4()),
        "user_id": str(user_id),
        "title": "Deadline Only Focus",
        "scheduled_date": None,
        "deadline": deadline_dt.isoformat(),
        "created_at": "2026-11-08T10:00:00+00:00"
    }
    task_resp_fallback = repo._row_to_task(row_without_sched, [])
    assert task_resp_fallback.scheduled_date == deadline_dt.date()


def test_supabase_repository_atomic_approval_rpc_null_validation():
    """
    [MOCKED TRANSPORT] Verifies SEC-04 resolution:
    - RPC error code 22023 for NULL decisions or non-array decisions is properly caught
      and surfaced rather than silently succeeding.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")
    repo = SupabaseRepository(client=client)
    user_id = uuid4()
    prop_id = uuid4()
    item_id = uuid4()

    fake_prop_row = {
        "id": str(prop_id),
        "user_id": str(user_id),
        "status": "PENDING_REVIEW",
        "intent_summary": "Task",
        "created_at": "2026-11-08T10:00:00+00:00"
    }
    fake_item_row = {
        "id": str(item_id),
        "proposal_id": str(prop_id),
        "proposed_title": "Item 1",
        "created_at": "2026-11-08T10:00:00+00:00"
    }

    req = ProposalApproveRequest(idempotency_key="key-22023", items=[ProposalItemUpdate(id=item_id, is_approved=True)])

    with patch.object(client, "get_record_sync", side_effect=[None, fake_prop_row]), \
         patch.object(client, "list_records_sync", return_value=[fake_item_row]), \
         patch.object(client, "rpc_sync", side_effect=SupabaseQueryError(400, "22023: Decisions payload cannot be NULL")):
        with pytest.raises(SupabaseQueryError) as exc_info:
            repo.approve_proposal(prop_id, user_id, req)
        assert "22023" in str(exc_info.value.detail)


# ==============================================================================
# 4. ERROR PROPAGATION & NO SILENT SUCCESS
# ==============================================================================

def test_supabase_client_error_propagation_500_and_401():
    """
    [MOCKED TRANSPORT] Verifies that HTTP 500 raises SupabaseQueryError and HTTP 401 raises SupabaseAuthError.
    Never converts errors into successful empty results.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="bad-key")

    mock_500 = MagicMock(spec=httpx.Response)
    mock_500.status_code = 500
    mock_500.text = "Internal Server Error: Connection pool exhausted"

    mock_401 = MagicMock(spec=httpx.Response)
    mock_401.status_code = 401
    mock_401.text = "Invalid JWT token"

    with patch("httpx.Client.request", return_value=mock_500):
        with pytest.raises(SupabaseQueryError) as exc_info:
            client.list_records_sync("tasks", user_token="test-jwt")
        assert exc_info.value.status_code == 500

    with patch("httpx.Client.request", return_value=mock_401):
        with pytest.raises(SupabaseAuthError):
            client.list_records_sync("tasks", user_token="test-jwt")


def test_supabase_client_network_connection_error():
    """
    [MOCKED TRANSPORT] Verifies that network dropouts raise SupabaseConnectionError.
    """
    client = SupabaseClient(base_url="https://testproject.supabase.co/rest/v1", api_key="anon-key")

    with patch("httpx.Client.request", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(SupabaseConnectionError):
            client.list_records_sync("tasks", user_token="test-jwt")


# ==============================================================================
# 5. REPOSITORY FACTORY DETERMINISM & PRODUCTION FAST-FAIL
# ==============================================================================

def test_factory_production_missing_credentials_raises_fatal_error():
    """
    Verifies that when ENVIRONMENT='production', missing Supabase credentials raise a fatal
    RuntimeError immediately at startup. No silent RAM fallback permitted.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "SUPABASE_URL", ""), \
         patch.object(settings, "SUPABASE_KEY", ""):
        with pytest.raises(RuntimeError) as exc_info:
            get_repository()
        assert "CRITICAL STARTUP FAILURE" in str(exc_info.value)
    reset_repository()


def test_factory_production_invalid_url_raises_fatal_error():
    """
    Verifies that when ENVIRONMENT='production', an invalid URL raises a fatal RuntimeError.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "SUPABASE_URL", "not-a-valid-url"), \
         patch.object(settings, "SUPABASE_KEY", "test-placeholder-not-a-real-supabase-secret"):
        with pytest.raises(RuntimeError) as exc_info:
            get_repository()
        assert "Invalid SUPABASE_URL configured" in str(exc_info.value)
    reset_repository()


def test_factory_development_and_test_selects_in_memory_repository():
    """
    Verifies that development and test environments safely select InMemoryRepository by default.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "development"), patch.object(settings, "DATA_BACKEND", ""):
        repo = get_repository()
        assert isinstance(repo, InMemoryRepository)
    reset_repository()

    with patch.object(settings, "ENVIRONMENT", "test"), patch.object(settings, "DATA_BACKEND", ""):
        repo = get_repository()
        assert isinstance(repo, InMemoryRepository)
    reset_repository()


def test_factory_production_with_valid_credentials_selects_supabase_repository():
    """
    Verifies that production with valid credentials selects SupabaseRepository.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "SUPABASE_URL", "https://bwzqudaaxfubtbgwmevo.supabase.co/rest/v1"), \
         patch.object(settings, "SUPABASE_KEY", "test-placeholder-not-a-real-supabase-secret"):
        repo = get_repository()
        assert isinstance(repo, SupabaseRepository)
    reset_repository()


def test_factory_data_backend_supabase_with_valid_credentials():
    """
    Verifies that DATA_BACKEND=supabase in development selects SupabaseRepository.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "development"), \
         patch.object(settings, "DATA_BACKEND", "supabase"), \
         patch.object(settings, "SUPABASE_URL", "https://bwzqudaaxfubtbgwmevo.supabase.co/rest/v1"), \
         patch.object(settings, "SUPABASE_KEY", "test-placeholder-not-a-real-supabase-secret"):
        repo = get_repository()
        assert isinstance(repo, SupabaseRepository)
    reset_repository()


def test_factory_data_backend_supabase_missing_credentials_raises():
    """
    Verifies that DATA_BACKEND=supabase with missing credentials raises fatal RuntimeError.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "development"), \
         patch.object(settings, "DATA_BACKEND", "supabase"), \
         patch.object(settings, "SUPABASE_URL", ""), \
         patch.object(settings, "SUPABASE_KEY", ""), \
         patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", ""):
        with pytest.raises(RuntimeError) as exc_info:
            get_repository()
        assert "CRITICAL STARTUP FAILURE" in str(exc_info.value)
    reset_repository()


def test_factory_data_backend_supabase_with_service_role_key_preferred():
    """
    Verifies that SUPABASE_SERVICE_ROLE_KEY is supported as preferred key name.
    """
    reset_repository()
    with patch.object(settings, "ENVIRONMENT", "development"), \
         patch.object(settings, "DATA_BACKEND", "supabase"), \
         patch.object(settings, "SUPABASE_URL", "https://bwzqudaaxfubtbgwmevo.supabase.co/rest/v1"), \
         patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "test-placeholder-not-a-real-supabase-secret"), \
         patch.object(settings, "SUPABASE_KEY", ""):
        repo = get_repository()
        assert isinstance(repo, SupabaseRepository)
    reset_repository()
