# 04 — Non-Functional Requirements Specification (NFRS)

## 1. Document Control & Scope
- **Document Stage:** Stage 1 — Non-Functional Architecture & Quality Attributes
- **Product:** THOZHI
- **Status:** Architecture Specification (Implementation Prohibited)
- **Framework:** ISO/IEC 25010 Software Quality Model covering Performance, Reliability, Security, Usability, Maintainability, and Regulatory Compliance.

---

## 2. Performance & Latency Budgets

### 2.1 End-to-End Latency Budget (Voice-to-Proposal Card)
For a typical 15-second conversational Tanglish voice dump recorded over a 4G/5G mobile connection, the total perceived round-trip time (RTT) from the user tapping "Stop Speaking" to the Proposal Card rendering must not exceed **3,500 milliseconds (3.5 seconds)**.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOTAL END-TO-END LATENCY BUDGET: $\le 3,500\text{ ms}$                  │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Client Audio WAV Encoding (WebAssembly):       $\le 150\text{ ms}$  │
│ 2. Network Payload Transmission (Client -> API):  $\le 250\text{ ms}$  │
│ 3. ASR Inference (Gnani Prisma REST v3):          $\le 1,400\text{ ms}$│
│ 4. LLM Structured Extraction (Fast NLU Adapter):        $\le 1,100\text{ ms}$│
│ 5. Deterministic Planning Math (Python DAG/CSP):  $\le 50\text{ ms}$   │
│ 6. DB Insertion (`task_proposals` table):         $\le 150\text{ ms}$  │
│ 7. Network Response & UI Render:                  $\le 400\text{ ms}$  │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Client-Side Web Performance Metrics
The Next.js frontend must meet Google Core Web Vitals thresholds on mobile devices (tested against simulated Moto G Power / 4G network):
- **First Contentful Paint (FCP):** $\le 1.2\text{ seconds}$.
- **Time to Interactive (TTI):** $\le 2.0\text{ seconds}$.
- **Cumulative Layout Shift (CLS):** $\le 0.05$ (preventing jumpy UI during proposal card loading).
- **Client Bundle Size:** Total initial JavaScript payload $\le 180\text{ KB}$ gzipped.

---

## 3. Reliability & Availability

| Metric ID | Parameter | Target Standard | Architectural Mechanism |
| :--- | :--- | :--- | :--- |
| **NFR-REL-01** | System Uptime | $\ge 99.5\%$ monthly uptime (excluding scheduled maintenance). | Deployed on managed cloud infrastructure (Vercel serverless frontend + FastAPI on containerized PaaS + Supabase managed DB). |
| **NFR-REL-02** | ASR Failover Circuit Breaker | Failover triggering within $1,000\text{ ms}$ of primary failure. | Abstract ASR Adapter catches HTTP 401/429/504 or $3\text{s}$ timeout on Gnani Prisma $\rightarrow$ instantly routes to Sarvam Saaras API. |
| **NFR-REL-03** | Graceful Degradation | Zero total system lockouts on external API outage. | If both ASR providers fail, UI alerts the user and immediately displays the manual text input box. If LLM fails, raw transcript is saved to notes. |
| **NFR-REL-04** | Data Transaction Integrity | 100% ACID compliance on task approval. | PostgreSQL transactions wrap proposal status promotion and task persistence; zero partial or orphaned tasks. |

---

## 4. Scalability & Resource Constraints

### 4.1 Developer Machine Footprint (Local Dev Constraint)
In accordance with Section 9 of the Stage 1 Master Execution Prompt, the architecture must run seamlessly on a **standard, resource-constrained developer laptop** without requiring complex virtualization clusters:
- **RAM Footprint:** Entire local development stack (Next.js dev server, FastAPI backend, local Supabase CLI or lightweight PostgreSQL) must operate within $\le 4.0\text{ GB}$ of active RAM.
- **CPU Footprint:** No heavy local model weights (no local 7B LLM or local Whisper models); all heavy inference is offloaded to remote cloud APIs (Gemini Flash & Gnani/Sarvam).
- **Storage Footprint:** Repository and dependencies must occupy $< 1.5\text{ GB}$ on disk.

### 4.2 Production Serverless Scalability
- **Concurrency:** FastAPI modular monolith must handle $\ge 50$ concurrent active planning sessions per container instance.
- **Scale-to-Zero:** Architecture must support scale-to-zero serverless hosting (e.g., Vercel + Fly.io / Render / Cloud Run) to maintain near-zero idle infrastructure costs during early pilot testing.

---

## 5. Security & Regulatory Compliance

### 5.1 India Digital Personal Data Protection (DPDP) Act 2023 Compliance
As an application handling Indian citizens' personal voice recordings and schedule data, THOZHI must comply with the DPDP Act 2023:
1. **Notice & Consent:** Explicit bilingual consent modal displayed at first audio recording: *"THOZHI processes your voice purely to extract tasks. Raw audio is deleted immediately after transcription."*
2. **Right to Erasure (Data Erasure):** A single-tap "Delete My Entire Account & Data" action in Settings that executes a cascading delete across `users`, `raw_captures`, `task_proposals`, and `saved_tasks`.
3. **Data Localization:** User database tables must reside in Indian cloud data centers (e.g., Supabase India region - `ap-south-1` Mumbai) to minimize cross-border data transfer concerns.

### 5.2 Zero-Retention Audio Architecture
- **Raw Audio Ephemerality:** Audio blobs streamed from client are held in-memory (RAM buffer) or in a volatile `/tmp` directory with lifecycle expiration of 60 seconds.
- **Post-ASR Deletion:** Immediately upon receiving the text transcript from Gnani or Sarvam, the temporary audio file is permanently unlinked (`os.remove()`). Raw audio is **NEVER** stored in permanent object storage (AWS S3, Google Cloud Storage, or Supabase Storage).

### 5.3 Authentication & Multi-Tenant Data Isolation
- **Row-Level Security (RLS):** Every PostgreSQL table (`task_proposals`, `saved_tasks`, `raw_captures`) enforces strict Supabase RLS:
  ```sql
  CREATE POLICY "Users can only access their own tasks"
  ON saved_tasks FOR ALL
  USING (auth.uid() = user_id);
  ```
- **API Token Security:** Client communicates with backend using short-lived Supabase JWT bearer tokens. Backend validates JWT signatures using Supabase JWT secret.

### 5.4 Abuse Prevention & API Rate Limiting
To prevent catastrophic credit exhaustion on paid ASR and LLM endpoints:
- **Audio Capture Rate Limit:** Maximum 10 audio captures per user per 10-minute window.
- **Text Capture Rate Limit:** Maximum 20 text captures per user per 10-minute window.
- **Audio Duration Cap:** Hard client-side and server-side cap of 60 seconds per voice recording.

---

## 6. Usability & Accessibility (WCAG 2.1 AA)

1. **Bilingual UI Toggle:** The user interface must support instant switching between **Tamil UI strings** and **English UI strings** without requiring page reloads.
2. **Accessible Color Contrast:** Conflict warning badges and text must maintain a contrast ratio of at least $4.5:1$ against backgrounds (complying with WCAG 2.1 Level AA).
3. **Keyboard Operability:** The entire Proposal Card workflow must be 100% navigable via keyboard:
   - `Enter` / `Space`: Toggle audio recording.
   - `Tab` / `Shift+Tab`: Navigate between proposed tasks.
   - `E`: Inline edit selected task.
   - `X` / `Delete`: Reject / veto selected task.
   - `Ctrl + Enter` / `Cmd + Enter`: Batch approve all feasible tasks.
4. **Cognitive Load Minimization:** The Proposal Card must never display more than 7 proposed items at once without pagination or collapsing, preventing executive dysfunction and cognitive overwhelm.

