# THOZHI — Phase 1.6: Database Compatibility Remediation Architecture

**Author:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Remediation Architecture for `research/architecture-audit/13_DATABASE_SCHEMA_COMPATIBILITY_AUDIT.md`
**Target Systems:** PostgreSQL 15+, Supabase PostgREST 12+, `backend/app/db/repositories/supabase.py`, `backend/app/db/supabase_client.py`
**Execution Mode:** **ARCHITECTURE & SPECIFICATION DESIGN** (Zero live database execution, zero git commits)
**Status:** **APPROVED FOR REVIEW — AWAITING EXPLICIT USER APPROVAL BEFORE EXECUTION**

---

## 1. Executive Summary & Remediation Strategy

Following the Phase 1.5 read-only compatibility audit, this document provides the formal remediation architecture to prepare THOZHI for genuine PostgreSQL durability, Row Level Security (RLS) enforcement, and upcoming JWT authentication.

The primary objective is to eliminate all runtime schema mismatches, establish single-transaction ACID guarantees for human proposal approvals, and eliminate cross-tenant data leakage risks while strictly preserving existing business logic and application behavior.

### Key Architectural Tenets:
1. **The Invariant Holds:** *"The AI proposes. The user decides."* Human approval remains the immutable prerequisite for all durable task creation.
2. **Forward-Only, Non-Destructive Migrations:** Existing migrations `001_initial_schema.sql`, `002_rls_policies.sql`, and `003_schema_alignment.sql` remain completely unmodified. All corrections are encapsulated in a forward-only `004_schema_alignment_and_rpc.sql`.
3. **Transaction-Safe ACID Commitment:** The 7-step sequential HTTP approval workflow in `SupabaseRepository` is replaced with an atomic PostgreSQL stored procedure (`commit_proposal_atomic` RPC).
4. **Zero Live Database Mutations:** No SQL is executed against production or staging environments during this design phase.

---

## 2. Independent Validation of Audit Findings (ISS-01 through ISS-11)

Each issue identified in Report 13 has been independently re-verified against the source codebase and migration files. Inaccurate assumptions from the initial audit have been corrected based on verified PostgreSQL 15+ engine behaviors.

```
+---------------------------------------------------------------------------------------------------+
| ISSUE VALIDATION MATRIX                                                                           |
+--------+-----------------------+-----------+----------------------+-------------------------------+
| ID     | Domain                | Status    | Severity             | Verified Impact               |
+--------+-----------------------+-----------+----------------------+-------------------------------+
| ISS-01 | Enum Incompatibility  | CONFIRMED | CRITICAL             | Capture ingestion crashes     |
| ISS-02 | Missing Column (Task) | CONFIRMED | CRITICAL             | Task completion crashes       |
| ISS-03 | Missing Persistence   | CONFIRMED | CRITICAL             | Clarifications lost on reload |
| ISS-04 | Migration Dependency  | CONFIRMED | CRITICAL             | Cannot run on 001 alone       |
| ISS-05 | Transaction Integrity | CONFIRMED | HIGH                 | Approval race condition       |
| ISS-06 | RLS Policy Defect     | REFINED   | HIGH                 | Audit log immutability gap    |
| ISS-07 | Missing Constraint    | CONFIRMED | HIGH                 | Duplicate tasks on retry      |
| ISS-08 | Service Role Bypass   | CONFIRMED | MEDIUM               | Database RLS not enforced     |
| ISS-09 | Tenant Isolation Gap  | CONFIRMED | MEDIUM               | Cross-tenant dependency edge  |
| ISS-10 | GDPR Purge Gap        | CONFIRMED | MEDIUM               | Incomplete data destruction   |
| ISS-11 | Supabase Auth Link    | CONFIRMED | LOW                  | Potential orphaned profile    |
+--------+-----------------------+-----------+----------------------+-------------------------------+
```

---

### Detailed Finding Breakdown

#### ISS-01: `captures.processing_status = 'COMPLETED'` Invalid Enum
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/repositories/supabase.py#L148`, `supabase/migrations/001_initial_schema.sql#L14`
- **Root Cause:** `001_initial_schema.sql` defines `capture_status_enum` as `('RECEIVED', 'TRANSCRIBED', 'PROCESSED', 'FAILED')`. In `003_schema_alignment.sql#L25`, an inline comment erroneously claimed the enum contained `'COMPLETED'`. `SupabaseRepository.create_capture()` sets the default parameter `processing_status="COMPLETED"`.
- **Failure Mode:** PostgreSQL rejects insertion with SQLState `22P02` (`invalid input value for enum capture_status_enum: "COMPLETED"`). Capture creation fails completely.
- **Correct Remediation:**
  1. In Migration 004: `ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';`
  2. In `SupabaseRepository.create_capture`: Allow both `'PROCESSED'` and `'COMPLETED'` gracefully.
- **Required Tests:** Test capture creation with both `'PROCESSED'` and `'COMPLETED'`.

#### ISS-02: Missing Column `tasks.actual_duration_min`
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/repositories/supabase.py#L761-L766`, `supabase/migrations/001_initial_schema.sql#L101-L114`, `003_schema_alignment.sql#L60-L64`
- **Root Cause:** `TaskCompleteRequest` supports optional `actual_duration_min`. The repository attempts to update `"actual_duration_min": act_dur` on `PATCH /tasks`. Neither migration defines this column.
- **Failure Mode:** PostgREST returns HTTP 400 Bad Request with code `42703` (`column tasks.actual_duration_min does not exist`). Calling `POST /api/v1/tasks/{id}/complete` with actual duration fails.
- **Correct Remediation:** Add column in Migration 004:
  `ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_duration_min INT;`
- **Required Tests:** Test task completion with and without `actual_duration_min`.

#### ISS-03: Dropped Proposal Clarification Questions
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/repositories/supabase.py#L243-L246`, `supabase.py#L643`, `supabase/migrations/001_initial_schema.sql#L69-L78`
- **Root Cause:** `ExtractionResponse.clarification_questions` are generated by NLU, but `proposals` table lacks a `clarifications` column. The repository does not write them to database, and `get_proposal()` hardcodes `clarifications=[]`.
- **Failure Mode:** Clarification questions generated during voice capture are permanently dropped from persistent storage. Users refreshing the page lose pending clarifications.
- **Correct Remediation:**
  1. Add column in Migration 004:
     `ALTER TABLE proposals ADD COLUMN IF NOT EXISTS clarifications JSONB DEFAULT '[]'::JSONB NOT NULL;`
  2. Update `create_proposal_from_extraction` to insert `clarifications`.
  3. Update `_row_to_proposal` to read `clarifications`.
- **Required Tests:** Verify clarification question persistence and roundtrip retrieval.

#### ISS-04: Migration 003 Strict Prerequisite
- **Status:** **CONFIRMED**
- **File Reference:** `supabase/migrations/003_schema_alignment.sql#L11-L75`
- **Root Cause:** `SupabaseRepository` requires fields introduced only in 003 (`proposals.status = 'PENDING_REVIEW'`, `captures.lifecycle_status`, `tasks.origin_proposal_id`, `memory_preferences.category`).
- **Failure Mode:** Running against a database with only 001 and 002 applied crashes on virtually all endpoints.
- **Correct Remediation:** Document Migration 003 as a mandatory prerequisite and ensure CI/CD applies migrations strictly in sequence: 001 -> 002 -> 003 -> 004.
- **Required Tests:** Migration order validation test.

#### ISS-05: Non-Atomic Multi-Step Proposal Approval
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/repositories/supabase.py#L391-L503`
- **Root Cause:** Approval coordinates 7 separate HTTP calls across 5 tables over the network. If two concurrent requests arrive, both pass the idempotency check, both create tasks, and both update proposal items. If network drops mid-stream, partial writes are committed without rollback.
- **Failure Mode:** Duplicate tasks created in database; partial state inconsistency.
- **Correct Remediation:** Implement `commit_proposal_atomic` PostgreSQL stored procedure executed in 1 network roundtrip with row-level locking (`SELECT ... FOR UPDATE`).
- **Required Tests:** Concurrent approval simulation, mid-transaction failure rollback verification.

#### ISS-06: RLS Policy Deficiencies & Immutability Gaps
- **Status:** **REFINED / CLARIFIED**
- **File Reference:** `supabase/migrations/002_rls_policies.sql#L28-L44`
- **Audit Correction / Fact vs Assumption:**
  - *Audit Claim:* Claimed that `FOR ALL USING (expr)` allows tenant reassignment on `UPDATE`.
  - *PostgreSQL Reality:* In PostgreSQL, `FOR ALL USING (expr)` automatically applies `USING (expr)` as the default `WITH CHECK` for `INSERT` and `UPDATE` unless overridden. An update attempting to reassign `user_id` to another user fails the default `WITH CHECK`.
  - *Actual Verified Vulnerabilities:*
    1. **Audit Log Immutability Breach:** `002_rls_policies.sql#L40` defines `audit_self ON audit_logs FOR ALL USING (user_id = current_user_id())`. This allows an authenticated user to `UPDATE` or `DELETE` their own audit log entries, destroying the legal audit trail! Audit logs must be strictly `INSERT`-only and `SELECT`-only.
    2. **Idempotency Tampering:** `approval_idempotency` has `FOR ALL`, allowing users to delete idempotency records and re-execute actions.
    3. **Subquery Clarity:** Explicit `WITH CHECK` on `plan_items` ensures clarity for complex nested queries during inserts.
- **Correct Remediation:** Re-declare explicit policies per action (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) with explicit `WITH CHECK`, and make `audit_logs` append-only.
- **Required Tests:** Test that authenticated users cannot `UPDATE` or `DELETE` audit log rows.

#### ISS-07: Missing Unique Constraint on `tasks.source_proposal_item_id`
- **Status:** **CONFIRMED**
- **File Reference:** `supabase/migrations/001_initial_schema.sql#L104`
- **Root Cause:** `source_proposal_item_id` has a foreign key to `proposal_items(id)`, but lacks a `UNIQUE` constraint. Multiple tasks can point to the same proposal item.
- **Failure Mode:** Retried or concurrent approvals can produce duplicate tasks for the same proposal item.
- **Pre-Condition & Remediation:**
  *Pre-condition Check:* Manual tasks created without a proposal have `source_proposal_item_id = NULL`. Standard unique constraints allow multiple NULLs in PostgreSQL, but a **partial unique index** is significantly more robust:
  `CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item ON tasks (source_proposal_item_id) WHERE source_proposal_item_id IS NOT NULL;`
- **Required Tests:** Verify that inserting two tasks with the same `source_proposal_item_id` fails with a unique constraint violation.

#### ISS-08: Repository Relies on Service-Role Key (Bypassing RLS)
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/supabase_client.py#L59-L65`
- **Root Cause:** `SupabaseClient` sends `SUPABASE_KEY` (service-role key). PostgREST runs as `service_role` which has PostgreSQL `BYPASSRLS`.
- **Failure Mode:** RLS policies are completely inactive; tenant isolation is enforced exclusively by Python application code.
- **Correct Remediation:** Design repository and client to support user bearer tokens (`user_token`). In Phase 2, FastAPI auth middleware will extract and forward JWT tokens to PostgREST.
- **Required Tests:** Verify that calling client with `user_token` passes token in `Authorization: Bearer <token>`.

#### ISS-09: Cross-User Dependency Edge Creation in `task_dependencies`
- **Status:** **CONFIRMED**
- **File Reference:** `supabase/migrations/001_initial_schema.sql#L117-L126`, `002_rls_policies.sql#L33`
- **Root Cause:** RLS checks `user_id = current_user_id()`, but does not verify that `predecessor_task_id` and `successor_task_id` belong to `current_user_id()`.
- **Failure Mode:** User A can create a dependency edge between User B's private tasks (if IDs are known) or link their own task to User B's task.
- **Correct Remediation:** Harden RLS policy on `task_dependencies`:
  ```sql
  CREATE POLICY dependencies_insert ON task_dependencies FOR INSERT
  WITH CHECK (
      user_id = current_user_id()
      AND EXISTS (SELECT 1 FROM tasks WHERE id = predecessor_task_id AND user_id = current_user_id())
      AND EXISTS (SELECT 1 FROM tasks WHERE id = successor_task_id AND user_id = current_user_id())
  );
  ```
- **Required Tests:** Attempt to insert a dependency where predecessor belongs to another tenant; verify rejection.

#### ISS-10: GDPR Purge Omits User-Scoped Tables
- **Status:** **CONFIRMED**
- **File Reference:** `backend/app/db/repositories/supabase.py#L1104-L1133`
- **Root Cause:** `purge_user_data()` purges 8 tables, but omits `approval_idempotency`, `contextual_summaries`, and `availability_windows`.
- **Failure Mode:** Incomplete sovereign data wipe; orphaned user records persist.
- **Correct Remediation:** Extend `purge_user_data()` to delete from all 11 user-scoped tables and record the purge event.
- **Required Tests:** Verify that after `purge_user_data()`, zero user records remain in any user-scoped table.

#### ISS-11: `users.id` Decoupled from `auth.users(id)`
- **Status:** **CONFIRMED** (Low Severity)
- **File Reference:** `supabase/migrations/001_initial_schema.sql#L45-L53`
- **Root Cause:** Standalone UUID primary key without foreign key to `auth.users(id)`.
- **Failure Mode:** Deleting a user in Supabase Auth does not automatically cascade-delete `public.users`.
- **Correct Remediation:** Maintain architectural decoupling for testing flexibility, but provide a trigger/cascade definition in Migration 004 for production Supabase Auth environments.
- **Required Tests:** Profile lifecycle test.

---

## 3. Schema & Constraint Alignment Specifications

The following table summarizes all required database modifications to be included in `004_schema_alignment_and_rpc.sql`:

```
+---------------------+-------------------------------+--------------------------------------------+
| Table / Type        | Modification                  | Specification Details                      |
+---------------------+-------------------------------+--------------------------------------------+
| capture_status_enum | ADD VALUE                     | 'COMPLETED'                                |
| tasks               | ADD COLUMN                    | actual_duration_min INT                    |
| tasks               | ADD COLUMN                    | scheduled_date DATE                        |
| tasks               | CREATE UNIQUE INDEX (partial) | uq_task_source_proposal_item (WHERE NOT NULL)|
| proposals           | ADD COLUMN                    | clarifications JSONB DEFAULT '[]' NOT NULL |
| task_dependencies   | RLS POLICY UPDATE             | Enforce predecessor & successor ownership  |
| audit_logs          | RLS POLICY UPDATE             | INSERT & SELECT only (No UPDATE / DELETE)  |
| approval_idempotency| RLS POLICY UPDATE             | INSERT & SELECT only (No UPDATE / DELETE)  |
| Stored Procedure    | CREATE FUNCTION               | commit_proposal_atomic(UUID, UUID, ...)    |
+---------------------+-------------------------------+--------------------------------------------+
```

---

## 4. Next Implementation Step

Upon explicit review and authorization by the user:
1. `004_schema_alignment_and_rpc.sql` will be placed in `supabase/migrations/`.
2. `SupabaseRepository` will be updated to route `approve_proposal` to `commit_proposal_atomic`.
3. Clarification persistence and task actual duration columns will be wired.
4. Comprehensive test suite will be executed.
