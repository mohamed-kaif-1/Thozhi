from typing import Optional, List
from datetime import date, datetime, timedelta
from backend.app.providers.nlu.base import BaseNLUProvider
from backend.app.schemas.intent import (
    ExtractionResponse,
    ProposedItemExtraction,
    ItemTypeEnum,
    PriorityEnum,
    ClarificationQuestion
)

class MockNLUProvider(BaseNLUProvider):
    """
    High-fidelity deterministic NLU provider for automated testing and offline dev.
    Accurately emulates extraction for Tanglish, Tamil, and English inputs.
    """
    async def extract_intent(
        self,
        transcript_text: str,
        reference_date: Optional[date] = None,
        user_timezone: str = "Asia/Kolkata"
    ) -> ExtractionResponse:
        ref_date = reference_date or date.today()
        text_lower = transcript_text.lower()
        
        items = []
        clarifications: List[ClarificationQuestion] = []
        summary = "Extracted actionable items and commitments from user input."
        detected_lang = "Tanglish"
        
        # Test Case 1: Client call + report submission
        if "client call" in text_lower or "report submit" in text_lower:
            summary = "User has an evening client call followed by report submission."
            call_dt = datetime.combine(ref_date, datetime.min.time()) + timedelta(hours=17)
            report_dt = datetime.combine(ref_date, datetime.min.time()) + timedelta(hours=20)
            
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.COMMITMENT,
                    proposed_title="Attend client call",
                    description="Scheduled evening call with client",
                    source_expression="evening 5 manikku client call irukku",
                    deadline_expression="5:00 PM today",
                    normalized_deadline_iso=call_dt.isoformat(),
                    estimated_duration_min=45,
                    duration_source="MODEL_ESTIMATE",
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.96,
                    dependencies=[]
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Submit project report",
                    description="Complete and submit report after the client call",
                    source_expression="adhe mudichitu report submit pannanum",
                    deadline_expression="tonight after call",
                    normalized_deadline_iso=report_dt.isoformat(),
                    estimated_duration_min=60,
                    duration_source="MODEL_ESTIMATE",
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.94,
                    dependencies=["item_1"]
                )
            )
            clarifications.append(
                ClarificationQuestion(
                    id="clar_1",
                    target_item_temp_id="item_1",
                    question_text="How long is the client call expected to take?",
                    suggested_options=["30 mins", "45 mins", "60 mins"],
                    field_to_update="estimated_duration_min"
                )
            )
        # Test Case 2: Conditional intention ("mazhai peyyalana cricket")
        elif "mazhai" in text_lower or "cricket" in text_lower:
            summary = "User noted a conditional leisure plan depending on weather."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.CONDITIONAL_INTENTION,
                    proposed_title="Play cricket with friends",
                    description="Contingent on clear weather",
                    source_expression="mazhai peyyalana cricket vilayadalam",
                    deadline_expression=None,
                    estimated_duration_min=90,
                    priority=PriorityEnum.P3_LOW,
                    confidence=0.88,
                    condition_trigger="If it does not rain",
                    uncertainty_flags=["WEATHER_DEPENDENT"]
                )
            )
            clarifications.append(
                ClarificationQuestion(
                    id="clar_1",
                    target_item_temp_id="item_1",
                    question_text="If rain cancels cricket, what backup task would you like scheduled?",
                    suggested_options=["Read project documentation", "Indoor workout", "Rest"],
                    field_to_update="proposed_title"
                )
            )
        # Test Case 3: Cancellation ("cancel pannidu")
        elif "cancel" in text_lower or "vendam" in text_lower:
            summary = "User requested cancellation of a prior task."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.CANCELLED,
                    proposed_title="Cancel scheduled appointment",
                    description="Explicit user cancellation detected",
                    source_expression=transcript_text,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.95
                )
            )
        # Generic fallback extraction
        else:
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title=transcript_text[:50].capitalize(),
                    description=transcript_text,
                    source_expression=transcript_text,
                    estimated_duration_min=30,
                    duration_source="MODEL_ESTIMATE",
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.85
                )
            )

        return ExtractionResponse(
            intent_summary=summary,
            detected_language=detected_lang,
            extracted_items=items,
            clarifications=clarifications
        )
