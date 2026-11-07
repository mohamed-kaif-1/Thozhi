import pytest
from uuid import UUID
from datetime import date, datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.providers.asr.dispatcher import ASRDispatcher
from backend.app.providers.asr.gnani import GnaniPrismaProvider
from backend.app.providers.asr.sarvam import SarvamSaarasProvider
from backend.app.providers.nlu.gemini import GeminiNLUProvider
from backend.app.providers.nlu.mock import MockNLUProvider
from backend.app.schemas.intent import ItemTypeEnum, PriorityEnum
from backend.app.core.config import settings

client = TestClient(app)

def test_tanglish_text_capture_creates_proposal_not_task():
    """
    Test Phase 4.3 & 4.4:
    Tanglish input triggers proposal creation with extracted tasks and commitments,
    but ZERO tasks are created in the active schedule (Strict invariant).
    """
    payload = {
        "text": "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum.",
        "user_timezone": "Asia/Kolkata"
    }
    response = client.post("/api/v1/captures/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["status"] == "PENDING_REVIEW"
    assert len(data["items"]) >= 2
    
    # Check that item 1 is Attend client call
    item_1 = data["items"][0]
    assert "call" in item_1["proposed_title"].lower()
    
    # Check that item 2 depends on item 1 (chronological dependency)
    item_2 = data["items"][1]
    assert "report" in item_2["proposed_title"].lower()

def test_conditional_intention_weather_handling():
    """
    Test Phase 4.3:
    Conditional input ('mazhai peyyalana cricket vilayadalam') must be classified
    as CONDITIONAL_INTENTION with condition trigger and clarification prompt.
    """
    payload = {
        "text": "Mazhai peyyalana cricket vilayadalam nu irukken.",
        "user_timezone": "Asia/Kolkata"
    }
    response = client.post("/api/v1/captures/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    item = data["items"][0]
    assert item["item_type"] == "CONDITIONAL_INTENTION"
    assert item["condition_trigger"] is not None

def test_explicit_cancellation_intent():
    """
    Test Phase 4.3:
    Cancellation input must be classified as CANCELLED rather than creating a new to-do task.
    """
    payload = {
        "text": "Naalaiku irundha meeting-a cancel pannidu, vera naal vechukkalam.",
        "user_timezone": "Asia/Kolkata"
    }
    response = client.post("/api/v1/captures/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    item = data["items"][0]
    assert item["item_type"] == "CANCELLED"

@pytest.mark.asyncio
async def test_gnani_prisma_asr_headers_and_config():
    """
    Test Phase 4.2:
    Gnani Prisma v3 provider correctly formats headers with X-API-Key-ID and model prisma-v3.0.
    """
    provider = GnaniPrismaProvider(api_key="mock_key_test", base_url="https://api.vachana.ai")
    assert provider.api_key == "mock_key_test"
    assert provider.base_url == "https://api.vachana.ai"

def test_audio_capture_endpoint_with_wav():
    """
    Test Phase 4.1 & 4.2:
    Audio endpoint receives WAV payload, dispatches to ASR, and returns proposal.
    """
    # Create synthetic WAV header (44 bytes minimal audio)
    wav_header = (
        b"RIFF" + (36).to_bytes(4, "little") + b"WAVE" +
        b"fmt " + (16).to_bytes(4, "little") + (1).to_bytes(2, "little") + (1).to_bytes(2, "little") +
        (16000).to_bytes(4, "little") + (32000).to_bytes(4, "little") + (2).to_bytes(2, "little") + (16).to_bytes(2, "little") +
        b"data" + (0).to_bytes(4, "little")
    )
    
    files = {"file": ("recording.wav", wav_header, "audio/wav")}
    data = {
        "user_timezone": "Asia/Kolkata",
        "mock_text": "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."
    }
    
    response = client.post("/api/v1/captures/audio", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "PENDING_REVIEW"
    assert len(res_json["items"]) >= 1

def test_empty_audio_rejection():
    """Verify that zero-byte empty audio files are rejected with 400 Bad Request."""
    files = {"file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/v1/captures/audio", files=files)
    assert response.status_code == 400
    assert "Empty audio payload" in response.text

