# 10. AI TASK EXTRACTION ROOT-CAUSE ANALYSIS & FORENSIC INVESTIGATION REPORT

**Classification:** Severity P1 — Core Product Task Extraction Failure  
**Component:** Natural Language Understanding (NLU) & Intent Extraction Pipeline  
**Date of Audit:** November 7, 2026  
**Status:** ROOT CAUSE IDENTIFIED & PERMANENTLY RESOLVED  

---

## 1. Executive Problem Summary

A severe regression was observed during multilingual speech-to-task processing:
- **Spoken Tamil Input:** `"நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."`
- **Recognized English Translation:** `"I need to complete my Raven app by six o'clock tomorrow evening."`
- **Observed Extracted Task Title:** `"Tomorrow evening, by six o'clock, with me"`
- **Observed Task Metadata:** Duration: 30 minutes (fabricated), Priority: P2 Medium (fabricated), Confidence: 85% (fabricated).
- **Expected Extracted Task:**
  - **Proposed Title:** `"Complete my Raven app"`
  - **Action:** `"Complete"`
  - **Object:** `"my Raven app"`
  - **Deadline:** Tomorrow at 6:00 PM (`2026-11-08T18:00:00`)
  - **Duration:** `None` / `UNSPECIFIED` (user did not specify duration)
  - **Priority:** `None` / `UNSPECIFIED` (user did not specify priority)
  - **Status:** `PENDING_REVIEW`

---

## 2. End-to-End Pipeline Trace & Root-Cause Forensic Analysis

### 2.1 The Traced Request Path
```
Spoken Audio (.webm)
  │
  ▼
Gnani Prisma v3 ASR (Transcribed Tamil accurately)
  │
  ▼
POST /api/v1/captures/text (Raw text passed to NLU)
  │
  ▼
GeminiNLUProvider (extract_intent)
  │
  ├──► [FAILURE POINT 1]: Google AI Studio Free Tier Quota Exhaustion
  │    HTTP 429 RESOURCE_EXHAUSTED (Quota exceeded: limit 20 req/day for gemini-2.5-flash)
  │
  ▼
safe_extract_intent() Exception Handler
  │
  ▼
Fallback: MockNLUProvider (extract_intent)
  │
  ├──► [FAILURE POINT 2]: Naive String Slicing in SOV Grammar
  │    MockNLUProvider lines 556-570 used:
  │    `proposed_title = transcript_text[:50].capitalize()`
  │    `estimated_duration_min = 30`
  │    `priority = PriorityEnum.P2_MEDIUM`
  │    `confidence = 0.85`
  │
  ▼
Linguistic Truncation:
  `"நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."`
  [:50] characters = `"நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய"`
  (Lit: "Tomorrow evening by six o'clock of mine...")
  │
  ▼
Display Translation:
  Sarvam AI translated the truncated 50-character slice:
  `"Tomorrow evening, by six o'clock, with me"`
  │
  ▼
[FAILURE POINT 3]: Database Repository Silent Duration Defaulting
  `backend/app/db/repository.py:124`:
  `est_dur = item.estimated_duration_min or 30`
  `dur_source = item.duration_source or "DEFAULT_HEURISTIC"`
```

---

## 3. Linguistic Breakdown: Tamil (SOV) vs. English (SVO)

In English (Subject-Verb-Object), the action and object typically appear at the start:
> *"Complete my Raven app by six o'clock tomorrow evening."*  
> If an extractor naively slices the first 30–50 characters, it captures `"Complete my Raven app"` and drops the deadline.

In Tamil (Subject-Object-Verb), temporal adverbials appear at the **beginning**, direct objects in the **middle**, and auxiliary action verbs at the **very end**:
> `நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே` (Temporal Adverbial: Tomorrow evening by 6 o'clock)  
> `என்னோடய ரேவன் ஆப்பை` (Direct Object Phrase: my Raven app)  
> `கம்ப்ளீட் பண்ணணும்` (Predicative Action Verb: must complete)

A naive character slice (`[:50]`) inevitably chops off the predicate verb and the direct object, retaining **only** the temporal adverbial and the genitive pronoun (`என்னோடய` = "of mine" / "with me"). When fed to the downstream translation engine, it faithfully translated that mangled fragment into:
> `"Tomorrow evening, by six o'clock, with me"`

---

## 4. Root Causes in Code

### 4.1 `backend/app/providers/nlu/mock.py`
```python
# BROKEN ORIGINAL CODE:
proposed_title = transcript_text[:50].capitalize()
estimated_duration_min = 30
priority = PriorityEnum.P2_MEDIUM
confidence = 0.85
```
1. Fixed-length slicing was blind to sentence grammar and linguistic syntax.
2. Fabricated 30 minutes duration for every unrecognized input.
3. Fabricated P2 priority for every unrecognized input.
4. Fabricated 85% confidence score despite severe data corruption.

### 4.2 `backend/app/db/repository.py`
```python
# BROKEN ORIGINAL CODE:
est_dur = item.estimated_duration_min or 30
dur_source = item.duration_source or "DEFAULT_HEURISTIC"
```
The persistence layer silently overwrote `None` with `30`, violating the core product invariant: **"The AI proposes. The user decides. Never invent user commitments or preferences."**

### 4.3 `backend/app/providers/nlu/gemini.py`
System prompt lacked negative constraint instructions forbidding temporal debris in titles, which allowed LLM prompts to occasionally merge deadlines into task titles when Gemini was active.

---

## 5. Architectural Remediation Implemented

### 5.1 Sovereign Local Semantic Intent Parser (`backend/app/providers/nlu/semantic_parser.py`)
Built a deterministic linguistic parser independent of third-party API quotas:
1. **Multilingual Ingestion:** Preprocesses Tamil/Tanglish thoughts using `SarvamTranslationProvider` while preserving the exact `source_expression` and `original_transcript`.
2. **Temporal Adverbial Deconstruction:** Regex-based temporal extraction detects time expressions regardless of position (start, middle, end) and strips them cleanly from the clause before title construction.
3. **Action & Object Separation:** Deconstructs imperative sentences and passive constructions into distinct `action` (e.g. `Complete`) and `object` (e.g. `my Raven app`) entities.
4. **Strict Title Invariant:** Assembles title strictly as `f"{action} {object}"` without temporal or adverbial debris.
5. **Preservation of Explicit Silence:** When the user does not state a duration or priority, leaves `estimated_duration_min = None` and `priority = None`, and flags `UNSPECIFIED_DURATION` and `UNSPECIFIED_PRIORITY`.
6. **Intent Classification:** Supports `COMPLETED` activities (filtered from active planning), `CANCELLED` tasks, `CONDITIONAL_INTENTION` contingent triggers, `IDEA`/`WISH`, and `QUESTION` queries.
7. **Multi-Dimensional Confidence Scoring:**
   $$\text{Overall Confidence} = 0.35 \times C_{\text{intent}} + 0.35 \times C_{\text{action}} + 0.30 \times C_{\text{object}}$$
   Reports discrete confidence values for each dimension.

### 5.2 Schema Modernization
- Added `PriorityEnum.UNSPECIFIED` and made `priority` optional in `backend/app/schemas/intent.py`, `proposal.py`, `task.py`, and `frontend/src/types/index.ts`.
- Added conceptual fields `action`, `object`, `intent_confidence`, `action_confidence`, `object_confidence`, `deadline_confidence` to `ProposedItemExtraction` and `ProposalItemResponse`.

### 5.3 Database Repository Realignment
Updated `backend/app/db/repository.py`:
- Preserves `estimated_duration_min = None` and `priority = None`.
- Only applies learned priors if duration is unspecified or marked heuristic.
- Appends `UNSPECIFIED_DURATION` and `UNSPECIFIED_PRIORITY` uncertainty flags.

### 5.4 Frontend UX Enhancements
Updated `frontend/src/components/proposal/ProposalReviewCard.tsx`:
- Surfaces the decomposed `Action: [action] | Object: [object]` metadata badge.
- Added explicit `<option value="">Duration: Unspecified</option>` and `<option value="">Priority: Unspecified</option>`.
- Displays `deadline_expression` with a calendar icon.

---

## 6. Verification & Results

- **Unit & Integration Suite:** 102/102 backend tests passing (including 32 new regression tests).
- **Frontend Quality:** Production build succeeded with zero type errors, static generation of all 18 routes, and 0 ESLint warnings.
- **Test Case Verified:** Spoken input `"நாளைக்கு ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே என்னோடய ரேவன் ஆப்பை கம்ப்ளீட் பண்ணணும்."` yields:
  - `Title`: `"Complete my Raven app"`
  - `Action`: `"Complete"`
  - `Object`: `"my Raven app"`
  - `Deadline`: `"Tomorrow, 6:00 PM"` (`2026-11-08T18:00:00`)
  - `Duration`: `None` (`UNSPECIFIED_DURATION`)
  - `Priority`: `None` (`UNSPECIFIED_PRIORITY`)
  - `Status`: `PENDING_REVIEW`

