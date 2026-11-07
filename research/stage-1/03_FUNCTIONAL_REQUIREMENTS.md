# 03 — Functional Requirements Specification (FRS)

## 1. Document Control & Scope
- **Document Stage:** Stage 1 — Functional Specification
- **Product:** THOZHI
- **Status:** Architecture Specification (Implementation Prohibited)
- **Framework:** Formal Functional Requirements (FR-01 through FR-42) categorized by system domain.

---

## 2. Master Functional Requirements Catalog

### 2.1 Domain 1: Ingestion & Multilingual Capture

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-01** | Spoken Audio Ingestion | **P0** | User taps and holds/toggles "Speak" button in web UI. | Browser captures microphone input via Web Audio API; encodes client-side to 16kHz Mono WAV. | Base64 or Binary Audio Blob sent to `/api/v1/captures/audio`. | Clean audio stream encoded without clicks or clipping; captures up to 60 seconds. |
| **FR-02** | Text Capture Ingestion | **P0** | User types unstructured thought in input box and hits Enter/Plan. | Text payload validated and sanitized; dispatches to `/api/v1/captures/text`. | Ingestion payload stored in `raw_captures` table with `input_type='TEXT'`. | Accepts up to 2,000 characters; handles Unicode Tamil, English, and Latin phonetics. |
| **FR-03** | Tanglish Speech Transcription | **P0** | Audio blob received at backend speech pipeline. | Dispatches audio to Gnani Prisma v3 REST API (`indic-auto` / `ta`). Fallback to Sarvam Saaras if Gnani fails. | Raw code-mixed text transcript (e.g., *"நாளைக்கு afternoon 3 PM-க்கு review"*). | Concept Error Rate (CER) $\le 10\%$; latency $\le 1.8\text{s}$ for 15s audio. |
| **FR-04** | ASR Failover & Circuit Breaker | **P0** | Gnani returns HTTP 401, 429, 504, or network timeout ($>3\text{s}$). | Backend catches error and instantly retries audio with Sarvam AI Saaras API. | Seamless transcript returned without exposing error to client. | Failover latency penalty $\le 1.2\text{s}$; error logged to audit monitoring. |

---

### 2.2 Domain 2: Intent Understanding & Semantic Taxonomy

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-05** | Modality Classification | **P0** | Raw transcript passed to Replaceable NLU extraction prompt (evaluating Gemini 1.5 Flash, GPT-4o-mini, Haiku). | LLM classifies every distinct clause into: `COMMITMENT`, `IDEA`, `WISH`, `CONDITIONAL`, `COMPLETED`, `CANCELLED`. | JSON array of classified items with modality enums. | Zero confusion between hard commitments and casual ideas across the 18 synthetic test scenarios. |
| **FR-06** | Casual Idea Isolation | **P0** | User speaks an aspirational thought (*"Maybe I should start a podcast"*). | Item tagged as `CASUAL_IDEA`; omitted from daily schedule; routed to "Ideas Backlog". | Daily plan remains free of aspirational clutter. | Ideas accessible in a separate "Ideas Tab" without due dates or calendar slots. |
| **FR-07** | Conditional Task Handling | **P0** | User states an if-then intention (*"If Suresh approves, send the PO"*). | Item tagged as `CONDITIONAL_TASK`; trigger condition extracted as a metadata string. | Held in "Pending Triggers" list; not booked on calendar. | Scheduled only when user confirms condition is met. |
| **FR-08** | Retrospective / Completed Filtering | **P0** | User mentions past actions (*"I already paid the electricity bill"*). | Item tagged as `COMPLETED_ACTION`; zero scheduling overhead generated. | Item logged in completed history or discarded from proposal card. | Completed actions never appear on the proposed daily agenda. |
| **FR-09** | Relative Date Normalization | **P0** | Colloquial date expressions in Tamil or English (*"naalaiki sayanthiram"*). | LLM anchors relative expression to server ISO-8601 timestamp + Asia/Kolkata timezone. | Target deadline output as ISO-8601 string (e.g., `2026-11-08T17:00:00+05:30`). | Zero off-by-one date errors; accurately maps "day after tomorrow", "next Monday", etc. |
| **FR-10** | Negation & Mid-Stream Correction | **P0** | User corrects self mid-sentence (*"Thursday 4 PM... wait, no, make that Friday 11 AM"*). | LLM identifies self-repair; discards revoked timestamp (Thursday); retains active intent (Friday). | Single proposed task targeting Friday 11:00 AM. | No duplicate or zombie tasks generated from retracted statements. |

---

### 2.3 Domain 3: Deterministic Planning & Constraint Logic

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-11** | Task Dependency Extraction | **P0** | User states sequential tasks (*"Before deploying, run tests"*). | LLM maps dependency IDs: `Task_Deploy.dependencies = [Task_Tests]`. | Structured dependency array in ParsedIntent. | Correct predecessor-successor relationships captured. |
| **FR-12** | DAG Topological Sort & Cycle Detection | **P0** | Extracted dependency graph passed to Python planning module. | Python executes Kahn’s algorithm on Directed Acyclic Graph (DAG). | Linear execution sequence produced, OR `CIRCULAR_DEPENDENCY` error raised. | 100% deterministic cycle detection; zero infinite scheduling loops. |
| **FR-13** | Working Hours Free Space Computation | **P0** | Planning engine queries user calendar for target date. | Calculates unbooked intervals between `working_hours_start` and `working_hours_end`. | Array of available time windows $[w_1, w_2, \dots]$. | Accurately accounts for existing external calendar meetings. |
| **FR-14** | Workload Capacity Deficit Warning | **P0** | Sum of estimated durations exceeds available free window minutes. | Python calculates: $\text{Deficit} = \sum d_j - \sum w_i$. | Flag `CAPACITY_DEFICIT` attached to proposal with exact deficit minutes. | Warning displayed prominently on Proposal Card: *"You are 2.5 hours overbooked today."* |
| **FR-15** | Realistic Interval Bin-Packing | **P0** | Feasible set of tasks fitted into open calendar windows. | Deterministic greedy interval assignment: tasks placed in open slots respecting dependencies. | Proposed start time and end time attached to each proposed task. | Zero overlapping task intervals; strictly respects existing calendar meetings. |

---

### 2.4 Domain 4: Proposal Card & Human-in-the-Loop Governance

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-16** | Proposal Card Rendering | **P0** | Backend dispatches proposal payload to frontend. | Next.js UI renders Proposal Card with task titles, tags, durations, and conflict badges. | Clean, visual proposal card displayed to user. | Renders in $<200\text{ms}$ upon API response; all conflict flags visually highlighted. |
| **FR-17** | Inline Proposal Editing | **P0** | User clicks on proposed task title, duration, or deadline pill. | UI switches to inline edit mode; user updates values; local state updates. | Modified proposal ready for approval. | No full-page reload; updates reflected in proposal state machine instantly. |
| **FR-18** | One-Tap Proposal Veto / Reject | **P0** | User swipes or clicks "Reject / Delete" on a proposed item. | Item removed from active proposal; proposal status updated to `REJECTED`. | Item discarded; capacity deficit recalculated in real time. | Rejected items never written to `saved_tasks`. |
| **FR-19** | Explicit User Approval Gate | **P0** | User clicks "Approve All" or "Approve Selected". | UI sends POST to `/api/v1/proposals/{id}/approve` with approved task IDs. | ACID transaction commits items into `saved_tasks`. | **ZERO tasks created without this explicit user action.** |
| **FR-20** | Idempotent Task Creation | **P0** | User double-clicks "Approve" button rapidly or experiences network retry. | Backend checks idempotency key in PostgreSQL. | Single task set created; duplicate requests return 200 OK without re-inserting. | Zero duplicate tasks in database under any network race condition. |

---

### 2.5 Domain 5: Task Management & Persistence

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-21** | Task Lifecycle State Transitions | **P0** | User completes, pauses, or cancels a task. | Updates `saved_tasks.status`: `PENDING` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED` / `CANCELLED`. | Task marked with strike-through or moved to completed view. | State transitions recorded with timestamps for auditability. |
| **FR-22** | Daily Agenda View | **P0** | User opens app home screen. | Fetches approved tasks for `scheduled_date = CURRENT_DATE`. | Clean, focused daily to-do list with time-blocks and priority indicators. | Loads in $<300\text{ms}$; displays overdue items from yesterday with "Roll Over" prompt. |
| **FR-23** | One-Click Task Postponement | **P0** | User clicks "Move to Tomorrow" on an uncompleted task. | Updates `scheduled_date = CURRENT_DATE + 1`; status set to `POSTPONED`. | Task moved to tomorrow's queue. | Preserves original creation audit trail. |

---

### 2.6 Domain 6: Memory, Context & Personalization

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-24** | Consensual Duration Prior Learning | **P1** | User manually corrects task duration (e.g., changes 30m to 60m for "Code Review"). | If "Learn from Edits" is enabled in settings, updates moving average in `user_duration_priors`. | Future "Code Review" proposals default to 60m. | Never learns without explicit user opt-in toggle in settings. |
| **FR-25** | One-Click Memory Purge | **P0** | User clicks "Purge All Learned Preferences" in Settings. | Database deletes all records in `user_duration_priors` and clears contextual summaries. | Memory reset to factory defaults. | Complete, irreversible deletion confirmed in $<500\text{ms}$. |
| **FR-26** | Audio Zero-Retention Enforcement | **P0** | Speech recognition completes and transcript is stored. | Backend background task deletes audio WAV file from temp storage immediately. | Zero raw audio persisted on disk or cloud storage. | Audio file existence verified 0 bytes post-transcription. |

---

### 2.7 Domain 7: Calendar Integration (P1 Post-MVP)

| Req ID | Requirement Title | Priority | Trigger / Input | System Processing | Output / Result | Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **FR-27** | Google Calendar Event Export | **P1** | User approves daily proposal with "Sync to Google Calendar" enabled. | Dispatches authorized OAuth call to Google Calendar API; creates calendar event. | Calendar event created with task title and duration time-block. | Synchronizes in $<1.5\text{s}$; stores Google `event_id` in `saved_tasks`. |
| **FR-28** | Standard `.ics` File Export | **P0** | User clicks "Export Day as iCal". | Backend formats approved daily tasks into standard RFC 5545 `.ics` file. | File downloaded to user device for import into Apple Calendar / Outlook. | 100% compliant RFC 5545 formatting. |

