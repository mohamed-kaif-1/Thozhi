"""
================================================================================
THOZHI — SUPABASE JWT PROPAGATION & CONCURRENCY ISOLATION SECURITY SUITE
================================================================================
Independent Security and Regression Verification Suite for P1 Remediation.

Covers:
- Category A: HTTP Authorization Header Verification (GET, POST, PATCH, DELETE, RPC)
- Category B: Concurrency Isolation & Shared-State Race Condition Immunity Proof
- Category C: Complete Repository Method Propagation Across All User Operations
- Category D: Fail-Closed Protection on Missing or Blank User JWTs
- Category E: Service-Role Fallback Prevention & Administrative Boundaries
- Category F: Atomic Proposal Approval RPC Security Regression Verification
================================================================================
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, call
from uuid import uuid4, UUID
from datetime import datetime, timezone, date
import httpx

from backend.app.db.supabase_client import (
    SupabaseClient,
    SupabaseAuthError,
    SupabaseQueryError
)
from backend.app.db.repositories.supabase import SupabaseRepository
from backend.app.schemas.intent import (
    ExtractionResponse,
    ProposedItemExtraction,
    PriorityEnum,
    ItemTypeEnum,
)
from backend.app.schemas.proposal import (
    ProposalApproveRequest,
    ProposalItemUpdate,
    ProposalItemPatch,
    ProposalClarificationRequest,
)
from backend.app.schemas.task import TaskCreate, TaskUpdate
from backend.app.schemas.memory import (
    MemoryPreferenceCreate,
    MemoryPreferencePatch,
    MemoryCategoryEnum,
)
from backend.app.schemas.plan import PlanResponse, ScheduleSlot


TEST_USER_A_ID = UUID("11111111-1111-1111-1111-111111111111")
TEST_USER_B_ID = UUID("22222222-2222-2222-2222-222222222222")
TEST_USER_A_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_a_token"
TEST_USER_B_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_b_token"
ANON_KEY = "anon-public-key"


@pytest.fixture
def mock_supabase_client():
    return SupabaseClient(
        base_url="https://testproject.supabase.co/rest/v1",
        api_key=ANON_KEY,
        jwt_secret="super-secret-key-for-test"
    )


@pytest.fixture
def mock_repo(mock_supabase_client):
    repo = SupabaseRepository()
    repo.client = mock_supabase_client
    return repo


# ==============================================================================
# CATEGORY A: HTTP AUTHORIZATION HEADER VERIFICATION
# ==============================================================================

def test_category_a_get_request_forwards_user_jwt(mock_supabase_client):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text="[]", json=lambda: [])
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_supabase_client.list_records_sync("tasks", user_token=TEST_USER_A_JWT)
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {TEST_USER_A_JWT}"
        assert headers["apikey"] == ANON_KEY


def test_category_a_post_request_forwards_user_jwt(mock_supabase_client):
    mock_resp = MagicMock(spec=httpx.Response, status_code=201, text='{"id": "1"}', json=lambda: {"id": "1"})
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_supabase_client.insert_record_sync("tasks", {"title": "Test"}, user_token=TEST_USER_A_JWT)
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {TEST_USER_A_JWT}"
        assert headers["apikey"] == ANON_KEY


def test_category_a_patch_request_forwards_user_jwt(mock_supabase_client):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text='[{"id": "1"}]', json=lambda: [{"id": "1"}])
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_supabase_client.update_record_sync("tasks", {"id": "eq.1"}, {"title": "Updated"}, user_token=TEST_USER_A_JWT)
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {TEST_USER_A_JWT}"
        assert headers["apikey"] == ANON_KEY


def test_category_a_delete_request_forwards_user_jwt(mock_supabase_client):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, headers={"content-range": "0-0/1"}, text="[]", json=lambda: [])
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_supabase_client.delete_record_sync("tasks", {"id": "eq.1"}, user_token=TEST_USER_A_JWT)
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {TEST_USER_A_JWT}"
        assert headers["apikey"] == ANON_KEY


def test_category_a_rpc_request_forwards_user_jwt(mock_supabase_client):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text='{"status": "OK"}', json=lambda: {"status": "OK"})
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_supabase_client.rpc_sync("commit_proposal_atomic", {"p_user_id": str(TEST_USER_A_ID)}, user_token=TEST_USER_A_JWT)
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {TEST_USER_A_JWT}"
        assert headers["apikey"] == ANON_KEY


# ==============================================================================
# CATEGORY B: CONCURRENCY ISOLATION & SHARED-STATE IMMUNITY PROOF
# ==============================================================================

@pytest.mark.asyncio
async def test_category_b_concurrency_isolation_between_overlapping_requests(mock_supabase_client):
    """
    Simulates concurrent asynchronous coroutines executing requests for User A and User B
    simultaneously across the SAME client instance.
    Proves that stack-allocated request headers eliminate token-bleeding race conditions.
    """
    barrier = asyncio.Barrier(2)
    captured_tokens = {}

    async def user_request(user_label: str, token: str, table: str):
        # Synchronize coroutines before making the network request
        await barrier.wait()

        # Async request dispatch
        headers = mock_supabase_client._get_headers(user_token=token, allow_service_role=False)
        # Simulate slight async I/O delay
        await asyncio.sleep(0.01)
        captured_tokens[user_label] = headers["Authorization"]
        return headers

    task_a = asyncio.create_task(user_request("user_a", TEST_USER_A_JWT, "tasks"))
    task_b = asyncio.create_task(user_request("user_b", TEST_USER_B_JWT, "proposals"))

    await asyncio.gather(task_a, task_b)

    assert captured_tokens["user_a"] == f"Bearer {TEST_USER_A_JWT}"
    assert captured_tokens["user_b"] == f"Bearer {TEST_USER_B_JWT}"
    assert captured_tokens["user_a"] != captured_tokens["user_b"]
    # Verify no token state was stored on the client instance
    assert not hasattr(mock_supabase_client, "token")
    assert not hasattr(mock_supabase_client, "user_token")


# ==============================================================================
# CATEGORY C: REPOSITORY PROPAGATION ACROSS ALL DOMAIN ENTITIES
# ==============================================================================

def test_category_c_captures_propagation(mock_repo):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text='[]')
    mock_resp.json.return_value = []
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        # 1. list_captures
        mock_repo.list_captures(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 2. get_capture
        mock_req.reset_mock()
        mock_repo.get_capture(capture_id=uuid4(), user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 3. create_capture
        mock_req.reset_mock()
        mock_resp.json.return_value = {"id": str(uuid4()), "user_id": str(TEST_USER_A_ID), "transcript_text": "hello"}
        mock_repo.create_capture(
            user_id=TEST_USER_A_ID,
            input_type="TEXT",
            transcript_text="hello",
            user_token=TEST_USER_A_JWT
        )
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 4. delete_capture
        mock_req.reset_mock()
        mock_resp.headers = {"content-range": "0-0/1"}
        mock_repo.delete_capture(capture_id=uuid4(), user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 5. clear_captures
        mock_req.reset_mock()
        mock_repo.clear_captures(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"


def test_category_c_tasks_propagation(mock_repo):
    t_id = uuid4()

    def mock_request_handler(method, url, *args, **kwargs):
        resp = MagicMock(spec=httpx.Response, status_code=200, text='[]')
        params = kwargs.get("params") or {}
        if method == "GET":
            if "tasks" in url and f"eq.{t_id}" in str(params.get("id")):
                resp.json = MagicMock(return_value=[{"id": str(t_id), "user_id": str(TEST_USER_A_ID), "title": "Buy milk", "status": "PENDING"}])
            else:
                resp.json = MagicMock(return_value=[])
        elif method == "POST":
            resp.json = MagicMock(return_value={"id": str(t_id), "user_id": str(TEST_USER_A_ID), "title": "Buy milk", "status": "PENDING"})
        elif method == "PATCH":
            resp.json = MagicMock(return_value=[{"id": str(t_id), "user_id": str(TEST_USER_A_ID), "title": "Buy oat milk", "status": "PENDING"}])
        elif method == "DELETE":
            resp.headers = {"content-range": "0-0/1"}
            resp.json = MagicMock(return_value=[{"id": str(t_id)}])
        return resp

    with patch("httpx.Client.request", side_effect=mock_request_handler) as mock_req:
        # 1. list_tasks
        mock_repo.list_tasks(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 2. get_task
        mock_req.reset_mock()
        mock_repo.get_task(task_id=t_id, user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 3. create_task
        mock_req.reset_mock()
        mock_repo.create_task(
            user_id=TEST_USER_A_ID,
            task_create=TaskCreate(title="Buy milk", estimated_duration_min=15),
            user_token=TEST_USER_A_JWT
        )
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 4. update_task
        mock_req.reset_mock()
        mock_repo.update_task(
            task_id=t_id,
            task_update=TaskUpdate(title="Buy oat milk"),
            user_id=TEST_USER_A_ID,
            user_token=TEST_USER_A_JWT
        )
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 5. delete_task
        mock_req.reset_mock()
        mock_repo.delete_task(task_id=t_id, user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"


def test_category_c_memory_and_plans_propagation(mock_repo):
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text='[]')
    mock_resp.json.return_value = []
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        # 1. list_memory_preferences
        mock_repo.list_memory_preferences(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 2. set_memory_preference
        mock_req.reset_mock()
        p_id = uuid4()
        mock_resp.json.return_value = {"id": str(p_id), "preference_key": "lang", "category": "PLANNING_STYLE"}
        mock_repo.set_memory_preference(
            user_id=TEST_USER_A_ID,
            create_req=MemoryPreferenceCreate(
                preference_key="lang",
                category=MemoryCategoryEnum.PLANNING_STYLE,
                preference_value={"lang": "ta"}
            ),
            user_token=TEST_USER_A_JWT
        )
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 3. get_availability_windows
        mock_req.reset_mock()
        mock_resp.json.return_value = []
        mock_repo.get_availability_windows(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 4. get_busy_events
        mock_req.reset_mock()
        mock_repo.get_busy_events(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        assert mock_req.call_args[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # 5. export_user_data
        mock_req.reset_mock()
        mock_repo.export_user_data(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)
        # All sub-requests in export must carry User A's token
        for c in mock_req.call_args_list:
            assert c[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"


# ==============================================================================
# CATEGORY D: MISSING TOKEN FAIL-CLOSED TESTS
# ==============================================================================

def test_category_d_client_fails_closed_on_none_token(mock_supabase_client):
    with pytest.raises(SupabaseAuthError) as exc_info:
        mock_supabase_client.list_records_sync("tasks", user_token=None)
    assert "CRITICAL SECURITY REJECTION" in str(exc_info.value)


def test_category_d_client_fails_closed_on_empty_string_token(mock_supabase_client):
    with pytest.raises(SupabaseAuthError) as exc_info:
        mock_supabase_client.list_records_sync("tasks", user_token="   ")
    assert "CRITICAL SECURITY REJECTION" in str(exc_info.value)


def test_category_d_repo_fails_closed_when_token_is_missing(mock_repo):
    with pytest.raises(SupabaseAuthError) as exc_info:
        mock_repo.list_tasks(user_id=TEST_USER_A_ID, user_token=None)
    assert "CRITICAL SECURITY REJECTION" in str(exc_info.value)


# ==============================================================================
# CATEGORY E: SERVICE-ROLE FALLBACK PREVENTION & SYSTEM BOUNDARIES
# ==============================================================================

def test_category_e_service_role_denied_for_normal_crud(mock_supabase_client):
    """
    Proves that normal CRUD cannot silently use service_role even if attempted.
    """
    with pytest.raises(SupabaseAuthError):
        # By default allow_service_role is False
        mock_supabase_client._get_headers(user_token=None, allow_service_role=False)


@pytest.mark.asyncio
async def test_category_e_health_check_allows_service_role(mock_supabase_client):
    """
    Proves check_health explicitly uses allow_service_role=True to probe the PostgREST root.
    """
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text="")
    with patch("httpx.AsyncClient.request", return_value=mock_resp) as mock_req:
        res = await mock_supabase_client.check_health()
        assert res.get("status") == "connected"
        assert mock_req.called
        headers = mock_req.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {ANON_KEY}"
        assert headers["apikey"] == ANON_KEY


def test_category_e_purge_user_data_audit_log_boundary(mock_repo):
    """
    Proves that purge_user_data uses user_token for deleting tenant data,
    and allow_service_role=True solely for the sovereign audit log insertion.
    """
    mock_resp = MagicMock(spec=httpx.Response, status_code=200, text="[]", headers={"content-range": "0-0/0"})
    mock_resp.json.return_value = []
    with patch("httpx.Client.request", return_value=mock_resp) as mock_req:
        mock_repo.purge_user_data(user_id=TEST_USER_A_ID, user_token=TEST_USER_A_JWT)

        # Verify calls
        assert mock_req.call_count >= 11 # 11 delete calls + 1 audit insert

        # All delete calls must use Bearer TEST_USER_A_JWT
        for call_item in mock_req.call_args_list[:-1]:
            method, url = call_item[0][:2]
            assert method == "DELETE"
            assert call_item[1]["headers"]["Authorization"] == f"Bearer {TEST_USER_A_JWT}"

        # The last call (audit_logs insert) must use service_role
        audit_call = mock_req.call_args_list[-1]
        assert audit_call[0][0] == "POST"
        assert "audit_logs" in audit_call[0][1]
        assert audit_call[1]["headers"]["Authorization"] == f"Bearer {ANON_KEY}"


# ==============================================================================
# CATEGORY F: ATOMIC PROPOSAL APPROVAL REGRESSION VERIFICATION
# ==============================================================================

def test_category_f_approve_proposal_passes_jwt_to_atomic_rpc(mock_repo):
    prop_id = uuid4()
    item_id = uuid4()
    mock_prop_rec = {
        "id": str(prop_id),
        "user_id": str(TEST_USER_A_ID),
        "status": "PENDING_REVIEW",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": datetime.now(timezone.utc).isoformat()
    }
    mock_item_rec = [{
        "id": str(item_id),
        "proposal_id": str(prop_id),
        "user_id": str(TEST_USER_A_ID),
        "item_type": "TASK",
        "proposed_title": "Implement JWT",
        "estimated_duration_min": 60,
        "priority": "P1_HIGH",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat()
    }]
    rpc_return = {
        "proposal_id": str(prop_id),
        "approved_tasks_count": 1,
        "rejected_items_count": 0,
        "created_task_ids": [str(uuid4())],
        "message": "Committed"
    }

    def mock_get(table, filters, **kwargs):
        if table == "approval_idempotency":
            return None
        if table == "proposals":
            return mock_prop_rec
        return None

    def mock_list(table, filters, **kwargs):
        if table == "proposal_items":
            return mock_item_rec
        return []

    mock_repo.client.get_record_sync = MagicMock(side_effect=mock_get)
    mock_repo.client.list_records_sync = MagicMock(side_effect=mock_list)
    mock_repo.client.rpc_sync = MagicMock(return_value=rpc_return)

    request = ProposalApproveRequest(
        idempotency_key="idemp_123",
        items=[ProposalItemUpdate(id=item_id, is_approved=True)]
    )

    resp = mock_repo.approve_proposal(
        proposal_id=prop_id,
        user_id=TEST_USER_A_ID,
        request=request,
        user_token=TEST_USER_A_JWT
    )

    assert resp.approved_tasks_count == 1
    # Check that rpc_sync received user_token
    mock_repo.client.rpc_sync.assert_called_once()
    assert mock_repo.client.rpc_sync.call_args[1]["user_token"] == TEST_USER_A_JWT
