# 05 — System Architecture & C4 Structural Design

## 1. Architectural Principles & Philosophy
THOZHI is designed as a **Modular Monolith** optimized for developer ergonomics, minimal infrastructure overhead, and extreme reliability.

In strict adherence to Section 9 of the Master Execution Prompt:
- **NO Kubernetes:** Replaced by single-container Docker or PaaS hosting.
- **NO Microservices:** All backend services operate within a single, cleanly modularized FastAPI application package.
- **NO Redis / Kafka:** Ephemeral state is managed in-memory or in PostgreSQL transactions.
- **NO LangChain / Multi-Agent Frameworks:** Prompting and structured schema enforcement use the official, native Google GenAI SDK with Pydantic.
- **Strict Decoupling:** AI providers (Gnani, Sarvam, Gemini) are isolated behind abstract Python interfaces.

---

## 2. C4 Architecture Level 1: System Context Diagram

The System Context diagram illustrates how THOZHI interacts with human users and external third-party software systems.

```mermaid
C4Context
    title System Context Diagram for THOZHI
    
    Person(user, "User (Freelancer / Student / Professional)", "Captures thoughts verbally in Tanglish/English; reviews proposed plans.")
    
    System(thozhi, "THOZHI System", "Translates unstructured thoughts into realistic, user-approved schedules with conflict detection.")
    
    System_Ext(gnani, "Gnani.ai Prisma STT", "Primary Indic speech recognition engine for Tamil and Tanglish audio.")
    System_Ext(sarvam, "Sarvam AI Saaras STT", "Commercial fallback ASR engine providing pay-as-you-go Indic transcription.")
    System_Ext(gemini, "Replaceable NLU Provider", "Multilingual NLU adapter evaluating candidate models (Gemini 1.5 Flash, GPT-4o-mini, Claude 3.5 Haiku) enforcing Pydantic structured JSON task extraction.")
    System_Ext(supabase, "Supabase Managed Cloud", "PostgreSQL database, Row-Level Security, and user authentication.")
    System_Ext(gcal, "Google Calendar API", "Optional external calendar for fetching busy intervals and exporting approved tasks.")

    Rel(user, thozhi, "Speaks Tanglish thoughts, reviews proposal cards, approves tasks", "HTTPS / Web Audio")
    Rel(thozhi, gnani, "Sends 16kHz mono audio, receives Tanglish transcript", "HTTPS REST (X-API-Key-ID)")
    Rel(thozhi, sarvam, "Failover: Sends audio, receives transcript", "HTTPS REST (Bearer Token)")
    Rel(thozhi, gemini, "Sends raw transcript + date anchor, receives JSON entities", "HTTPS (Google GenAI SDK)")
    Rel(thozhi, supabase, "Authenticates users, stores raw captures, proposals, and approved tasks", "PostgreSQL Wire / RLS")
    Rel(thozhi, gcal, "Queries busy slots, pushes approved events", "HTTPS OAuth 2.0")
```

---

## 3. C4 Architecture Level 2: Container Diagram

The Container diagram decomposes THOZHI into its runtime executable environments, storage repositories, and boundary protocols.

```mermaid
C4Container
    title Container Diagram for THOZHI

    Person(user, "User", "Bilingual knowledge worker or freelancer")

    Container_Boundary(c1, "THOZHI Platform") {
        Container(spa, "Single Page Application (SPA)", "Next.js 14 / React / TypeScript / Tailwind / shadcn/ui", "Provides mobile-first web UI, Web Audio recording, Zustand proposal review state machine.")
        Container(api, "API Application (Modular Monolith)", "Python 3.11 / FastAPI / Pydantic v2", "Ingests speech, coordinates ASR/LLM, executes deterministic graph/capacity math, manages approval state.")
        ContainerDb(db, "Relational Database", "PostgreSQL 15 (Supabase)", "Stores users, captures, task proposals, approved tasks, duration priors, and audit logs with RLS.")
    }

    System_Ext(speech_ext, "Indic ASR Layer", "Gnani Prisma v3 / Sarvam Saaras")
    System_Ext(llm_ext, "LLM Extraction Layer", "Replaceable NLU Adapter")
    System_Ext(auth_ext, "Identity Provider", "Supabase Auth (Magic Link / OAuth)")

    Rel(user, spa, "Interacts via responsive browser UI", "HTTPS")
    Rel(spa, auth_ext, "Authenticates user session", "HTTPS / JWT")
    Rel(spa, api, "Dispatches audio/text, receives proposals, submits approvals", "HTTPS REST (Bearer JWT)")
    Rel(api, db, "Reads/writes domain entities within transactions", "asyncpg / SQLAlchemy (Pool)")
    Rel(api, speech_ext, "Transcribes raw voice", "HTTPS REST")
    Rel(api, llm_ext, "Extracts structured task JSON", "HTTPS REST")
```

---

## 4. C4 Architecture Level 3: Component Diagram (FastAPI Modular Monolith)

The Component diagram details the internal modular structure of the backend application. Every domain module is self-contained with clear interface boundaries:

```mermaid
graph TD
    subgraph "FastAPI Modular Monolith (`app/`)"
        subgraph "Ingestion Router (`app/routers/`)"
            R_Cap["Captures Router<br/>`POST /api/v1/captures`"]
            R_Prop["Proposals Router<br/>`POST /api/v1/proposals/{id}/approve`"]
            R_Task["Tasks Router<br/>`GET /api/v1/tasks`"]
        end

        subgraph "Core Business Services (`app/services/`)"
            S_Speech["Speech Ingestion Service<br/>(Audio Normalization & Temp Storage)"]
            S_NLU["Semantic Extraction Service<br/>(Gemini Prompting & Schema Validator)"]
            S_Plan["Deterministic Planning Engine<br/>(Kahn's DAG, Deficit Math & Bin-Packing)"]
            S_Task["Task & Proposal Manager<br/>(ACID Promotion & Idempotency)"]
            S_Mem["Memory & Preferences Service<br/>(User Duration Priors & Purge)"]
        end

        subgraph "External Integration Adapters (`app/adapters/`)"
            A_Gnani["Gnani Prisma Adapter<br/>(`X-API-Key-ID`)"]
            A_Sarvam["Sarvam Saaras Adapter<br/>(Failover Circuit Breaker)"]
            A_Gemini["Gemini Client Adapter<br/>(Pydantic Native Schema)"]
            A_GCal["Google Calendar Adapter<br/>(OAuth Busy Slots & Event Push)"]
        end

        subgraph "Data Access & Persistence (`app/repositories/`)"
            Repo_User["User & Profile Repo"]
            Repo_Capture["Raw Capture Repo"]
            Repo_Prop["Proposal Repo"]
            Repo_Task["Saved Task Repo"]
        end
    end

    %% Router to Service Wiring
    R_Cap --> S_Speech
    R_Cap --> S_NLU
    R_Cap --> S_Plan
    R_Prop --> S_Task
    R_Task --> S_Task

    %% Service to Adapter Wiring
    S_Speech --> A_Gnani
    S_Speech --> A_Sarvam
    S_NLU --> A_Gemini
    S_Plan --> A_GCal

    %% Service to Repository Wiring
    S_Speech --> Repo_Capture
    S_Plan --> Repo_Prop
    S_Task --> Repo_Prop
    S_Task --> Repo_Task
    S_Task --> S_Mem
```

---

## 5. End-to-End Dataflow Pipelines

### 5.1 Pipeline 1: Voice Ingestion to Proposal Assembly
1. **Audio Capture:** Client browser captures audio via `navigator.mediaDevices.getUserMedia()`, encodes stream into a 16kHz Mono WAV blob client-side using a lightweight WebAssembly encoder, and dispatches a multipart `POST` to `/api/v1/captures/audio`.
2. **ASR Dispatch:** `SpeechIngestionService` writes audio to volatile memory (`io.BytesIO`) and calls `GnaniPrismaAdapter`.
3. **Circuit-Breaker Failover:** If Gnani returns an error code or times out ($>3\text{s}$), the service dispatches immediately to `SarvamSaarasAdapter`.
4. **Transcript Forwarding:** Raw transcript (e.g., *"Naalaiki morning 10 AM-ku client meeting, draft ready pannanum"*) is forwarded to `SemanticExtractionService`. Audio buffer is immediately deallocated from RAM.
5. **NLU Schema Extraction:** `GeminiClientAdapter` sends prompt with server timestamp anchor (`Asia/Kolkata`) and Pydantic `ExtractionResponse` schema.
6. **Constraint Checking:** `DeterministicPlanningEngine` receives parsed tasks:
   - Evaluates task dependencies via Kahn’s DAG algorithm.
   - Calculates available working hours free windows from database/calendar.
   - Computes capacity deficit ($\sum \text{Durations} - \text{Free Capacity}$).
   - Assigns provisional start/end slots.
7. **Proposal Storage:** A draft record is committed to `task_proposals` with status `PENDING_APPROVAL`.
8. **Client Response:** Frontend receives the complete proposal payload and renders the interactive Proposal Card.

### 5.2 Pipeline 2: Human Decision to Execution
1. **User Action:** User inspects Proposal Card. User edits a duration from 30m to 45m, clicks the "X" button to reject an aspirational idea, and clicks "Approve All Remaining".
2. **Approval Dispatch:** Client sends `POST /api/v1/proposals/{proposal_id}/approve` with payload:
   ```json
   {
     "approved_item_ids": ["item_1", "item_3"],
     "edited_items": [{ "id": "item_1", "duration_minutes": 45 }],
     "idempotency_key": "user123_prop456_20261107"
   }
   ```
3. **Atomic Transaction:** Backend opens PostgreSQL transaction:
   - Verifies `idempotency_key` (rejects duplicates).
   - Updates `task_proposals` status to `APPROVED`.
   - Inserts approved items into `saved_tasks` table with status `PENDING`.
   - Commits transaction.
4. **Calendar Push (Optional):** If user enabled calendar sync, dispatches background task to push events to Google Calendar.
5. **UI Confirmation:** Next.js UI updates to display the active Daily Plan view.

---

## 6. Hardware & Deployment Footprint

| Component | Target Deployment Environment | Runtime Specs & Resource Constraints |
| :--- | :--- | :--- |
| **Frontend UI** | Vercel Serverless / Cloudflare Pages | Node.js 18+ Edge Runtime; memory cap 512 MB. |
| **Backend API** | Single Container PaaS (Render / Fly.io / Cloud Run) | Python 3.11, 1 vCPU, 1 GB RAM (scales to zero when idle). |
| **Database** | Supabase Managed Cloud (PostgreSQL 15) | Hosted in `ap-south-1` (Mumbai); 500 MB storage tier sufficient for MVP pilot. |
| **Local Dev** | Single Developer Machine (macOS / Windows / Linux) | Docker Compose or native virtualenv + Next.js dev server; total active RAM $\le 3.5\text{ GB}$. |

