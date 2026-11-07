import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.supabase_client import supabase_client
from backend.app.db.repository import store
from backend.app.core.errors import AppException

client = TestClient(app)

def test_settings_whitespace_stripping():
    """Verify that settings strip leading/trailing whitespace automatically."""
    assert not settings.GNANI_API_KEY.startswith(" ")
    assert not settings.GNANI_API_KEY.endswith(" ")
    assert settings.API_V1_STR == "/api/v1"

@pytest.mark.asyncio
async def test_supabase_client_configuration():
    """Verify Supabase client configuration and health check logic."""
    health = await supabase_client.check_health()
    assert "status" in health
    assert health["status"] in ("connected", "offline", "unconfigured")

def test_primary_gnani_configuration():
    """Verify that Gnani Prisma v3 is recognized as the primary ASR engine."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["primary_asr"]["engine"] == "Gnani AI Prisma v3"
    assert data["primary_asr"]["model"] == "prisma-v3.0"
    assert data["database"]["status"] in ("connected", "offline", "unconfigured")

def test_rfc7807_exception_handler():
    """Verify that custom application exceptions serialize to RFC 7807 Problem Details."""
    # Attempting to fetch non-existent proposal returns 404 with problem details
    fake_id = uuid4()
    response = client.get(f"/api/v1/proposals/{fake_id}")
    assert response.status_code == 404
    data = response.json()
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert data["status"] == 404

def test_user_tenant_isolation():
    """Verify that tasks from user A cannot leak into queries for user B."""
    user_a = uuid4()
    user_b = uuid4()
    
    # Create proposal and tasks for user_a
    from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction
    from backend.app.schemas.proposal import ProposalApproveRequest, ProposalItemDecision
    
    extraction = ExtractionResponse(
        intent_summary="Private project tasks",
        detected_language="English",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item_a",
                item_type="TASK",
                proposed_title="User A Secret Blueprint",
                source_expression="blueprint draft",
                priority="P1_CRITICAL",
                confidence=0.9
            )
        ]
    )
    
    prop_a = store.create_proposal_from_extraction(user_id=user_a, extraction=extraction)
    approve_req = ProposalApproveRequest(
        idempotency_key=f"idemp_{uuid4()}",
        items=[
            ProposalItemDecision(
                id=prop_a.items[0].id,
                is_approved=True,
                proposed_title=prop_a.items[0].proposed_title
            )
        ]
    )
    store.approve_proposal(proposal_id=prop_a.id, user_id=user_a, request=approve_req)
    
    # Query tasks for user_a vs user_b
    tasks_a = store.list_tasks(user_id=user_a)
    tasks_b = store.list_tasks(user_id=user_b)
    
    assert len(tasks_a) >= 1
    assert any(t.title == "User A Secret Blueprint" for t in tasks_a)
    assert not any(t.title == "User A Secret Blueprint" for t in tasks_b)

