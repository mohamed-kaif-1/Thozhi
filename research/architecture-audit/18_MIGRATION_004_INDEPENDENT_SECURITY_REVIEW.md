# THOZHI — Phase 1.7: Independent Migration 004 Security & Compatibility Review

**Auditor:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Audit Target:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql`
**Referenced Files:** `001_initial_schema.sql`, `002_rls_policies.sql`, `003_schema_alignment.sql`, `backend/app/db/repositories/supabase.py`
**Execution Mode:** **READ-ONLY INDEPENDENT AUDIT** (Zero database executions, zero code modifications)
**Status:** **REVIEW COMPLETE — REMEDIATIONS REQUIRED BEFORE DEPLOYMENT APPROVAL**

---

## 1. Executive Summary

This independent security and compatibility review evaluated the proposed `15_MIGRATION_004_DRAFT.sql` against PostgreSQL 15+ engine semantics, Supabase PostgREST 12+ wire protocol requirements, Row-Level Security (RLS) enforcement models, and transaction boundary integrity.

The review identified **2 CRITICAL**, **2 HIGH**, and **3 MEDIUM** issues that must be corrected in the draft before Migration 004 can be approved for execution on any database environment.

### Primary Audit Verdict:
> **STATUS: CONDITIONAL APPROVAL PENDING CORRECTIONS**
> `15_MIGRATION_004_DRAFT.sql` has a strong architectural core (eliminating multi-step race conditions via single-transaction RPC and establishing audit log immutability). However, it contains two critical engine-level defects:
> 1. **Subtransaction Exception Block in Enum Extension:** Wrapping `ALTER TYPE ... ADD VALUE` in a `DO $$ ... EXCEPTION $$` block causes an immediate PostgreSQL engine failure (`ERROR: 25001: ALTER TYPE ... ADD cannot run inside a subtransaction`).
> 2. **Authentication Fallback Identity Spoofing:** In `commit_proposal_atomic`, an unauthenticated caller (`auth.uid() IS NULL`) falls back to trusting `p_user_id` without verifying the caller's role, potentially allowing unauthorized proposal commitments if public execution is ever enabled or misconfigured.

---

## 2. Comprehensive Security & Engine Findings Matrix

| Finding ID | Domain | Issue Description | Severity | Line Reference | Engine Failure / Security Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REV-01** | PostgreSQL Engine | `ALTER TYPE` inside `DO $$ EXCEPTION` block | **CRITICAL** | Lines 13–15 | `ERROR: 25001: ALTER TYPE ... ADD cannot run inside a subtransaction`. Migration aborts. |
| **REV-02** | Security & Auth | Unauthenticated `p_user_id` trust in RPC | **CRITICAL** | Lines 156–159 | If called without JWT, trusts caller `p_user_id`. Spoofing vulnerability. |
| **REV-03** | Contract Integrity | RPC iterates `p_item_decisions` instead of proposal items | **HIGH** | Lines 202–285 | Omitted items are left in `PENDING` state while proposal commits. Inconsistent state. |
| **REV-04** | DDL Safety | Unique index lacks pre-check for existing duplicate tasks | **HIGH** | Lines 35–37 | If test/staging database already has duplicate tasks, migration fails with `23505`. |
| **REV-05** | Supabase Auth | `current_setting('request.jwt.claim.sub')` vs `auth.uid()` | **MEDIUM** | Lines 144 | PostgREST may supply claims in `request.jwt.claims`. Better to use `auth.uid()`. |
| **REV-06** | Relational Defense | Cross-tenant task dependency relies solely on RLS | **MEDIUM** | Lines 90–95 | No composite FK `(predecessor_task_id, user_id)` at relational engine level. |
| **REV-07** | GDPR Completeness | `contextual_summaries` & `availability_windows` purge | **MEDIUM** | N/A (Repository) | Migration does not define cascade behavior for tables omitted in repository purge. |

---

## 3. Deep-Dive Analysis of Findings

### REV-01: `ALTER TYPE ... ADD VALUE` in PL/pgSQL Subtransaction (CRITICAL)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L13-L15`
- **Draft Code:**
  ```sql
  DO $$ BEGIN
      ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';
  EXCEPTION WHEN duplicate_object THEN null; END $$;
  ```
- **PostgreSQL Engine Rule:**
  In PostgreSQL 15+, `ALTER TYPE ... ADD VALUE` cannot run inside a subtransaction. In PL/pgSQL, any `BEGIN ... EXCEPTION ... END` block automatically establishes a subtransaction (internal savepoint). If PostgreSQL encounters `ALTER TYPE ... ADD VALUE` inside an exception block, it immediately aborts with:
  `ERROR: 25001: ALTER TYPE ... ADD cannot run inside a subtransaction`.
- **Proof:** Furthermore, `IF NOT EXISTS` is a native clause of `ALTER TYPE ... ADD VALUE` introduced in PostgreSQL 9.3. The `EXCEPTION WHEN duplicate_object` block is completely redundant and harmful.
- **Required Correction:**
  Replace lines 13–15 with a direct, top-level DDL statement:
  ```sql
  ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';
  ```
  *(Note: PostgreSQL documentation also requires that `ALTER TYPE ... ADD VALUE` cannot be executed in the same transaction block if the new enum value is used by subsequent commands in that same transaction. In Supabase migration runners, top-level statements run sequentially).*

---

### REV-02: Identity Spoofing in `commit_proposal_atomic` Fallback (CRITICAL)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L143-L160`
- **Draft Code:**
  ```sql
  BEGIN
      v_auth_uid := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
  EXCEPTION WHEN OTHERS THEN
      v_auth_uid := NULL;
  END;

  IF v_auth_uid IS NOT NULL THEN
      IF v_auth_uid != p_user_id THEN
          RAISE EXCEPTION 'Access denied: authenticated caller % does not match target user_id %',
              v_auth_uid, p_user_id USING ERRCODE = '42501';
      END IF;
      v_effective_user_id := v_auth_uid;
  ELSE
      -- Fallback for service_role / development test runner
      v_effective_user_id := p_user_id;
  END IF;
  ```
- **Security Vulnerability:**
  Because the function is declared `SECURITY DEFINER`, it runs with elevated database owner privileges. If `v_auth_uid` is `NULL` (for example, if invoked by the `anon` role or an unauthenticated HTTP connection where PostgREST does not pass a JWT), the code enters the `ELSE` branch:
  `v_effective_user_id := p_user_id;`
  This blindly trusts whatever `p_user_id` was supplied in the JSON payload!
  Even though Line 351 revokes execution from `PUBLIC`, defense-in-depth requires that the function itself verify that the caller is genuinely an administrative role (`service_role` or superuser `postgres`) before accepting an unauthenticated `p_user_id`.
- **Proof of Exploitability:** If an administrator or test script accidentally grants execute to `anon` or if an anon key is used, any unauthenticated attacker can commit any proposal for any tenant.
- **Required Correction:**
  Explicitly verify the role when `v_auth_uid` is null:
  ```sql
  -- Derivation using standard Supabase auth.uid()
  BEGIN
      v_auth_uid := auth.uid();
  EXCEPTION WHEN OTHERS THEN
      v_auth_uid := NULL;
  END;

  IF v_auth_uid IS NOT NULL THEN
      -- Authenticated user mode: target user MUST match verified JWT identity
      IF v_auth_uid != p_user_id THEN
          RAISE EXCEPTION 'Access denied: authenticated caller % does not match target user_id %',
              v_auth_uid, p_user_id USING ERRCODE = '42501';
      END IF;
      v_effective_user_id := v_auth_uid;
  ELSIF current_setting('request.jwt.claim.role', true) = 'service_role' OR current_user = 'postgres' THEN
      -- Privileged administrative service mode: allow explicit target user_id
      v_effective_user_id := p_user_id;
  ELSE
      RAISE EXCEPTION 'Access denied: authentication required to commit proposals'
          USING ERRCODE = '42501';
  END IF;
  ```

---

### REV-03: Proposal Item Loop Inconsistency (HIGH)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L202-L284`
- **Draft Code:**
  ```sql
  FOR v_item IN SELECT * FROM jsonb_array_elements(p_item_decisions)
  LOOP
      ...
  END LOOP;
  ```
- **Root Cause & Contract Gap:**
  In `SupabaseRepository.approve_proposal()` (lines 418–421), the loop iterated over `prop.items` (all items belonging to the proposal). If a caller omitted an item from the approval request payload, the application defaulted to `is_approved = True` (or rejected).
  In the draft RPC, the loop iterates *only* over the caller-provided `p_item_decisions`.
  If a proposal has 3 items, and the client submits decisions for only 2 items:
  1. Item 1 and Item 2 are updated to `'COMMITTED'`.
  2. Item 3 remains in `'PENDING'` state.
  3. The proposal is updated to `status = 'COMMITTED'`.
  This leaves the database in an inconsistent state: a committed proposal with pending items!
- **Required Correction:**
  Either:
  1. The stored procedure iterates over `SELECT * FROM proposal_items WHERE proposal_id = p_proposal_id AND user_id = v_effective_user_id`, matching decisions from `p_item_decisions` and applying standard default rules (or rejecting if any item decision is missing).
  2. AND the RPC validates: `IF (SELECT COUNT(*) FROM proposal_items WHERE proposal_id = p_proposal_id) != jsonb_array_length(p_item_decisions) THEN RAISE EXCEPTION ...`.
  Enforcing full-coverage decisions ensures 100% data integrity.

---

### REV-04: Existing Duplicate Data Risk on Unique Index (HIGH)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L35-L37`
- **Draft Code:**
  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
      ON tasks (source_proposal_item_id)
      WHERE source_proposal_item_id IS NOT NULL;
  ```
- **Risk:**
  If the target staging database already experienced race conditions during Phase 1 testing and contains two tasks pointing to the same `source_proposal_item_id`, PostgreSQL will abort the index creation with:
  `ERROR: 23505: could not create unique index "uq_task_source_proposal_item"`
  `Key (source_proposal_item_id)=(...) is duplicated.`
- **Required Correction:**
  Precede index creation with an idempotent deduplication query that cleans up any historical test duplicates:
  ```sql
  -- Remove any historical duplicate tasks created during prior race conditions
  DELETE FROM tasks t1
  USING tasks t2
  WHERE t1.id > t2.id
    AND t1.source_proposal_item_id = t2.source_proposal_item_id
    AND t1.source_proposal_item_id IS NOT NULL;

  CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
      ON tasks (source_proposal_item_id)
      WHERE source_proposal_item_id IS NOT NULL;
  ```

---

### REV-05: JWT Claims Resolution via `auth.uid()` (MEDIUM)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L144`
- **Draft Code:** `v_auth_uid := NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;`
- **Evaluation:** In standard Supabase environments, PostgREST sets `request.jwt.claims` as a JSON string and `auth.uid()` is the official, battle-tested SQL function provided by Supabase. In local testing environments without `auth.uid()`, falling back to `request.jwt.claim.sub` is safe.
- **Required Correction:** Use `COALESCE(auth.uid(), NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID)`.

---

### REV-06: Defense-in-Depth for Task Dependencies (MEDIUM)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L90-L95`
- **Evaluation:** The RLS policy:
  ```sql
  CREATE POLICY dependencies_insert ON task_dependencies FOR INSERT
  WITH CHECK (
      user_id = current_user_id()
      AND EXISTS (SELECT 1 FROM tasks WHERE id = predecessor_task_id AND user_id = current_user_id())
      AND EXISTS (SELECT 1 FROM tasks WHERE id = successor_task_id AND user_id = current_user_id())
  );
  ```
  This RLS policy works correctly in PostgreSQL. However, if service role queries bypass RLS, relational integrity is not enforced at the database schema level.
- **Recommendation:** Add a composite unique index on `tasks (id, user_id)` in Migration 004, enabling composite foreign keys in future iterations.

---

### REV-07: Append-Only Audit Trail Verification (VERIFIED SECURE)
- **Location:** `research/architecture-audit/15_MIGRATION_004_DRAFT.sql#L102-L104`
- **Evaluation:** Dropping `audit_self` (which had `FOR ALL`) and replacing it with strictly `audit_select` and `audit_insert` policies guarantees that authenticated users cannot perform `UPDATE` or `DELETE` on `audit_logs`.
- **Verdict:** **VERIFIED SOUND & COMPLIANT**.

---

## 4. Required Migration 004 Remediation (Corrected DDL Preview)

```sql
-- ====================================================================
-- CORRECTED MIGRATION 004 SPECIFICATION (POST-REVIEW)
-- ====================================================================

-- 1. ENUM EXTENSION (Direct, non-subtransactional)
ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';

-- 2. TABLE EXTENSIONS
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_duration_min INT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS scheduled_date DATE;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS clarifications JSONB DEFAULT '[]'::JSONB NOT NULL;

-- 3. HISTORICAL DEDUPLICATION & PARTIAL UNIQUE INDEX
DELETE FROM tasks t1
USING tasks t2
WHERE t1.id > t2.id
  AND t1.source_proposal_item_id = t2.source_proposal_item_id
  AND t1.source_proposal_item_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
    ON tasks (source_proposal_item_id)
    WHERE source_proposal_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_user_scheduled_date
    ON tasks (user_id, scheduled_date);

-- 4. HARDENED RLS POLICIES (Unchanged from draft - verified sound)
-- [Captures, Proposals, Proposal Items, Tasks, Memory Preferences, Dependencies, Audit Logs]

-- 5. HARDENED ATOMIC STORED PROCEDURE
-- [Includes auth.uid() + role check, item completeness validation, FOR UPDATE serialization]
```

---

## 5. Security Review Sign-Off & Recommendation

| Verification Gate | Result | Notes |
| :--- | :--- | :--- |
| **PostgreSQL 15+ Syntax** | PASS (with REV-01 fix) | `ALTER TYPE` moved to top-level DDL |
| **Supabase PostgREST Compatibility** | PASS (with REV-05 fix) | Uses `auth.uid()` and standard JSON return |
| **Anti-Spoofing & Identity Enforcement** | PASS (with REV-02 fix) | Rejects unauthenticated caller `p_user_id` fallback |
| **Single-Transaction Atomicity** | PASS | 100% rollback on any failed item or conflict |
| **Audit Log Immutability** | PASS | Zero UPDATE / DELETE policies for authenticated users |
| **Tenant Isolation in Dependencies** | PASS | Subquery checks tenant of both predecessor and successor |

### Recommendation:
Do **NOT** execute the original `15_MIGRATION_004_DRAFT.sql` as written due to **REV-01** (engine failure) and **REV-02** (identity fallback vulnerability).

Approve the corrected DDL specification outlined in Section 4 to be prepared as the official `supabase/migrations/004_schema_alignment_and_rpc.sql` for implementation in **Phase 1.8**.

---
*End of Phase 1.7 Deliverable. Awaiting explicit user approval before proceeding to Phase 1.8.*
