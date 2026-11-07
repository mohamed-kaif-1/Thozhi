import pytest
from datetime import datetime, date
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.intent import ItemTypeEnum, PriorityEnum
from backend.app.providers.nlu.semantic_parser import SemanticIntentParser

client = TestClient(app)
parser = SemanticIntentParser()


@pytest.mark.asyncio
async def test_regression_01_exact_tamil_raven_app():
    """
    Test Case 1: Exact Tamil test sentence from user report.
    Spoken: "நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."
    Must produce:
    - Action: Complete
    - Object: my Raven app
    - Title: Complete my Raven app (no temporal debris)
    - Deadline: Tomorrow at 6:00 PM (18:00)
    - Duration: None / UNSPECIFIED
    - Priority: None / UNSPECIFIED
    """
    text = "நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."
    res = await parser.parse(text)
    assert len(res.extracted_items) == 1
    item = res.extracted_items[0]
    assert item.action.lower() == "complete"
    assert "raven" in item.object.lower()
    assert item.proposed_title == "Complete my Raven app"
    assert "Tomorrow" in item.deadline_expression and "6:00 PM" in item.deadline_expression
    assert "18:00:00" in item.normalized_deadline_iso
    assert item.estimated_duration_min is None
    assert item.duration_source == "UNSPECIFIED"
    assert item.priority is None or item.priority == PriorityEnum.UNSPECIFIED


@pytest.mark.asyncio
async def test_regression_02_tanglish_raven_app():
    """
    Test Case 2: Tanglish test sentence.
    "Naalaikku evening six o'clock kulla ennoda Raven app-a complete pannanum."
    """
    text = "Naalaikku evening six o'clock kulla ennoda Raven app-a complete pannanum."
    res = await parser.parse(text)
    assert len(res.extracted_items) == 1
    item = res.extracted_items[0]
    assert item.action.lower() == "complete"
    assert "raven" in item.object.lower()
    assert item.proposed_title == "Complete my Raven app"
    assert "Tomorrow" in item.deadline_expression and "6:00 PM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_03_english_raven_app():
    """
    Test Case 3: English recognized translation.
    "I need to complete my Raven app by six o'clock tomorrow evening."
    """
    text = "I need to complete my Raven app by six o'clock tomorrow evening."
    res = await parser.parse(text)
    assert len(res.extracted_items) == 1
    item = res.extracted_items[0]
    assert item.action.lower() == "complete"
    assert item.object.lower() == "my raven app"
    assert item.proposed_title == "Complete my Raven app"
    assert "Tomorrow" in item.deadline_expression and "6:00 PM" in item.deadline_expression
    assert item.estimated_duration_min is None
    assert item.priority is None


@pytest.mark.asyncio
async def test_regression_04_action_before_object():
    """
    Test Case 4: Action preceding object.
    "Submit my assignment before Friday."
    """
    text = "Submit my assignment before Friday."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "submit"
    assert "assignment" in item.object.lower()
    assert item.proposed_title == "Submit my assignment"
    assert "Friday" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_05_object_before_action_passive():
    """
    Test Case 5: Object preceding action (passive voice construction).
    "The research paper must be reviewed by tomorrow."
    """
    text = "The research paper must be reviewed by tomorrow."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "review"
    assert "research paper" in item.object.lower()
    assert item.proposed_title == "Review the research paper"
    assert "Tomorrow" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_06_deadline_at_start():
    """
    Test Case 6: Temporal phrase located at the beginning of utterance.
    "Tomorrow at 10 AM, call the client."
    """
    text = "Tomorrow at 10 AM, call the client."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "call"
    assert "client" in item.object.lower()
    assert item.proposed_title == "Call the client"
    assert "10:00 AM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_07_deadline_at_end():
    """
    Test Case 7: Temporal phrase located at the end of utterance.
    "Call the client tomorrow at 10 AM."
    """
    text = "Call the client tomorrow at 10 AM."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "call"
    assert "client" in item.object.lower()
    assert item.proposed_title == "Call the client"
    assert "10:00 AM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_08_multiple_tasks_in_one_sentence():
    """
    Test Case 8: Compound sentence extracting two distinct tasks.
    "Attend client call and submit project report"
    """
    text = "Attend client call and submit project report"
    res = await parser.parse(text)
    assert len(res.extracted_items) == 2
    assert res.extracted_items[0].proposed_title == "Attend client call"
    assert res.extracted_items[1].proposed_title == "Submit project report"


@pytest.mark.asyncio
async def test_regression_09_missing_deadline():
    """
    Test Case 9: Sentence without deadline; deadline must be None.
    "Read the architecture specification."
    """
    text = "Read the architecture specification."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.deadline_expression is None
    assert item.normalized_deadline_iso is None
    assert "UNKNOWN_DEADLINE" in item.uncertainty_flags


@pytest.mark.asyncio
async def test_regression_10_missing_duration_unspecified():
    """
    Test Case 10: Sentence without duration; system must NOT fabricate 30m.
    "Fix the authentication login bug."
    """
    text = "Fix the authentication login bug."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.estimated_duration_min is None
    assert item.duration_source == "UNSPECIFIED"
    assert "UNSPECIFIED_DURATION" in item.uncertainty_flags


@pytest.mark.asyncio
async def test_regression_11_explicit_duration_hours():
    """
    Test Case 11: Explicit duration in hours converted accurately to minutes.
    "Study DSP algorithms for 2 hours."
    """
    text = "Study DSP algorithms for 2 hours."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.estimated_duration_min == 120
    assert item.duration_source == "USER_EXPLICIT"


@pytest.mark.asyncio
async def test_regression_12_explicit_duration_minutes():
    """
    Test Case 12: Explicit duration in minutes.
    "Review PR for 45 minutes."
    """
    text = "Review PR for 45 minutes."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.estimated_duration_min == 45
    assert item.duration_source == "USER_EXPLICIT"


@pytest.mark.asyncio
async def test_regression_13_explicit_priority_critical():
    """
    Test Case 13: Explicit critical priority.
    "Fix critical production outage ASAP."
    """
    text = "Fix critical production outage ASAP."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.priority == PriorityEnum.P1_CRITICAL


@pytest.mark.asyncio
async def test_regression_14_explicit_priority_low():
    """
    Test Case 14: Explicit low priority.
    "Clean up old test files when free."
    """
    text = "Clean up old test files when free."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.priority in (PriorityEnum.P3_LOW, PriorityEnum.BACKBURNER)


@pytest.mark.asyncio
async def test_regression_15_implicit_urgency_without_priority_fabrication():
    """
    Test Case 15: Urgent sounding context without explicit priority level.
    "Submit grant application before portal closes."
    Must NOT invent P2.
    """
    text = "Submit grant application before portal closes."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.priority is None or item.priority == PriorityEnum.UNSPECIFIED
    assert "UNSPECIFIED_PRIORITY" in item.uncertainty_flags


@pytest.mark.asyncio
async def test_regression_16_negation_and_cancellation():
    """
    Test Case 16: Explicit cancellation / negative constraint.
    "Do not deploy to production today."
    """
    text = "Do not deploy to production today."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.CANCELLED
    assert "EXPLICIT_CANCELLATION" in item.uncertainty_flags


@pytest.mark.asyncio
async def test_regression_17_completed_activity_english():
    """
    Test Case 17: Retrospective completed activity in English.
    "I already completed the database assignment."
    Must be marked COMPLETED so it is filtered from active scheduling.
    """
    text = "I already completed the database assignment."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.COMPLETED
    assert "database assignment" in item.proposed_title.lower()


@pytest.mark.asyncio
async def test_regression_18_completed_activity_tamil():
    """
    Test Case 18: Retrospective completed activity in Tamil.
    "ரிப்போர்ட்டை முடிச்சிட்டேன்."
    """
    text = "ரிப்போர்ட்டை முடிச்சிட்டேன்."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.COMPLETED


@pytest.mark.asyncio
async def test_regression_19_conditional_intention_english():
    """
    Test Case 19: Contingent action based on external trigger.
    "If it doesn't rain tomorrow, go for a run."
    """
    text = "If it doesn't rain tomorrow, go for a run."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.CONDITIONAL_INTENTION
    assert "rain" in item.condition_trigger.lower()
    assert item.proposed_title == "Go for a run"


@pytest.mark.asyncio
async def test_regression_20_conditional_intention_tamil():
    """
    Test Case 20: Contingent action in Tamil.
    "மழை பெய்யலனா கடைக்கு போகணும்."
    """
    text = "மழை பெய்யலனா கடைக்கு போகணும்."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type == ItemTypeEnum.CONDITIONAL_INTENTION
    assert "rain" in item.condition_trigger.lower()


@pytest.mark.asyncio
async def test_regression_21_acoustic_midstream_correction():
    """
    Test Case 21: Speaker correcting time midstream.
    "Schedule meeting at 4 PM, wait no, 5 PM tomorrow."
    """
    text = "Schedule meeting at 4 PM, wait no, 5 PM tomorrow."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert "5:00 PM" in item.deadline_expression
    assert "wait no" not in item.proposed_title.lower()


@pytest.mark.asyncio
async def test_regression_22_technical_project_raven():
    """
    Test Case 22: Preservation of project names without distortion.
    "Deploy Raven backend to Docker container."
    """
    text = "Deploy Raven backend to Docker container."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "deploy"
    assert "raven" in item.object.lower()
    assert item.proposed_title == "Deploy Raven backend to Docker container"


@pytest.mark.asyncio
async def test_regression_23_technical_project_thozhi():
    """
    Test Case 23: Application identity reference preservation.
    "Optimize THOZHI ASR pipeline tomorrow morning."
    """
    text = "Optimize THOZHI ASR pipeline tomorrow morning."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "optimize"
    assert "thozhi" in item.object.lower()
    assert item.proposed_title == "Optimize THOZHI ASR pipeline"
    assert "Tomorrow" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_24_multiple_coursework_assignments():
    """
    Test Case 24: Multiple university deliverables.
    "Complete DB Normalization Assignment and CN Packet Tracing Assignment"
    """
    text = "Complete DB Normalization Assignment and CN Packet Tracing Assignment"
    res = await parser.parse(text)
    assert len(res.extracted_items) == 2
    assert "DB Normalization" in res.extracted_items[0].proposed_title
    assert "CN Packet Tracing" in res.extracted_items[1].proposed_title


@pytest.mark.asyncio
async def test_regression_25_personal_family_errand():
    """
    Test Case 25: Real-world family errand with destination.
    "Buy medicines for mom from Apollo pharmacy this evening."
    """
    text = "Buy medicines for mom from Apollo pharmacy this evening."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "buy"
    assert "medicines" in item.object.lower()
    assert "apollo pharmacy" in item.object.lower()
    assert "Today" in item.deadline_expression or "6:00 PM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_26_casual_idea_wish():
    """
    Test Case 26: Aspirational idea without commitment.
    "Maybe someday I will learn Rust."
    """
    text = "Maybe someday I will learn Rust."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type in (ItemTypeEnum.IDEA, ItemTypeEnum.WISH)
    assert item.deadline_expression is None


@pytest.mark.asyncio
async def test_regression_27_question_disambiguation():
    """
    Test Case 27: Informational query; must not create scheduled task.
    "What time is the team sync tomorrow?"
    """
    text = "What time is the team sync tomorrow?"
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.item_type in (ItemTypeEnum.QUESTION, ItemTypeEnum.INFORMATIONAL)


@pytest.mark.asyncio
async def test_regression_28_tamil_task_without_deadline():
    """
    Test Case 28: Tamil action without deadline.
    "ப்ராஜெக்ட் டாகுமெண்ட்டை ரெடி பண்ணணும்."
    """
    text = "ப்ராஜெக்ட் டாகுமெண்ட்டை ரெடி பண்ணணும்."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert "project document" in item.proposed_title.lower()
    assert item.deadline_expression is None


@pytest.mark.asyncio
async def test_regression_29_mixed_script_tamil_english():
    """
    Test Case 29: Mixed script code-switching.
    "Tomorrow morning 10 மணிக்கு client call irukku."
    """
    text = "Tomorrow morning 10 மணிக்கு client call irukku."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert "10:00 AM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_30_complex_multipart_with_duration_and_deadline():
    """
    Test Case 30: Multi-part instruction with duration, action, object, and deadline.
    "Need to write lab record for 1 hour before 6 PM tomorrow."
    """
    text = "Need to write lab record for 1 hour before 6 PM tomorrow."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "write"
    assert "lab record" in item.object.lower()
    assert item.proposed_title == "Write lab record"
    assert item.estimated_duration_min == 60
    assert "6:00 PM" in item.deadline_expression


@pytest.mark.asyncio
async def test_regression_31_standalone_reminder():
    """
    Test Case 31: Standalone personal reminder at specific time.
    "Remind me to take medication at 8 PM."
    """
    text = "Remind me to take medication at 8 PM."
    res = await parser.parse(text)
    item = res.extracted_items[0]
    assert item.action.lower() == "take"
    assert "medication" in item.object.lower()
    assert "8:00 PM" in item.deadline_expression


def test_regression_32_full_api_endpoint_exact_tamil_raven_app():
    """
    Test Case 32: Full End-to-End API route test via POST /api/v1/captures/text.
    Verifies that the entire pipeline:
    - Ingests the Tamil thought
    - Generates a proposal item with clean title "Complete my Raven app"
    - Sets action="Complete" and object="my Raven app"
    - Extracts deadline "Tomorrow, 6:00 PM"
    - Leaves duration as None / UNSPECIFIED
    - Leaves priority as None / UNSPECIFIED
    - Appends uncertainty flags
    """
    thought = "நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."
    resp = client.post("/api/v1/captures/text", json={"text": thought})
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] in ("PROPOSED", "PENDING_REVIEW")
    items = data.get("proposal", {}).get("items") if "proposal" in data else data.get("items", [])
    assert len(items) == 1
    prop_item = items[0]

    assert prop_item["proposed_title"] == "Complete my Raven app"
    assert prop_item["action"] == "Complete"
    assert "raven" in prop_item["object"].lower()
    assert "6:00 PM" in prop_item["deadline_expression"]
    assert prop_item["estimated_duration_min"] is None
    assert prop_item["duration_source"] == "UNSPECIFIED"
    assert prop_item["priority"] is None or prop_item["priority"] == "UNSPECIFIED"
    assert "UNSPECIFIED_DURATION" in prop_item["uncertainty_flags"]
    assert "UNSPECIFIED_PRIORITY" in prop_item["uncertainty_flags"]

