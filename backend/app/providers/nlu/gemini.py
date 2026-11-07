import httpx
import json
from typing import Optional
from datetime import date
from backend.app.providers.nlu.base import BaseNLUProvider
from backend.app.schemas.intent import ExtractionResponse
from backend.app.core.config import settings

SYSTEM_INSTRUCTION = """
You are THOZHI's multilingual intent parser.
Your role: Transform unstructured thoughts in Tamil, Tanglish, or English into structured task proposals.
STRICT RULES:
1. "The AI proposes. The user decides."
2. Never hallucinate fake deadlines. If no time is mentioned, leave deadline as null and flag 'UNKNOWN_DEADLINE'.
3. Classify each item precisely into one of the following item_types:
   - TASK: An action the user needs to perform.
   - COMMITMENT: A fixed promise, scheduled meeting, or sync with other people.
   - CONDITIONAL_INTENTION: An action contingent upon a condition (e.g., "if it does not rain", "mazhai peyyalana", "if client confirms"). MUST populate `condition_trigger`.
   - CANCELLED: An explicit cancellation, drop, or removal of an appointment/task (e.g., "cancel pannidu", "vendam", "don't need meeting", "drop the call").
   - COMPLETED: An action the user explicitly says is already done/finished (e.g., "mudichiten", "done with report").
   - IDEA / WISH: Non-urgent concepts or speculative wishes.
4. Express task titles in clear, concise imperative English (e.g. "Attend client call", "Submit report", "Cancel meeting").
5. Preserve the exact source substring in `source_expression`.
6. Identify chronological dependencies between items in the monologue (e.g. item_2 depends on item_1).
7. Estimate realistic duration in minutes (default 30m if unspecified).
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
      "proposed_title": "string",
      "description": "string or null",
      "source_expression": "string",
      "deadline_expression": "string or null",
      "normalized_deadline_iso": "ISO-8601 string or null",
      "estimated_duration_min": integer or null,
      "duration_source": "USER_EXPLICIT" | "MODEL_ESTIMATE" | "UNKNOWN",
      "priority": "P1_CRITICAL" | "P2_MEDIUM" | "P3_LOW" | "BACKBURNER",
      "confidence": float,
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
            return ExtractionResponse.model_validate(parsed_data)

