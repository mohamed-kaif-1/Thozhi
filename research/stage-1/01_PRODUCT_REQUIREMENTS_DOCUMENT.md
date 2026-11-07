# 01 — Product Requirements Document (PRD)

## 1. Document Control & Executive Overview
- **Product Name:** THOZHI
- **Product Category:** Multilingual AI-powered personal planning and execution assistant
- **Project Theme:** Sovereign AI for India
- **Document Stage:** Stage 1 — Engineering Specification & Technical Design
- **Status:** Architecture Specification — Pending Owner Approval
- **Implementation Status:** Strictly Prohibited
- **Decision Authority:** Project Owner Exclusively
- **Reference Document:** Master Product Requirements Document ([`Masterprd.md`](file:///c:/Users/moham/OneDrive - ELCOT/Projects/Thozhi/Masterprd.md))

THOZHI is designed to bridge the cognitive divide between how humans think (unstructured, spontaneous, fragmented, multilingual) and how productivity tools operate (rigid, structured, monolingual). 

**The Governing Axiom:**
$$\mathbf{The\ AI\ Proposes.\ The\ User\ Decides.}$$
THOZHI must never silently convert uncertain thoughts into confirmed commitments.

---

## 2. Comprehensive Traceability Matrix

This matrix establishes end-to-end traceability connecting Stage 0 research findings ([`research/stage-0/`](file:///c:/Users/moham/OneDrive - ELCOT/Projects/Thozhi/research/stage-0/README.md)), evidence quality ratings, user problems, functional requirements, architectural decisions, and unresolved assumptions.

| Finding ID & Stage 0 Source | Evidence Quality Level | Core User Problem | Derived Product Requirement | Architectural Decision Implemented | Unresolved Assumption / Open Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TR-01** (Doc `01`, `06`, `17`) | **[FACT]** (Verified via primary Todoist language docs) | Global tools (Todoist Ramble, MS To Do) officially omit Tamil and fail on spoken Tanglish phonetics. | **PRD-FR-01:** System must natively ingest, transcribe, and parse conversational Tanglish voice without forcing translation to English. | Abstract ASR Adapter behind `SpeechToTextProvider` supporting Gnani Prisma v3 (`indic-auto`) with Sarvam Saaras failover. | ASR accuracy on low-end microphones in noisy Tier-2 environments requires acoustic field benchmarking. |
| **TR-02** (Doc `01`, `03`, `18`) | **[FACT]** (Kahneman & Tversky, 1979; GTD Theory) | Users conflate casual ideas, conditional wishes, and legal commitments, causing todo-list paralysis and guilt. | **PRD-FR-02:** Intent classifier must categorize clauses into 10 distinct modalities (Commitment, Idea, Wish, Conditional, etc.). | Pydantic v2 structured JSON schema validator; ideas routed to non-calendar backlog. | Willingness of users to review categorized proposals versus manual checklists requires interview validation. |
| **TR-03** (Doc `06`, `07`, `17`) | **[SECONDARY]** (Motion G2 reviews & user churn) | Autonomous auto-reschedulers (Motion) create anxiety and cognitive disorientation by moving calendar blocks without asking. | **PRD-FR-03:** "AI proposes, user decides." Zero tasks scheduled without explicit human authorization. | Strict entity separation: `proposals` $\rightarrow$ `proposal_items` $\overset{\text{Approval Gate}}{\Longrightarrow}$ `tasks`. Database enforces transactional RLS boundary. | Optimal UI pattern for batch approval without review fatigue requires usability testing in Stage 2. |
| **TR-04** (Doc `08`, `17`) | **[FACT]** (Documented LLM arithmetic drift) | LLMs cannot reliably solve multi-variable bin-packing; they hallucinate time math and double-book calendar slots. | **PRD-FR-04:** Planning engine must calculate temporal capacity, free windows, and dependency validation using deterministic mathematics. | Decouple LLM from scheduling: Python backend runs Kahn’s DAG Topological Sort and Interval Capacity Deficit math. Optional Google OR-Tools CP-SAT evaluation. | Accuracy of user-provided durations (GIGO risk); requires optional duration prior learning. |
| **TR-05** (Doc `04`, `17`) | **[UNVERIFIED HYPOTHESIS]** (Pending field interviews) | Freelancer willingness-to-pay (WTP) and habit displacement of WhatsApp self-chat remain unconfirmed. | **PRD-FR-05:** Core architecture must be persona-agnostic and modular to accommodate multiple beachhead groups. | Persona-agnostic commitment data model (`Actor` + `Commitment` + `Duration` + `Deadline` + `Calendar Space`). | Final target market (Freelancers vs. Students vs. ASHA) is an unresolved product decision. |
| **TR-06** (Doc `10`, `17`, `Masterprd`) | **[FACT]** (Provider availability audit) | Gemini 2.0 Flash is not an approved choice; model availability and deprecation cycles require vendor decoupling. | **PRD-FR-06:** NLU extraction layer must operate behind a replaceable adapter with benchmarked models. | Replaceable LLM adapter evaluating candidate models (Gemini 1.5 Flash, GPT-4o-mini, Claude 3.5 Haiku, Llama 3.3) under identical datasets. | Final model selection pending benchmark execution on the 18 synthetic scenarios. |

---

## 3. Target Audience Reconciliation & Persona Framework

### 3.1 Reconciliation Analysis
In accordance with Section 5 of the Master Execution Prompt and Section 3 of `Masterprd.md`:
- **College Students:** Initial exploratory cohort. High problem frequency, very low friction, high campus virality, but **near-zero direct SaaS willingness-to-pay**.
- **Bilingual Freelancers & Solo Consultants:** High problem frequency, severe financial penalties for dropped deliverables, high Tanglish usage, validated willingness-to-expense software ($₹299–₹799/\text{mo}$), but high habit inertia from WhatsApp self-chat.
- **ASHA & Community Health Workers:** Mentioned in early exploratory notes. Operates under government reporting hierarchies (RCH portal), physical registers, and strict health ministry mandates. Building an unverified consumer planner for ASHA workers is premature and carries safety risks.

**Architectural Governance Directive:**  
The Stage 1 architecture **DOES NOT hard-code student-specific, corporate-specific, or ASHA-specific logic**. It models **universal human commitment workflows**. The final beachhead persona remains an **Unresolved Product Decision** awaiting human field interviews.

### 3.2 Candidate Personas

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Persona 1: Karthi — Bilingual Freelance Web & UI Consultant            │
├────────────────────────────────────────────────────────────────────────┤
│ Needs: Client commitments, overlapping project deadlines, billable     │
│        hours, GST filing, ad-hoc WhatsApp client requests.             │
│ Friction: Commits to deliverables without checking calendar deficits.   │
│ Language: Speaks fluent Tanglish during commute and planning.          │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Persona 2: Meena — Final-Year Engineering Student & Aspirant           │
├────────────────────────────────────────────────────────────────────────┤
│ Needs: Assignment deadlines, semester exam prep, placement coding,     │
│        team hackathons, lab record submissions.                        │
│ Friction: Drowned in class WhatsApp group notifications; cramming.     │
│ Language: High-density colloquial Tanglish with peer slang.            │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ Persona 3: Selvi — Community Health / Field Coordinator (ASHA Scout)   │
├────────────────────────────────────────────────────────────────────────┤
│ Needs: Field visits, child immunization follow-ups, village meetings.  │
│ Friction: Heavy paper registers, forgotten follow-up dates in the sun. │
│ Language: Pure regional Tamil dialect with Tamil medical terms.        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Product Objectives & Non-Goals

### 4.1 Primary Objectives
1. **Reduce Friction:** Eliminate the cognitive overhead of manually structuring thoughts into tasks.
2. **Commitment Disambiguation:** Distinguish genuine commitments from casual ideas, wishes, and conditionals.
3. **Temporal Truthfulness:** Verify workload feasibility against real calendar capacity; flag deficits proactively.
4. **Preserve Human Control:** Enforce "The AI proposes. The user decides." Zero silent task creation.
5. **Multilingual Integrity:** Natively handle Tamil, English, and Tanglish without forced English translation.
6. **Transparent Memory:** Provide user-sovereign memory with one-click purge and zero raw audio retention.

### 4.2 Non-Goals
THOZHI is explicitly NOT:
- A general-purpose conversational chatbot.
- A full-featured replacement for external calendars (Google/Outlook).
- An autonomous personal agent with unrestricted external execution permissions.
- A medical or clinical decision-support tool.
- A financial advisory system.
- An employee surveillance or keystroke logging platform.
- A complex multi-agent AI framework.

---

## 5. Core Product Workflow (The 10-Step Lifecycle)

In strict alignment with Section 5 of `Masterprd.md`:
$$\mathbf{Capture} \rightarrow \mathbf{ASR} \rightarrow \mathbf{Understand} \rightarrow \mathbf{Structure} \rightarrow \mathbf{Clarify} \rightarrow \mathbf{Plan} \rightarrow \mathbf{Conflict\ Detect} \rightarrow \mathbf{Propose} \rightarrow \mathbf{Approve} \rightarrow \mathbf{Execute}$$

1. **Step 1: Capture:** User inputs raw text or records audio (up to 60s) via browser Web Audio API.
2. **Step 2: Speech Recognition:** Audio processed by Gnani Prisma v3 REST API (with Sarvam Saaras failover). Raw audio is destroyed immediately post-ASR.
3. **Step 3: Intent Understanding:** Replaceable LLM adapter extracts tasks, commitments, ideas, deadlines, dependencies, negations, and self-repairs.
4. **Step 4: Structured Representation:** Items mapped into typed Pydantic proposals (`proposal_items`). Unknown durations and dates are left explicitly unknown.
5. **Step 5: Clarification:** Targeted questions generated ONLY when missing information directly affects scheduling feasibility.
6. **Step 6: Planning:** Deterministic Python engine evaluates deadlines, priority, estimated duration, dependencies, and available working hours.
7. **Step 7: Conflict Detection:** Identifies overloaded days ($\sum \text{Durations} > \text{Free Capacity}$) and circular dependencies. Explains trade-offs.
8. **Step 8: Proposal Presentation:** Renders editable Proposal Card showing tasks, durations, conflict badges, and inline edit controls.
9. **Step 9: User Approval:** User clicks "Approve All", approves selected items, edits, or vetoes.
10. **Step 10: Execution:** Approved items promoted atomically to `tasks` table in PostgreSQL. Optional export to Google Calendar.

---

## 6. MVP Scope (MoSCoW Breakdown)

In alignment with Section 18 of `Masterprd.md`:

### P0 — Essential (Must-Have for MVP)
- Authentication (Supabase Auth: Magic Link / Google OAuth).
- Text capture & microphone audio capture (16kHz WAV mono).
- Verified Gnani Prisma ASR integration (with Sarvam failover).
- Multilingual intent extraction (Commitments, Ideas, Wishes, Conditionals, Completed).
- Structured proposal generation with inline editing.
- Explicit human approval gate & idempotent task promotion.
- Task management (List, Complete, Edit, Cancel, Delete).
- User-provided availability windows (`working_hours_start`, `working_hours_end`).
- Dependency detection & Kahn's DAG cycle detection.
- Deterministic capacity deficit & conflict analysis.
- Memory & privacy controls (zero audio retention, one-click memory purge).
- Responsive web interface (Next.js + Tailwind + shadcn/ui).

### P1 — Important (Should-Have Post-MVP)
- User-approved duration priors (consensual learning from manual edits).
- Optional one-way Google Calendar export.
- Conversational clarification prompts for ambiguous deadlines.
- Recurring task rules.
- Daily dashboard workload summaries.

### P2 — Future Roadmap (Could-Have)
- Native mobile applications (React Native / Capacitor).
- Full bi-directional calendar synchronization.
- WhatsApp / Telegram webhook ingestion.
- Semantic contextual retrieval via `pgvector`.
- Sub-task decomposition (Goblin Tools style).
