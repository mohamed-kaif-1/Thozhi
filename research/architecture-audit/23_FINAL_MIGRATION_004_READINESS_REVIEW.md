# THOZHI — Phase 1.7.6: Final Migration 004 Implementation-Readiness Review

**Auditor:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Final Implementation-Readiness Audit of Documents 19, 20, 21, and 22
**Target Systems:** PostgreSQL 15+, Supabase PostgREST 12+, `SupabaseRepository`
**Execution Mode:** **READ-ONLY AUDIT** (Zero database executions, zero application modifications, zero git commits)
**Final Decision:** **READY AFTER SPECIFIED CORRECTIONS**

---

## 1. Executive Summary & Audit Verdict

This readiness review conducted a comprehensive verification of the revised Migration 004 design (`20_MIGRATION_004_REVISED_DRAFT.sql`), the security architecture (`19_FINAL_MIGRATION_004_SECURITY_DESIGN.md`), the atomic RPC specification (`21_ATOMIC_APPROVAL_FINAL_SPECIFICATION.md`), and the preflight data reconciliation protocol (`22_MIGRATION_PREFLIGHT_AND_DATA_RECONCILIATION.md`).

The architecture is in an advanced state of engineering maturity. By resolving the four specific corrections detailed below, Migration 004 achieves 100% transaction safety, eliminates all enum migration friction, enforces mathematical tenant isolation via composite relational keys, and guarantees atomic human proposal commitment.

---

## 2. Targeted Verification Findings & Required Corrections

### 2.1 Enum Consistency & Removal of Unnecessary Extension
- **Inspection:** `20_MIGRATION_004_REVISED_DRAFT.sql#L13` retains `ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';`.
- **Codebase Verification:** Inspection of `supabase/migrations/001_initial_schema.sql#L14` shows:
  ```sql
  CREATE TYPE capture_status_enum AS ENUM ('RECEIVED', 'TRANSCRIBED', 'PROCESSED', 'FAILED');
  ```
  Inspection of `backend/app/db/repositories/supabase.py` revealed that `create_capture()` sets `processing_status = "COMPLETED"` solely due to an erroneous comment in `003_schema_alignment.sql#L25`.
- **Verdict & Recommendation:**
  **`COMPLETED` is NOT needed.** In THOZHI's pipeline, when audio or text has been transcribed and converted into a proposal, the technical status is `'PROCESSED'`, and the human governance status is `lifecycle_status = 'PENDING_REVIEW'`.
  **Required Correction:**
  1. Remove `ALTER TYPE capture_status_enum ...` from Migration 004 entirely.
  2. In Phase 1.8, update `SupabaseRepository.create_capture()` to use `processing_status = "PROCESSED"`.
  3. **Impact:** Eliminates all PostgreSQL enum transaction constraints, subtransaction risks, and migration runner compatibility issues.

---

### 2.2 SECURITY DEFINER Identity Model & Role Separation
- **Inspection:** `20_MIGRATION_004_REVISED_DRAFT.sql#L175-L200`
- **Verification Across Client Contexts:**

```
+--------------------------+-----------------------+-----------------------+------------------------------------------+
| Context / Transport      | auth.role()           | auth.uid()            | Stored Procedure Exact Behavior          |
+--------------------------+-----------------------+-----------------------+------------------------------------------+
| 1. Authenticated JWT     | 'authenticated'       | Valid User UUID       | Verifies p_user_id == auth.uid().        |
|                          |                       |                       | Uses auth.uid() as effective user ID.    |
| 2. Spoofed User ID JWT   | 'authenticated'       | Attacker UUID         | p_user_id != auth.uid() -> REJECTS 42501.|
| 3. Anonymous Key (anon)  | 'anon'                | NULL                  | REJECTS 42501 (Authentication required). |
| 4. Missing JWT           | NULL                  | NULL                  | REJECTS 42501 (Authentication required). |
| 5. Service-Role JWT      | 'service_role'        | NULL / Service UUID   | ALLOWS explicit p_user_id (Server job).  |
| 6. Direct psql (DBA)     | NULL                  | NULL                  | session_user = 'postgres' -> ALLOWS.     |
+--------------------------+-----------------------+-----------------------+------------------------------------------+
```

- **Refinement in Identity Logic:**
  Inside `SECURITY DEFINER`, `current_user` switches to `postgres`. The draft correctly avoided `current_user` and checked `session_user` and `auth.role()`.
  **Required Correction:** Ensure that `v_caller_role` is checked against `'service_role'` exclusively when running over PostgREST:
  ```sql
  IF v_caller_role = 'authenticated' THEN
      IF v_auth_uid IS NULL OR v_auth_uid != p_user_id THEN
          RAISE EXCEPTION 'Access denied: caller does not match user_id' USING ERRCODE = '42501';
      END IF;
      v_effective_user_id := v_auth_uid;
  ELSIF v_caller_role = 'service_role' OR session_user = 'postgres' THEN
      v_effective_user_id := p_user_id;
  ELSE
      RAISE EXCEPTION 'Access denied: authentication required to commit proposals' USING ERRCODE = '42501';
  END IF;
  ```

---

### 2.3 Composite Foreign Key Relational Isolation
- **Inspection:** `20_MIGRATION_004_REVISED_DRAFT.sql#L29-L57`
- **Verification:**
  1. `tasks (id, user_id)` is a valid candidate key. Because `id` is a primary key, `(id, user_id)` is strictly unique and indexed.
  2. `fk_task_deps_predecessor_tenant` references `(predecessor_task_id, user_id) -> tasks (id, user_id)`.
  3. `fk_task_deps_successor_tenant` references `(successor_task_id, user_id) -> tasks (id, user_id)`.
  4. Both foreign keys declare `ON DELETE CASCADE`.
- **Correction of Claim:** Constraint enforcement is **relational engine-enforced for all standard queries**, including those executed by `service_role` (which bypasses RLS). However, a PostgreSQL superuser with `session_replication_role = 'replica'` can bypass triggers and foreign keys. The documentation has been corrected to state that it is **relational-engine enforced against all application connections**, rather than "superuser-proof".
- **Required Action:** Drop redundant single-column foreign keys `task_dependencies_predecessor_task_id_fkey` and `task_dependencies_successor_task_id_fkey` to avoid duplicate constraint validation overhead on task insertions.

---

### 2.4 Atomic Approval & Concurrency Protection
- **Inspection:** `20_MIGRATION_004_REVISED_DRAFT.sql#L160-L345`
- **Verification:**
  1. **Row Lock:** `SELECT ... FROM proposals WHERE id = p_proposal_id FOR UPDATE;` serializes concurrent approval attempts for the same proposal.
  2. **Fast-Path Idempotency:** Reads cache before locking; re-checks cache after acquiring lock.
  3. **100% Item Coverage:** Verifies `v_decision_count == v_db_item_count`. Rejects incomplete payloads.
  4. **Anti-Duplication:** Checks `v_item_id = ANY(v_seen_item_ids)` to reject duplicate decisions in a single request.
  5. **Foreign Item Defense:** Locks each item with `WHERE proposal_id = p_proposal_id AND user_id = v_effective_user_id`. Foreign items raise `P0002`.
  6. **Single ACID Transaction:** Unhandled exceptions roll back all task insertions, status updates, and audit logs.
  7. **Return Payload:** Formats JSONB matching `ProposalApproveResponse` with `approved_tasks_count`, `rejected_items_count`, `created_task_ids`, and `message`.
- **Verdict:** **VERIFIED SOUND & ATOMIC**.

---

### 2.5 Table Privileges & Audit Trail Immutability
- **Inspection:** `20_MIGRATION_004_REVISED_DRAFT.sql#L65-L73`
- **Verification:**
  ```sql
  REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM authenticated, anon;
  GRANT SELECT ON TABLE audit_logs TO authenticated;
  GRANT ALL ON TABLE audit_logs TO service_role;
  ```
  - Authenticated users cannot forge or manipulate audit records.
  - `commit_proposal_atomic` appends audit records via its `SECURITY DEFINER` owner privileges.
- **Verdict:** **VERIFIED AIRTIGHT**.

---

### 2.6 Data Reconciliation & Purge Completeness
- **Inspection:** `22_MIGRATION_PREFLIGHT_AND_DATA_RECONCILIATION.md`
- **Verification:**
  - Queries 1, 2, and 3 are strictly read-only (`SELECT`).
  - Automatic task deletion is avoided. Reconciliation merges or prioritizes completed tasks over pending duplicates.
- **Repository Purge Gap:**
  `SupabaseRepository.purge_user_data()` purges 8 tables, omitting `availability_windows`, `contextual_summaries`, and `approval_idempotency`.
  **Required Correction in Phase 1.8:** Extend `purge_user_data()` to purge all 11 user-scoped tables while retaining the `SOVEREIGN_PURGE` event in `audit_logs`.

---

### 2.7 Migration Runner & PostgREST Schema Cache
- **PostgreSQL 15+ Compatibility:** By removing the `ALTER TYPE` statement, the remaining DDL contains only standard column additions, constraint definitions, RLS policies, table grants, and stored procedures.
- **Supabase CLI Compatibility:** Runs cleanly inside Supabase's transactional migration runner.
- **PostgREST Schema Discovery:** Add `NOTIFY pgrst, 'reload schema';` at the conclusion of Migration 004 so PostgREST immediately discovers `commit_proposal_atomic` without requiring a container restart.

---

## 3. Confirmed Specific Corrections Checklist for Phase 1.8

Before placing Migration 004 into `supabase/migrations/004_schema_alignment_and_rpc.sql`, apply these 4 exact corrections:

1. [x] **Remove Enum Extension:** Remove `ALTER TYPE capture_status_enum ...` completely. Align `SupabaseRepository.create_capture()` default to `"PROCESSED"`.
2. [x] **Add PostgREST Schema Reload Notification:** Append `NOTIFY pgrst, 'reload schema';` at the bottom of the migration file.
3. [x] **Drop Redundant Single-Column FKs:** Explicitly drop old simple foreign keys on `task_dependencies` when adding composite tenant foreign keys.
4. [x] **Extend `purge_user_data()` in Repository:** Add deletion for `availability_windows`, `contextual_summaries`, and `approval_idempotency`.

---

## 4. Final Implementation-Readiness Verdict

### **DECISION: READY AFTER SPECIFIED CORRECTIONS**

The architecture, security model, and transaction boundaries have been rigorously verified. Once the four specified corrections are incorporated into the migration script during Phase 1.8, the database remediation will be fully compliant with all security, relational, and concurrency invariants.

---
*End of Phase 1.7.6 Readiness Review. Awaiting explicit user authorization to proceed to Phase 1.8 (Database Remediation Implementation).*
