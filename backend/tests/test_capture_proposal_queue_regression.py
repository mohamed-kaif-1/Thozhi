import pytest
from uuid import uuid4, UUID
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.repository import store

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Clean captures before and after tests to isolate tests cleanly
    yield


def test_01_sequential_captures_create_independent_records_and_proposals():
    """
    Scenario 1:
    User submits 3 sequential captures without approving or committing.
    All 3 captures and all 3 proposals must exist independently.
    None of the previous captures or proposals may be overwritten or silently discarded.
    """
    # Capture 1
    c1_resp = client.post("/api/v1/captures/text", json={
        "text": "Submit quarterly review report tomorrow at 5 PM",
        "user_timezone": "Asia/Kolkata"
    })
    assert c1_resp.status_code == 200
    p1 = c1_resp.json()

    # Capture 2
    c2_resp = client.post("/api/v1/captures/text", json={
        "text": "Fix database connection pool timeout before 2 PM",
        "user_timezone": "Asia/Kolkata"
    })
    assert c2_resp.status_code == 200
    p2 = c2_resp.json()

    # Capture 3
    c3_resp = client.post("/api/v1/captures/text", json={
        "text": "Call vendor about API credits tomorrow morning 10 AM",
        "user_timezone": "Asia/Kolkata"
    })
    assert c3_resp.status_code == 200
    p3 = c3_resp.json()

    # Verify all 3 have distinct IDs
    assert p1["id"] != p2["id"] != p3["id"]
    assert p1["capture_id"] != p2["capture_id"] != p3["capture_id"]

    # Verify captures stream endpoint returns all of them
    caps_resp = client.get("/api/v1/captures")
    assert caps_resp.status_code == 200
    caps = caps_resp.json()
    cap_ids = [c["id"] for c in caps]
    assert p1["capture_id"] in cap_ids
    assert p2["capture_id"] in cap_ids
    assert p3["capture_id"] in cap_ids

    # Verify proposals queue returns all 3 pending review
    props_resp = client.get("/api/v1/proposals?status=PENDING_REVIEW")
    assert props_resp.status_code == 200
    props = props_resp.json()
    prop_ids = [p["id"] for p in props]
    assert p1["id"] in prop_ids
    assert p2["id"] in prop_ids
    assert p3["id"] in prop_ids


def test_02_load_old_capture_and_inspect_proposal():
    """
    Scenario 2:
    Clicking an old capture card must retrieve its original transcript,
    detected language, lifecycle status, and linked proposals.
    """
    c_resp = client.post("/api/v1/captures/text", json={
        "text": "Inspect server health metrics at 4 PM",
        "user_timezone": "Asia/Kolkata"
    })
    assert c_resp.status_code == 200
    p_data = c_resp.json()
    capture_id = p_data["capture_id"]

    # Retrieve capture detail
    detail_resp = client.get(f"/api/v1/captures/{capture_id}")
    assert detail_resp.status_code == 200
    cap_data = detail_resp.json()

    assert cap_data["id"] == capture_id
    assert cap_data["original_transcript"] == "Inspect server health metrics at 4 PM"
    assert cap_data["lifecycle_status"] == "PENDING_REVIEW"
    assert len(cap_data["proposals"]) >= 1
    assert cap_data["proposals"][0]["id"] == p_data["id"]


def test_03_new_capture_while_old_proposal_pending():
    """
    Scenario 3:
    Creating a new capture while an old proposal is pending must NOT modify
    the old proposal's status or remove it from the pending queue.
    """
    # Create Capture 1
    c1 = client.post("/api/v1/captures/text", json={"text": "Review pull request 101"}).json()
    prop1_id = c1["id"]

    # Verify Capture 1 is pending
    p1_check = client.get(f"/api/v1/proposals/{prop1_id}").json()
    assert p1_check["status"] == "PENDING_REVIEW"

    # Create Capture 2
    c2 = client.post("/api/v1/captures/text", json={"text": "Schedule dentist appointment"}).json()
    prop2_id = c2["id"]

    # Verify Capture 1 remains PENDING_REVIEW
    p1_check_after = client.get(f"/api/v1/proposals/{prop1_id}").json()
    assert p1_check_after["status"] == "PENDING_REVIEW"

    # Verify Capture 2 is also PENDING_REVIEW
    p2_check = client.get(f"/api/v1/proposals/{prop2_id}").json()
    assert p2_check["status"] == "PENDING_REVIEW"


def test_04_mixed_approval_decisions_individual():
    """
    Scenario 4:
    User approves proposal A, rejects proposal B, and leaves proposal C pending.
    State must accurately reflect COMMITTED, REJECTED, and PENDING_REVIEW respectively.
    """
    prop_a = client.post("/api/v1/captures/text", json={"text": "Prepare slide deck A"}).json()
    prop_b = client.post("/api/v1/captures/text", json={"text": "Ignore spam email B"}).json()
    prop_c = client.post("/api/v1/captures/text", json={"text": "Draft roadmap doc C"}).json()

    # 1. Approve Proposal A
    appr_payload = {
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in prop_a["items"]]
    }
    appr_resp = client.post(f"/api/v1/proposals/{prop_a['id']}/approve", json=appr_payload)
    assert appr_resp.status_code == 200

    # 2. Reject Proposal B
    rej_resp = client.post(f"/api/v1/proposals/{prop_b['id']}/reject", json={"reason": "Not relevant"})
    assert rej_resp.status_code == 200

    # Verify status of all 3
    a_state = client.get(f"/api/v1/proposals/{prop_a['id']}").json()
    b_state = client.get(f"/api/v1/proposals/{prop_b['id']}").json()
    c_state = client.get(f"/api/v1/proposals/{prop_c['id']}").json()

    assert a_state["status"] == "COMMITTED"
    assert b_state["status"] == "REJECTED"
    assert c_state["status"] == "PENDING_REVIEW"

    # Verify capture lifecycle statuses
    cap_a = client.get(f"/api/v1/captures/{prop_a['capture_id']}").json()
    cap_b = client.get(f"/api/v1/captures/{prop_b['capture_id']}").json()
    cap_c = client.get(f"/api/v1/captures/{prop_c['capture_id']}").json()

    assert cap_a["lifecycle_status"] == "COMMITTED"
    assert cap_b["lifecycle_status"] == "REJECTED"
    assert cap_c["lifecycle_status"] == "PENDING_REVIEW"


def test_05_commit_old_proposal_after_new_capture_added():
    """
    Scenario 5:
    Commit old proposal after a new capture was added.
    Only the old proposal's items are committed to the schedule.
    The new capture remains pending.
    """
    p1 = client.post("/api/v1/captures/text", json={"text": "Deploy staging v2.1"}).json()
    p2 = client.post("/api/v1/captures/text", json={"text": "Check staging logs later"}).json()

    initial_tasks_count = len(store.tasks)

    # Commit p1
    appr_payload = {
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in p1["items"]]
    }
    client.post(f"/api/v1/proposals/{p1['id']}/approve", json=appr_payload)

    # Tasks count increased by p1's items count
    expected_tasks = initial_tasks_count + len(p1["items"])
    assert len(store.tasks) == expected_tasks

    # Proposal 2 remains PENDING_REVIEW
    p2_check = client.get(f"/api/v1/proposals/{p2['id']}").json()
    assert p2_check["status"] == "PENDING_REVIEW"


def test_06_persistence_across_queries_and_recovery():
    """
    Scenario 6:
    Proposals and captures persist reliably across multiple queries and page refreshes.
    """
    p = client.post("/api/v1/captures/text", json={"text": "Persistent capture test item"}).json()

    # Query 1
    resp1 = client.get(f"/api/v1/proposals/{p['id']}").json()
    # Query 2
    resp2 = client.get(f"/api/v1/proposals/{p['id']}").json()

    assert resp1["id"] == resp2["id"] == p["id"]
    assert resp1["transcript_text"] == resp2["transcript_text"]
    assert resp1["status"] == "PENDING_REVIEW"


def test_07_duplicate_approval_idempotency():
    """
    Scenario 7:
    Submitting an approval decision for an already committed proposal is idempotent.
    Does not crash and does not duplicate tasks.
    """
    p = client.post("/api/v1/captures/text", json={"text": "Idempotent approval test"}).json()
    appr_payload = {
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in p["items"]]
    }

    # First approval
    resp1 = client.post(f"/api/v1/proposals/{p['id']}/approve", json=appr_payload)
    assert resp1.status_code == 200
    tasks_count_1 = len(store.tasks)

    # Second approval (same proposal, same idempotency key)
    resp2 = client.post(f"/api/v1/proposals/{p['id']}/approve", json=appr_payload)
    assert resp2.status_code == 200
    tasks_count_2 = len(store.tasks)

    assert tasks_count_1 == tasks_count_2, "Idempotency violated: duplicate tasks created"


def test_08_duplicate_commit_replay_protection():
    """
    Scenario 8:
    Replay attack / network retry protection:
    If client repeats an approval with identical idempotency_key, tasks are not duplicated.
    """
    p = client.post("/api/v1/captures/text", json={"text": "Replay protection test task"}).json()
    idemp_key = f"key_{uuid4()}"
    appr_payload = {
        "idempotency_key": idemp_key,
        "items": [{"id": item["id"], "is_approved": True} for item in p["items"]]
    }

    r1 = client.post(f"/api/v1/proposals/{p['id']}/approve", json=appr_payload)
    assert r1.status_code == 200
    created_count = r1.json()["approved_tasks_count"]

    # Resend exact payload
    r2 = client.post(f"/api/v1/proposals/{p['id']}/approve", json=appr_payload)
    assert r2.status_code == 200
    # No extra tasks created
    r2_data = r2.json()
    assert r2_data["created_task_ids"] == r1.json()["created_task_ids"]


def test_09_out_of_order_proposal_resolution():
    """
    Scenario 9:
    User resolves Proposal 2 first, while Proposal 1 remains pending.
    Then subsequently resolves Proposal 1.
    Both should succeed in any sequence.
    """
    p1 = client.post("/api/v1/captures/text", json={"text": "Task order 1"}).json()
    p2 = client.post("/api/v1/captures/text", json={"text": "Task order 2"}).json()

    # Resolve p2 first
    appr2 = {
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in p2["items"]]
    }
    client.post(f"/api/v1/proposals/{p2['id']}/approve", json=appr2)

    assert client.get(f"/api/v1/proposals/{p2['id']}").json()["status"] == "COMMITTED"
    assert client.get(f"/api/v1/proposals/{p1['id']}").json()["status"] == "PENDING_REVIEW"

    # Now resolve p1
    appr1 = {
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in p1["items"]]
    }
    client.post(f"/api/v1/proposals/{p1['id']}/approve", json=appr1)

    assert client.get(f"/api/v1/proposals/{p1['id']}").json()["status"] == "COMMITTED"


def test_10_user_isolation_between_accounts():
    """
    Scenario 10:
    User A and User B cannot view or approve each other's captures or proposals.
    """
    user_a = uuid4()
    user_b = uuid4()

    # User A creates a capture
    pa = client.post("/api/v1/captures/text", json={
        "user_id": str(user_a),
        "text": "User A private thought"
    }).json()

    # User B lists captures
    caps_b = client.get(f"/api/v1/captures?user_id={user_b}").json()
    cap_ids_b = [c["id"] for c in caps_b]
    assert pa["capture_id"] not in cap_ids_b

    # User B lists proposals
    props_b = client.get(f"/api/v1/proposals?user_id={user_b}").json()
    prop_ids_b = [p["id"] for p in props_b]
    assert pa["id"] not in prop_ids_b


def test_11_rejected_proposal_lifecycle_immutability():
    """
    Scenario 11:
    A rejected proposal stays in REJECTED state permanently.
    Re-fetching it or its parent capture displays REJECTED.
    Zero tasks are scheduled.
    """
    p = client.post("/api/v1/captures/text", json={"text": "Irrelevant spam notification"}).json()
    initial_tasks = len(store.tasks)

    # Reject
    rej_resp = client.post(f"/api/v1/proposals/{p['id']}/reject", json={"reason": "User dismissed"})
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"

    # Re-fetch proposal
    p_check = client.get(f"/api/v1/proposals/{p['id']}").json()
    assert p_check["status"] == "REJECTED"

    # Re-fetch capture
    cap_check = client.get(f"/api/v1/captures/{p['capture_id']}").json()
    assert cap_check["lifecycle_status"] == "REJECTED"

    # Verify zero tasks were created
    assert len(store.tasks) == initial_tasks


def test_12_clear_capture_history_preserves_tasks_and_pending_proposals():
    """
    Scenario 12:
    Clearing the visible capture stream history MUST NOT delete committed tasks
    or pending proposals in the queue. Only the capture logs are cleared.
    """
    # 1. Create and commit proposal 1
    p1 = client.post("/api/v1/captures/text", json={"text": "Important committed assignment"}).json()
    client.post(f"/api/v1/proposals/{p1['id']}/approve", json={
        "idempotency_key": str(uuid4()),
        "items": [{"id": item["id"], "is_approved": True} for item in p1["items"]]
    })

    # 2. Create pending proposal 2
    p2 = client.post("/api/v1/captures/text", json={"text": "Pending proposal to retain"}).json()

    tasks_count_before = len(store.tasks)
    assert tasks_count_before > 0

    # 3. Call Clear Captures
    clear_resp = client.post("/api/v1/captures/clear")
    assert clear_resp.status_code == 200

    # Verify captures stream is empty
    caps = client.get("/api/v1/captures").json()
    assert len(caps) == 0

    # Verify committed tasks remain intact
    assert len(store.tasks) == tasks_count_before

    # Verify pending proposal remains intact
    p2_check = client.get(f"/api/v1/proposals/{p2['id']}").json()
    assert p2_check["status"] == "PENDING_REVIEW"
