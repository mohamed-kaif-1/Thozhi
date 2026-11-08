import os
import pytest
import httpx
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.auth import verify_jwt

test_client = TestClient(app)
test_client._skip_test_auth = True

# Supabase Auth configuration from settings
SUPABASE_URL = getattr(settings, "SUPABASE_URL", "")
SUPABASE_KEY = getattr(settings, "SUPABASE_KEY", "")
BASE_AUTH_URL = SUPABASE_URL.replace("/rest/v1/", "").rstrip("/") + "/auth/v1" if SUPABASE_URL else ""


def is_live_supabase_reachable() -> bool:
    if not BASE_AUTH_URL or not SUPABASE_KEY:
        return False
    try:
        res = httpx.get(f"{BASE_AUTH_URL}/health", headers={"apikey": SUPABASE_KEY}, timeout=3.0)
        return res.status_code == 200
    except Exception:
        return False


LIVE_SUPABASE_AVAILABLE = is_live_supabase_reachable()


@pytest.fixture(scope="module")
def synthetic_supabase_user():
    """
    Creates an isolated synthetic user in live Supabase GoTrue Auth,
    obtains a real provider-issued JWT, and guarantees teardown cleanup.
    """
    if not LIVE_SUPABASE_AVAILABLE:
        pytest.skip("Live Supabase Auth endpoint is not reachable or unconfigured.")

    admin_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    email = f"thozhi_test_{uuid4().hex[:8]}@thozhi.ai"
    password = f"P4ssw0rd!_{uuid4().hex[:8]}"

    # 1. Create synthetic user via Admin API
    create_res = httpx.post(
        f"{BASE_AUTH_URL}/admin/users",
        headers=admin_headers,
        json={"email": email, "password": password, "email_confirm": True},
        timeout=5.0
    )
    assert create_res.status_code == 200, f"Failed to create synthetic user: {create_res.text}"
    user_data = create_res.json()
    user_id = user_data["id"]

    # 2. Authenticate to obtain real provider-issued JWT
    token_res = httpx.post(
        f"{BASE_AUTH_URL}/token?grant_type=password",
        headers={"apikey": SUPABASE_KEY},
        json={"email": email, "password": password},
        timeout=5.0
    )
    assert token_res.status_code == 200, f"Failed to acquire token: {token_res.text}"
    token_data = token_res.json()
    access_token = token_data["access_token"]

    yield {
        "user_id": user_id,
        "email": email,
        "token": access_token
    }

    # Teardown: delete synthetic user
    try:
        httpx.delete(f"{BASE_AUTH_URL}/admin/users/{user_id}", headers=admin_headers, timeout=5.0)
    except Exception as exc:
        print(f"Warning: Failed to clean up synthetic user {user_id}: {exc}")


@pytest.mark.live_supabase
@pytest.mark.skipif(not LIVE_SUPABASE_AVAILABLE, reason="Live Supabase GoTrue API is unavailable")
def test_p4_provider_issued_jwt_validation(synthetic_supabase_user):
    """
    Verifies that a genuine token issued by Supabase GoTrue Auth
    is cryptographically verified and validated by THOZHI's backend.
    """
    token = synthetic_supabase_user["token"]
    expected_sub = synthetic_supabase_user["user_id"]

    claims = verify_jwt(token)
    assert claims["sub"] == expected_sub
    assert claims["role"] == "authenticated"
    assert claims["aud"] == "authenticated"
    assert claims.get("email") == synthetic_supabase_user["email"]


@pytest.mark.live_supabase
@pytest.mark.skipif(not LIVE_SUPABASE_AVAILABLE, reason="Live Supabase GoTrue API is unavailable")
def test_p4_backend_endpoint_execution_with_real_jwt(synthetic_supabase_user):
    """
    Verifies calling a protected backend endpoint using a genuine provider-issued JWT
    executes under the user's verified identity and returns HTTP 200.
    """
    token = synthetic_supabase_user["token"]
    res = test_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.live_supabase
@pytest.mark.skipif(not LIVE_SUPABASE_AVAILABLE, reason="Live Supabase GoTrue API is unavailable")
def test_p4_tampered_provider_jwt_rejection(synthetic_supabase_user):
    """
    Verifies that tampering with a genuine provider-issued JWT triggers immediate HTTP 401.
    """
    token = synthetic_supabase_user["token"]
    tampered_token = token[:-5] + "aaaaa"
    res = test_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers
