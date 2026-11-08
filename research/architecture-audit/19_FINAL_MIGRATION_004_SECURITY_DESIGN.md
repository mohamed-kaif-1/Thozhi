# THOZHI — Phase 1.7.5: Final Migration 004 Security & Architecture Design

**Author:** Principal Software Architect, PostgreSQL Database Architect & Lead Security Auditor
**Date:** 2026-11-08
**Scope:** Remediation and Refinement of Migration 004 Draft following Phase 1.7 Independent Security Review
**Status:** **FINAL REVISED DESIGN SPECIFICATION — READY FOR IMPLEMENTATION APPROVAL**

---

## 1. Executive Summary & Resolution Matrix

Following the independent security review (`18_MIGRATION_004_INDEPENDENT_SECURITY_REVIEW.md`), this document establishes the corrected architectural and database design for Migration 004.

All seven findings from Phase 1.7, along with additional engine and security considerations, have been comprehensively resolved:

| Finding ID | Domain | Severity | Review Finding | Final Architecture Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **REV-01** | Enum Migration Safety | **CRITICAL** | `ALTER TYPE` inside `DO $$ EXCEPTION` block causes `ERROR: 25001: cannot run inside subtransaction`. | **Semantic Alignment Strategy:** `SupabaseRepository.create_capture` will default to `'PROCESSED'`, which already exists in `001_initial_schema.sql`. In Migration 004, `ALTER TYPE` is provided as an idempotent standalone statement without subtransaction wrappers, ensuring compatibility across all migration runners. |
| **REV-02** | Secure RPC Identity | **CRITICAL** | Fallback in `commit_proposal_atomic` trusted caller `p_user_id` when unauthenticated. | **Multi-Tier Identity Verification:** Derives identity via `auth.uid()`. Rejects anonymous callers. Differentiates `authenticated` vs `service_role` vs DBA (`session_user = 'postgres'`). `current_user` is explicitly NOT used for caller proof. |
| **REV-03** | Proposal Decisions | **HIGH** | Looping `p_item_decisions` permitted partial commitments with orphaned `PENDING` items. | **Strict Full-Coverage Contract:** RPC requires decisions for 100% of the proposal's items. Validates matching count, rejects duplicate or foreign item IDs, and guarantees that no item remains in `PENDING` state upon commitment. |
| **REV-04** | Duplicate Task Handling | **HIGH** | Automatic task deletion risks destroying legitimate user data if duplicates exist. | **Preflight Data Reconciliation Protocol:** Designed a read-only detection query and interactive reconciliation procedure. Unique index creation is strictly sequenced after data reconciliation. |
| **REV-05** | Identity Helper | **MEDIUM** | Fragile JWT claim casting via string GUCs. | **Standardized Helper:** Uses Supabase's native `auth.uid()` and `auth.role()` functions with safe nullability handling. |
| **REV-06** | Relational Tenant Safety | **MEDIUM** | RLS alone on `task_dependencies` allows cross-tenant edges via service role. | **Relational Composite Foreign Keys:** Added candidate key `UNIQUE (id, user_id)` on `tasks`, and composite foreign keys on `task_dependencies` linking `(predecessor_task_id, user_id)` and `(successor_task_id, user_id)`. Mathematically impossible to link another user's task. |
| **REV-07** | Audit-Log Privileges | **SOUND** | RLS policy was hardened, but table grants were not explicitly restricted. | **Privilege Revocation:** Revoked `INSERT`, `UPDATE`, `DELETE` on `audit_logs` from `authenticated`. Only `SECURITY DEFINER` functions and `service_role` can append audit events. Authenticated users are strictly read-only. |

---

## 2. Deep-Dive Remediation Architectures

### 2.1 Enum Migration & Semantic Alignment (REV-01)

#### 2.1.1 Supabase CLI & PostgreSQL Engine Behavior
In Supabase CLI (`supabase db push` / `supabase migration up`), migration scripts are wrapped in a transaction block:
```sql
BEGIN;
-- migration file contents
COMMIT;
```
In PostgreSQL 15+, `ALTER TYPE ... ADD VALUE` is supported within a transaction block, **provided that**:
1. It is not executed inside a subtransaction (e.g., inside an `EXCEPTION` block in PL/pgSQL).
2. The newly added enum value is not referenced by subsequent queries or DML statements *within that same transaction*.

#### 2.1.2 The Semantic Realignment Solution
In `supabase/migrations/001_initial_schema.sql` (Line 14):
```sql
CREATE TYPE capture_status_enum AS ENUM ('RECEIVED', 'TRANSCRIBED', 'PROCESSED', 'FAILED');
```
The application code in `SupabaseRepository.create_capture()` had set `processing_status="COMPLETED"` due to an erroneous comment in `003_schema_alignment.sql#L25`.

**Architectural Decision:**
1. **Primary Fix (Application Alignment):** Update `SupabaseRepository.create_capture()` to use `processing_status: str = "PROCESSED"`. In THOZHI's pipeline, once audio/text has been processed into a proposal, `'PROCESSED'` is the semantically accurate technical status.
2. **Defensive Migration (Additive Safety):** For backwards compatibility with any legacy code that might send `'COMPLETED'`, Migration 004 includes:
   ```sql
   ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';
   ```
   executed directly at the top of the migration file, outside of any PL/pgSQL block.

---

### 2.2 Secure RPC Identity Verification & Caller Role Separation (REV-02)

Inside a PostgreSQL function declared with `SECURITY DEFINER`:
- `current_user` switches to the owner of the function (typically `postgres` or `supabase_admin`).
- `session_user` **remains the role of the connected client** (e.g., `authenticated`, `anon`, `service_role`, or `postgres`).
- PostgREST sets request-scoped GUCs: `request.jwt.claim.role` and `request.jwt.claim.sub`.
- Supabase provides the native security functions `auth.uid()` and `auth.role()`.

#### 2.2.1 Secure Authentication Matrix
```
+------------------+---------------------+-------------------+-----------------------------------------+
| Caller Role      | auth.uid()          | Target p_user_id  | Stored Procedure Action                 |
+------------------+---------------------+-------------------+-----------------------------------------+
| authenticated    | UUID-A              | UUID-A            | ALLOW: Executes as UUID-A               |
| authenticated    | UUID-A              | UUID-B (Spoofed)  | REJECT: 42501 Access Denied             |
| anon             | NULL                | Any UUID          | REJECT: 42501 Authentication Required   |
| service_role     | NULL / Service UUID | Any UUID          | ALLOW: Privileged server-side execution |
| postgres (DBA)   | NULL                | Any UUID          | ALLOW: Direct psql / maintenance        |
| unverified role  | Any                 | Any UUID          | REJECT: 42501 Unauthorized Role         |
+------------------+---------------------+-------------------+-----------------------------------------+
```

#### 2.2.2 Concrete Identity Verification Logic
```sql
DECLARE
    v_caller_role TEXT;
    v_auth_uid UUID;
    v_effective_user_id UUID;
BEGIN
    -- Extract caller context securely
    v_caller_role := COALESCE(
        NULLIF(current_setting('request.jwt.claim.role', true), ''),
        NULLIF(auth.role(), '')
    );
    v_auth_uid := auth.uid();

    -- Enforce role-based identity boundaries
    IF v_caller_role = 'authenticated' THEN
        IF v_auth_uid IS NULL THEN
            RAISE EXCEPTION 'Access denied: authenticated token missing subject' USING ERRCODE = '42501';
        END IF;
        IF v_auth_uid != p_user_id THEN
            RAISE EXCEPTION 'Access denied: caller % cannot approve proposal for user %',
                v_auth_uid, p_user_id USING ERRCODE = '42501';
        END IF;
        v_effective_user_id := v_auth_uid;

    ELSIF v_caller_role = 'service_role' OR session_user = 'postgres' THEN
        -- Explicitly authorized server-side execution
        v_effective_user_id := p_user_id;

    ELSE
        -- Deny anonymous callers, unverified tokens, and unintended roles
        RAISE EXCEPTION 'Access denied: valid user authentication required' USING ERRCODE = '42501';
    END IF;
```

---

### 2.3 Strict Full-Coverage Proposal Item Decisions (REV-03)

To prevent partial commitments where some items become tasks while others linger in `PENDING`, `commit_proposal_atomic` enforces **100% item coverage**:

1. **Lock Proposal and All Items:**
   ```sql
   SELECT * INTO v_proposal FROM proposals WHERE id = p_proposal_id AND user_id = v_effective_user_id FOR UPDATE;
   ```
2. **Item Count & Ownership Verification:**
   The function retrieves all items belonging to the proposal:
   ```sql
   SELECT COUNT(*) INTO v_db_item_count FROM proposal_items WHERE proposal_id = p_proposal_id AND user_id = v_effective_user_id;
   ```
3. **Decisions Array Validation:**
   - The number of decisions in `p_item_decisions` must exactly match `v_db_item_count`.
   - Every `id` in `p_item_decisions` must exist in `proposal_items` for that proposal.
   - Duplicate decision IDs in `p_item_decisions` are rejected using a uniqueness check.
4. **All-or-Nothing Transition:**
   - Approved items become tasks (`tasks.status = 'PENDING'`) and `proposal_items.status = 'APPROVED', decision_state = 'COMMITTED'`.
   - Rejected items become `proposal_items.status = 'REJECTED', decision_state = 'REJECTED'`.
   - Zero items remain in `status = 'PENDING'`.

---

### 2.4 Tenant-Safe Relational Integrity for Task Dependencies (REV-06)

Relying solely on Row-Level Security (RLS) policies leaves a gap if queries are ever executed via the `service_role` (which bypasses RLS).

To guarantee multi-tenant graph isolation at the database engine level:

1. **Candidate Key on Tasks:**
   ```sql
   ALTER TABLE tasks ADD CONSTRAINT uq_tasks_id_user_id UNIQUE (id, user_id);
   ```
2. **Composite Foreign Keys on Task Dependencies:**
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
**Architectural Consequence:** It is physically impossible for a dependency row to reference a predecessor or successor task that does not have the exact same `user_id`. PostgreSQL’s foreign key engine rejects cross-tenant edges even under `BYPASSRLS`.

---

### 2.5 Table Privileges & Audit Trail Immutability (REV-07)

To ensure that `audit_logs` is truly tamper-proof against authenticated users:

1. **Table Level Grants (PostgreSQL Engine Level):**
   ```sql
   REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM authenticated, anon;
   GRANT SELECT ON TABLE audit_logs TO authenticated;
   GRANT ALL ON TABLE audit_logs TO service_role;
   ```
2. **SECURITY DEFINER Append Mechanism:**
   Because `commit_proposal_atomic` is `SECURITY DEFINER`, it executes as the table owner (`postgres`) and can insert audit log entries. An authenticated user interacting directly with PostgREST cannot forge, alter, or delete any audit entry.

---

## 3. Preflight Data Reconciliation Protocol (REV-04)

Before creating the partial unique index `uq_task_source_proposal_item`, the database must be audited for existing duplicate records.

The complete read-only detection queries and reconciliation steps are specified in:
[`research/architecture-audit/22_MIGRATION_PREFLIGHT_AND_DATA_RECONCILIATION.md`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/research/architecture-audit/22_MIGRATION_PREFLIGHT_AND_DATA_RECONCILIATION.md).
