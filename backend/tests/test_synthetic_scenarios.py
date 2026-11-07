import pytest
from datetime import date
from backend.app.providers.nlu.mock import MockNLUProvider
from backend.app.schemas.intent import ItemTypeEnum, PriorityEnum

@pytest.mark.asyncio
async def test_scenario_1_tanglish_client_call_and_report():
    nlu = MockNLUProvider()
    input_text = "Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."
    res = await nlu.extract_intent(input_text, reference_date=date(2026, 11, 10))
    
    assert len(res.extracted_items) == 2
    assert res.extracted_items[0].item_type == ItemTypeEnum.COMMITMENT
    assert res.extracted_items[0].proposed_title == "Attend client call"
    assert res.extracted_items[1].item_type == ItemTypeEnum.TASK
    assert res.extracted_items[1].proposed_title == "Submit project report"
    assert "item_1" in res.extracted_items[1].dependencies

@pytest.mark.asyncio
async def test_scenario_2_conditional_weather_intention():
    nlu = MockNLUProvider()
    input_text = "Mazhai peyyalana cricket vilayadalam."
    res = await nlu.extract_intent(input_text)
    
    assert len(res.extracted_items) == 1
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.CONDITIONAL_INTENTION
    assert "cricket" in item.proposed_title.lower()
    assert item.condition_trigger is not None
    assert "WEATHER_DEPENDENT" in item.uncertainty_flags

@pytest.mark.asyncio
async def test_scenario_3_explicit_cancellation():
    nlu = MockNLUProvider()
    input_text = "Andha meeting vendam, cancel pannidu."
    res = await nlu.extract_intent(input_text)
    
    assert len(res.extracted_items) == 1
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.CANCELLED
    assert "cancel" in item.proposed_title.lower()

