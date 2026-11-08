# THOZHI — PHASE 1.8 DATABASE REMEDIATION IMPLEMENTATION REPORT

**Document ID:** `24_DATABASE_REMEDIATION_IMPLEMENTATION_REPORT.md`
**Execution Phase:** Phase 1.8 — Database Remediation Implementation
**Project:** THOZHI (`mohamed-kaif-1/Thozhi`)
**Workspace:** `C:\Users\moham\OneDrive - ELCOT\Projects\Thozhi`
**Date:** November 8, 2026
**Status:** IMPLEMENTATION COMPLETE & VERIFIED — READY FOR PHASE 1.9 GATE
**Operating Invariant:** *"The AI proposes. The user decides."*

---

## 1. Executive Summary

Phase 1.8 has successfully implemented the database remediation architecture formulated and reviewed across Phases 1.6, 1.7, 1.7.5, and 1.7.6.

All verified database schema incompatibilities identified in `13_DATABASE_SCHEMA_COMPATIBILITY_AUDIT.md` have been corrected through:
1. The creation of production-grade `supabase/migrations/004_schema_alignment_and_rpc.sql`.
2. Full repository alignment in `backend/app/db/repositories/supabase.py`.
3. Alignment of capture processing schemas in `backend/app/schemas/capture.py` and `backend/app/db/repositories/memory.py`.
4. Addition of domain security exception `PermissionDeniedException` in `backend/app/core/errors.py`.
5. Expansion and passing of the full backend test suite (**145 passed in 64.40s**) and verification of the Next.js frontend production build (**18/18 static pages rendered, 0 errors**).

Zero database migrations were executed against live, staging, or production databases during this phase.

---

## 2. Inventory of Files Created and Modified

### 2.1 Files Created
| File Path | Purpose | Lines of Code |
| :--- | :--- | :--- |
| `supabase/migrations/004_schema_alignment_and_rpc.sql` | Master Migration 004 providing table extensions, composite multi-tenant FKs, audit privilege hardening, RLS policies, and atomic approval RPC. | 456 lines |
| `research/architecture-audit/24_DATABASE_REMEDIATION_IMPLEMENTATION_REPORT.md` | Formal audit and engineering closeout report for Phase 1.8. | This document |

### 2.2 Files Modified
| File Path | Component | Changes Implemented |
| :--- | :--- | :--- |
| `backend/app/core/errors.py` | Domain Exceptions | Added `PermissionDeniedException(AppException)` with HTTP 403 status code for unauthorized proposal approval attempts. |
| `backend/app/schemas/capture.py` | API Schemas | Aligned `processing_status` default to `"PROCESSED"`, matching database enum `capture_status_enum` without requiring transactional enum alterations. |
| `backend/app/db/repositories/memory.py` | In-Memory Repository | Defaulted `processing_status` to `"PROCESSED"` for parity with PostgreSQL schema. |
| `backend/app/db/repositories/supabase.py` | Supabase Repository | • `create_capture`: uses `"PROCESSED"` and normalizes `"COMPLETED"` to `"PROCESSED"`.<br>• `create_proposal_from_extraction`: persists `clarifications` JSONB and handles model attribute variations (`intent_summary`, `proposed_items`).<br>• `_row_to_proposal`: deserializes stored `clarifications` JSONB back into `ClarificationQuestion` models.<br>• `approve_proposal`: replaced sequential independent HTTP calls with single atomic `commit_proposal_atomic` RPC call; maps SQL error codes (`P0002`, `23505`, `22023`, `42501`) to domain exceptions.<br>• `complete_task`: persists `actual_duration_min`.<br>• `purge_user_data`: expanded deletion to all 11 user-owned tables in correct FK dependency order, appending an immutable `SOVEREIGN_PURGE` event to `audit_logs`. |
| `backend/tests/test_supabase_real_persistence.py` | Repository Test Suite | • Updated `create_and_get_capture` to assert `"PROCESSED"`.<br>• Updated `approve_proposal` tests to mock atomic RPC execution.<br>• Added `test_supabase_repository_atomic_approval_error_mapping`.<br>• Added `test_supabase_repository_task_completion_persists_actual_duration`.<br>• Added `test_supabase_repository_clarification_persistence_roundtrip`.<br>• Expanded `test_supabase_repository_sovereign_purge` to verify all 11 tables are purged. |

---

## 3. Detailed Migration 004 Structure & Safety Analysis

File: `supabase/migrations/004_schema_alignment_and_rpc.sql` (456 lines)

### 3.1 Removal of Enum Alteration (REV-01 Resolved)
As established in Phase 1.7.5 and Phase 1.7.6, PostgreSQL prohibits using newly added enum values inside transactional DO blocks or functions within the same transaction. Rather than introducing fragile DDL hacks, Migration 004 completely eliminates `ALTER TYPE capture_status_enum ADD VALUE 'COMPLETED'`. The application layer was refactored to use the existing, semantically valid enum value `'PROCESSED'`, achieving 100% compatibility with Migration 001 without transactional risks.

### 3.2 Schema Extensions
1. **`tasks.actual_duration_min` (INT):** Added to store the actual duration in minutes upon task completion, fulfilling the `complete_task()` repository interface contract.
2. **`tasks.scheduled_date` (DATE):** Added to support date-based calendar queries and scheduled day buckets.
3. **`proposals.clarifications` (JSONB NOT NULL DEFAULT '[]'::JSONB):** Added to preserve AI clarification questions across page reloads and client reconnects.

### 3.3 Relational Multi-Tenant Integrity & Composite Foreign Keys
1. **Candidate Unique Key:** Added `CONSTRAINT uq_tasks_id_user_id UNIQUE (id, user_id)` on `tasks`.
2. **Obsolete Constraint Drop:** Conditionally dropped obsolete single-column foreign keys (`task_dependencies_predecessor_task_id_fkey` and `task_dependencies_successor_task_id_fkey`) using defensive `DO $$ BEGIN ... END $$;` blocks.
3. **Composite Foreign Keys:**
   ```sql
   ALTER TABLE task_dependencies
       ADD CONSTRAINT fk_task_deps_predecessor_tenant
       FOREIGN KEY (predecessor_task_id, user_id)
       REFERENCES tasks (id, user_id)
       ON DELETE CASCADE;

   ALTER TABLE task_dependencies
       ADD CONSTRAINT fk_task_deps_successor_tenant
       FOREIGN KEY (successor_task_id, user_id)
       REFERENCES tasks (id, user_id)
       ON DELETE CASCADE;
   ```
   **Security Guarantee:** Enforces cross-tenant dependency prevention at the relational engine level. A task owned by User A can never reference a predecessor or successor task owned by User B, even during administrative or service-role mutations that bypass RLS.

### 3.4 Constraint & Performance Index Hardening
1. **Partial Unique Index:**
   ```sql
   CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
       ON tasks (source_proposal_item_id)
       WHERE source_proposal_item_id IS NOT NULL;
   ```
   Prevents accidental duplicate task creation from identical proposal items, while allowing unlimited manually created tasks (`source_proposal_item_id IS NULL`).
2. **Calendar Performance Index:**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_tasks_user_scheduled_date
       ON tasks (user_id, scheduled_date);
   ```

### 3.5 Privilege & Audit Trail Hardening
Client roles (`authenticated`, `anon`) are stripped of write permissions on audit tables:
- `REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM authenticated, anon;`
- `GRANT SELECT ON TABLE audit_logs TO authenticated;`
- `GRANT ALL ON TABLE audit_logs TO service_role;`
- `REVOKE UPDATE, DELETE, TRUNCATE ON TABLE approval_idempotency FROM authenticated, anon;`
- `GRANT SELECT, INSERT ON TABLE approval_idempotency TO authenticated, service_role;`

Only `SECURITY DEFINER` stored procedures and trusted backend administrative connections can append to the immutable audit trail.

### 3.6 Row-Level Security (RLS) Alignment
Separated grouped policies into explicit per-operation policies (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) with strict `auth.uid()` checks across all primary tables:
- `captures`
- `proposals`
- `proposal_items`
- `tasks`
- `memory_preferences`
- `task_dependencies`
- `audit_logs` (SELECT only for authenticated users)
- `approval_idempotency` (SELECT, INSERT for authenticated users)

### 3.7 Atomic Proposal Approval RPC (`commit_proposal_atomic`)
The stored procedure implements full atomicity, multi-tier identity checks, and strict validation:
- **Signature:** `commit_proposal_atomic(p_user_id UUID, p_proposal_id UUID, p_idempotency_key VARCHAR, p_item_decisions JSONB) RETURNS JSONB`
- **Identity Verification:**
  - Authenticated caller: verifies `auth.uid() IS NOT NULL` and `auth.uid() = p_user_id` (raises `42501` on mismatch).
  - Service-role / postgres caller: accepts `p_user_id` as authorized effective tenant.
  - Anonymous caller: strictly denied (raises `42501`).
- **Concurrency Control & Locking:**
  - Queries `approval_idempotency` for fast-path return.
  - Obtains row-level exclusive lock on proposal: `SELECT * FROM proposals WHERE id = p_proposal_id FOR UPDATE;`.
  - Obtains row-level exclusive locks on each proposal item: `SELECT * FROM proposal_items WHERE id = v_item_id FOR UPDATE;`.
- **Validation Rules:**
  - Full item decision coverage: `v_decision_count == v_db_item_count` (raises `22023` if any items omitted).
  - Duplicate item rejection: checks `v_seen_item_ids` (raises `22023`).
  - Foreign item rejection: verifies item belongs to proposal and user (raises `P0002`).
  - Terminal state validation: rejects committed (`23505`) or rejected (`22023`) proposals.
- **Atomic Operations in Transaction:**
  - Inserts approved items into `tasks` table with computed scheduling date and durations.
  - Updates `proposal_items` status to `APPROVED` or `REJECTED`.
  - Updates `proposals` status to `COMMITTED`.
  - Updates parent `captures` lifecycle status to `COMMITTED` if linked.
  - Caches response in `approval_idempotency`.
  - Records immutable `PROPOSAL_COMMITTED` event in `audit_logs`.
- **Search Path:** Fixed to `SET search_path = public, extensions, pg_temp;` preventing search path injection vulnerabilities.
- **Schema Reload Notification:** Concludes with `NOTIFY pgrst, 'reload schema';`.

---

## 4. Repository Integration Details

### 4.1 RPC Invocation in `SupabaseRepository.approve_proposal`
Replaced the previous 7-stage sequential HTTP mutation loop with a single atomic call:
```python
rpc_params = {
    "p_user_id": str(user_id),
    "p_proposal_id": str(proposal_id),
    "p_idempotency_key": idempotency_key,
    "p_item_decisions": decisions_payload,
}
raw_result = self.client.rpc_sync("commit_proposal_atomic", rpc_params)
```
SQL error codes from the RPC are mapped cleanly to THOZHI domain exceptions:
- `P0002` / `not found` $\rightarrow$ `ResourceNotFoundException` (HTTP 404)
- `23505` / `already been committed` $\rightarrow$ `IdempotencyConflictException` (HTTP 409)
- `22023` / `already been rejected` $\rightarrow$ `ProposalExpiredException` (HTTP 400)
- `42501` / `access denied` $\rightarrow$ `PermissionDeniedException` (HTTP 403)

### 4.2 Full Sovereign Data Purge (`purge_user_data`)
The sovereign deletion pipeline in `SupabaseRepository` was expanded to purge all 11 user-scoped database tables in strict dependency order:
1. `task_dependencies`
2. `tasks`
3. `proposal_items`
4. `proposals`
5. `captures`
6. `plans`
7. `busy_events`
8. `availability_windows`
9. `contextual_summaries`
10. `memory_preferences`
11. `approval_idempotency`

Following the deletion cascade, an immutable audit entry recording `SOVEREIGN_PURGE` is persisted into `audit_logs`.

---

## 5. Security & Multi-Tenant Architecture Review

| Dimension | Implementation | Security Boundary / Evaluation |
| :--- | :--- | :--- |
| **Row-Level Security (RLS)** | `auth.uid() = user_id` on all tables | Valid for authenticated end-user requests (Phase 2). |
| **Composite Foreign Keys** | `(predecessor_task_id, user_id) REFERENCES tasks(id, user_id)` | Prevents cross-tenant dependency tampering even when using service-role keys. |
| **Partial Unique Index** | `tasks(source_proposal_item_id) WHERE ... IS NOT NULL` | Prevents replay task inflation at the storage engine level. |
| **Audit Log Tamper Resistance** | REVOKE write grants from `authenticated` & `anon` | End-users cannot modify or delete audit trails. |
| **Function Execution Rights** | REVOKE ALL FROM PUBLIC; GRANT TO `authenticated`, `service_role` | Anonymous callers cannot invoke internal RPCs. |
| **Execution Context** | `SECURITY DEFINER` with fixed `search_path` | Eliminates search path spoofing and privilege escalation. |
| **Service-Role Boundary** | Service-role credentials bypass PostgreSQL RLS | **CRITICAL ARCHITECTURAL DISTINCTION:** Backend services utilizing service-role keys must rely on composite foreign keys, explicit query filtering, and repository isolation, not RLS. RLS becomes effective once client-passed JWT tokens are propagated in Phase 2. |

---

## 6. Verification and Test Results

### 6.1 Backend Test Suite (Pytest)
Command executed:
```powershell
$env:PYTHONPATH="."; python -m pytest backend/tests
```
**Results:**
- **Status:** **PASSED**
- **Passed:** **145 tests**
- **Failed:** **0**
- **Warnings:** 2 (upstream deprecation notices for Pytest asyncio and Starlette testclient)
- **Execution Time:** 64.40 seconds

#### New & Updated Tests in `backend/tests/test_supabase_real_persistence.py`:
1. `test_supabase_repository_create_and_get_capture`: Verifies capture creation defaults to `"PROCESSED"`.
2. `test_supabase_repository_approve_proposal_creates_tasks_and_audit`: Verifies `commit_proposal_atomic` RPC execution, parameter mapping, and response model construction.
3. `test_supabase_repository_atomic_approval_error_mapping`: Verifies translation of Postgres SQLSTATE codes (`P0002`, `23505`, `22023`, `42501`) into appropriate domain exceptions.
4. `test_supabase_repository_task_completion_persists_actual_duration`: Verifies `complete_task()` persists `actual_duration_min`.
5. `test_supabase_repository_clarification_persistence_roundtrip`: Verifies serialization and deserialization of `clarifications` JSONB.
6. `test_supabase_repository_sovereign_purge`: Verifies all 11 user-scoped tables are deleted during user account purge.

*Note: In accordance with test integrity guidelines, unit tests use mocked HTTP/PostgREST responses. Real PostgreSQL integration testing requires a live database and is scheduled for Phase 1.9 / Phase 1.10.*

### 6.2 Frontend Production Build (Next.js)
Command executed:
```powershell
npm run build --prefix frontend
```
**Results:**
- **Status:** **PASSED**
- **Static Pages Generated:** **18/18**
- **Exit Code:** 0
- **Routes Validated:** `/`, `/capture`, `/planner`, `/tasks`, `/projects`, `/calendar`, `/goals`, `/insights`, `/notifications`, `/assistant`, `/settings`, `/memory` (redirect-only stub).

---

## 7. Known Limitations and Architectural Notes

1. **Service-Role vs Authenticated Execution:**
   During backend repository testing with service-role configuration, PostgreSQL RLS is bypassed by database design. Full RLS validation will occur when JWT authentication and user context forwarding are established in Phase 2.
2. **Duplicate Preflight Checks:**
   When Migration 004 is applied to an existing database, preflight scripts must verify that no duplicate `source_proposal_item_id` values exist on `tasks` before the partial unique index is generated. (Detailed preflight script is available in `22_MIGRATION_PREFLIGHT_AND_DATA_RECONCILIATION.md`).
3. **No Migration Execution on Live DB:**
   In strict adherence to the project instructions, Migration 004 has **NOT** been applied to any remote or live database instance.

---

## 8. Stopping Condition Adherence & Recommendation

All Phase 1.8 objectives have been achieved:
- [x] Corrected Migration 004 authored without enum alterations.
- [x] Backend repository integrated with atomic RPC and schema updates.
- [x] Exceptions and error mappings aligned.
- [x] Test suite expanded and 100% passing (145/145).
- [x] Frontend build clean (18/18 static pages).
- [x] Zero Git commits, zero pushes, zero live database mutations executed.

### Recommendation
Phase 1.8 is complete. **Antigravity has stopped at the Phase 1.8 boundary.**
Upon user review and authorization, the project may proceed to **Phase 1.9 — Database Compatibility and Regression Verification**.
