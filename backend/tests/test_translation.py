import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.repository import store
from backend.app.schemas.intent import ExtractionResponse, ProposedItemExtraction, ClarificationQuestion, ItemTypeEnum, PriorityEnum
from backend.app.schemas.memory import MemoryCategoryEnum
from backend.app.providers.translation.sarvam import SarvamTranslationProvider

client = TestClient(app)

@pytest.mark.asyncio
async def test_sarvam_provider_tamil_to_english_translation():
    provider = SarvamTranslationProvider()
    input_text = "நாளைக்கு காலை ஆறு மணிக்குள்ள ஒரு submission பண்ணனும்."
    result = await provider.translate(input_text, source_language="ta", target_language="en")
    
    assert result.translated_text
    assert "submission" in result.translated_text.lower() or "submit" in result.translated_text.lower()
    assert result.target_language in ["en-IN", "en"]


@pytest.mark.asyncio
async def test_sarvam_provider_english_to_tamil_translation():
    provider = SarvamTranslationProvider()
    input_text = "I need to finish my project report by Friday."
    result = await provider.translate(input_text, source_language="en", target_language="ta")
    
    assert result.translated_text
    assert provider.has_tamil_script(result.translated_text)
    assert result.target_language in ["ta-IN", "ta"]


@pytest.mark.asyncio
async def test_sarvam_provider_tanglish_to_english_translation():
    provider = SarvamTranslationProvider()
    input_text = "Naalaikku morning ten manikku meeting irukku."
    result = await provider.translate(input_text, source_language="tanglish", target_language="en")
    
    assert result.translated_text
    assert "meeting" in result.translated_text.lower()
    assert result.target_language in ["en-IN", "en"]


@pytest.mark.asyncio
async def test_proposal_translation_preserves_original_invariants():
    """
    Core Invariants:
    1. original_transcript is NEVER overwritten.
    2. source_expression is NEVER altered.
    3. normalized_deadline, estimated_duration_min, priority are 100% preserved.
    4. Reverting to 'original' restores original title and transcript instantly.
    """
    user_id = store.default_user_id
    raw_tamil = "நாளைக்கு காலை 10 மணிக்கு க்ளையண்ட் மீட்டிங் நடத்த வேண்டும்."
    
    extraction = ExtractionResponse(
        transcript_text=raw_tamil,
        intent_summary="வாடிக்கையாளர் மீட்டிங் மற்றும் திட்டமிடல்",
        detected_language="ta",
        extracted_items=[
            ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.TASK,
                proposed_title="க்ளையண்ட் மீட்டிங்",
                description="முக்கிய திட்ட விவாதம்",
                source_expression="க்ளையண்ட் மீட்டிங் நடத்த வேண்டும்",
                deadline_expression="நாளைக்கு காலை 10 மணி",
                normalized_deadline_iso="2026-11-08T10:00:00+05:30",
                estimated_duration_min=45,
                priority=PriorityEnum.P1_CRITICAL
            )
        ],
        clarifications=[
            ClarificationQuestion(
                id="clar_1",
                question_text="மீட்டிங் கால அவகாசம் எவ்வளவு?",
                suggested_options=["30 mins", "45 mins", "1 hour"]
            )
        ]
    )

    proposal = store.create_proposal_from_extraction(user_id=user_id, extraction=extraction)
    prop_id = proposal.id

    assert proposal.display_language == "original"
    assert proposal.original_transcript == raw_tamil
    assert proposal.items[0].proposed_title == "க்ளையண்ட் மீட்டிங்"
    assert proposal.items[0].estimated_duration_min == 45
    assert proposal.items[0].priority == PriorityEnum.P1_CRITICAL

    # Translate to English via API endpoint
    res_en = client.post(f"/api/v1/proposals/{prop_id}/translate?target_language=en")
    assert res_en.status_code == 200
    data_en = res_en.json()

    assert data_en["display_language"] == "en"
    assert data_en["translation_status"] == "TRANSLATED"
    # Original is intact!
    assert data_en["original_transcript"] == raw_tamil
    # Title translated
    assert data_en["items"][0]["original_title"] == "க்ளையண்ட் மீட்டிங்"
    assert data_en["items"][0]["proposed_title"] != "க்ளையண்ட் மீட்டிங்"
    # Invariants preserved
    assert data_en["items"][0]["estimated_duration_min"] == 45
    assert data_en["items"][0]["priority"] == "P1_CRITICAL"
    assert data_en["items"][0]["source_expression"] == "க்ளையண்ட் மீட்டிங் நடத்த வேண்டும்"

    # Revert to Original language
    res_orig = client.post(f"/api/v1/proposals/{prop_id}/translate?target_language=original")
    assert res_orig.status_code == 200
    data_orig = res_orig.json()

    assert data_orig["display_language"] == "original"
    assert data_orig["translation_status"] == "ORIGINAL"
    assert data_orig["transcript_text"] == raw_tamil
    assert data_orig["items"][0]["proposed_title"] == "க்ளையண்ட் மீட்டிங்"
    assert data_orig["items"][0]["estimated_duration_min"] == 45


@pytest.mark.asyncio
async def test_preferred_display_language_auto_applies_on_capture():
    """
    If user sets preferred_display_language to 'en' in sovereign memory preferences,
    new captures automatically display in English while preserving original spoken Tamil.
    """
    user_id = store.default_user_id
    
    # Set preferred_display_language in memory
    pref_id = uuid4()
    store.memory_preferences[pref_id] = {
        "id": pref_id,
        "user_id": user_id,
        "category": MemoryCategoryEnum.LANGUAGE,
        "preference_key": "preferred_display_language",
        "preference_value": {"display_language": "en"},
        "description": "User prefers English display for all proposals.",
        "is_active": True,
        "consent_level": "USER_APPROVED"
    }

    # Submit text capture with Tamil
    resp = client.post(
        "/api/v1/captures/text",
        json={"text": "நாளைக்கு மாலை ஐந்து மணிக்கு ரிப்போர்ட் அனுப்ப வேண்டும்."}
    )
    assert resp.status_code == 200
    prop_data = resp.json()

    assert prop_data["original_transcript"] == "நாளைக்கு மாலை ஐந்து மணிக்கு ரிப்போர்ட் அனுப்ப வேண்டும்."
    assert prop_data["display_language"] == "en"
    assert prop_data["translation_status"] == "TRANSLATED"

    # Clean up test preference
    del store.memory_preferences[pref_id]
