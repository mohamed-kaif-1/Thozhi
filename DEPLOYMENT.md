# THOZHI (தோழி) — Production Deployment & Release Runbook

> **Core System Principle:**  
> **"The AI proposes. The user decides."**  
> *Zero silent task creation. Zero unconfirmed calendar modifications. Zero raw audio persistence.*

---

## 1. Executive Summary & Architecture Topology

THOZHI is engineered as a decoupled, multi-tenant AI productivity platform optimized for Indic language nuances (Tamil, Tanglish, and English code-mixing).

```
                     ┌───────────────────────────────────────────┐
                     │          User Interface (Next.js 14)      │
                     │  - Neo-Brutalism Theme (Obsidian/Blue)    │
                     │  - App Router, React 18, Tailwind CSS     │
                     │  - Zero Client Secret Exposure            │
                     └─────────────────────┬─────────────────────┘
                                           │ HTTPS / WSS
                                           ▼
                     ┌───────────────────────────────────────────┐
                     │          API Gateway / ASGI Server        │
                     │  - FastAPI (Python 3.11+)                 │
                     │  - RFC 7807 Problem Details Error Model   │
                     │  - Multi-Tenant Request Isolation         │
                     └──────┬──────────────┬──────────────┬──────┘
                            │              │              │
           ┌────────────────┘              │              └────────────────┐
           ▼                               ▼                               ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  Primary ASR Engine  │      │  NLU Reasoning Engine│      │  Database & Auth     │
│  Gnani AI Prisma v3  │      │  Gemini 2.5 Flash    │      │  Supabase PostgreSQL │
│  (Zero RAM Retention)│      │  (Intent Extraction) │      │  (14 Tables + RLS)   │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
```

---

## 2. Infrastructure & Hosting Selection

### Option A: Containerized Cloud (Recommended for Production)
- **Backend:** Google Cloud Run / AWS ECS / Render (Containerized FastAPI, auto-scaling from 1 to 10 instances).
- **Frontend:** Vercel / Cloudflare Pages / AWS Amplify (Edge CDN caching, global low-latency SSR/SSG).
- **Database & Auth:** Supabase Managed PostgreSQL (pgvector-ready, Automated Backups, Point-in-Time Recovery).

### Option B: Self-Hosted Docker Compose (Air-Gapped / Private Cloud)
Both frontend and backend are pre-configured to build into minimal Alpine-based containers via `docker-compose.yml`.

---

## 3. Environment Variables & Secrets Matrix

All production secrets must be provisioned via secret managers (e.g., GCP Secret Manager, Doppler, or AWS Secrets Manager) and never committed to version control.

| Environment Variable | Required | Default / Format | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `production` | Runtime mode (`development`, `staging`, `production`). |
| `PORT` | No | `8000` | HTTP listening port for FastAPI ASGI server. |
| `CORS_ORIGINS` | **Yes** | `https://thozhi.app,https://*.vercel.app` | Comma-delimited list of allowed origin URLs. |
| `GNANI_API_KEY` | **Yes** | `Secret` | Primary ASR authentication key for Gnani AI Prisma v3. |
| `GNANI_API_URL` | No | `https://api.vachana.ai` | Gnani AI STT API root endpoint (`/stt/v3`). |
| `SARVAM_API_KEY` | No | `Secret` | Commercial fallback speech-to-text API key. |
| `SARVAM_API_URL` | No | `https://api.sarvam.ai` | Sarvam AI STT endpoint (`/speech-to-text`). |
| `GEMINI_API_KEY` | **Yes** | `Secret` | Google AI Studio / Vertex AI key for Gemini 2.5 Flash. |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | LLM reasoning model for structured intent extraction. |
| `SUPABASE_URL` | **Yes** | `https://<ref>.supabase.co` | Supabase project URL. |
| `SUPABASE_KEY` | **Yes** | `Secret` | Supabase service-role or anon key. |
| `NEXT_PUBLIC_API_URL` | **Yes** | `https://api.thozhi.app/api/v1` | Public backend API URL consumed by frontend. |

---

## 4. Database Setup & Supabase Migrations

The database foundation consists of 14 normalized, indexed relational tables protected by Row-Level Security (RLS).

### Step 1: Execute Schema DDL
Run `supabase/migrations/001_initial_schema.sql` in the Supabase SQL Editor or via CLI:
```bash
supabase db push
```
This provisions:
- `users`, `user_tenants`, `user_settings`
- `audio_captures` (stores transcription metadata; audio bytes strictly omitted)
- `intent_proposals`, `proposal_items`, `proposal_clarifications`
- `tasks`, `task_dependencies`, `task_revisions`
- `plans`, `schedule_blocks`
- `memory_preferences`, `operational_metrics`

### Step 2: Enforce Tenant Isolation (RLS)
Run `supabase/migrations/002_rls_policies.sql` to apply strict tenant boundary policies ensuring zero cross-tenant data leakage.

---

## 5. Local Execution & Docker Deployment

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/thozhi-ai/thozhi.git
cd thozhi
cp .env.example .env
# Edit .env with your authenticated API credentials
```

### Step 2: Docker Compose Launch
```bash
docker compose up --build -d
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### Step 3: Verify Container Health
```bash
docker compose ps
docker compose logs backend --tail=50
```

---

## 6. Production Health Checks & Smoke Tests

### Automated Health Verification
FastAPI exposes a deep health check endpoint at `/health` verifying DB connectivity and speech engine configuration:
```bash
curl -s http://localhost:8000/health | jq .
```
**Expected Response:**
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "code": 200
  },
  "primary_asr": {
    "engine": "Gnani AI Prisma v3",
    "configured": true
  }
}
```

### Automated End-to-End Test Suite Execution
Execute the full 47-test verification suite:
```bash
python -m pytest backend/tests -v
```

### Frontend Production Build Verification
```bash
cd frontend
npm run lint
npm run build
```

---

## 7. Security, Privacy & Compliance Policies

1. **Zero Raw Audio Retention:**
   Raw audio WAV/MP3 streams uploaded to `POST /api/v1/captures/audio` are processed in ephemeral memory buffers and never written to disk or database storage.
2. **Sovereign Right to be Forgotten:**
   Users can purge all active and historical tasks, proposals, and preferences instantly via `DELETE /api/v1/memory/purge`.
3. **Sovereign Data Portability:**
   Users can export their complete data footprint in JSON format via `POST /api/v1/memory/export`.
4. **Deterministic Scheduling Guarantee:**
   All calendar placement, capacity math, and dependency validations are governed by Kahn's DAG topological algorithm. The AI cannot hallucinate task times or silently schedule commitments.
