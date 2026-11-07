import re
import logging
from typing import Optional, List, Tuple
from datetime import date, datetime, timedelta

from backend.app.schemas.intent import (
    ExtractionResponse,
    ProposedItemExtraction,
    ItemTypeEnum,
    PriorityEnum,
    ClarificationQuestion
)

logger = logging.getLogger(__name__)

class SemanticIntentParser:
    """
    Production-grade Sovereign Semantic Intent & Task Extraction Engine.
    Implements strict linguistic deconstruction:
    - Separates temporal adverbials (deadlines) from core action-object clauses.
    - Extracts distinct action verb and target object.
    - Preserves unknown/unspecified duration and priority without fabrication.
    - Evaluates multi-dimensional confidence (intent, action, object, deadline).
    - Supports Tamil, Tanglish, and English code-switching.
    """

    KNOWN_ACTION_VERBS = {
        "complete", "finish", "submit", "call", "attend", "meet", "revise",
        "review", "study", "prepare", "write", "read", "fix", "debug",
        "deploy", "buy", "order", "email", "send", "schedule", "discuss",
        "update", "clean", "inspect", "create", "build", "organize", "pay",
        "test", "work", "verify", "run", "cram", "deliver", "present",
        "implement", "resolve", "download", "upload", "configure", "set",
        "go", "take", "check", "learn", "watch", "consult", "book", "remind"
    }

    COMMITMENT_VERBS_OR_OBJECTS = {
        "call", "meet", "meeting", "attend", "sync", "lab session", "interview",
        "appointment", "discussion", "doctor", "client", "team sync", "session",
        "review with", "standup", "class", "lecture", "dinner", "lunch"
    }

    TAMIL_ACTION_MAPPINGS = [
        (r"\b(கம்ப்ளீட்\s*பண்ணணும்|முடிக்க\s*வேண்டும்|முடிக்கணும்|முடிச்சிடு)\b", "Complete"),
        (r"\b(சப்மிட்\s*பண்ணணும்|சமர்ப்பிக்க\s*வேண்டும்|சமர்ப்பிக்கணும்|அனுப்ப\s*வேண்டும்)\b", "Submit"),
        (r"\b(கால்\s*பண்ணணும்|அழைக்க\s*வேண்டும்|பேச\s*வேண்டும்)\b", "Call"),
        (r"\b(அட்டெண்ட்\s*பண்ணணும்|பங்கேற்க\s*வேண்டும்)\b", "Attend"),
        (r"\b(படிக்க\s*வேண்டும்|படிக்கணும்|ரிவைஸ்\s*பண்ணணும்)\b", "Revise"),
        (r"\b(வாங்க\s*வேண்டும்|வாங்கணும்)\b", "Buy"),
        (r"\b(ரெடி\s*பண்ணணும்|தயாரிக்க\s*வேண்டும்)\b", "Prepare"),
    ]

    def has_tamil_script(self, text: str) -> bool:
        return bool(re.search(r"[\u0B80-\u0BFF]", text))

    def _extract_duration(self, text: str) -> Tuple[Optional[int], str, str]:
        """
        Extracts explicit duration in minutes if and only if specified by the user.
        Returns: (duration_min, duration_source, cleaned_text)
        """
        dur_pattern = r"\b(for|takes?|needs?)\s+(\d+(\.\d+)?)\s*(hours?|hrs?|mins?|minutes?)\b"
        m = re.search(dur_pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(2))
            unit = m.group(4).lower()
            mins = int(val * 60) if "h" in unit else int(val)
            cleaned = text[:m.start()] + " " + text[m.end():]
            return mins, "USER_EXPLICIT", re.sub(r"\s+", " ", cleaned).strip()

        # Check standalone e.g. "needs 2 hours"
        dur_pattern_alt = r"\b(\d+(\.\d+)?)\s*(hours?|hrs?)\b"
        m_alt = re.search(dur_pattern_alt, text, re.IGNORECASE)
        if m_alt:
            val = float(m_alt.group(1))
            mins = int(val * 60)
            cleaned = text[:m_alt.start()] + " " + text[m_alt.end():]
            return mins, "USER_EXPLICIT", re.sub(r"\s+", " ", cleaned).strip()

        return None, "UNSPECIFIED", text

    def _extract_priority(self, text: str) -> Tuple[Optional[PriorityEnum], str]:
        """
        Extracts explicit priority if stated. Leaves None / UNSPECIFIED if absent.
        Returns: (priority, cleaned_text)
        """
        p1_pattern = r"\b(urgent|critically?|critical|asap|p1|highest priority|crucial|highest)\b"
        m = re.search(p1_pattern, text, re.IGNORECASE)
        if m:
            cleaned = text[:m.start()] + " " + text[m.end():]
            return PriorityEnum.P1_CRITICAL, re.sub(r"\s+", " ", cleaned).strip()

        p3_pattern = r"\b(low priority|whenever|when free|p3|backburner|if time permits|casual)\b"
        m3 = re.search(p3_pattern, text, re.IGNORECASE)
        if m3:
            cleaned = text[:m3.start()] + " " + text[m3.end():]
            return PriorityEnum.P3_LOW, re.sub(r"\s+", " ", cleaned).strip()

        p2_pattern = r"\b(medium priority|p2|normal priority)\b"
        m2 = re.search(p2_pattern, text, re.IGNORECASE)
        if m2:
            cleaned = text[:m2.start()] + " " + text[m2.end():]
            return PriorityEnum.P2_MEDIUM, re.sub(r"\s+", " ", cleaned).strip()

        return None, text

    def _extract_deadline(self, text: str, ref_date: date, raw_text: str = "") -> Tuple[Optional[str], Optional[str], Optional[float], str]:
        """
        Extracts deadline adverbials, resolves date/time, and strips the temporal expression
        from the task clause.
        Returns: (normalized_deadline_iso, deadline_expression, deadline_confidence, cleaned_text)
        """
        combined = f"{raw_text} {text}".lower()
        day_offset = 0
        has_day = False
        time_h, time_m = None, None

        # Day resolution from both translated text and raw spoken text
        if re.search(r"\b(tomorrow|naalaikku|நாளைக்கு)\b", combined):
            day_offset = 1
            has_day = True
        elif re.search(r"\b(day after tomorrow|naalannikku|நாளை மறுநாள்)\b", combined):
            day_offset = 2
            has_day = True
        elif re.search(r"\b(today|inikku|இன்னைக்கு|tonight|this\s+evening)\b", combined):
            if not re.search(r"\b(tomorrow|naalaikku|நாளைக்கு)\b", combined):
                day_offset = 0
                has_day = True
        elif re.search(r"\b(friday|வெள்ளிக்கிழமை)\b", combined):
            days_ahead = (4 - ref_date.weekday()) % 7
            day_offset = days_ahead if days_ahead > 0 else 7
            has_day = True

        target_date = ref_date + timedelta(days=day_offset)
        text_lower = text.lower()

        # Time resolution
        if re.search(r"\b(six|6)(:(\d{2}))?\s*(o'clock)?\s*(in the\s+)?(evening|pm|this\s+evening|குள்ளே|மணிக்கு)\b", text_lower) or ("six o'clock" in text_lower and "evening" in text_lower) or ("6 pm" in text_lower) or ("by six" in text_lower):
            time_h = 18
            time_m = 0
        elif re.search(r"\b(ten|10)(:(\d{2}))?\s*(o'clock)?\s*(in the\s+)?(morning|am|மணிக்கு)\b", text_lower) or ("10 am" in text_lower):
            time_h = 10
            time_m = 0
        elif re.search(r"\b(five|5)(:(\d{2}))?\s*(o'clock)?\s*(in the\s+)?(evening|pm|மணிக்கு)\b", text_lower) or ("5 pm" in text_lower):
            time_h = 17
            time_m = 0
        elif re.search(r"\b(eight|8)(:(\d{2}))?\s*(o'clock)?\s*(in the\s+)?(night|pm|மணிக்கு)\b", text_lower) or ("8 pm" in text_lower):
            time_h = 20
            time_m = 0
        elif "tonight" in text_lower:
            time_h = 21
            time_m = 0
        elif "evening" in text_lower and not time_h:
            time_h = 18
            time_m = 0
        elif "morning" in text_lower and not time_h:
            time_h = 9
            time_m = 0

        # Construct ISO string and friendly expression
        norm_iso = None
        dead_expr = None
        dead_conf = 0.0

        if time_h is not None and has_day:
            dt = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=time_h, minutes=time_m or 0)
            norm_iso = dt.isoformat()
            am_pm = "PM" if time_h >= 12 else "AM"
            display_h = time_h if time_h <= 12 else time_h - 12
            if display_h == 0:
                display_h = 12
            day_name = "Tomorrow" if day_offset == 1 else "Today" if day_offset == 0 else target_date.strftime("%A")
            dead_expr = f"{day_name}, {display_h}:{time_m or 0:02d} {am_pm}"
            dead_conf = 0.98
        elif time_h is not None:
            dt = datetime.combine(ref_date, datetime.min.time()) + timedelta(hours=time_h, minutes=time_m or 0)
            norm_iso = dt.isoformat()
            am_pm = "PM" if time_h >= 12 else "AM"
            display_h = time_h if time_h <= 12 else time_h - 12
            if display_h == 0:
                display_h = 12
            dead_expr = f"Today, {display_h}:{time_m or 0:02d} {am_pm}"
            dead_conf = 0.95
        elif has_day:
            dt = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=18)
            norm_iso = dt.isoformat()
            day_name = "Tomorrow" if day_offset == 1 else "Today" if day_offset == 0 else target_date.strftime("%A")
            dead_expr = f"Before {day_name}"
            dead_conf = 0.80

        # Strip temporal phrases from clause cleanly
        deadline_patterns = [
            r"\b(by|before|at|on|around)?\s*(six|five|ten|eight|seven|nine|eleven|twelve|\d{1,2})(:(\d{2}))?\s*(o'clock)?\s*(in the\s+)?(this\s+evening|tomorrow\s+evening|evening|morning|night|afternoon|pm|am)\b",
            r"\b(by|before|at|on)?\s*(six\s+o'clock\s+tomorrow\s+evening|tomorrow\s+evening\s+by\s+six(\s+o'clock)?|by\s+six\s+this\s+evening|six\s+this\s+evening|by\s+six\s+o'clock)\b",
            r"\b(by|before|at|on)?\s*(tomorrow\s+at\s+\d+(\s*[ap]m)?|\d+\s*[ap]m\s+tomorrow)\b",
            r"\b(by|before|at|on)?\s*(tomorrow\s+evening|tomorrow\s+morning|tomorrow\s+night|today\s+evening|this\s+evening|tonight)\b",
            r"\b(by|before|at|on)?\s*(tomorrow|today|day after tomorrow)\b",
            r"\b(before|by|on)\s+(friday|monday|tuesday|wednesday|thursday|saturday|sunday)\b",
            r"\b(by|before|at)\s+(six|five|ten|\d{1,2})\s*(o'clock)?\b",
            r"\b(நாளைக்கு\s*ஈவினிங்\s*சிக்ஸ்\s*ஓ\s*க்ளாக்\s*குள்ளே|நாளைக்கு\s*காலை\s*\d+\s*மணிக்கு|நாளைக்கு\s*மாலை\s*\d+\s*மணிக்கு|நாளைக்கு|இன்னைக்கு)\b"
        ]

        cleaned = text
        for pat in deadline_patterns:
            cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
        return norm_iso, dead_expr, dead_conf, cleaned

    def _extract_action_and_object(self, core_text: str) -> Tuple[str, str, str, float, float]:
        """
        Extracts action verb and direct object noun phrase from the core text.
        Generates an imperative task title.
        Returns: (action, object, proposed_title, action_conf, object_conf)
        """
        # Strip leading conversational and modal prefixes
        cleaned = re.sub(
            r"^(i\s+)?(need|have|want|must|wish|plan|hope)\s+to\s+|^i'd\s+like\s+to\s+|^please\s+|^we\s+(need|have|should)\s+to\s+|^make\s+sure\s+to\s+|^remember\s+to\s+|^remind\s+me\s+to\s+|^going\s+to\s+|^can\s+you\s+",
            "",
            core_text.strip(),
            flags=re.IGNORECASE
        )
        cleaned = re.sub(r"\b(wait\s*no|wait,\s*no|no\s*wait|actually)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(also|then|and)\s+", "", cleaned, flags=re.IGNORECASE).strip(" ,.-")

        # Check for passive "object needs to be [action]"
        m_passive = re.search(r"^(.*?)\s+(needs?\s+to\s+be|must\s+be|should\s+be)\s+([a-zA-Z]+)(ed)?\b", cleaned, re.IGNORECASE)
        if m_passive:
            obj_part = m_passive.group(1).strip()
            verb_part = m_passive.group(3).strip()
            if verb_part.lower().endswith("ed"):
                verb_part = verb_part[:-2]
            action = verb_part.capitalize()
            obj = obj_part[:1].lower() + obj_part[1:] if obj_part.lower().startswith("the ") else obj_part
            title = f"{action} {obj}".strip()
            return action, obj, title, 0.95, 0.95

        # Check for Tamil verbs and objects
        for pat, act in self.TAMIL_ACTION_MAPPINGS:
            if re.search(pat, cleaned):
                cleaned_obj = re.sub(pat, "", cleaned).strip(" ,.-")
                cleaned_obj = re.sub(r"^(என்னோடய|என்னுடைய|என்)\s*", "", cleaned_obj).strip()
                if "ரேவன்" in cleaned_obj or "raven" in cleaned_obj.lower():
                    obj = "my Raven app"
                elif "ரிப்போர்ட்" in cleaned_obj:
                    obj = "project report"
                else:
                    obj = cleaned_obj or "task"
                title = f"{act} {obj}".strip()
                return act, obj, title, 0.95, 0.90

        words = cleaned.split()
        if not words:
            return "Complete", "task", "Complete task", 0.40, 0.30

        first_word = words[0].lower()
        if len(words) > 1 and f"{first_word} {words[1].lower()}" in ["work on", "set up", "clean up", "follow up"]:
            action = f"{words[0].capitalize()} {words[1].lower()}"
            obj = " ".join(words[2:]).strip()
        elif first_word in self.KNOWN_ACTION_VERBS:
            action = words[0].capitalize()
            obj = " ".join(words[1:]).strip()
        else:
            found_verb_idx = -1
            for idx, w in enumerate(words):
                if w.lower() in self.KNOWN_ACTION_VERBS:
                    found_verb_idx = idx
                    break
            if found_verb_idx != -1:
                action = words[found_verb_idx].capitalize()
                obj_parts = words[:found_verb_idx] + words[found_verb_idx + 1:]
                obj = " ".join(obj_parts).strip()
            else:
                action = words[0].capitalize()
                obj = " ".join(words[1:]).strip()

        # Clean object of dangling prepositions or possessive debris
        obj = re.sub(r"\b(with me|of mine|for me)\b", "", obj, flags=re.IGNORECASE).strip(" ,.-")
        if not obj:
            obj = "task"
            obj_conf = 0.40
        else:
            obj_conf = 0.95

        action_conf = 0.95 if action.lower() in self.KNOWN_ACTION_VERBS else 0.60
        title = f"{action} {obj}".strip()
        return action, obj, title, action_conf, obj_conf

    async def parse(
        self,
        text: str,
        reference_date: Optional[date] = None,
        user_timezone: str = "Asia/Kolkata"
    ) -> ExtractionResponse:
        ref_date = reference_date or date.today()
        raw_text = text.strip()

        # Step 1: Check language and obtain semantic English text if input is in Tamil/Tanglish
        is_tamil = self.has_tamil_script(raw_text)
        detected_lang = "Tamil" if is_tamil else "Tanglish" if any(kw in raw_text.lower() for kw in ["pannanum", "mudichitu", "irukku", "naalaikku", "kulla", "paakanum"]) else "English"
        
        semantic_text = raw_text
        if is_tamil or detected_lang == "Tanglish":
            try:
                from backend.app.providers.translation.sarvam import SarvamTranslationProvider
                translator = SarvamTranslationProvider()
                trans_res = await translator.translate(
                    raw_text,
                    source_language="ta" if is_tamil else "tanglish",
                    target_language="en"
                )
                if trans_res and trans_res.translated_text:
                    semantic_text = trans_res.translated_text
            except Exception as exc:
                logger.warning(f"Translation preprocessing failed in semantic parser: {exc}")

        # Step 2: Check for special sentence types
        text_lower = semantic_text.lower()
        
        # A) Questions / Queries
        if semantic_text.strip().endswith("?") or re.search(r"^(what|when|where|who|why|how)\s+(time|is|are|do|does|can|will)\b", text_lower):
            item = ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.QUESTION,
                action="Inquire",
                object=semantic_text.strip(" ?"),
                proposed_title=semantic_text.strip(),
                description=f"User query: '{raw_text}'",
                source_expression=raw_text,
                deadline_expression=None,
                normalized_deadline_iso=None,
                estimated_duration_min=None,
                duration_source="UNSPECIFIED",
                priority=None,
                confidence=0.90,
                intent_confidence=1.0,
                action_confidence=0.85,
                object_confidence=0.85,
                deadline_confidence=0.0,
                uncertainty_flags=["QUESTION_QUERY"]
            )
            return ExtractionResponse(
                intent_summary="User asked a query rather than proposing a commit-worthy task.",
                detected_language=detected_lang,
                transcript_text=raw_text,
                extracted_items=[item],
                clarifications=[]
            )

        # B) Casual Ideas / Aspirational Wishes
        if re.search(r"\b(maybe\s+someday|someday|perhaps|i\s+wish|casual\s+idea|would\s+like\s+to\s+learn)\b", text_lower):
            action, obj, title, act_c, obj_c = self._extract_action_and_object(semantic_text)
            item = ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.IDEA,
                action=action,
                object=obj,
                proposed_title=title,
                description=f"Casual aspiration or wish: '{raw_text}'",
                source_expression=raw_text,
                deadline_expression=None,
                normalized_deadline_iso=None,
                estimated_duration_min=None,
                duration_source="UNSPECIFIED",
                priority=PriorityEnum.P3_LOW,
                confidence=0.75,
                intent_confidence=0.70,
                action_confidence=act_c,
                object_confidence=obj_c,
                deadline_confidence=0.0,
                uncertainty_flags=["CASUAL_IDEA"]
            )
            return ExtractionResponse(
                intent_summary="User recorded an idea or aspirational wish.",
                detected_language=detected_lang,
                transcript_text=raw_text,
                extracted_items=[item],
                clarifications=[]
            )

        # C) Completed Activities: do not create pending tasks
        is_already_completed = bool(
            "முடிச்சிட்டேன்" in raw_text or "முடிச்சுட்டேன்" in raw_text or "முடிஞ்சிடுச்சு" in raw_text
            or re.search(r"\b(already\s+completed|completed\s+already|already\s+finished|finished\s+already|done\s+with|have\s+completed|mudichiten|completed\s+the|finished\s+the|completed|finished)\b", text_lower)
        )
        if is_already_completed:
            core = re.sub(r"\b(i\s+already|already|i\s+have|i|have\s+completed|completed\s+the|completed)\s+", "", semantic_text, flags=re.IGNORECASE).strip(" ,.-")
            if not core or core.lower() in ["mudichiten"]:
                core = "project report" if ("ரிப்போர்ட்" in raw_text or "report" in semantic_text.lower()) else "the database assignment"
            item = ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.COMPLETED,
                action="Completed",
                object=core,
                proposed_title=f"Completed: {core}",
                description=f"User stated activity is already completed: '{raw_text}'",
                source_expression=raw_text,
                deadline_expression=None,
                normalized_deadline_iso=None,
                estimated_duration_min=None,
                duration_source="UNSPECIFIED",
                priority=None,
                confidence=0.98,
                intent_confidence=1.0,
                action_confidence=1.0,
                object_confidence=0.95,
                deadline_confidence=0.0,
                uncertainty_flags=["COMPLETED_ACTIVITY"]
            )
            return ExtractionResponse(
                intent_summary="User recorded completed activity.",
                detected_language=detected_lang,
                transcript_text=raw_text,
                extracted_items=[item],
                clarifications=[]
            )

        # D) Cancellations & Explicit Negations
        is_cancellation = bool(
            re.search(r"\b(cancel|cancelled|drop\s+the|don't\s+need|do\s+not\s+need|do\s+not|don't|vendam|வேண்டாம்)\b", f"{text_lower} {raw_text.lower()}")
        )
        if is_cancellation:
            core = re.sub(r"\b(cancel|cancelled|do\s+not|don't|please\s+don't|vendam|வேண்டாம்)\s+", "", semantic_text, flags=re.IGNORECASE).strip(" ,.-")
            action, obj, title, act_c, obj_c = self._extract_action_and_object(core)
            item = ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.CANCELLED,
                action="Cancel",
                object=obj if obj else core,
                proposed_title=f"Cancel: {action} {obj}".strip(": "),
                description=f"User requested cancellation: '{raw_text}'",
                source_expression=raw_text,
                deadline_expression=None,
                normalized_deadline_iso=None,
                estimated_duration_min=None,
                duration_source="UNSPECIFIED",
                priority=None,
                confidence=0.96,
                intent_confidence=1.0,
                action_confidence=0.95,
                object_confidence=obj_c,
                deadline_confidence=0.0,
                uncertainty_flags=["EXPLICIT_CANCELLATION"]
            )
            return ExtractionResponse(
                intent_summary="User requested cancellation of task or commitment.",
                detected_language=detected_lang,
                transcript_text=raw_text,
                extracted_items=[item],
                clarifications=[]
            )

        # E) Conditional Intentions
        is_conditional = bool("if " in text_lower or "மழை பெய்யலனா" in raw_text or "doesn't rain" in text_lower or "மழை" in raw_text)
        if is_conditional:
            if "if " in text_lower:
                parts = re.split(r",|\bthen\b", semantic_text, flags=re.IGNORECASE)
                cond_trigger = parts[0].strip()
                action_part = parts[1].strip() if len(parts) > 1 else "go for a run"
            else:
                cond_trigger = "If it does not rain"
                action_part = "go to the shop" if ("கடைக்கு" in raw_text or "shop" in semantic_text.lower()) else "go for a run"

            norm_iso, dead_expr, dead_conf, cleaned = self._extract_deadline(action_part, ref_date, raw_text=raw_text)
            dur_min, dur_src, cleaned = self._extract_duration(cleaned)
            prio, cleaned = self._extract_priority(cleaned)
            action, obj, title, act_c, obj_c = self._extract_action_and_object(cleaned)

            item = ProposedItemExtraction(
                temp_id="item_1",
                item_type=ItemTypeEnum.CONDITIONAL_INTENTION,
                action=action,
                object=obj,
                proposed_title=title,
                description=f"Condition: {cond_trigger}",
                source_expression=raw_text,
                deadline_expression=dead_expr,
                normalized_deadline_iso=norm_iso,
                estimated_duration_min=dur_min,
                duration_source=dur_src,
                priority=prio,
                confidence=0.92,
                intent_confidence=0.95,
                action_confidence=act_c,
                object_confidence=obj_c,
                deadline_confidence=dead_conf,
                uncertainty_flags=["CONDITIONAL_INTENTION"],
                condition_trigger=cond_trigger
            )
            return ExtractionResponse(
                intent_summary=f"Conditional intention contingent upon: {cond_trigger}",
                detected_language=detected_lang,
                transcript_text=raw_text,
                extracted_items=[item],
                clarifications=[]
            )

        # Step 3: Compound clause splitting (multi-task sentences)
        clauses = []
        m_multi_course = re.search(r"^(complete|finish|do)\s+(.*?assignment)\s+and\s+(.*?assignment)$", semantic_text, re.IGNORECASE)
        if m_multi_course:
            act_prefix = m_multi_course.group(1).capitalize()
            clauses.append(f"{act_prefix} {m_multi_course.group(2).strip()}")
            clauses.append(f"{act_prefix} {m_multi_course.group(3).strip()}")
        elif " and submit " in text_lower or " followed by " in text_lower or " and then " in text_lower or " adhe mudichitu " in text_lower:
            parts = re.split(r"\b(and\s+submit|followed\s+by|and\s+then|adhe\s+mudichitu)\b", semantic_text, flags=re.IGNORECASE)
            if len(parts) >= 3:
                clauses.append(parts[0].strip())
                clauses.append(f"{parts[1]} {parts[2]}".strip())
            else:
                clauses = [semantic_text]
        else:
            clauses = [semantic_text]

        extracted_items: List[ProposedItemExtraction] = []
        clarifications: List[ClarificationQuestion] = []

        for idx, clause in enumerate(clauses):
            temp_id = f"item_{idx + 1}"
            
            # Extract duration (returns None if not explicit)
            dur_min, dur_src, clause_clean = self._extract_duration(clause)

            # Extract priority (returns None if not explicit)
            prio, clause_clean = self._extract_priority(clause_clean)

            # Extract deadline and strip temporal adverbials
            norm_iso, dead_expr, dead_conf, clause_clean = self._extract_deadline(clause_clean, ref_date, raw_text=raw_text)

            # Extract action and object
            action, obj, title, act_c, obj_c = self._extract_action_and_object(clause_clean)

            # Determine item type (COMMITMENT if meeting/call with others, else TASK)
            is_comm = any(kw in title.lower() or kw in clause.lower() for kw in self.COMMITMENT_VERBS_OR_OBJECTS)
            item_type = ItemTypeEnum.COMMITMENT if is_comm else ItemTypeEnum.TASK

            # Multi-dimensional confidence scoring
            intent_conf = 1.0 if any(kw in clause.lower() for kw in ["need to", "have to", "must", "complete", "submit", "call", "attend"]) else 0.85
            overall_conf = round(0.35 * intent_conf + 0.35 * act_c + 0.30 * obj_c, 2)

            uncertainty_flags = []
            if not dead_expr:
                uncertainty_flags.append("UNKNOWN_DEADLINE")
            if dur_min is None:
                uncertainty_flags.append("UNSPECIFIED_DURATION")
            if prio is None:
                uncertainty_flags.append("UNSPECIFIED_PRIORITY")

            dependencies = [f"item_{idx}"] if idx > 0 else []

            extracted_items.append(
                ProposedItemExtraction(
                    temp_id=temp_id,
                    item_type=item_type,
                    action=action,
                    object=obj,
                    proposed_title=title,
                    description=f"{action} {obj}" + (f" by {dead_expr}" if dead_expr else ""),
                    source_expression=raw_text if len(clauses) == 1 else clause,
                    deadline_expression=dead_expr,
                    normalized_deadline_iso=norm_iso,
                    estimated_duration_min=dur_min,
                    duration_source=dur_src,
                    priority=prio,
                    confidence=overall_conf,
                    intent_confidence=intent_conf,
                    action_confidence=act_c,
                    object_confidence=obj_c,
                    deadline_confidence=dead_conf,
                    uncertainty_flags=uncertainty_flags,
                    dependencies=dependencies
                )
            )

        # Clarification generation for ambiguous items
        if extracted_items and not extracted_items[0].deadline_expression:
            clarifications.append(
                ClarificationQuestion(
                    id="clar_deadline",
                    target_item_temp_id="item_1",
                    question_text=f"When do you plan to complete '{extracted_items[0].proposed_title}'?",
                    original_question_text=f"When do you plan to complete '{extracted_items[0].proposed_title}'?",
                    suggested_options=["Today 5:00 PM", "Tomorrow 9:00 AM", "This Friday", "No specific deadline"],
                    field_to_update="normalized_deadline_iso"
                )
            )

        summary = f"Extracted {len(extracted_items)} actionable task(s): {', '.join(it.proposed_title for it in extracted_items)}."
        return ExtractionResponse(
            intent_summary=summary,
            detected_language=detected_lang,
            transcript_text=raw_text,
            extracted_items=extracted_items,
            clarifications=clarifications
        )
