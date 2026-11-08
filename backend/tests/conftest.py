import os
import pytest
from starlette.testclient import TestClient
from uuid import UUID

from backend.app.core.config import settings

# Configure test environment isolation:
# Unit and functional test suites run against isolated InMemoryRepository by default.
# Live Supabase integration tests are explicitly marked with @pytest.mark.live_supabase.
os.environ["DATA_BACKEND"] = ""
settings.DATA_BACKEND = ""

from backend.app.db.repositories.factory import reset_repository, get_repository
reset_repository()
from backend.app.db.repository import store
import backend.app.db.repository as repo_module
repo_module.store = get_repository()

from backend.app.core.auth import create_test_jwt

DEFAULT_TEST_TOKEN = create_test_jwt(repo_module.store.default_user_id)

_orig_request = TestClient.request

def _patched_request(self, method, url, *args, **kwargs):
    # Check if caller disabled test auth auto-injection
    skip_auth = getattr(self, "_skip_test_auth", False) or kwargs.pop("_skip_test_auth", False)

    headers = kwargs.get("headers")
    if headers is None:
        headers = {}
    else:
        headers = dict(headers)

    # Auto-inject valid default test bearer token for legacy tests that do not pass Authorization
    if not skip_auth and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {DEFAULT_TEST_TOKEN}"
        kwargs["headers"] = headers

    return _orig_request(self, method, url, *args, **kwargs)

TestClient.request = _patched_request

def pytest_configure(config):
    config.addinivalue_line("markers", "live_supabase: tests requiring live remote Supabase credentials and database")
