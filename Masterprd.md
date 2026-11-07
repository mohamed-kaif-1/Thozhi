# THOZHI
## Master Product Requirements Document (Master PRD)

**Product:** THOZHI  
**Product Category:** Multilingual AI-powered personal planning and execution assistant  
**Project Theme:** Sovereign AI for India  
**Document Type:** Master Product Requirements Document  
**Version:** 1.0 — Consolidated Product Blueprint  
**Status:** Strategic Product Specification — Pending Owner Approval  
**Implementation Status:** Not authorized  
**Decision Authority:** Project Owner

---

# 1. PRODUCT VISION

## 1.1 What is THOZHI?

THOZHI is a multilingual AI-powered personal planning assistant designed to help people transform unstructured thoughts, responsibilities, commitments, and goals into realistic, organized, actionable plans.

People continuously think about things they need to do:

- Tasks they must complete.
- Promises they have made.
- Deadlines they need to meet.
- Ideas they want to explore.
- Responsibilities they cannot forget.
- Goals they want to accomplish.
- Things they need to coordinate with other people.

However, these thoughts are rarely organized when they occur.

They may be expressed through fragmented speech, text messages, Tanglish, English, Tamil, or a mixture of languages.

Existing productivity tools generally expect users to manually create and organize tasks. Voice assistants can capture information, but capturing information is not the same as understanding it, prioritizing it, and creating a realistic plan.

THOZHI aims to bridge that gap.

**THOZHI should understand what the user means, identify what actually needs to happen, reason about constraints, and propose a realistic plan that the user remains in control of.**

## 1.2 Product Philosophy

The governing principle:

**The AI proposes. The user decides.**

THOZHI must never silently convert uncertain thoughts into confirmed commitments.

It should:

1. Listen or read.
2. Understand.
3. Identify uncertainty.
4. Organize.
5. Analyze constraints.
6. Propose.
7. Explain.
8. Wait for approval.
9. Execute approved actions.
10. Learn only within the user's chosen memory permissions.

The objective is not to create another chatbot or another basic to-do list.

The objective is to build a reliable personal planning system.

---

# 2. THE PROBLEM

## 2.1 Core Problem Statement

People frequently express their responsibilities in unstructured, multilingual language, but traditional productivity systems require them to manually translate those thoughts into structured tasks, priorities, deadlines, and schedules.

This creates several problems:

- Cognitive overhead during task capture.
- Forgotten commitments.
- Confusion between ideas and actual responsibilities.
- Incorrect deadline interpretation.
- Poor prioritization.
- Unrealistic schedules.
- Hidden dependencies.
- Conflicting commitments.
- Repeated manual organization.
- Difficulty maintaining plans when circumstances change.

## 2.2 Problems THOZHI Investigates

### Problem A — Commitment Understanding

The system must distinguish between:

- A promise.
- An idea.
- A wish.
- A possible future intention.
- A conditional intention.
- A question.
- A completed responsibility.
- A cancelled responsibility.

Example:

"I should send the report tomorrow."

This may be an intention, but the system should not automatically assume it is a confirmed commitment.

Example:

"I promised my teammate that I would send the report tomorrow."

This expresses a stronger commitment.

Example:

"If I finish the assignment, I might attend the workshop."

This is conditional and should not become an unconditional task.

### Problem B — Realistic Planning

Users need more than a list of extracted tasks.

They need to understand:

- What should happen first?
- How much time is available?
- Which tasks have dependencies?
- Which tasks have deadlines?
- What can realistically be completed?
- What needs to be postponed?
- What cannot fit into the available schedule?

### Problem C — Deadline and Capacity Conflicts

THOZHI should identify:

- Overloaded days.
- Conflicting deadlines.
- Insufficient available time.
- Tasks dependent on unfinished work.
- Incompatible time windows.
- Unrealistic workload estimates.

### Problem D — Multilingual Intent Understanding

Users may communicate through:

- Tamil.
- English.
- Tanglish.
- Code-mixed sentences.
- Language switching.
- Informal spoken expressions.

The system must preserve meaning rather than simply translate everything into English.

These four areas remain research hypotheses. Their relative importance must be established through user validation.

---

# 3. TARGET USERS

## 3.1 Target Audience Status

The final market has not been approved.

Potential audiences include:

### A. Bilingual freelancers and solo consultants

Potential needs:

- Client commitments.
- Multiple projects.
- Deadlines.
- Deliverables.
- Meetings.
- Personal responsibilities.
- Workload management.

### B. College students

Potential needs:

- Assignments.
- Examinations.
- Project deadlines.
- Team commitments.
- Workshops and events.
- Personal routines.

College students are currently an exploratory research cohort, not automatically the final target audience.

### C. ASHA and community health workers

Potential needs:

- Field responsibilities.
- Follow-ups.
- Scheduled activities.
- Community commitments.
- Multilingual communication.

This audience requires a separate workflow and safety assessment. It must not be assumed that a general student/freelancer planner is appropriate for this context.

## 3.2 Persona Selection Rule

The beachhead persona must be selected using evidence from:

- Problem frequency.
- Problem severity.
- Current workaround.
- Existing alternatives.
- Willingness to adopt.
- User accessibility.
- Ability to test the solution.
- Demonstrated improvement after using a prototype.

Do not choose a target market solely because it is technically convenient.

---

# 4. PRODUCT OBJECTIVES

## 4.1 Primary Objectives

THOZHI must aim to:

1. Reduce the effort required to organize unstructured thoughts.
2. Identify genuine commitments and actionable intentions.
3. Extract useful task information accurately.
4. Identify deadlines, priorities, and dependencies.
5. Help users understand their workload.
6. Detect impossible or conflicting schedules.
7. Generate understandable, editable action plans.
8. Preserve user control over every important action.
9. Support natural multilingual communication.
10. Provide transparent, controllable memory.

## 4.2 Non-Goals

The initial product is NOT intended to be:

- A general-purpose conversational chatbot.
- A replacement for every calendar application.
- An autonomous personal agent with unrestricted permissions.
- A medical decision-support system.
- A financial decision-making assistant.
- An employee surveillance system.
- A social media management system.
- A fully autonomous task execution platform.
- A complex multi-agent AI framework.

---

# 5. CORE PRODUCT EXPERIENCE

## 5.1 Main User Journey

The primary workflow:

**Capture → Understand → Structure → Analyze → Plan → Review → Approve → Execute**

### Step 1: Capture

The user provides thoughts through:

- Text input.
- Voice recording.
- Future optional integrations.

Example:

"Tomorrow I have college until four. I need to finish the project report by Friday. I promised Arjun that I would send the research material today. I also have two assignments this week."

### Step 2: Speech Recognition

For voice input:

1. Request microphone permission.
2. Capture audio.
3. Submit it to the configured speech recognition provider.
4. Receive a transcript.
5. Preserve language and relevant expression.
6. Handle transcription failure explicitly.

THOZHI should not retain raw audio by default.

### Step 3: Intent Understanding

The AI extracts:

- Tasks.
- Commitments.
- Ideas.
- Deadlines.
- Time references.
- Conditional statements.
- Priorities.
- People or entities mentioned.
- Dependencies.
- Uncertainties.
- Corrections.
- Negations.

Every extracted item must include a confidence or uncertainty representation appropriate to the extraction type.

### Step 4: Structured Representation

Transform the input into structured proposal items.

Example:

Item 1:
- Title: Send research material to teammate.
- Type: Commitment.
- Due: Today.
- Source: Explicit user statement.
- Duration: Unknown.
- Status: Proposed.

Item 2:
- Title: Finish project report.
- Type: Task.
- Due: Friday.
- Duration: Unknown.
- Status: Proposed.

Item 3:
- Title: Complete assignment one.
- Type: Task.
- Due: Unknown within this week.
- Duration: Unknown.
- Status: Proposed.

Do not invent missing information.

### Step 5: Clarification

If important information is missing, THOZHI should ask targeted questions.

Examples:

- "You said this week. Is there a specific deadline?"
- "How much time do you expect this assignment to take?"
- "Is sending the report a confirmed commitment or just something you are considering?"

Do not ask unnecessary questions when the missing detail does not affect the decision.

### Step 6: Planning

The deterministic planning engine evaluates:

- Deadlines.
- Priorities.
- Estimated duration.
- Duration uncertainty.
- Task dependencies.
- Available time.
- Existing commitments.
- Time windows.
- User preferences.

### Step 7: Conflict Detection

Example:

"You have approximately six hours of available study time, but the tasks you want to complete require nine hours."

The system should explain:

- Which constraints conflict.
- What information is uncertain.
- Which tasks cannot fit.
- What alternatives exist.

### Step 8: Proposal Presentation

Present a clear, editable proposal.

Each task should show:

- Title.
- Type.
- Deadline.
- Estimated duration and its source.
- Priority.
- Dependencies.
- Confidence or uncertainty.
- Conflicts.
- Recommended action.

### Step 9: User Approval

The user may:

- Approve all.
- Approve selected items.
- Edit.
- Reject.
- Defer.
- Request clarification.

No proposed item becomes an approved task without explicit user approval.

### Step 10: Execution

Only approved actions are persisted as active tasks or sent to authorized integrations.

External calendar creation, notifications, or other integrations require their own explicit permissions and action confirmation.

---

# 6. FUNCTIONAL REQUIREMENTS

## 6.1 Capture Management

FR-01: Support text-based thought capture.

FR-02: Support microphone-based audio capture.

FR-03: Display recording and processing states.

FR-04: Handle microphone permission denial.

FR-05: Handle failed uploads and interrupted requests.

FR-06: Support transcript correction before task extraction.

FR-07: Allow users to discard captures.

## 6.2 Multilingual Understanding

FR-08: Support the languages verified for the configured ASR provider.

FR-09: Evaluate Tamil-English code-mixing.

FR-10: Handle language switching within one input.

FR-11: Preserve original language expressions where useful.

FR-12: Detect negation and corrections.

FR-13: Detect ambiguous dates and time expressions.

FR-14: Avoid inventing information missing from the original input.

## 6.3 Intent Extraction

FR-15: Identify tasks and actionable responsibilities.

FR-16: Identify commitments.

FR-17: Identify ideas and non-actionable thoughts.

FR-18: Identify conditional intentions.

FR-19: Identify questions and informational statements.

FR-20: Identify completed and cancelled tasks.

FR-21: Extract deadlines and time windows.

FR-22: Extract dependencies.

FR-23: Represent unknown fields explicitly.

FR-24: Preserve provenance linking extracted fields to the original input.

## 6.4 Task Management

FR-25: Create approved tasks.

FR-26: Edit tasks.

FR-27: Mark tasks complete.

FR-28: Cancel tasks.

FR-29: Delete tasks.

FR-30: Filter and search tasks.

FR-31: Display task deadlines and priorities.

FR-32: Display dependency relationships.

## 6.5 Planning

FR-33: Accept user-provided availability.

FR-34: Estimate workload.

FR-35: Detect schedule conflicts.

FR-36: Detect dependency cycles.

FR-37: Identify infeasible plans.

FR-38: Generate proposed schedules.

FR-39: Explain scheduling decisions.

FR-40: Allow users to adjust proposed plans.

FR-41: Recalculate plans after changes.

## 6.6 Approval

FR-42: Support approval of individual proposal items.

FR-43: Support approval of selected items.

FR-44: Prevent duplicate task creation during repeated approval.

FR-45: Record approval provenance.

FR-46: Reject approval of expired, cancelled, or invalid proposals.

FR-47: Maintain an auditable state-transition history.

## 6.7 Memory

FR-48: Maintain task history.

FR-49: Support optional user-controlled duration preferences.

FR-50: Allow users to inspect stored personal preferences.

FR-51: Allow users to edit and delete stored preferences.

FR-52: Support user data export and deletion.

## 6.8 External Integrations

FR-53: Keep external calendar integration optional for the initial MVP.

FR-54: If enabled, retrieve availability through explicitly authorized calendar access.

FR-55: Allow approved calendar event creation.

FR-56: Keep calendar failure independent of successful internal task approval.

FR-57: Prevent duplicate external event creation.

---

# 7. NON-FUNCTIONAL REQUIREMENTS

## 7.1 Performance

Initial engineering targets, subject to benchmarking:

- Text capture should feel immediate.
- Standard API responses should target sub-second latency where practical.
- Voice transcription and AI extraction should be measured independently.
- Full voice-to-proposal processing should target a responsive experience, with a provisional P95 target of 10 seconds for supported short inputs.
- Planning calculations should remain deterministic and locally executable within the backend process for typical personal workloads.

Do not claim these targets have been achieved before testing.

## 7.2 Reliability

- Failed provider requests must not create tasks.
- Repeated approvals must not duplicate tasks.
- Partial failures must be recoverable.
- User data must remain isolated.
- AI output must pass schema and semantic validation.
- Uncertain plans must be labelled accordingly.

## 7.3 Scalability

Start with a modular monolith.

Do not introduce distributed infrastructure until measurable workload justifies it.

## 7.4 Accessibility

- Responsive layouts.
- Keyboard navigation.
- Accessible labels.
- Readable contrast.
- Mobile-friendly controls.
- Clear recording and processing feedback.
- Support for Unicode Tamil text.

## 7.5 Compatibility

Target modern desktop and mobile browsers.

Microphone capture requires HTTPS and browser permission.

Background or lock-screen recording is not promised by the web MVP.

---

# 8. COMPLETE RECOMMENDED TECHNOLOGY STACK

The following is the proposed implementation stack. Versions must be checked for current compatibility before installation.

## 8.1 Frontend

**Framework: Next.js**

Recommended:
- Next.js App Router.
- React.
- TypeScript.
- Stable supported Node.js LTS release.

Why:
- Strong web application ecosystem.
- Server rendering where useful.
- Responsive PWA support.
- Good developer experience.
- Straightforward deployment.

**Styling:**
- Tailwind CSS.
- shadcn/ui.
- Lucide icons.

**State Management:**
- Zustand only for genuine shared client state.
- React built-in state for local UI state.
- TanStack Query for server state, caching, and request lifecycle.

**Forms and Validation:**
- React Hook Form.
- Zod.

**Audio Capture:**
- Browser MediaDevices API.
- MediaRecorder API.
- Audio conversion pipeline only if required by the verified ASR provider.
- Explicit recording state management.

**Frontend Testing:**
- Vitest.
- React Testing Library.
- Playwright.
- axe-core for accessibility testing.

Avoid unnecessary state-management layers.

## 8.2 Backend

**Framework: FastAPI**

Recommended:
- Python 3.12 or another currently supported Python version verified against required SDKs.
- FastAPI.
- Pydantic v2.
- Uvicorn.
- HTTPX.
- SQLAlchemy 2.x or a consistently selected database-access strategy.
- Alembic for migrations.

Responsibilities:

- Authentication verification.
- Capture management.
- ASR provider integration.
- AI extraction.
- Output validation.
- Scheduling.
- Proposal management.
- Approval.
- Task management.
- Memory management.
- Security enforcement.

Use a modular monolith, not microservices.

## 8.3 Database

**Primary database: Supabase PostgreSQL**

Services:
- PostgreSQL.
- Supabase Auth.
- Row Level Security.
- Supabase database backups, according to the selected plan.
- Optional Supabase Storage only if future product requirements justify persistent files.

Preferred region: Mumbai (`ap-south-1`), subject to account availability and a full data-flow residency assessment.

Use PostgreSQL as the source of truth.

Do not introduce a second database for the MVP.

## 8.4 Authentication

Recommended:
- Supabase Auth.
- Email-based authentication.
- OAuth only where justified.
- Secure session management.
- JWT verification in FastAPI.

Authentication and authorization must be separate.

Never trust a user ID supplied by the client without verifying it against the authenticated identity.

## 8.5 AI and Speech Architecture

### Primary Speech Recognition

**Gnani AI Prisma**

Purpose:
- Convert supported speech into text.
- Enable the challenge's meaningful Gnani model integration.
- Evaluate Indian-language speech recognition and code-mixing.

Before implementation, verify:

- Actual endpoint.
- API authentication.
- Supported models.
- Supported languages.
- Audio formats.
- File size and duration limits.
- Rate limits.
- Account credits.
- Concurrency.
- Error responses.
- Retention and data-processing terms.

Do not treat a document's endpoint claim as a verified integration.

### Optional ASR Alternative

**Sarvam AI Saaras**

Potential role:
- Comparative ASR benchmark.
- Optional explicitly configured fallback.

Do not automatically send private audio to a second provider without a clear disclosure and permission policy.

Fallback must not create duplicate captures or silently change the provider's data-handling assumptions.

### NLU and Intent Extraction

Use a replaceable LLM provider adapter.

The selected model must be verified for:

- Availability.
- Structured output.
- Tamil support.
- Tanglish extraction.
- Language switching.
- Negation.
- Date/time interpretation.
- Context handling.
- Pricing.
- Latency.
- Data retention.

Gemini 2.0 Flash is NOT an approved choice because it has been shut down.

No new model should be approved merely because it is the newest or cheapest.

Benchmark candidates using the same synthetic evaluation dataset before selection.

### Deterministic Processing

Use Python services for:

- Schema validation.
- Date normalization.
- Dependency validation.
- Cycle detection.
- Capacity calculation.
- Conflict detection.
- Approval enforcement.
- Duplicate prevention.

LLMs must not directly write approved tasks or decide that an infeasible schedule is feasible.

## 8.6 Scheduling Engine

Initial recommendation:

- Python deterministic planning module.
- Graph algorithms for dependency ordering.
- Interval and capacity calculations.
- Explicit constraint validation.
- Optional Google OR-Tools CP-SAT after evaluating its complexity and requirements.

Scheduling inputs:

- Available time windows.
- Existing busy periods.
- Deadlines.
- Earliest start times.
- Duration estimates.
- Dependencies.
- Priorities.
- User constraints.

Scheduling outputs:

- Proposed time allocations.
- Conflicts.
- Unscheduled tasks.
- Capacity deficits.
- Uncertainty explanations.
- Feasibility status.

Possible statuses:

- FEASIBLE.
- INFEASIBLE.
- NEEDS_CLARIFICATION.
- INCOMPLETE_INFORMATION.

A topological sort alone does not solve scheduling optimization.

A greedy scheduler must not claim to guarantee optimal feasibility.

## 8.7 Memory

Use PostgreSQL initially.

Do not introduce Redis, Pinecone, Weaviate, or a separate vector database in the MVP.

Potential future use:
- pgvector for contextual semantic retrieval, only if proven necessary.

## 8.8 Deployment

**Frontend:**
- Vercel or another compatible managed frontend platform.

**Backend:**
- Render, Google Cloud Run, or another managed Python hosting service.
- Choose after evaluating free-tier restrictions, regional availability, uptime, cold starts, and pricing.

**Database:**
- Supabase managed PostgreSQL.

**Domain and HTTPS:**
- Managed domain and HTTPS.

**CI/CD:**
- GitHub.
- GitHub Actions.
- Automated linting, tests, and deployment checks.

Do not commit API keys or environment files.

## 8.9 Monitoring and Logging

Recommended:
- Structured application logs.
- Request IDs.
- Error tracking such as Sentry, if its privacy and pricing terms are acceptable.
- Provider latency metrics.
- Task approval metrics.
- AI extraction evaluation.

Do not log raw audio, API keys, access tokens, or unrestricted personal transcripts.

## 8.10 Tools and Development Environment

- Git and GitHub.
- VS Code.
- PowerShell on Windows.
- Python virtual environment.
- Node package manager.
- Docker only when required for reproducible local services.
- Postman or Bruno for API testing.
- Playwright for browser workflows.
- Pytest for backend testing.

Avoid heavy local AI models due to limited development hardware.

---

# 9. SYSTEM ARCHITECTURE

## 9.1 High-Level Architecture

```text
                  USER
                   |
                   v
        NEXT.JS WEB APPLICATION
        - Dashboard
        - Capture Interface
        - Proposal Review
        - Task Management
        - Planning View
                   |
                   | HTTPS + Authenticated JWT
                   v
             FASTAPI BACKEND
                   |
        +----------+-----------+
        |          |           |
        v          v           v
     Capture    AI Service   Planning
     Service    Layer        Engine
        |          |           |
        v          v           v
     Audio/     Gnani ASR   Deterministic
     Text       Provider    Constraint Logic
        |          |
        |          v
        |       LLM NLU
        |          |
        +----------+
                   |
                   v
             VALIDATION
                   |
                   v
             PROPOSALS
                   |
                   v
             USER APPROVAL
                   |
                   v
          APPROVAL TRANSACTION
                   |
                   v
             POSTGRESQL
                   |
          +--------+--------+
          |        |        |
          v        v        v
        Tasks    Memory   Audit
                          History
```

## 9.2 Backend Module Structure

```text
backend/
  app/
    main.py

    core/
      config.py
      security.py
      errors.py
      logging.py

    modules/
      auth/
      captures/
      speech/
      ai/
      intent/
      proposals/
      planning/
      tasks/
      memory/
      integrations/
      audit/

    providers/
      asr/
      nlu/

    database/
      models/
      repositories/
      migrations/

    schemas/
    tests/
```

## 9.3 Frontend Structure

```text
frontend/
  src/
    app/

    components/
      capture/
      proposals/
      tasks/
      planning/
      dashboard/
      common/

    features/
      authentication/
      capture/
      intent-review/
      task-management/
      planning/
      memory-settings/

    hooks/
    services/
    stores/
    schemas/
    types/
    lib/
```

The structure is a logical recommendation, not a mandate to create every folder immediately.

---

# 10. DATABASE ARCHITECTURE

PostgreSQL is the single source of truth.

## 10.1 Core Tables

### users / profiles

Stores application-level user preferences and profile information.

Supabase Auth remains responsible for identity authentication.

### captures

Stores capture metadata and permitted transcript data.

Suggested fields:

- id
- user_id
- input_type
- transcript_text
- detected_language
- processing_status
- provider_metadata
- created_at
- retention_expires_at

Raw audio is not persisted by default.

### proposals

One parent proposal per processing result.

Suggested fields:

- id
- user_id
- capture_id
- status
- model_provider
- model_version
- created_at
- expires_at

### proposal_items

Individual extracted items.

Suggested fields:

- id
- proposal_id
- user_id
- item_type
- proposed_title
- description
- deadline
- earliest_start
- estimated_duration_min
- duration_source
- priority
- confidence
- uncertainty_flags
- source_reference
- status

### tasks

Only approved task items become active tasks.

Suggested fields:

- id
- user_id
- source_proposal_item_id
- title
- description
- deadline
- estimated_duration_min
- priority
- status
- created_at
- updated_at

### task_dependencies

Normalized dependency relationships.

Suggested fields:

- id
- user_id
- predecessor_task_id
- successor_task_id
- dependency_type

Use foreign keys and ownership constraints.

### availability_windows

User-entered working or available periods.

Suggested fields:

- id
- user_id
- start_time
- end_time
- recurrence_rule
- timezone

### busy_events

Stores relevant busy intervals supplied by the user or authorized external calendar integrations.

### plans

Stores generated planning sessions.

### plan_items

Stores proposed schedule allocations and their relationship to tasks.

### memory_preferences

Stores explicit user-controlled duration and planning preferences.

### contextual_summaries

Optional summaries with explicit retention and deletion rules.

### approval_idempotency

Stores approval operation identifiers and replay results.

### audit_logs

Stores necessary security and state-transition events without unrestricted copies of sensitive input.

## 10.2 Database Rules

- Every user-owned record must be isolated.
- Use RLS on user-owned tables.
- Enforce ownership through foreign keys or equivalent integrity rules.
- Prevent duplicate promotion of proposal items.
- Use unique idempotency constraints.
- Use database transactions for approval.
- Keep schema changes versioned with migrations.
- Avoid storing duplicate personal content without justification.

---

# 11. AI ARCHITECTURE

## 11.1 AI Pipeline

```text
Raw Input
    |
    v
Speech Recognition (if audio)
    |
    v
Transcript
    |
    v
Language and Context Analysis
    |
    v
Intent Classification
    |
    v
Entity Extraction
    |
    v
Temporal Interpretation
    |
    v
Dependency Extraction
    |
    v
Structured Output Validation
    |
    v
Uncertainty and Conflict Detection
    |
    v
Proposal Generation
    |
    v
Human Review
```

## 11.2 Structured Intent Schema

Each proposed item should represent:

- Item identifier.
- Item type.
- Title.
- Description.
- Original source expression.
- Deadline.
- Earliest start.
- Time window.
- Duration.
- Duration source.
- Priority.
- Dependencies.
- Conditional status.
- Confidence.
- Uncertainty.
- Clarification requirements.

## 11.3 Intent Categories

- TASK
- COMMITMENT
- IDEA
- WISH
- CONDITIONAL_INTENTION
- QUESTION
- REMINDER
- COMPLETED
- CANCELLED
- INFORMATIONAL

These categories should be refined through evaluation.

## 11.4 Uncertainty Rules

If the system does not know:

- A date: do not invent one.
- A duration: leave it unknown.
- A priority: ask or use an explicitly labelled provisional suggestion.
- A dependency: mark it uncertain.
- A commitment status: request clarification when consequential.

Confidence scores must not be presented as perfectly calibrated probabilities unless calibration has been measured.

## 11.5 Prompt Injection and Untrusted Output

Treat all captured text and model responses as untrusted.

The system must:

- Validate structured output.
- Validate field ranges.
- Check user ownership.
- Reject unsupported actions.
- Separate model reasoning from executable actions.
- Prevent model output from directly invoking privileged database operations.
- Apply deterministic business rules after model extraction.

---

# 12. MEMORY ARCHITECTURE

THOZHI uses a hybrid memory approach with explicit user control.

## 12.1 Layer One — Operational Memory

Purpose:
- Task history.
- Completion state.
- Approved plans.
- Dependencies.
- Corrections.

Storage:
- PostgreSQL.

## 12.2 Layer Two — User-Controlled Personal Memory

Potential information:

- Preferred working hours.
- Preferred planning style.
- User-approved duration priors.
- Explicit recurring preferences.

The user must be able to:

- Inspect.
- Edit.
- Disable.
- Delete.

Do not infer sensitive personal attributes.

## 12.3 Layer Three — Contextual Summaries

Optional summaries of relevant task or planning context.

These must:

- Have explicit purposes.
- Be user-isolated.
- Have retention rules.
- Be deletable.
- Avoid retaining unnecessary raw personal information.

## 12.4 Duration Learning

Duration priors may be learned only from sufficient, relevant task history.

Distinguish:

- User-provided duration.
- Model suggestion.
- Learned estimate.
- Unknown.

A learned estimate must not silently become a confirmed fact.

---

# 13. API ARCHITECTURE

Use versioned REST APIs.

Base path:

`/api/v1`

## 13.1 Authentication

- Supabase Auth.
- JWT verification.
- User-scoped authorization.

## 13.2 Capture APIs

- `POST /captures/text`
- `POST /captures/audio`
- `GET /captures`
- `GET /captures/{capture_id}`
- `DELETE /captures/{capture_id}`

## 13.3 Proposal APIs

- `GET /proposals`
- `GET /proposals/{proposal_id}`
- `PATCH /proposals/{proposal_id}/items/{item_id}`
- `POST /proposals/{proposal_id}/approve`
- `POST /proposals/{proposal_id}/reject`

Approval requests must support selected item IDs and persistent idempotency.

## 13.4 Task APIs

- `GET /tasks`
- `POST /tasks` for explicitly user-created tasks
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `POST /tasks/{task_id}/complete`

## 13.5 Planning APIs

- `POST /plans`
- `GET /plans/{plan_id}`
- `PATCH /plans/{plan_id}`
- `POST /plans/{plan_id}/recalculate`

## 13.6 Availability APIs

- `GET /availability`
- `POST /availability`
- `PATCH /availability/{id}`
- `DELETE /availability/{id}`

## 13.7 Memory APIs

- `GET /memory/preferences`
- `PATCH /memory/preferences`
- `DELETE /memory/preferences/{id}`
- `POST /privacy/export`
- `DELETE /account/data`

## 13.8 API Rules

Every endpoint must define:

- Authentication.
- Authorization.
- Request schema.
- Response schema.
- Validation errors.
- Rate limits.
- Idempotency requirements.
- Ownership checks.
- Failure handling.

---

# 14. APPROVAL AND EXECUTION SAFETY

The system must maintain separate entities and state transitions:

```text
RAW_INPUT
    |
    v
PARSED_INTENT
    |
    v
PROPOSED_ITEM
    |
    +----> REJECTED
    |
    +----> NEEDS_CLARIFICATION
    |
    v
APPROVED_ITEM
    |
    v
ACTIVE_TASK
    |
    +----> COMPLETED
    |
    +----> CANCELLED
```

Important rules:

1. Parsing does not create tasks.
2. Proposal creation does not create tasks.
3. Editing a proposal does not approve it.
4. Approval must be authenticated.
5. Approval must be atomic.
6. Repeated approval must return the original outcome.
7. External side effects must have separate idempotency.
8. Failed integrations must not silently reverse successful internal approval.
9. All important state transitions must be auditable.

---

# 15. SECURITY AND PRIVACY

## 15.1 Authentication and Authorization

- Supabase Auth.
- JWT validation.
- User ownership verification.
- RLS.
- Least-privilege service access.
- Restricted service-role usage.

Service-role credentials bypass ordinary RLS enforcement and must never be exposed to the browser.

## 15.2 Audio Privacy

- Do not persist raw audio by default.
- Avoid recording without permission.
- Avoid raw audio logging.
- Use short-lived processing buffers.
- Document third-party ASR processing and retention.
- Do not claim provider-side deletion unless verified.

## 15.3 Transcript Privacy

Transcript retention must be an explicit product policy.

Users should be able to choose from clearly explained retention settings where supported.

Deletion must cover derived copies and contextual summaries, subject to clearly documented legal and security retention exceptions.

## 15.4 Data Protection

- HTTPS.
- Secrets in server-side environment configuration.
- No secrets committed to Git.
- Input validation.
- Rate limiting.
- Secure error handling.
- Audit logging.
- Backup and recovery procedures.
- Data export and deletion.

## 15.5 Sovereign AI Considerations

THOZHI should prioritize Indian-language AI capabilities and transparent handling of Indian user data.

However, the use of an Indian AI provider alone does not prove complete data sovereignty.

Assess:

- Data location.
- Processing location.
- Subprocessors.
- Retention.
- Cross-border transfer.
- Model training policies.
- Logging.
- Backup location.

---

# 16. UI/UX REQUIREMENTS

## 16.1 Product Design Direction

The experience should be:

- Calm.
- Minimal.
- Clear.
- Trustworthy.
- Mobile-first.
- Accessible.
- Fast to use.

Avoid an overly complicated productivity dashboard.

## 16.2 Main Screens

### 1. Authentication

- Sign up.
- Login.
- Account recovery.

### 2. Home Dashboard

Displays:

- Today's approved tasks.
- Upcoming deadlines.
- Current workload.
- Pending proposals.
- Quick capture.

### 3. Capture Screen

- Text entry.
- Voice recording.
- Transcript preview.
- Processing state.
- Error state.

### 4. Proposal Review

- Extracted items.
- Confidence and uncertainty.
- Deadline.
- Duration.
- Dependencies.
- Conflicts.
- Edit and reject actions.
- Approval controls.

### 5. Planning View

- Available time.
- Proposed task placement.
- Unscheduled tasks.
- Workload deficits.
- Conflict explanations.

### 6. Task Management

- Task list.
- Task detail.
- Completion.
- Editing.
- Cancellation.

### 7. Memory and Privacy Settings

- Stored preferences.
- Transcript retention.
- Memory controls.
- Data export.
- Account deletion.

### 8. Settings

- Language preference.
- Timezone.
- Working hours.
- Notification preferences.
- Connected integrations.

---

# 17. TESTING AND EVALUATION

## 17.1 Testing Categories

### Unit Tests

- Date parsing.
- Dependency graph.
- Cycle detection.
- Capacity calculations.
- Conflict detection.
- State transitions.
- Idempotency logic.

### Integration Tests

- Supabase authentication.
- RLS isolation.
- AI provider adapters.
- Capture processing.
- Approval transactions.
- Memory deletion.

### End-to-End Tests

- Signup.
- Capture text.
- Capture voice.
- Review proposal.
- Edit proposal.
- Approve selected items.
- Manage tasks.
- Delete data.

### AI Evaluation

Test:

- Commitment extraction.
- Negation.
- Conditional statements.
- Tamil.
- English.
- Tanglish.
- Language switching.
- Date extraction.
- Corrections.
- Ambiguity.
- Dependencies.
- False-positive task creation.

### Security Testing

- Cross-user access.
- Invalid JWT.
- Prompt injection.
- Malformed model output.
- Duplicate approval.
- Unauthorized task creation.
- Data deletion.
- Rate limiting.

## 17.2 Evaluation Metrics

Measure independently:

- ASR word error rate.
- Intent classification precision and recall.
- Commitment extraction precision and recall.
- Deadline extraction accuracy.
- Negation detection accuracy.
- Dependency extraction accuracy.
- False task creation rate.
- Proposal edit rate.
- Proposal rejection rate.
- Approval rate.
- Schedule feasibility rate.
- Duplicate task creation rate.
- End-to-end latency.

Do not report synthetic benchmark performance as real-world market validation.

## 17.3 Critical Safety Metric

**Zero Silent Task Creation**

No AI-generated proposal item may become an active task without explicit approval.

This is a hard acceptance requirement.

---

# 18. MVP SCOPE

## 18.1 MVP — Must Have

1. Authentication.
2. Text capture.
3. Voice capture.
4. Verified Gnani speech recognition integration.
5. Multilingual intent extraction.
6. Structured proposal generation.
7. Editable proposal items.
8. Explicit approval.
9. Task management.
10. User-provided availability.
11. Basic dependency detection.
12. Deterministic workload and conflict analysis.
13. Basic plan proposal.
14. Memory controls.
15. Privacy controls.
16. Evaluation suite.
17. Responsive web interface.

## 18.2 MVP — Should Have

- More detailed planning optimization.
- User-approved duration priors.
- Recurring tasks.
- Optional calendar integration.
- Improved multilingual correction handling.
- Notifications.

## 18.3 Future Scope

- Native Android application.
- Native iOS application.
- Calendar synchronization.
- Email integrations.
- WhatsApp integrations, subject to platform policies.
- Advanced personal memory.
- Semantic contextual retrieval.
- Voice responses.
- Shared planning.
- Team workflows.
- Advanced scheduling optimization.

Do not add these before the core workflow demonstrates value.

---

# 19. DEVELOPMENT ROADMAP

## Stage 0 — Product Validation

Objectives:

- Competitor research.
- User interviews.
- Problem prioritization.
- Target audience selection.
- Gnani API feasibility verification.
- Product hypothesis evaluation.

Exit criteria:
- Evidence-backed problem selection.
- Initial target persona.
- Clear MVP problem.
- Technical feasibility established.

## Stage 1 — Product and System Architecture

Objectives:

- Master PRD.
- Functional requirements.
- System architecture.
- Database design.
- API contracts.
- AI architecture.
- Memory design.
- Security and privacy.
- Testing strategy.

Exit criteria:
- Cross-document consistency.
- Owner-approved decisions.
- No critical architecture blockers.

## Stage 2 — UI/UX Design

Objectives:

- User flows.
- Wireframes.
- Design system.
- Responsive layouts.
- Interactive prototypes.
- Usability testing.

Exit criteria:
- Core user journey approved.

## Stage 3 — Development Foundation

Objectives:

- Repository structure.
- Frontend foundation.
- Backend foundation.
- Database migrations.
- Authentication.
- CI/CD.
- Environment configuration.

Exit criteria:
- Secure application skeleton.
- Automated baseline tests.

## Stage 4 — Capture and AI Understanding

Objectives:

- Text capture.
- Audio capture.
- Gnani ASR.
- NLU provider integration.
- Structured extraction.
- Multilingual evaluation.

Exit criteria:
- Reliable extraction on defined test scenarios.

## Stage 5 — Task and Planning Engine

Objectives:

- Proposal management.
- Approval transactions.
- Task management.
- Dependency graph.
- Availability model.
- Conflict detection.
- Schedule proposal.

Exit criteria:
- No silent task creation.
- Correctly validated planning constraints.

## Stage 6 — Memory and Personalization

Objectives:

- Operational history.
- User-controlled preferences.
- Duration priors.
- Memory inspection.
- Memory deletion.

Exit criteria:
- Correct isolation and deletion behaviour.

## Stage 7 — Integration

Objectives:

- Frontend/backend integration.
- AI integration.
- Database integration.
- Error recovery.
- Optional external services.

Exit criteria:
- End-to-end core workflow passes.

## Stage 8 — Quality and Security

Objectives:

- Functional tests.
- AI evaluation.
- Performance tests.
- Security tests.
- Privacy review.
- Usability tests.

Exit criteria:
- All mandatory acceptance criteria pass.

## Stage 9 — Deployment and Submission

Objectives:

- Production deployment.
- Documentation.
- Demo preparation.
- Synthetic test data.
- Challenge submission.
- Public project communication.

Exit criteria:
- Working application.
- Demonstrable Gnani integration.
- Required challenge deliverables.

---

# 20. ACCEPTANCE CRITERIA

THOZHI MVP cannot be declared complete unless:

1. Users can capture text and supported speech.
2. The system can produce structured intent proposals.
3. Uncertain commitments are not silently confirmed.
4. Unknown durations remain unknown.
5. Ambiguous deadlines are handled safely.
6. Task dependencies are validated.
7. Schedule conflicts are detectable.
8. Infeasible schedules are explicitly identified.
9. Users can edit and reject proposals.
10. Only approved items become active tasks.
11. Concurrent duplicate approvals do not create duplicate tasks.
12. User data remains isolated.
13. Memory controls work.
14. Deletion covers derived personal data according to the documented policy.
15. AI provider failures do not create incorrect tasks.
16. The application works on supported desktop and mobile browsers.
17. The Gnani integration is real, authenticated, and demonstrable.
18. Testing results are documented honestly.

---

# 21. TECHNICAL DECISIONS — APPROVAL STATUS

| Decision | Proposed choice | Status |
|---|---|---|
| Product platform | Responsive web/PWA | Pending approval |
| Frontend | Next.js + TypeScript | Proposed |
| UI styling | Tailwind + shadcn/ui | Proposed |
| Backend | Python + FastAPI | Proposed |
| Validation | Pydantic v2 + Zod | Proposed |
| Database | Supabase PostgreSQL | Proposed |
| Authentication | Supabase Auth | Proposed |
| AI speech | Gnani Prisma | Account verification required |
| NLU | Replaceable LLM provider | Benchmark required |
| Planning | Deterministic Python engine | Proposed |
| Scheduling optimization | OR-Tools evaluation | Optional |
| Memory | PostgreSQL hybrid model | Proposed |
| Vector database | Deferred | Proposed |
| Frontend deployment | Vercel or equivalent | Pending |
| Backend deployment | Managed Python hosting | Pending |
| Monitoring | Structured logs and error tracking | Proposed |

No technical decision becomes formally approved merely because it appears in this document.

---

# 22. EXPLICITLY REJECTED COMPLEXITY

Do not introduce without a demonstrated requirement:

- Kubernetes.
- Microservices.
- Multi-agent orchestration.
- LangChain.
- Redis.
- Dedicated vector databases.
- Local LLM inference.
- Complex event streaming.
- Autonomous calendar modification.
- Unrestricted AI tool execution.

The architecture should remain maintainable by a small development team.

---

# 23. PRODUCT SUCCESS DEFINITION

THOZHI succeeds only if it creates measurable user value.

It is not enough to demonstrate that:

- Speech can be transcribed.
- An LLM can extract tasks.
- A database can store tasks.
- A calendar can display schedules.

The real success question is:

**Can THOZHI reduce the effort required to turn complicated, unstructured responsibilities into a plan that users understand, trust, and can realistically execute?**

The product must be evaluated against existing user behaviour and tools.

Success should include:

- Less manual organization.
- Fewer misunderstood commitments.
- Better recognition of conflicts.
- More realistic plans.
- High user comprehension.
- Meaningful user acceptance.
- Low correction burden.
- No unauthorized actions.

---

# 24. OPEN DECISIONS REQUIRING PROJECT OWNER APPROVAL

1. Which target persona should the first MVP serve?
2. Is the initial product a responsive web application/PWA?
3. Should the MVP use only user-entered availability, or must it connect to a calendar?
4. Which Gnani API/model is available to the challenge account?
5. Which NLU model passes the multilingual benchmark?
6. What is the default transcript retention policy?
7. Should duration priors be enabled by default or opt-in?
8. Which deployment platform meets the budget and regional requirements?
9. Which scheduling constraints are mandatory for the first release?
10. What minimum evidence is required to declare product validation successful?

---

# 25. FINAL GOVERNANCE RULES

- This Master PRD is the central product reference.
- Detailed specifications must remain consistent with it.
- Changes require documented decisions.
- Research hypotheses must remain distinguishable from proven findings.
- Technical claims must be verified.
- No implementation begins without explicit approval of the applicable stage.
- No AI action may bypass user authorization.
- No sensitive data should be collected without a defined purpose and retention policy.
- No architecture review may approve itself without independent verification.

**THOZHI: Understand the thought. Organize the responsibility. Make the plan realistic. Keep the human in control.**

**The AI proposes. The user decides.**