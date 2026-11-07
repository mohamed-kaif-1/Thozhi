import httpx
import json
from typing import Optional
from datetime import date
from backend.app.providers.nlu.base import BaseNLUProvider
from backend.app.schemas.intent import ExtractionResponse
from backend.app.core.config import settings

SYSTEM_INSTRUCTION = """
You are THOZHI's sovereign multilingual intent parser.
Your role: Transform unstructured thoughts in Tamil, Tanglish, or English into structured task proposals.
STRICT RULES:
1. "The AI proposes. The user decides."
2. TASK TITLE STRICT RULE: The proposed_title MUST describe only the actual work: an imperative verb (action) plus its direct object (e.g., "Complete my Raven app", "Submit assignment", "Call client").
3. SEPARATE TEMPORAL ADVERBIALS: NEVER put deadlines, dates, times, or days into proposed_title. Deadlines belong strictly in `deadline_expression` and `normalized_deadline_iso`.
4. POPULATE ACTION AND OBJECT: Always extract `action` (e.g., "Complete", "Submit", "Call") and `object` (e.g., "my Raven app", "assignment") as separate fields.
5. DO NOT INVENT DURATION: If the user did not state an explicit duration (e.g., "for 2 hours"), leave `estimated_duration_min` as null and set `duration_source="UNSPECIFIED"`. Never default to 30 minutes!
6. DO NOT INVENT PRIORITY: If the user did not express explicit urgency or priority, leave `priority` as null or "UNSPECIFIED". Never default to P2 Medium!
7. CLASSIFY PRECISELY:
   - TASK: An action the user needs to perform.
   - COMMITMENT: A fixed promise, scheduled meeting, call, or sync with other people.
   - CONDITIONAL_INTENTION: An action contingent upon a condition (e.g., "if it does not rain"). MUST populate `condition_trigger`.
   - CANCELLED: An explicit cancellation or removal of an appointment/task.
   - COMPLETED: An action the user explicitly says is already done/finished (e.g., "already completed", "mudichiten").
8. Preserve the exact source substring in `source_expression`.
9. Provide multi-dimensional confidence scores for intent, action, object, and deadline.
"""

class GeminiNLUProvider(BaseNLUProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def extract_intent(
        self,
        transcript_text: str,
        reference_date: Optional[date] = None,
        user_timezone: str = "Asia/Kolkata"
    ) -> ExtractionResponse:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        ref_date_str = (reference_date or date.today()).isoformat()
        
        prompt = f"""
Reference Today's Date: {ref_date_str}
Timezone: {user_timezone}
User Monologue / Input:
\"\"\"{transcript_text}\"\"\"

Return a valid JSON object matching the ExtractionResponse schema.
Schema:
{{
  "intent_summary": "string",
  "detected_language": "string",
  "extracted_items": [
    {{
      "temp_id": "item_1",
      "item_type": "TASK" | "COMMITMENT" | "IDEA" | "WISH" | "CONDITIONAL_INTENTION" | "QUESTION" | "REMINDER" | "COMPLETED" | "CANCELLED" | "INFORMATIONAL",
      "action": "string (imperative action verb e.g. 'Complete')",
      "object": "string (target direct object e.g. 'my Raven app')",
      "proposed_title": "string (action + object only without temporal info)",
      "description": "string or null",
      "source_expression": "string",
      "deadline_expression": "string or null",
      "normalized_deadline_iso": "ISO-8601 string or null",
      "estimated_duration_min": integer or null,
      "duration_source": "USER_EXPLICIT" | "LEARNED_PRIOR" | "MODEL_ESTIMATE" | "UNSPECIFIED",
      "priority": "P1_CRITICAL" | "P2_MEDIUM" | "P3_LOW" | "BACKBURNER" | "UNSPECIFIED" | null,
      "confidence": float,
      "intent_confidence": float or null,
      "action_confidence": float or null,
      "object_confidence": float or null,
      "deadline_confidence": float or null,
      "uncertainty_flags": ["string"],
      "dependencies": ["temp_id"],
      "condition_trigger": "string or null"
    }}
  ]
}}
"""

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned {resp.status_code}: {resp.text}")

            result = resp.json()
            text_candidate = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed_data = json.loads(text_candidate)
            extraction_res = ExtractionResponse.model_validate(parsed_data)
            extraction_res.transcript_text = transcript_text
            return extraction_res

