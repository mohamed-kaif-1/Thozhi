import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.repository import store
from uuid import uuid4, UUID

client = TestClient(app)

def test_zero_silent_task_creation():
    """
    Core Rule Verification:
    Submitting a thought/capture creates a PROPOSAL only.
    It MUST NOT add any task to the tasks table until the user explicitly commits approval.
    """
    initial_tasks_count = len(store.tasks)
    
    # User inputs a Tanglish thought
    thought = "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."
    resp = client.post("/api/v1/captures/text", json={"text": thought})
    assert resp.status_code == 200
    proposal_data = resp.json()
    
    proposal_id = proposal_data["id"]
    items = proposal_data["items"]
    
    assert len(items) == 2
    assert proposal_data["status"] == "PENDING_REVIEW"
    
    # VERIFY: tasks table count has NOT changed!
    assert len(store.tasks) == initial_tasks_count, "VIOLATION: Tasks were silently created before human approval!"

    # Now simulate user review: user approves item 1, rejects item 2
    item_1 = items[0]
    item_2 = items[1]
    
    approve_payload = {
        "idempotency_key": str(uuid4()),
        "items": [
            {
                "id": item_1["id"],
                "proposed_title": item_1["proposed_title"],
                "is_approved": True
            },
            {
                "id": item_2["id"],
                "is_approved": False,
                "rejection_reason": "Will do next week instead"
            }
        ]
    }
    
    approval_resp = client.post(f"/api/v1/proposals/{proposal_id}/approve", json=approve_payload)
    assert approval_resp.status_code == 200
    approval_data = approval_resp.json()
    
    assert approval_data["approved_tasks_count"] == 1
    assert approval_data["rejected_items_count"] == 1
    assert len(approval_data["created_task_ids"]) == 1
    
    # VERIFY: Exactly 1 new task is in the store now
    assert len(store.tasks) == initial_tasks_count + 1
    created_task_id = UUID(approval_data["created_task_ids"][0])
    created_task = store.tasks[created_task_id]
    assert created_task["title"] == item_1["proposed_title"]
    assert created_task["status"] == "PENDING"
