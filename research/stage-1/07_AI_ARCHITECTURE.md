# 07 — AI Systems Architecture & Inference Pipeline

## 1. Executive Summary & Core Mandates
The AI subsystem in THOZHI performs two distinct perceptual functions:
1. **Speech-to-Text (ASR):** Converts acoustic waveforms of conversational Tanglish, Tamil, or English into normalized text transcripts.
2. **Semantic Extraction & Classification (NLU):** Maps unstructured text into structured, typed Pydantic entities with temporal anchors.

**Architectural Law (Master PRD Section 8.5 & 11.5):**  
- The AI subsystem is strictly **perceptual and analytical**. It NEVER solves scheduling algorithms or executes database state changes. Its sole output is a validated, typed data contract passed to the deterministic planning engine.
- **Model Selection Policy:** Gemini 2.0 Flash is **NOT** an approved choice because it has been shut down. The NLU layer is placed behind a **Replaceable LLM Provider Adapter** benchmarking verified candidates (Gemini 1.5 Flash, GPT-4o-mini, Claude 3.5 Haiku, Llama 3.3 70B) under identical evaluation scenarios before final production lock.
- **ASR Policy:** Primary ASR is **Gnani AI Prisma v3.0**, with **Sarvam AI Saaras v3** as an explicitly configured, transparent commercial fallback.

---

## 2. Speech Recognition (ASR) Subsystem

### 2.1 Abstract ASR Service Interface
To ensure vendor independence and guarantee that THOZHI is never crippled by Gnani account limits, the backend enforces an **Abstract Base Class (ABC)** pattern:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """
        Transcribes audio bytes and returns normalized dictionary:
        {
            "transcript": str,
            "detected_language": str,
            "confidence": float,
            "provider": str,
            "provider_metadata": dict
        }
        """
        pass
```

### 2.2 Primary Engine: Gnani.ai Prisma v3.0
- **Endpoint:** `POST https://api.vachana.ai/stt/v3`
- **Authentication:** `X-API-Key-ID: <GNANI_API_KEY>`
- **Request Format:** `multipart/form-data`
  - `audio_file`: Binary WAV stream (16kHz, 16-bit Mono PCM).
  - `model`: `prisma-v3.0`
  - `language_code`: `indic-auto` (or `ta` for explicit Tamil mode).
  - `formatting_mode`: `code-mix` (preserves Latin script for English loanwords).
- **Latency Target:** $\le 1,400\text{ ms}$ for 15 seconds of audio.

### 2.3 Commercial Fallback Engine: Sarvam AI Saaras v3
- **Trigger:** Invoked automatically if Gnani returns HTTP 401, 429, 504, or times out after 3.0 seconds.
- **Endpoint:** `POST https://api.sarvam.ai/speech-to-text`
- **Authentication:** `api-subscription-key: <SARVAM_API_KEY>`
- **Request Format:** `multipart/form-data`
  - `file`: Binary WAV stream.
  - `model`: `saaras-v3`
  - `language_code`: `ta-IN`
- **Billing Rate:** ₹30.00 / audio hour (₹0.50 / minute billed per second).

---

## 3. Semantic Extraction & Classification Subsystem

### 3.1 Replaceable NLU Provider Adapter Architecture
The extraction pipeline is isolated behind `NaturalLanguageUnderstandingProvider`:

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any

class NaturalLanguageUnderstandingProvider(ABC):
    @abstractmethod
    async def extract_intent(self, text: str, system_context: Dict[str, Any]) -> "ExtractionResponse":
        """Extracts structured tasks and modalities according to ExtractionResponse schema."""
        pass
```

### 3.2 Candidate Model Evaluation Roster
Candidate models evaluated under the 18 synthetic test scenarios:
1. **Google Gemini 1.5 Flash:** High multimodal/multilingual throughput; low token cost; native Pydantic schema enforcement.
2. **OpenAI GPT-4o-mini:** Highly reliable instruction following; strict structured JSON mode.
3. **Anthropic Claude 3.5 Haiku:** High linguistic subtlety in complex negations and colloquial Indian English idioms.
4. **Meta Llama 3.3 70B (via Groq):** Ultra-low latency inference ($>250\text{ tokens/sec}$); open weights.

### 3.3 Formal Pydantic Extraction Schemas

In alignment with `Masterprd.md` Section 11.2 & 11.3:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ItemTypeEnum(str, Enum):
    TASK = "TASK"
    COMMITMENT = "COMMITMENT"
    IDEA = "IDEA"
    WISH = "WISH"
    CONDITIONAL_INTENTION = "CONDITIONAL_INTENTION"
    QUESTION = "QUESTION"
    REMINDER = "REMINDER"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    INFORMATIONAL = "INFORMATIONAL"

class PriorityEnum(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"
    BACKBURNER = "BACKBURNER"

class ProposedItemExtraction(BaseModel):
    temp_id: str = Field(description="Unique incremental string id (e.g., 'item_1')")
    item_type: ItemTypeEnum = Field(description="Classification of the sentence intention")
    proposed_title: str = Field(description="Clear, actionable imperative task title in English")
    description: Optional[str] = Field(description="Additional details or context")
    source_expression: str = Field(description="Exact substring from input corresponding to this item")
    deadline_expression: Optional[str] = Field(description="Raw temporal expression extracted from text")
    normalized_deadline_iso: Optional[str] = Field(description="ISO-8601 timestamp anchored to the current system date, or null if unknown")
    estimated_duration_min: Optional[int] = Field(default=None, description="Estimated duration in minutes, or null if unstated")
    duration_source: str = Field(default="MODEL_ESTIMATE", description="'USER_EXPLICIT', 'MODEL_ESTIMATE', or 'UNKNOWN'")
    priority: PriorityEnum = Field(default=PriorityEnum.P2_MEDIUM)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    uncertainty_flags: List[str] = Field(default_factory=list, description="Flags like 'UNKNOWN_DEADLINE', 'AMBIGUOUS_TIME'")
    dependencies: List[str] = Field(default_factory=list, description="List of temp_ids that must complete before this task")
    condition_trigger: Optional[str] = Field(description="Trigger condition if item_type is CONDITIONAL_INTENTION")

class ExtractionResponse(BaseModel):
    intent_summary: str = Field(description="One-sentence English summary of the user's mental monologue")
    detected_language: str = Field(description="e.g. 'Tanglish', 'English', 'Tamil'")
    extracted_items: List[ProposedItemExtraction] = Field(description="List of all extracted items")
```

---

## 4. System Prompt Design & Temporal Grounding

```
You are the NLU Engine of THOZHI, an intelligent bilingual personal planning assistant.
Your job is to analyze unstructured spoken or typed thoughts in Tamil, English, or Tanglish 
and extract actionable tasks into strict JSON format matching the ExtractionResponse schema.

CURRENT SYSTEM CONTEXT:
- Current Timestamp: {CURRENT_SYSTEM_ISO_TIMESTAMP} (Timezone: Asia/Kolkata)
- Current Day of Week: {CURRENT_DAY_OF_WEEK}

TAXONOMY CLASSIFICATION RULES (Master PRD Section 11.3):
1. COMMITMENT: A definite promise or obligation made to someone else or self with high intent.
2. TASK: A standard actionable responsibility.
3. IDEA: Aspirational thought, concept, or brainstorming ("maybe I should learn Rust").
4. WISH: Desire without immediate intent ("I wish I had more free time").
5. CONDITIONAL_INTENTION: Actions dependent on external triggers ("If Suresh calls, send the PO").
6. QUESTION: Inquiries or informational requests.
7. REMINDER: Simple point-in-time notification request.
8. COMPLETED: Tasks explicitly stated as already done ("I already sent the email").
9. CANCELLED: Tasks explicitly retracted or cancelled.
10. INFORMATIONAL: Non-actionable context or background statements.

UNCERTAINTY AND INFERENCE RULES (Master PRD Section 11.4):
- If the user does not mention a date, DO NOT invent one. Set normalized_deadline_iso = null and append 'UNKNOWN_DEADLINE' to uncertainty_flags.
- If duration is not mentioned, set estimated_duration_min = null and duration_source = 'UNKNOWN'.
- If the user corrects themselves mid-stream ("Thursday 4 PM... no, Friday 11 AM"), discard the retracted date and output ONLY the active intent.
- Tamil date expressions: "inniku" = today, "naalaiki" = tomorrow, "naalaiki marunaal" = day after tomorrow.
```
