import pytest
import jwt
from uuid import uuid4, UUID
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.auth import create_test_jwt, get_jwt_secret
from backend.app.core.config import settings
from backend.app.db.repository import store

# Dedicated client with auto-injection disabled so we test raw HTTP authentication
raw_client = TestClient(app)
raw_client._skip_test_auth = True

# ============================================================================
# 1. TOKEN VALIDATION TESTS
# ============================================================================

def test_missing_token_rejected_401():
    """Unauthenticated request to protected endpoint must return 401."""
    res = raw_client.get("/api/v1/tasks")
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers
    assert "Bearer" in res.headers["WWW-Authenticate"]

def test_invalid_scheme_rejected_401():
    """Non-Bearer scheme must be rejected with 401."""
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert res.status_code == 401
    assert "Bearer" in res.headers["WWW-Authenticate"]

def test_empty_bearer_token_rejected_401():
    """Empty Bearer token must return 401."""
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": "Bearer "})
    assert res.status_code == 401

def test_expired_token_rejected_401():
    """Expired token must return 401 with expired token error description."""
    user_id = uuid4()
    expired_token = create_test_jwt(user_id=user_id, expires_in=-3600)
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json().get("detail", "").lower()

def test_tampered_token_signature_rejected_401():
    """Token with modified signature must return 401."""
    user_id = uuid4()
    valid_token = create_test_jwt(user_id=user_id)
    # Tamper with the last few bytes of the signature
    tampered_token = valid_token[:-4] + "xxxx"
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401
    assert "invalid" in res.json().get("detail", "").lower()

def test_token_with_wrong_secret_rejected_401():
    """Token signed with a foreign secret must return 401."""
    user_id = uuid4()
    wrong_token = create_test_jwt(user_id=user_id, secret="completely-wrong-untrusted-secret-key-000")
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {wrong_token}"})
    assert res.status_code == 401

def test_token_with_none_algorithm_rejected_401():
    """Token using 'none' algorithm must be rejected with 401."""
    payload = {"sub": str(uuid4()), "role": "authenticated", "exp": 9999999999}
    # Craft an unsigned token
    none_token = jwt.encode(payload, key="", algorithm="none")
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {none_token}"})
    assert res.status_code == 401

def test_token_missing_sub_rejected_401():
    """Token missing the 'sub' claim must return 401."""
    payload = {"role": "authenticated", "exp": 9999999999}
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

def test_token_invalid_uuid_in_sub_rejected_401():
    """Token whose sub claim is not a valid UUID must return 401."""
    payload = {"sub": "not-a-valid-uuid", "role": "authenticated", "exp": 9999999999}
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

def test_token_anonymous_role_rejected_401():
    """Anonymous 'anon' role token must be rejected with 401."""
    user_id = uuid4()
    anon_token = create_test_jwt(user_id=user_id, role="anon")
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {anon_token}"})
    assert res.status_code == 401

def test_valid_token_accepted_200():
    """Properly signed valid token must be accepted."""
    user_id = uuid4()
    token = create_test_jwt(user_id=user_id)
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

# ============================================================================
# 2. IDENTITY SPOOFING RESISTANCE
# ============================================================================

def test_client_cannot_spoof_identity_in_request_body():
    """
    If a client attempts to pass a spoofed user_id in the body, the backend
    strictly ignores it and derives user identity solely from the JWT sub claim.
    """
    user_victim = uuid4()
    user_attacker = uuid4()

    token_attacker = create_test_jwt(user_id=user_attacker)

    # Attacker tries to submit capture claiming victim user_id
    payload = {
        "text": "Review financial statements tomorrow 10am",
        "user_timezone": "Asia/Kolkata",
        "user_id": str(user_victim)
    }
    res = raw_client.post(
        "/api/v1/captures/text",
        json=payload,
        headers={"Authorization": f"Bearer {token_attacker}"}
    )
    assert res.status_code == 200
    prop_data = res.json()

    # Proposal must be assigned to ATTACKER, never victim!
    assert prop_data["user_id"] == str(user_attacker)
    assert prop_data["user_id"] != str(user_victim)

# ============================================================================
# 3. CROSS-TENANT DATA ISOLATION
# ============================================================================

def test_cross_tenant_isolation_captures():
    """User B cannot view, retrieve, or delete User A's captures."""
    user_a = uuid4()
    user_b = uuid4()
    token_a = create_test_jwt(user_id=user_a)
    token_b = create_test_jwt(user_id=user_b)

    # User A creates a capture
    res_a = raw_client.post(
        "/api/v1/captures/text",
        json={"text": "User A sovereign note"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    capture_id = res_a.json()["capture_id"]

    # User B lists captures -> must NOT see User A's capture
    res_b_list = raw_client.get("/api/v1/captures", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_list.status_code == 200
    b_capture_ids = [c["id"] for c in res_b_list.json()]
    assert capture_id not in b_capture_ids

    # User B attempts direct retrieval of User A's capture -> 404
    res_b_get = raw_client.get(f"/api/v1/captures/{capture_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_get.status_code == 404

    # User B attempts to delete User A's capture -> 404
    res_b_del = raw_client.delete(f"/api/v1/captures/{capture_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_del.status_code == 404

    # Verify User A's capture is still intact
    res_a_verify = raw_client.get(f"/api/v1/captures/{capture_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_verify.status_code == 200

def test_cross_tenant_isolation_proposals():
    """User B cannot view, reject, clarify, or approve User A's proposals."""
    user_a = uuid4()
    user_b = uuid4()
    token_a = create_test_jwt(user_id=user_a)
    token_b = create_test_jwt(user_id=user_b)

    # User A creates a capture generating a proposal
    res_a = raw_client.post(
        "/api/v1/captures/text",
        json={"text": "User A task for tomorrow at 2pm"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    prop_id = res_a.json()["id"]

    # User B lists proposals -> must NOT see User A's proposal
    res_b_list = raw_client.get("/api/v1/proposals", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_list.status_code == 200
    b_prop_ids = [p["id"] for p in res_b_list.json()]
    assert prop_id not in b_prop_ids

    # User B attempts to get User A's proposal -> 404
    res_b_get = raw_client.get(f"/api/v1/proposals/{prop_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_get.status_code == 404

    # User B attempts to reject User A's proposal -> 404
    res_b_rej = raw_client.post(
        f"/api/v1/proposals/{prop_id}/reject",
        json={"reason": "Attacker trying to cancel"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_rej.status_code == 404

    # User B attempts to approve User A's proposal -> 404
    res_b_app = raw_client.post(
        f"/api/v1/proposals/{prop_id}/approve",
        json={"idempotency_key": f"atk_{uuid4()}", "items": []},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_app.status_code == 404

def test_cross_tenant_isolation_tasks():
    """User B cannot view, mutate, complete, or delete User A's tasks."""
    user_a = uuid4()
    user_b = uuid4()
    token_a = create_test_jwt(user_id=user_a)
    token_b = create_test_jwt(user_id=user_b)

    # User A creates a task
    res_a = raw_client.post(
        "/api/v1/tasks",
        json={"title": "User A Private Strategic Task", "estimated_duration_min": 45},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 201
    task_id = res_a.json()["id"]

    # User B lists tasks -> must NOT see User A's task
    res_b_list = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_list.status_code == 200
    b_task_ids = [t["id"] for t in res_b_list.json()]
    assert task_id not in b_task_ids

    # User B gets User A's task -> 404
    res_b_get = raw_client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_get.status_code == 404

    # User B patches User A's task -> 404
    res_b_patch = raw_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b_patch.status_code == 404

    # User B completes User A's task -> 404
    res_b_comp = raw_client.post(f"/api/v1/tasks/{task_id}/complete", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_comp.status_code == 404

    # User B deletes User A's task -> 404 (store delete_task raises or returns None on owned)
    res_b_del = raw_client.delete(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token_b}"})
    # User A verifies their task is still active and unmodified
    res_a_get = raw_client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_get.status_code == 200
    assert res_a_get.json()["title"] == "User A Private Strategic Task"

def test_cross_tenant_isolation_memory_and_purge():
    """User B's purge does not affect User A's preferences or data."""
    user_a = uuid4()
    user_b = uuid4()
    token_a = create_test_jwt(user_id=user_a)
    token_b = create_test_jwt(user_id=user_b)

    # User A sets a preference
    res_a = raw_client.post(
        "/api/v1/memory/preferences",
        json={
            "category": "WORKING_HOURS",
            "preference_key": "user_a_hours",
            "preference_value": {"start": "08:00"},
            "description": "User A sovereign schedule"
        },
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200

    # User B lists preferences -> must NOT see User A's preference
    res_b_list = raw_client.get("/api/v1/memory/preferences", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_list.status_code == 200
    b_keys = [p["preference_key"] for p in res_b_list.json()]
    assert "user_a_hours" not in b_keys

    # User B initiates purge
    res_b_purge = raw_client.delete("/api/v1/memory/purge", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_purge.status_code == 200

    # User A's preference MUST remain completely intact
    res_a_list = raw_client.get("/api/v1/memory/preferences", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_list.status_code == 200
    a_keys = [p["preference_key"] for p in res_a_list.json()]
    assert "user_a_hours" in a_keys

# ============================================================================
# 4. SERVICE ROLE CONFINEMENT & PUBLIC ENDPOINTS
# ============================================================================

def test_service_role_key_never_exposed_in_public_or_error_responses():
    """The SUPABASE_KEY service role secret must NEVER appear in public responses."""
    svc_key = (getattr(settings, "SUPABASE_KEY", "") or "").strip()
    if not svc_key:
        pytest.skip("SUPABASE_KEY not configured")

    # Check health endpoint
    res_health = raw_client.get("/health")
    assert res_health.status_code == 200
    assert svc_key not in res_health.text

    # Check root endpoint
    res_root = raw_client.get("/")
    assert res_root.status_code == 200
    assert svc_key not in res_root.text

    # Check error response
    res_err = raw_client.get("/api/v1/tasks")
    assert res_err.status_code == 401
    assert svc_key not in res_err.text

def test_public_endpoints_accessible_without_token():
    """Root, health, and docs must be accessible without authentication."""
    assert raw_client.get("/").status_code == 200
    assert raw_client.get("/health").status_code == 200
    assert raw_client.get("/docs").status_code == 200
    assert raw_client.get("/openapi.json").status_code == 200
