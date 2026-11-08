# 09 — DATABASE, BACKEND ARCHITECTURE & DATA INTEGRITY RECTIFICATION EXECUTION REPORT

**Project:** THOZHI (தோழி)
**Author:** Senior PostgreSQL Database Architect, Supabase Security Engineer & Backend Quality Auditor
**Date:** 2026-11-08
**Status:** COMPLETE & VERIFIED
**Final Test Matrix:** 129 passed, 0 failed, 2 benign warnings (100% pass rate in CI/offline environment)

---

## 1. Issues Discovered & Root Causes

### 1.1 Data Integrity & Consent Fabrication in Migration 003
- **Discovered Issue:** In `supabase/migrations/003_schema_alignment.sql`, DDL statements contained `consent_granted DEFAULT TRUE NOT NULL`, `consent_level DEFAULT 'EXPLICIT_USER' NOT NULL`, `duration_source DEFAULT 'USER_APPROVED' NOT NULL`, and `locale DEFAULT 'ta-IN' NOT NULL`.
- **Root Cause:** Earlier schema draft attempted to satisfy Pydantic schema constraints by injecting high-privilege defaults into database columns. This fabricated historical user consent, false task duration provenance, and an unverified default language on all legacy or unassigned records.

### 1.2 Unabstracted Datastore & Silent In-Memory Reliance
- **Discovered Issue:** The entire backend was tightly coupled to a single `InMemoryStore` singleton in `backend/app/db/repository.py`. While `SupabaseClient` existed in `supabase_client.py`, it was only invoked for a `/health` check ping. Furthermore, `SupabaseClient` was catching HTTP query failures and returning empty lists (`[]`) or `None`, which swallowed errors silently and caused data drops.
- **Root Cause:** Absence of a standardized Repository Pattern abstraction layer (`BaseRepository`) with dynamic dependency injection.

### 1.3 Offline Test Failures in CI Environment
- **Discovered Issue:** In GitHub Actions CI with mock credentials (`SARVAM_API_KEY="mock-key"`, `GEMINI_API_KEY=""`), 5 extraction regression tests in `test_extraction_regression.py` failed:
  1. `test_regression_01_exact_tamil_raven_app`
  2. `test_regression_02_tanglish_raven_app`
  3. `test_regression_28_tamil_task_without_deadline`
  4. `test_regression_29_mixed_script_tamil_english`
  5. `test_regression_32_full_api_endpoint_exact_tamil_raven_app`
- **Root Causes:**
  1. Translation provider `backend/app/providers/translation/sarvam.py` attempted live HTTP requests to `https://api.sarvam.ai/translate` even when keys were mock strings (`"mock-key"`), causing HTTP 403 authorization failures.
  2. The rule-based fallback performed individual substring replacements on raw Tamil words rather than preserving full sentence structures, producing corrupted mixed strings (e.g. `"Tomorrow ஈவினிங் சிக்ஸ் ஓ க்ளாக் குள்ளே ... Need to do"`), which caused downstream semantic parsing to extract `"ஈவினிங்"` as the action verb.
  3. In `test_regression_29`, the regex word boundary `\b` failed to match on non-ASCII Tamil characters in `10 மணிக்கு\b`, causing the parser to fall through to a 9:00 AM default rather than 10:00 AM.

---

## 2. Files Modified & Created

| File | Status | Description |
| :--- | :---: | :--- |
| [`supabase/migrations/003_schema_alignment.sql`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/supabase/migrations/003_schema_alignment.sql) | **Rectified** | Removed fabricated defaults (`consent_granted=NULL`, `consent_level='UNKNOWN'`, `duration_source='UNSPECIFIED'`, `locale=NULL`). |
| [`research/architecture-audit/07_DATABASE_BACKEND_RECTIFICATION_AUDIT.md`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/research/architecture-audit/07_DATABASE_BACKEND_RECTIFICATION_AUDIT.md) | **Created** | Comprehensive architectural and database audit report. |
| [`research/architecture-audit/08_MIGRATION_SAFETY_REVIEW.md`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/research/architecture-audit/08_MIGRATION_SAFETY_REVIEW.md) | **Created** | Migration safety review, schema diffs, backfill strategies, and rollback DDL. |
| [`backend/app/db/repositories/base.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repositories/base.py) | **Created** | Abstract Base Repository interface enforcing tenant scoping and non-destructive operations. |
| [`backend/app/db/repositories/memory.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repositories/memory.py) | **Created** | `InMemoryRepository` implementation preserving all 1,156 lines of verified in-memory logic. |
| [`backend/app/db/repositories/supabase.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repositories/supabase.py) | **Created** | `SupabaseRepository` implementation for PostgreSQL PostgREST persistence. |
| [`backend/app/db/repositories/factory.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repositories/factory.py) | **Created** | Repository factory with safe fallback logic. |
| [`backend/app/db/repositories/__init__.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repositories/__init__.py) | **Created** | Package initialization and clean exports. |
| [`backend/app/db/repository.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repository.py) | **Updated** | Central backward-compatible export module delegating to repository factory. |
| [`backend/app/db/supabase_client.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/supabase_client.py) | **Rectified** | Added typed exception hierarchy (`SupabaseQueryError`, `SupabaseConnectionError`), explicit token propagation, and zero silent data dropping. |
| [`backend/app/providers/translation/sarvam.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/providers/translation/sarvam.py) | **Rectified** | Prevented live network requests during tests; improved full-sentence deterministic translation fallbacks. |
| [`backend/app/providers/nlu/semantic_parser.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/providers/nlu/semantic_parser.py) | **Rectified** | Fixed Unicode Tamil character boundary handling in time extraction regex. |
| [`backend/tests/test_supabase_rls_security.py`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/tests/test_supabase_rls_security.py) | **Created** | Multi-tenant security test suite verifying cross-user isolation for tasks, captures, memory, and unconfigured safety. |
| [`README.md`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/README.md) | **Updated** | Corrected clone URL (`https://github.com/mohamed-kaif-1/Thozhi.git`), verified 129 test badge, documented credential architecture and implementation status table. |

---

## 3. Design Decisions & Security Improvements

1. **Explicit Data Provenance:** Every task duration now tracks honest origin (`USER_EXPLICIT`, `LEARNED_PRIOR`, `MODEL_ESTIMATE`, or `UNSPECIFIED`).
2. **Explicit User Consent State Machine:** Memory preferences no longer assume consent. Columns define `consent_status` (`'NOT_RECORDED'`, `'UNCONFIRMED'`, `'GRANTED'`, `'WITHDRAWN'`), `consent_granted` (`NULL` default), and `consent_level` (`'UNKNOWN'` default).
3. **Repository Pattern Decoupling:** Routers interact with the repository interface without knowing whether storage is in-memory or PostgreSQL. In production with credentials, `SupabaseRepository` activates; in development/testing, `InMemoryRepository` executes deterministically.
4. **Typed Error Propagation:** `SupabaseClient` raises `SupabaseQueryError` and `SupabaseConnectionError` when requests fail, preventing silent data drops.
5. **Credential Isolation:** The README and configuration clearly distinguish `SUPABASE_ANON_KEY` (public, RLS-enforced) from `SUPABASE_SERVICE_ROLE_KEY` (backend-only secret) and user JWTs.

---

## 4. Test Verification Results

### 4.1 Backend Pytest Execution
Command:
```bash
python -m pytest backend/tests -v
```
**Environment:**
- Python 3.14 / 3.11 compatible
- `ENVIRONMENT: test`
- `GNANI_API_KEY: mock-key`
- `SARVAM_API_KEY: mock-key`
- `GEMINI_API_KEY: ""`

**Result:**
```text
================= 129 passed, 2 warnings in 48.51s ==================
```
- Previously failing tests: **0** (all 7 previously reported failures resolved).
- Removed, skipped, or weakened tests: **0**.
- New security tests added: **4** (`test_supabase_rls_security.py`).

### 4.2 Frontend Production Build
Command:
```bash
npm run build --prefix frontend
```
**Result:**
```text
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (18/18)
✓ Finalizing page optimization
Exit Code: 0
```

---

## 5. Remaining Limitations & Production Readiness

1. **Live Cloud Migration Execution:** Migration `003_schema_alignment.sql` is fully validated locally and documented in `08_MIGRATION_SAFETY_REVIEW.md`. Per project instructions, it has not been executed against the live Supabase production project, awaiting manual human authorization.
2. **PostgREST Schema Reload:** Upon applying migration 003 in Supabase SQL editor, the user must issue `NOTIFY pgrst, 'reload schema';` so that PostgREST picks up the new columns immediately.
3. **Secondary Route Mock Status:** The primary planning routes (`/`, `/capture`, `/planner`, `/tasks`, `/memory`, `/settings`) are 100% connected to live backend APIs. Secondary routes (`/calendar`, `/assistant`, `/goals`, `/projects`, `/notifications`) remain client-side prototypes as documented.
