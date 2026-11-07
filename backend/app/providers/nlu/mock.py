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
    Accurately emulates extraction for Tanglish, Tamil, and English inputs across
    the synthetic benchmark scenarios defined in research/stage-0/11-synthetic-test-scenarios.md.
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
        
        # Test Case 1 / Scenario 03: Client call + report submission
        if "client call" in text_lower or "report submit" in text_lower or ("deck update" in text_lower and "karthik" in text_lower):
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

        # Scenario 01: Exam Preparation & Cramming Schedule (DSP exam)
        elif "dsp" in text_lower or "semester exam" in text_lower or "lab record" in text_lower:
            summary = "Student preparing for semester exam with scheduled college lab session."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Revise DSP Syllabus (Focus on Unit 3 FFT)",
                    description="Revise DSP syllabus full especially Unit 3 FFT algorithms",
                    source_expression="Today DSP syllabus full-ah cover pannanum, especially Unit 3 FFT algorithms paakanum",
                    deadline_expression="Today before midnight",
                    estimated_duration_min=240,
                    duration_source="MODEL_ESTIMATE",
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.95
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.COMMITMENT,
                    proposed_title="Attend College Lab Session & Submit Record",
                    description="Fixed lab session from 18:00 to 20:00",
                    source_expression="evening 6 to 8 PM college lab record submit panna lab session iruku",
                    deadline_expression="6:00 PM to 8:00 PM",
                    estimated_duration_min=120,
                    duration_source="EXPLICIT_USER",
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.98
                )
            )
            clarifications.append(
                ClarificationQuestion(
                    id="clar_1",
                    target_item_temp_id="item_2",
                    question_text="Is your lab record already written, or do you need time before 6:00 PM to finish writing it?",
                    suggested_options=["Already written", "Need 1 hour to write", "Need 2 hours to write"],
                    field_to_update="estimated_duration_min"
                )
            )

        # Scenario 02: Multiple Overlapping Coursework Assignments
        elif "database normalization" in text_lower or "packet tracing" in text_lower or ("three assignments" in text_lower and "friday" in text_lower):
            summary = "Three academic coursework deliverables due Friday totaling 10 hours."
            detected_lang = "English"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Complete DB Normalization Assignment",
                    description="Database Normalization assignment requiring 3 hours",
                    source_expression="Database Normalization... will take 3 hours",
                    deadline_expression="Friday 5:00 PM",
                    estimated_duration_min=180,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.96
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Complete CN Packet Tracing Assignment",
                    description="Computer Networks packet tracing requiring 2 hours",
                    source_expression="Computer Networks packet tracing, needs 2 hours",
                    deadline_expression="Friday 5:00 PM",
                    estimated_duration_min=120,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.95
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_3",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Research & Write SE Essay",
                    description="Software Engineering essay requiring 5 hours research",
                    source_expression="SE essay needs at least 5 hours of research",
                    deadline_expression="Friday 5:00 PM",
                    estimated_duration_min=300,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.94,
                    uncertainty_flags=["HEAVY_STUDY_LOAD"]
                )
            )
            clarifications.append(
                ClarificationQuestion(
                    id="clar_1",
                    target_item_temp_id="item_3",
                    question_text="You have only 2h free today but 10h of coursework due Friday. Should we allocate 2h tonight for CN and 8h across Thursday?",
                    suggested_options=["Yes, split CN tonight & DB+SE Thursday", "Focus entirely on DB tonight", "Request extension for SE essay"],
                    field_to_update="normalized_deadline_iso"
                )
            )

        # Scenario 05: Side Projects & Freelancer Deliverables (Vector export + Invoice)
        elif "logo vector" in text_lower or "milestone 2" in text_lower or ("branding client" in text_lower and "svg" in text_lower):
            summary = "Dual freelancer commitments for client: SVG tweaking and milestone invoicing."
            detected_lang = "English"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Tweak & Finalize Logo SVG Export Files",
                    description="Tweaking SVG exports for branding client",
                    source_expression="spend 90 minutes tweaking the SVG exports",
                    deadline_expression="Tonight 7:30 PM",
                    estimated_duration_min=90,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.97
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Generate & Send Milestone 2 Invoice with Files",
                    description="Send milestone 2 invoice with final files to client",
                    source_expression="invoice them for milestone 2... send the invoice with the files",
                    deadline_expression="Tonight 8:00 PM",
                    estimated_duration_min=15,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.96,
                    dependencies=["item_1"]
                )
            )

        # Scenario 09: Conditional Commitments ("If-Then" Intentions with Suresh)
        elif "suresh" in text_lower and ("purchase order" in text_lower or "budget approve" in text_lower):
            summary = "Conditional workflow contingent on Suresh's budget approval call."
            detected_lang = "Tanglish"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.CONDITIONAL_INTENTION,
                    proposed_title="Raise Purchase Order to Vendor",
                    description="Contingent on Suresh budget approval call",
                    source_expression="Suresh enaku call panni budget approve panna, udane vendor ku purchase order raise pannanum",
                    estimated_duration_min=30,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.92,
                    condition_trigger="If Suresh approves budget",
                    uncertainty_flags=["TRIGGER_DEPENDENT"]
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Send Budget Follow-up Message to Suresh",
                    description="Reminder message at 5 PM if no call received",
                    source_expression="call varlana evening 5 PM-ku avanuku oru reminder message podanum",
                    deadline_expression="Today 5:00 PM",
                    estimated_duration_min=15,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.95
                )
            )

        # Adversarial Prompt Injection Defense Test
        elif "drop table" in text_lower or "system prompt" in text_lower or "ignore previous instructions" in text_lower:
            summary = "Adversarial input detected and sanitized safely as neutral task note."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Review sanitized security note",
                    description=transcript_text[:100],
                    source_expression=transcript_text[:50],
                    estimated_duration_min=15,
                    priority=PriorityEnum.P3_LOW,
                    confidence=0.99,
                    uncertainty_flags=["SANITIZED_ADVERSARIAL_INPUT"]
                )
            )

        # Scenario 04: Family Medical & Errands Collision (Apollo Hospital)
        elif "apollo" in text_lower or "hospital" in text_lower or "bp medicine" in text_lower:
            summary = "Parent medical appointment and time-sensitive pharmacy errand."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.COMMITMENT,
                    proposed_title="Take Mother to Apollo Hospital for Checkup",
                    description="Hospital checkup from 17:30 to 19:30",
                    source_expression="Amma-va 5:30 PM-ku Apollo hospital checkup kootitu ponum",
                    estimated_duration_min=120,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.97
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Buy BP Medicine for Father",
                    description="Purchase BP medication before pharmacy closes at 21:00",
                    source_expression="appa ku BP medicine vanganum before 9 PM medical shop closes",
                    deadline_expression="Today 21:00",
                    estimated_duration_min=20,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.96
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_3",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Buy Groceries",
                    description="General grocery shopping",
                    source_expression="Meanwhile grocery list vera buy pannanum",
                    estimated_duration_min=45,
                    priority=PriorityEnum.P3_LOW,
                    confidence=0.89
                )
            )

        # Scenario 06: Calendar Conflict (All-hands offsite meeting)
        elif "all-hands" in text_lower or ("audit report" in text_lower and "4 pm" in text_lower):
            summary = "Direct calendar collision between mandatory meeting and deadline."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.COMMITMENT,
                    proposed_title="Attend All-Hands Offsite Meeting",
                    description="Locked meeting 14:00 to 17:00",
                    source_expression="Tomorrow from 2 PM to 5 PM I am stuck in an all-hands offsite meeting",
                    estimated_duration_min=180,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.99
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Quarterly Financial Audit Report",
                    description="Audit report due at 16:00",
                    source_expression="finish the 3-hour quarterly financial audit report by 4 PM tomorrow",
                    deadline_expression="Tomorrow 16:00",
                    estimated_duration_min=180,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.95,
                    uncertainty_flags=["CALENDAR_CONFLICT_EXCEEDED"]
                )
            )
            clarifications.append(
                ClarificationQuestion(
                    id="clar_1",
                    target_item_temp_id="item_2",
                    question_text="Conflict detected: 3h audit report is due at 4 PM, but meeting runs 2 PM-5 PM. Schedule tomorrow morning 9:30 AM?",
                    suggested_options=["Schedule tomorrow morning (09:30 - 12:30)", "Request deadline extension from manager", "Reschedule all-hands meeting"],
                    field_to_update="normalized_deadline_iso"
                )
            )

        # Scenario 07: Strict DAG Pipeline (Deepak PR -> Test -> Deploy -> DNS)
        elif "deepak" in text_lower or "regression test" in text_lower or "dns propagation" in text_lower:
            summary = "Multi-stage software release pipeline with strict topological order."
            detected_lang = "English"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Follow up with Deepak to merge backend PR",
                    description="Prerequisite backend merge before regression testing",
                    source_expression="Deepak needs to merge his backend PR",
                    estimated_duration_min=15,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.92
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Run Regression Test Suite",
                    description="Automated tests requiring 2 hours",
                    source_expression="run the regression test suite which takes 2 hours",
                    estimated_duration_min=120,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.97,
                    dependencies=["item_1"]
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_3",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Deploy Website to Production",
                    description="Deployment scheduled for Friday afternoon",
                    source_expression="deploy the website to production on Friday afternoon",
                    estimated_duration_min=30,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.95,
                    dependencies=["item_2"]
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_4",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Verify DNS Propagation & Production Smoke Test",
                    description="Post-deployment DNS smoke verification",
                    source_expression="verify DNS propagation",
                    estimated_duration_min=30,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.93,
                    dependencies=["item_3"]
                )
            )

        # Scenario 08: Casual Ideas vs Urgent Commitments (Podcast vs Auditor)
        elif "podcast" in text_lower or "bank statement" in text_lower or "auditor" in text_lower:
            summary = "Distinguished casual ideas from hard urgent financial compliance."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Email Bank Statement to Auditor",
                    description="Compliance deadline today before 16:00",
                    source_expression="inniku evening 4 PM kula auditor ku bank statement email pannanum",
                    deadline_expression="Today 16:00",
                    estimated_duration_min=15,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.98
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.IDEA,
                    proposed_title="Start a Tech Podcast next month",
                    description="Brainstorming future creative venture",
                    source_expression="maybe next month oru tech podcast start pannalaam nu yosikiren",
                    estimated_duration_min=0,
                    priority=PriorityEnum.BACKBURNER,
                    confidence=0.91
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_3",
                    item_type=ItemTypeEnum.WISH,
                    proposed_title="Research Podcast Microphone Prices",
                    description="Backburner market research",
                    source_expression="We should research mic prices sometime",
                    estimated_duration_min=30,
                    priority=PriorityEnum.BACKBURNER,
                    confidence=0.88
                )
            )

        # Scenario 10: Retrospective & Completed Filtered Out (Electricity bill, resume)
        elif "electricity bill" in text_lower or "resume" in text_lower:
            summary = "Filtered completed historical actions and retained future commitments."
            detected_lang = "English"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.COMPLETED,
                    proposed_title="Pay Electricity Bill",
                    description="Already paid this morning",
                    source_expression="I already paid the electricity bill this morning",
                    estimated_duration_min=0,
                    priority=PriorityEnum.P3_LOW,
                    confidence=0.99
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_2",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Prepare Slides for Tomorrow's Demo",
                    description="Slide preparation for demo",
                    source_expression="prepare the slides for tomorrow's demo",
                    estimated_duration_min=120,
                    priority=PriorityEnum.P1_CRITICAL,
                    confidence=0.95
                )
            )
            items.append(
                ProposedItemExtraction(
                    temp_id="item_3",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Schedule Bike Oil Change Appointment",
                    description="Maintenance service call",
                    source_expression="schedule an oil change for the bike",
                    estimated_duration_min=15,
                    priority=PriorityEnum.P3_LOW,
                    confidence=0.90
                )
            )

        # Scenario 11: Explicit Negations & Negative Constraints (Design agency)
        elif "design agency" in text_lower or ("do not schedule" in text_lower and "wednesday" in text_lower):
            summary = "Meeting request with explicit day prohibitions and morning boundary constraints."
            detected_lang = "English"
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Schedule Meeting with Design Agency",
                    description="Meeting outside Wed/Fri and after 10:00 AM",
                    source_expression="Meet with the design agency, but do NOT schedule it on Wednesday or Friday",
                    estimated_duration_min=60,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.94,
                    uncertainty_flags=["NEGATIVE_CONSTRAINTS_APPLIED"]
                )
            )

        # Scenario 12: Acoustic / Semantic Mid-Stream Self-Repair (Doctor appointment)
        elif "doctor appointment" in text_lower and ("illa illa" in text_lower or "make that friday" in text_lower):
            summary = "User corrected previous statement mid-stream; final intent is Friday 11:00 AM."
            items.append(
                ProposedItemExtraction(
                    temp_id="item_1",
                    item_type=ItemTypeEnum.TASK,
                    proposed_title="Book Doctor Appointment",
                    description="Clinic appointment scheduled for Friday 11:00 AM",
                    source_expression="actually, check if 11 AM is better",
                    deadline_expression="Friday 11:00 AM",
                    estimated_duration_min=30,
                    priority=PriorityEnum.P2_MEDIUM,
                    confidence=0.93
                )
            )

        # Scenario 02 / Weather Conditional ("mazhai peyyalana cricket")
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

        # Explicit Cancellation ("cancel pannidu")
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
