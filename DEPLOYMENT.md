# THOZHI (தோழி) — Deployment and Execution Runbook

**Core Principle:** *The AI proposes. The user decides.*  
Zero silent task creation or unconfirmed calendar modification.

---

## 1. Quick Start (Local Development)

### Prerequisites
- Python 3.11+ (Tested on Python 3.14)
- Node.js 18+ (npm)

### Backend Setup
1. Open a terminal and navigate to the root directory:
   ```bash
   cd "c:\Users\moham\OneDrive - ELCOT\Projects\Thozhi"
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start the FastAPI backend server:
   ```bash
   python -m uvicorn backend.app.main:app --reload --port 8000
   ```
   - API Root: `http://localhost:8000/`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

### Frontend Setup
1. In a separate terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install Node dependencies (if not already installed):
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   - Web Application: `http://localhost:3000`

---

## 2. Docker Deployment

Deploy both the backend and frontend using Docker Compose:

```bash
# 1. Copy and populate environment variables
cp .env.example .env

# 2. Build and launch containers
docker compose up --build -d

# 3. Check container logs
docker compose logs -f
```

---

## 3. Database & Supabase Migrations

The database foundation consists of 14 normalized tables and Row-Level Security (RLS) policies:

- `supabase/migrations/001_initial_schema.sql`: 14 tables, enums, foreign keys, and indexes.
- `supabase/migrations/002_rls_policies.sql`: Strict tenant isolation policies (`current_user_id() = user_id`).

To apply to your Supabase project:
```bash
# Via Supabase CLI
supabase db push

# Or execute the SQL migrations directly in the Supabase SQL Editor
```

---

## 4. Running Automated Tests

Run the complete test suite (Topological planning math, cycle detection, interval arithmetic, zero-silent-task enforcement, synthetic Tanglish parsing, privacy preferences):

```bash
python -m pytest backend/tests -v
```

All 12 unit and integration tests are verified green.

---

## 5. Verified Architecture & ASR Integration

- **Primary ASR:** Gnani AI Prisma v3 (`https://api.vachana.ai/stt/v3`, header `X-API-Key-ID`).
- **Commercial Failover:** Sarvam AI Saaras v3 (`https://api.sarvam.ai/speech-to-text`, header `api-subscription-key`).
- **Zero Raw Audio Retention:** Audio streams are held exclusively in RAM during speech-to-text conversion and purged immediately upon response generation.
- **Deterministic Scheduling:** Kahn's algorithm topological sort and interval bin packing. Zero hallucinated appointment times.

