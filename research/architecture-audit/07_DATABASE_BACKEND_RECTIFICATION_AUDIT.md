# 07 — DATABASE, BACKEND ARCHITECTURE & DATA INTEGRITY RECTIFICATION AUDIT

**Project:** THOZHI (தோழி)
**Author:** Senior PostgreSQL Database Architect & Backend Quality Auditor
**Date:** 2026-11-08
**Status:** COMPLETE & AUTHORITATIVE
**Repository Working Branch:** `master`

---

## Executive Summary

An independent, rigorous audit of THOZHI's database schemas, persistence implementations, authorization pipelines, and test suites was conducted. The audit inspected `supabase/migrations/001_initial_schema.sql`, `002_rls_policies.sql`, `003_schema_alignment.sql`, `backend/app/db/repository.py`, `backend/app/db/supabase_client.py`, core configuration, and the test matrix.

While THOZHI possesses strong algorithmic logic for Kahn's topological DAG scheduling and deterministic interval mathematics, critical architectural gaps exist across four core dimensions:
1. **Data Provenance & Consent Fabrication in Migration 003:** Inappropriate column defaults (`consent_granted DEFAULT TRUE`, `consent_level DEFAULT 'EXPLICIT_USER'`, `duration_source DEFAULT 'USER_APPROVED'`, and `locale DEFAULT 'ta-IN'`) fabricate historical user actions and provenance for unverified or legacy data.
2. **Missing Repository Abstraction & Silent In-Memory Default:** The application relies entirely on an in-memory dictionary store (`InMemoryStore`) hardcoded across all router endpoints. `SupabaseClient` is only invoked during health checks, leaving persistent Supabase storage unintegrated into actual user workflows. Furthermore, `SupabaseClient` silently swallows HTTP errors and returns empty lists or `None`.
3. **Authentication & RLS Gaps:** While PostgreSQL RLS policies in migration 002 are conceptually defined via `current_user_id() = NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID`, the backend `SupabaseClient` falls back to `Bearer {self.api_key}` when a user token is absent, conflating anon/service credentials with user session identity.
4. **Hermetic Test Suite Flaws:** In CI environments without live API credentials (`SARVAM_API_KEY="mock-key"`, `GEMINI_API_KEY=""`), 5 regression tests in `test_extraction_regression.py` failed because the extraction pipeline attempted live HTTP requests to `https://api.sarvam.ai/translate` and Google Gemini, which returned HTTP 403 / 429 quota errors without deterministic offline test doubles.

---

## 1. Existing Architecture & Persistence Review

### 1.1 In-Memory Store (`backend/app/db/repository.py`)
- **Structure:** Defined as `InMemoryStore` containing in-memory Python dictionaries: `self.users`, `self.captures`, `self.proposals`, `self.proposal_items`, `self.tasks`, `self.task_dependencies`, `self.availability_windows`, `self.busy_events`, `self.memory_preferences`, `self.idempotency_keys`.
- **Usage:** Instantiated as a global singleton `store = InMemoryStore()` at `backend/app/db/repository.py:1156`.
- **Router Coupling:** Every router directly imports and invokes methods on `store`:
  - `routers/captures.py`: `store.create_capture(...)`, `store.create_proposal_from_extraction(...)`
  - `routers/proposals.py`: `store.get_proposal(...)`, `store.commit_proposal(...)`, `store.reject_proposal(...)`
  - `routers/tasks.py`: `store.list_tasks(...)`, `store.create_task(...)`, `store.update_task(...)`
  - `routers/plans.py`: `store.get_availability_windows(...)`, `store.get_busy_events(...)`
  - `routers/memory.py`: `store.list_memory_preferences(...)`, `store.set_memory_preference(...)`, `store.purge_user_data(...)`
  - `routers/users.py`: `store.get_user_profile(...)`, `store.update_user_profile(...)`
- **Architectural Consequence:** No data persists across server restarts. In-memory data structures do not enforce SQL foreign keys, unique constraints, or PostgreSQL transactions.

### 1.2 Supabase Client Implementation (`backend/app/db/supabase_client.py`)
- **Structure:** `SupabaseClient` wraps `httpx.AsyncClient` targeting PostgREST endpoints (`{SUPABASE_URL}/{table}`).
- **Configuration:** Reads `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` from `backend/app/core/config.py`.
- **Defects Discovered:**
  1. **Token Conflation:** Line 28 defines `auth_bearer = user_token if user_token else self.api_key`. If `user_token` is omitted, the project API key is forwarded as a Bearer token.
  2. **Silent Failure & Data Swallowing:** Lines 75-79 and 104-108 catch HTTP errors and exceptions, log a warning, and return empty collections (`[]`) or `None`. A failed write or query masquerades as an empty state.
  3. **No Connection Pooling:** Every method instantiates a new `httpx.AsyncClient` context manager instead of managing a persistent HTTP connection pool.
  4. **Unused in Production Workflows:** Aside from `check_health()` in `main.py`, zero routes query or persist data via `SupabaseClient`.

---

## 2. Actual Database Schema & Migration Differences

The repository contains three SQL migrations in `supabase/migrations/`:

| Migration | Intended Purpose | Actual Implementation Status | Integrity Risks Identified |
| :--- | :--- | :--- | :--- |
| **001_initial_schema.sql** | Baseline 14-table schema, UUID extensions, and core enums. | Fully specified, idempotent (`CREATE TABLE IF NOT EXISTS`). | Missing fields required by Stages 4–8 (translations, confidence breakdown, capture lifecycle). |
| **002_rls_policies.sql** | Enables RLS across all 14 tables; defines `current_user_id()`. | Fully specified, depends on `request.jwt.claim.sub`. | Relies on PostgREST JWT claim injection; assumes all queries originate through PostgREST. |
| **003_schema_alignment.sql** | Adds missing fields for translations, multi-proposal queue, duration source, and memory consent. | **Untracked working-tree migration**; never applied to production. | **Severe Data Provenance Risks:** Fabricates `consent_granted=TRUE`, `consent_level='EXPLICIT_USER'`, `duration_source='USER_APPROVED'`, and `locale='ta-IN'`. |

---

## 3. Data Integrity & Provenance Violations in Migration 003

### 3.1 Consent Fabrication (`memory_preferences`)
- **Problematic DDL:**
  ```sql
  ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_granted BOOLEAN DEFAULT TRUE NOT NULL;
  ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_level VARCHAR(64) DEFAULT 'EXPLICIT_USER' NOT NULL;
  ```
- **Violation:** Any pre-existing rows in `memory_preferences`, or any programmatic insertion without explicit parameters, automatically inherit `consent_granted = TRUE` and `consent_level = 'EXPLICIT_USER'`. This creates legal and architectural liability by fabricating user consent.
- **Rectification Required:**
  - `consent_granted` must be nullable or use a strict state field (`NOT_RECORDED`, `PENDING_CONFIRMATION`, `EXPLICITLY_GRANTED`, `WITHDRAWN`).
  - `consent_level` must default to `'UNKNOWN'` or `'UNCONFIRMED'`.
  - Explicit consent must only be recorded when the user deliberately toggles or saves a preference.

### 3.2 Task Duration Provenance Fabrication (`tasks`)
- **Problematic DDL:**
  ```sql
  ALTER TABLE tasks ADD COLUMN IF NOT EXISTS duration_source VARCHAR(64) DEFAULT 'USER_APPROVED' NOT NULL;
  ```
- **Violation:** In THOZHI's NLU extraction pipeline, task durations can originate from:
  1. Spoken input (`USER_EXPLICIT`)
  2. Duration learning engine (`LEARNED_PRIOR`)
  3. Default heuristic fallback (`MODEL_ESTIMATE`)
  4. Unspecified (`UNSPECIFIED`)
  Defaulting new and existing database rows to `'USER_APPROVED'` falsely claims the user verified the duration when they may have only approved the task title without touching the duration slider.
- **Rectification Required:**
  - Default `duration_source` in `tasks` to `'UNSPECIFIED'` or `'LEGACY_UNKNOWN'`.
  - Propagate the true duration source from `proposal_items.duration_source` upon commit.

### 3.3 User Locale Fabrication (`users`)
- **Problematic DDL:**
  ```sql
  ALTER TABLE users ADD COLUMN IF NOT EXISTS locale VARCHAR(64) DEFAULT 'ta-IN' NOT NULL;
  ```
- **Violation:** Forces all historical and new users into Tamil (`ta-IN`) without user selection.
- **Rectification Required:**
  - Make `locale` default to `'en-IN'` or nullable (`NULL` = unset / prompt on onboarding).
  - Explicit user preference updates must update `locale`.

### 3.4 Capture Lifecycle vs. Processing Status Ambiguity (`captures`)
- **Existing Schema:** `processing_status capture_status_enum DEFAULT 'RECEIVED'`
- **Migration 003 Addition:** `lifecycle_status VARCHAR(64) DEFAULT 'PENDING_REVIEW'`
- **Analysis:** These fields represent distinct operational domains:
  - `processing_status`: Technical audio/text ingestion state (`RECEIVED`, `TRANSCRIBED`, `COMPLETED`, `FAILED`).
  - `lifecycle_status`: Human-in-the-loop governance status of proposals linked to this capture (`PENDING_REVIEW`, `COMMITTED`, `REJECTED`, `EXPIRED`, `NO_PROPOSALS`).
- **Rectification Required:** Keep both fields clearly separated in documentation, DDL, and Pydantic schemas with defined valid state transitions.

### 3.5 Proposal Status Enum Extension
- **Original Enum:** `DRAFT, PRESENTED, APPROVED, REJECTED, EXPIRED`
- **Migration 003 Added:** `PROCESSING, PENDING_REVIEW, COMMITTED, FAILED, ARCHIVED`
- **Analysis:** Adding values to a PostgreSQL enum in an uncommitted transaction requires careful handling (`ALTER TYPE ... ADD VALUE IF NOT EXISTS` cannot run inside a multi-statement transaction block in PostgreSQL < 12, though supported in modern versions).
- **Mapping:**
  - `DRAFT` / `PROCESSING` -> Ingestion & extraction.
  - `PRESENTED` / `PENDING_REVIEW` -> Awaiting human decision.
  - `APPROVED` / `COMMITTED` -> Converted to active task.
  - `REJECTED` -> User declined proposal.
  - `EXPIRED` -> Stale proposal past TTL.

---

## 4. Authentication, Authorization & RLS Audit

### 4.1 PostgREST RLS Invariant
Migration 002 implements:
```sql
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE;
```
When a client connects to PostgREST with an authenticated user JWT (`Authorization: Bearer <user_jwt>`), PostgREST validates the JWT against `SUPABASE_JWT_SECRET` and executes:
```sql
SET LOCAL request.jwt.claim.sub = '<jwt_sub>';
```
This enables `current_user_id()` to return the authenticated UUID.

### 4.2 Architectural Vulnerabilities
1. **Service Role Key Exposure Risk:** If backend code passes `SUPABASE_KEY` (when configured as the service-role key) in `Authorization: Bearer <key>`, RLS is completely bypassed.
2. **Missing User Context Propagation:** If backend code executes queries without forwarding the calling user's JWT or setting session context, `current_user_id()` evaluates to `NULL`, resulting in zero records returned under RLS.
3. **Dual Credential Clarification Needed:** The backend configuration currently defines a single `SUPABASE_KEY`. In production Supabase setups, two keys exist:
   - `SUPABASE_ANON_KEY`: Public client key, subject to strict RLS.
   - `SUPABASE_SERVICE_ROLE_KEY`: Secret administrative key, bypasses RLS for maintenance.

---

## 5. Repository Abstraction Design Plan

To cleanly decouple persistence from routing without disrupting working code, the architecture will introduce a standard Repository pattern:

```mermaid
flowchart TD
    Router["FastAPI Routers\n(captures, proposals, tasks, memory)"] --> Factory["get_repository()\n(backend/app/db/repositories/factory.py)"]
    Factory --> Interface["BaseRepository Protocol\n(backend/app/db/repositories/base.py)"]
    Interface -.-> MemoryImpl["InMemoryRepository\n(Deterministic Test & Dev)"]
    Interface -.-> SupabaseImpl["SupabaseRepository\n(PostgreSQL via PostgREST)"]
```

### Key Architectural Invariants:
1. **Zero Router Disruption:** `backend/app/db/repository.py` imports and instantiates the repository via the factory, preserving `from backend.app.db.repository import store`.
2. **Deterministic Fallback:** If `SUPABASE_URL` or `SUPABASE_KEY` are not configured in development, the system cleanly defaults to `InMemoryRepository` with an explicit log message.
3. **No Silent Data Drops:** The Supabase repository will raise explicit typed exceptions (`DatabaseConnectionError`, `DatabaseQueryError`) on failure rather than returning empty lists or fake successes.

---

## 6. Test Suite Analysis & Root-Cause Remediation

### 6.1 Hermetic Test Failure Root Cause
When running tests in CI with `GNANI_API_KEY="mock-key"` and `SARVAM_API_KEY="mock-key"`:
- `backend/app/providers/translation/sarvam.py` attempted a live HTTP POST to `https://api.sarvam.ai/translate`.
- Sarvam returned HTTP 403 `{"error":{"message":"Invalid or missing authentication credentials"}}`.
- `sarvam.py` logged a warning and returned the untranslated Tamil string.
- `semantic_parser.py` attempted keyword extraction on the raw Tamil string, missing the English action verbs and resulting in test failures:
  - `test_regression_01_exact_tamil_raven_app`: Expected `complete`, got `ஈவினிங்`.
  - `test_regression_02_tanglish_raven_app`: Failed title normalization.
  - `test_regression_28_tamil_task_without_deadline`: Missing fallback translation.
  - `test_regression_29_mixed_script_tamil_english`: Missing fallback translation.
  - `test_regression_32_full_api_endpoint_exact_tamil_raven_app`: API returned raw Tamil title.

### 6.2 Solution
1. In `backend/app/providers/translation/sarvam.py`: Enhance the deterministic offline mock / fallback dictionary for test and offline environments so that known test cases and standard Tamil/Tanglish phrasing resolve hermetically without external network dependencies.
2. In `backend/app/providers/nlu/semantic_parser.py`: Strengthen Tamil keyword and SOV deconstruction mappings for offline operation.

---

## 7. Prioritized Remediation Roadmap

1. **Step 1:** Rectify `supabase/migrations/003_schema_alignment.sql` to remove all fabricated defaults (`consent_granted`, `consent_level`, `duration_source`, `locale`).
2. **Step 2:** Produce `research/architecture-audit/08_MIGRATION_SAFETY_REVIEW.md` documenting schema diffs, backfill strategies, and rollback considerations.
3. **Step 3:** Implement repository interfaces in `backend/app/db/repositories/` (`base.py`, `memory.py`, `supabase.py`, `factory.py`) with backward compatibility.
4. **Step 4:** Rectify `backend/app/db/supabase_client.py` with explicit error propagation, timeout management, and key separation.
5. **Step 5:** Fix the offline translation fallback and semantic parsing so all 125 backend tests pass 100% hermetically in CI without live API keys.
6. **Step 6:** Add dedicated security tests verifying cross-user tenant isolation.
7. **Step 7:** Update `README.md` with honest architectural claims.
8. **Step 8:** Generate `research/architecture-audit/09_RECTIFICATION_EXECUTION_REPORT.md`.
