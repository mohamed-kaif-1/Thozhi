import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "THOZHI"
    assert "version" in data

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "The AI proposes. The user decides." in data["message"]

