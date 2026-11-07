import pytest
from datetime import date
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.repository import store

client = TestClient(app)

def test_full_end_to_end_thozhi_pipeline():
    """
    Complete lifecycle integration test:
    1. Multilingual Audio/Text Capture
    2. Zero Silent Task verification
    3. Proposal generation with dependencies
    4. Explicit user approval transaction
    5. Deterministic DAG scheduling and capacity calculation
    """
    # Step 1: Capture unstructured Tanglish thought
    thought = "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."
    resp_capture = client.post("/api/v1/captures/text", json={"text": thought})
    assert resp_capture.status_code == 200
    proposal = resp_capture.json()
    
    assert proposal["status"] == "PENDING_REVIEW"
    assert len(proposal["items"]) == 2
    
    call_item = next(i for i in proposal["items"] if "client call" in i["proposed_title"].lower())
    report_item = next(i for i in proposal["items"] if "report" in i["proposed_title"].lower())
    
    # Step 2: Verify zero silent tasks created
    tasks_before_approval = client.get("/api/v1/tasks").json()
    assert not any(t["origin_proposal_item_id"] == call_item["id"] for t in tasks_before_approval)
    assert not any(t["origin_proposal_item_id"] == report_item["id"] for t in tasks_before_approval)

    # Step 3: Human User reviews & commits approval
    idempotency_key = str(uuid4())
    approval_payload = {
        "idempotency_key": idempotency_key,
        "items": [
            {
                "id": call_item["id"],
                "proposed_title": "Attend Client Review Call",
                "estimated_duration_min": 45,
                "is_approved": True
            },
            {
                "id": report_item["id"],
                "proposed_title": "Submit Final Project Report",
                "estimated_duration_min": 60,
                "is_approved": True
            }
        ]
    }
    
    resp_approve = client.post(f"/api/v1/proposals/{proposal['id']}/approve", json=approval_payload)
    assert resp_approve.status_code == 200
    approval_res = resp_approve.json()
    assert approval_res["approved_tasks_count"] == 2
    assert len(approval_res["created_task_ids"]) == 2

    # Step 4: Verify tasks now exist in database
    tasks_after_approval = client.get("/api/v1/tasks").json()
    created_task_ids = approval_res["created_task_ids"]
    matched_tasks = [t for t in tasks_after_approval if t["id"] in created_task_ids]
    assert len(matched_tasks) == 2

    # Step 5: Test Planning & Capacity Engine
    plan_req = {
        "target_date": date.today().isoformat()
    }
    resp_plan = client.post("/api/v1/plans/generate", json=plan_req)
    assert resp_plan.status_code == 200
    plan_data = resp_plan.json()
    
    assert plan_data["status"] == "PROPOSED"
    assert plan_data["total_available_minutes"] > 0
    assert plan_data["total_scheduled_minutes"] >= 105 # 45 + 60
    assert len(plan_data["slots"]) >= 2

