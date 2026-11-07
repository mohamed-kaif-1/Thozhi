# THOZHI — Testing Suite, Dependency & Configuration Audit

## 1. Executive Summary

- **Total Test Cases:** 125 backend test cases across 17 test modules
- **Test Framework:** Pytest 8.0+ / 9.2 with `pytest-asyncio` & Starlette `TestClient`
- **Execution Time:** ~72 seconds full suite
- **Pass Rate:** **100% (125/125 PASSED)**
- **CI / CD Pipeline:** GitHub Actions (`.github/workflows/ci.yml`)
- **Key Finding:** While the test suite itself is comprehensive and rigorous with excellent regression coverage, the CI workflow is misconfigured (does not trigger on the default `master` branch and bypasses `requirements.txt`).

---

## 2. Test Suite Architecture & Coverage Map

| Test Module | Test Count | Domain / Focus | Provider Type | State Cleanliness |
|---|:---:|---|:---:|:---:|
| `test_capture_proposal_queue_regression.py` | 12 | Sequential captures, multiple proposals, independent decisions, replay protection, queue recovery | Real API Client + Mock NLU | **Isolated** (per-test autouse fixture) |
| `test_extraction_regression.py` | 32 | Sovereign Semantic Parser, Tamil/Tanglish/English SOV deconstruction, deadline parsing, duration non-fabrication | Real Semantic Parser | **Isolated** |
| `test_scheduling_regression.py` | 16 | Kahn's DAG scheduler, cycle detection, duration prior integration, interval capacity, deadline constraint checks | Planning Engine Core | **Isolated** |
| `test_translation.py` | 5 | Sarvam AI Translate provider, Tamil $\leftrightarrow$ English, preserve original invariants | Real & Mock Translation | **Isolated** |
| `test_stage8_ai_evaluation.py` | 16 | Indic synthetic scenario benchmarks, prompt injection sanitization, GDPR purge, load latency | Mock NLU Provider | **Isolated** (`clean_store` fixture) |
| `test_stage7_full_integration.py` | 3 | Full journey: Audio capture $\rightarrow$ proposal $\rightarrow$ commit $\rightarrow$ plan $\rightarrow$ purge | Real Pipeline Client | **Isolated** |
| `test_stage6_memory_and_privacy.py` | 7 | Sovereign memory, preference toggle, duration priors, data export | Real Memory API | **Isolated** |
| `test_stage5_planning_and_tasks.py` | 12 | Daily plan generation, task CRUD, DAG dependencies, capacity percentage | Real Plan API | **Isolated** |
| `test_stage4_ai_understanding.py` | 4 | ASR dispatcher, failover between Gnani & Sarvam, Gemini prompt formatting | ASR Dispatcher | **Isolated** |
| `test_stage3_foundation.py` | 3 | RFC 7807 Problem Details, database health discovery, CORS headers | FastAPI System API | **Isolated** |
| `test_synthetic_scenarios.py` | 3 | Master PRD synthetic scenarios (call + report, conditional weather, cancellations) | Real Pipeline | **Isolated** |
| `test_planning_engine.py` | 5 | Unit tests for topological sort, interval arithmetic, and reschedule suggestions | Pure Unit Tests | **Stateless** |
| `test_proposals_and_approvals.py` | 2 | Zero silent task creation invariant, idempotency key deduplication | Real API Client | **Isolated** |
| `test_memory.py` | 3 | Preferences CRUD, duration learning suggestion, export format | Real Memory API | **Isolated** |
| `test_e2e_workflow.py` | 1 | End-to-end full user journey | Full Pipeline | **Isolated** |
| `test_health.py` | 2 | `/health` and `/` endpoints | System Health | **Stateless** |

---

## 3. Detailed Testing & CI Findings

### Finding TD-01: CI Workflow Fails to Trigger on Default Branch `master`
- **Severity:** `P1 — High`
- **Exact File Path:** [`.github/workflows/ci.yml:5,7`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/.github/workflows/ci.yml#L5-L7)
- **Evidence:**
  ```yaml
  on:
    push:
      branches: [ main, develop ]
    pull_request:
      branches: [ main, develop ]
  ```
  The repository's active development branch is `master`.
- **Actual Problem:** Pushes and pull requests on `master` never execute GitHub Actions CI! The test suite is only executed manually on the developer machine.
- **Recommended Correction:** Add `master` to the branch trigger list:
  ```yaml
  on:
    push:
      branches: [ main, master, develop ]
    pull_request:
      branches: [ main, master, develop ]
  ```
- **Code Change Necessary:** Yes (Safe cleanup).

---

### Finding TD-02: CI Workflow Bypasses `requirements.txt`
- **Severity:** `P1 — High`
- **Exact File Path:** [`.github/workflows/ci.yml:27`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/.github/workflows/ci.yml#L27)
- **Evidence:**
  ```yaml
  run: |
    python -m pip install --upgrade pip
    pip install fastapi uvicorn pydantic pydantic-settings httpx pytest pytest-asyncio anyio
  ```
- **Actual Problem:** CI hardcodes a manual list of packages instead of executing `pip install -r backend/requirements.txt`. If a dependency is added or bumped in `requirements.txt`, CI will not test it, leading to configuration drift.
- **Recommended Correction:**
  ```yaml
  run: |
    python -m pip install --upgrade pip
    pip install -r backend/requirements.txt
  ```
- **Code Change Necessary:** Yes (Safe cleanup).

---

### Finding TD-03: Missing Audio Processing Dependencies in `requirements.txt`
- **Severity:** `P2 — Medium`
- **Exact File Paths:**
  - [`backend/requirements.txt`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/backend/requirements.txt)
  - [`backend/app/core/audio.py:31`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/backend/app/core/audio.py#L31)
- **Evidence:** `backend/app/core/audio.py` imports `av` (PyAV) for in-memory audio resampling to 16kHz mono WAV, but `av` is absent from `requirements.txt`.
- **Actual Problem:** Any container or clean machine built strictly from `requirements.txt` lacks PyAV. While `audio.py` contains a graceful try/except fallback, audio from certain browsers (e.g. Safari MP4/AAC) will not be normalized and will be rejected by Gnani Prisma v3.
- **Recommended Correction:** Append `av>=11.0.0` to `backend/requirements.txt`.
- **Code Change Necessary:** Yes.

---

### Finding TD-04: Unused Frontend Packages in `package.json`
- **Severity:** `P2 — Medium`
- **Exact File Path:** [`frontend/package.json`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/frontend/package.json#L12-L13)
- **Evidence:**
  - `@tanstack/react-query`: `^5.107.1` (Zero imports across `frontend/src/`)
  - `class-variance-authority`: `^0.7.1` (Zero imports across `frontend/src/`)
- **Actual Problem:** Unused packages increase install times, add maintenance debt, and introduce unnecessary vulnerability exposure.
- **Recommended Correction:** Remove both dependencies from `frontend/package.json` and regenerate `package-lock.json`.
- **Code Change Necessary:** Yes (Safe cleanup).

---

### Finding TD-05: Docker & Environment Alignment
- **Severity:** `INFO — Verified Compliant`
- **Exact File Paths:**
  - [`docker-compose.yml`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/docker-compose.yml)
  - [`backend/Dockerfile`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/backend/Dockerfile)
  - [`frontend/Dockerfile`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/frontend/Dockerfile)
  - [`.env.example`](file:///c:/Users/moham%20-%20ELCOT/Projects/Thozhi/.env.example)
- **Audit Assessment:**
  - Multi-stage Docker builds are properly isolated.
  - Next.js standalone server mode is configured in `next.config.mjs` matching `node server.js` in `frontend/Dockerfile`.
  - Environment variables in `docker-compose.yml` provide default fallbacks without leaking secrets.
  - `.env.example` provides clean template keys without sensitive credentials.
