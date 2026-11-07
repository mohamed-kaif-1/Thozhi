from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_memory_preference_lifecycle():
    # 1. Set a user preference with explicit consent
    pref_payload = {
        "preference_key": "preferred_focus_time",
        "preference_value": {"slot": "morning", "start_hour": 9},
        "consent_level": "EXPLICIT_CONSENT"
    }
    set_resp = client.post("/api/v1/memory/preferences", json=pref_payload)
    assert set_resp.status_code == 200
    pref_data = set_resp.json()
    assert pref_data["preference_key"] == "preferred_focus_time"
    assert pref_data["is_active"] is True
    
    # 2. List preferences
    list_resp = client.get("/api/v1/memory/preferences")
    assert list_resp.status_code == 200
    all_prefs = list_resp.json()
    assert any(p["preference_key"] == "preferred_focus_time" for p in all_prefs)

    # 3. Revoke/delete preference
    del_resp = client.delete("/api/v1/memory/preferences/preferred_focus_time")
    assert del_resp.status_code == 200
    
    # 4. Confirm gone
    list_resp2 = client.get("/api/v1/memory/preferences")
    assert not any(p["preference_key"] == "preferred_focus_time" for p in list_resp2.json())

