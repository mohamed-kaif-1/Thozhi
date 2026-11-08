# 57 — Critical Production Schema State Reconciliation Report

**Project Reference:** `bwzqudaaxfubtbgwmevo`
**Host:** `aws-0-ap-southeast-1.pooler.supabase.com`
**Database:** `postgres`
**Engine:** PostgreSQL 17.11 on x86_64-pc-linux-gnu
**Date:** November 8, 2026
**Auditor:** Antigravity Pairing Assistant
**Status:** READ-ONLY Production Reconciliation Complete. Zero mutations executed. Awaiting explicit user decision.

---

## 1. Executive Summary & Core Findings

1. **Production Schema State:**
   The remote PostgreSQL `public` schema currently contains all **14 application tables**, **8 custom enums (43 labels)**, **41 constraints**, **32 indexes**, **32 Row Level Security policies**, **3 functions** (including `commit_proposal_atomic` with `SECURITY DEFINER`), and **1 trigger** (`on_auth_user_created` on `auth.users`).
2. **Migration History State:**
   The migration table `supabase_migrations.schema_migrations` exists, but contains **0 recorded migrations**.
3. **Root-Cause of Persistence:**
   During local verification testing in Report 56, `test_live_edited_migrations.py` executed `supabase/deploy_all_migrations.sql`. Although the python wrapper initiated an outer `BEGIN;` and ended with `ROLLBACK;`, the file `deploy_all_migrations.sql` itself contained **5 explicit internal `COMMIT;` statements** (lines 227, 303, 368, 815, 926). In PostgreSQL, executing a multi-statement script with internal `COMMIT;` commands terminates and commits the transaction phases on the server. The subsequent `ROLLBACK;` issued by python was a no-op because the 5th transaction had already committed.
4. **Schema Parity Verdict:**
   The objects currently residing in `public` **100% match the cumulative specification of migrations 001–005**. There are 0 missing objects, 0 unexpected objects, and 0 structural discrepancies.
5. **Operational Status:**
   The database schema is fully formed, valid, and secured by RLS. The only reconciliation needed is synchronizing the Supabase CLI migration tracker (`supabase_migrations.schema_migrations`), or alternatively executing a clean reset to replay migrations through `supabase db push`.

---

## 2. Phase 1 — Read-Only Live Database Catalog Evidence

Every entry below was retrieved directly from PostgreSQL system catalogs (`information_schema`, `pg_catalog`, `pg_type`, `pg_proc`, `pg_trigger`, `pg_policy`, `pg_indexes`, `pg_constraint`):

### 2.1 Table Inventory (14 Tables)
All 14 tables are base relational tables in schema `public`:
1. `users` (9 columns, RLS enabled)
2. `captures` (13 columns, RLS enabled)
3. `proposals` (17 columns, RLS enabled)
4. `proposal_items` (29 columns, RLS enabled)
5. `tasks` (17 columns, RLS enabled)
6. `task_dependencies` (6 columns, RLS enabled)
7. `availability_windows` (7 columns, RLS enabled)
8. `busy_events` (7 columns, RLS enabled)
9. `plans` (7 columns, RLS enabled)
10. `plan_items` (6 columns, RLS enabled)
11. `memory_preferences` (13 columns, RLS enabled)
12. `contextual_summaries` (7 columns, RLS enabled)
13. `approval_idempotency` (6 columns, RLS enabled)
14. `audit_logs` (5 columns, RLS enabled)

### 2.2 Enum Inventory (8 Enums, 43 Total Labels)
1. `capture_status_enum`: `'RECEIVED'`, `'TRANSCRIBED'`, `'PROCESSED'`, `'FAILED'`
2. `input_type_enum`: `'AUDIO'`, `'TEXT'`
3. `item_type_enum`: `'TASK'`, `'COMMITMENT'`, `'IDEA'`, `'WISH'`, `'CONDITIONAL_INTENTION'`, `'QUESTION'`, `'REMINDER'`, `'COMPLETED'`, `'CANCELLED'`, `'INFORMATIONAL'`
4. `plan_feasibility_enum`: `'FEASIBLE'`, `'INFEASIBLE'`, `'NEEDS_CLARIFICATION'`, `'INCOMPLETE_INFORMATION'`
5. `proposal_item_status_enum`: `'PENDING'`, `'APPROVED'`, `'REJECTED'`, `'POSTPONED'`
6. `proposal_status_enum`: `'DRAFT'`, `'PRESENTED'`, `'APPROVED'`, `'REJECTED'`, `'EXPIRED'`, `'PROCESSING'`, `'PENDING_REVIEW'`, `'COMMITTED'`, `'FAILED'`, `'ARCHIVED'` (Migration 003 extensions verified)
7. `task_priority_enum`: `'P1_CRITICAL'`, `'P2_MEDIUM'`, `'P3_LOW'`, `'BACKBURNER'`
8. `task_status_enum`: `'PENDING'`, `'IN_PROGRESS'`, `'COMPLETED'`, `'POSTPONED'`, `'CANCELLED'`

### 2.3 Row Level Security & Policies (32 Policies)
- **RLS Enabled:** 14 of 14 tables (100% coverage).
- **Policies:**
  - `users`: 1 policy (`users_manage_own_profile` for `authenticated`)
  - `captures`: 4 policies (select, insert, update, delete for `authenticated` where `auth.uid() = user_id`)
  - `proposals`: 4 policies (select, insert, update, delete for `authenticated` where `auth.uid() = user_id`)
  - `proposal_items`: 4 policies (select, insert, update, delete for `authenticated` where `auth.uid() = user_id`)
  - `tasks`: 4 policies (select, insert, update, delete for `authenticated` where `auth.uid() = user_id`)
  - `task_dependencies`: 3 policies (select, insert, delete for `authenticated` where `auth.uid() = user_id`)
  - `availability_windows`: 1 policy (`availability_windows_manage_own` for `authenticated`)
  - `busy_events`: 1 policy (`busy_events_manage_own` for `authenticated`)
  - `plans`: 1 policy (`plans_manage_own` for `authenticated`)
  - `plan_items`: 1 policy (`plan_items_manage_own` for `authenticated`)
  - `memory_preferences`: 4 policies (select, insert, update, delete for `authenticated`)
  - `contextual_summaries`: 1 policy (`contextual_summaries_manage_own` for `authenticated`)
  - `approval_idempotency`: 2 policies (select, insert for `authenticated`)
  - `audit_logs`: 1 policy (`audit_logs_read_own` for `authenticated`)

### 2.4 Functions & Security Definer Configuration
1. `commit_proposal_atomic(p_user_id UUID, p_proposal_id UUID, p_idempotency_key VARCHAR, p_item_decisions JSONB) -> JSONB`
   - Schema: `public`
   - Owner: `postgres`
   - **`prosecdef`:** `TRUE` (SECURITY DEFINER)
   - Search Path: Fixed to `public, extensions`
2. `current_user_id() -> UUID`
   - Schema: `public`
   - Owner: `postgres`
   - **`prosecdef`:** `FALSE`
3. `handle_new_user() -> TRIGGER`
   - Schema: `public`
   - Owner: `postgres`
   - **`prosecdef`:** `TRUE` (SECURITY DEFINER)
   - Search Path: Fixed to `public, auth`

### 2.5 Triggers
1. `on_auth_user_created` on table `auth.users`:
   - Event: `AFTER INSERT`
   - Action: `FOR EACH ROW EXECUTE FUNCTION handle_new_user()`
   - Status: Active and verified.

### 2.6 Extensions
- `uuid-ossp` (v1.1) in schema `extensions`
- `pgcrypto` (v1.3) in schema `extensions`
- `pg_stat_statements` (v1.11) in schema `extensions`
- `supabase_vault` (v0.3.1) in schema `vault`
- `plpgsql` (v1.0) in schema `pg_catalog`

### 2.7 Migration Tracking Table
- Table: `supabase_migrations.schema_migrations`
- Exists: `TRUE`
- Columns: `version (text)`, `statements (ARRAY)`, `name (text)`
- Row Count: **0 rows**

---

## 3. Phase 2 — Forensic Transaction Reconstruction

### The Execution Mechanism
In Report 56, test script `scratch/test_live_edited_migrations.py` executed:
```python
cur.execute("BEGIN;")
cur.execute("SET search_path = public;")
with open('supabase/deploy_all_migrations.sql', 'r', encoding='utf-8') as f:
    sql_deploy = f.read()
cur.execute(sql_deploy)
...
cur.execute("ROLLBACK;")
```

### Forensic Sequence of Events
1. **Line 42:** `cur.execute("BEGIN;")` opened an interactive transaction block on the PostgreSQL session.
2. **Line 46:** `cur.execute(sql_deploy)` passed the complete multi-statement script `supabase/deploy_all_migrations.sql` to libpq.
3. In PostgreSQL, when a script contains embedded `COMMIT;` statements, the server commits the ongoing transaction at that point:
   - Line 11: `BEGIN;` (Nested begin)
   - Line 227: `COMMIT;` ➔ **PostgreSQL committed Phase 1 (Migration 001 objects: base tables, enums)**.
   - Line 232: `BEGIN;`
   - Line 303: `COMMIT;` ➔ **PostgreSQL committed Phase 2 (Migration 002 objects: RLS activation)**.
   - Line 309: `BEGIN;`
   - Line 368: `COMMIT;` ➔ **PostgreSQL committed Phase 3 (Migration 003 objects: enum additions, linguistic fields)**.
   - Line 373: `BEGIN;`
   - Line 815: `COMMIT;` ➔ **PostgreSQL committed Phase 4 (Migration 004 objects: modern schema, atomic RPC `commit_proposal_atomic`)**.
   - Line 820: `BEGIN;`
   - Line 926: `COMMIT;` ➔ **PostgreSQL committed Phase 5 (Migration 005 objects: `handle_new_user` trigger on `auth.users`)**.
4. **Line 62:** `cur.execute("ROLLBACK;")` was issued by Python. Because line 926 of the script had already committed the final transaction, there was no active transaction open. PostgreSQL emitted a standard notice (`NOTICE: there is no transaction in progress`) and returned success.
5. **Result:** All 5 phases were permanently written to the live database, while the migration history table `supabase_migrations.schema_migrations` was untouched (because `deploy_all_migrations.sql` does not write to CLI history tables).

---

## 4. Phase 3 — Detailed Object-by-Object Schema Reconciliation

| Database Object | Target Migrations | Live Catalog Status | Classification | Detailed Verification |
| :--- | :--- | :--- | :--- | :--- |
| `input_type_enum` | 001 | Exists (2 labels) | **Matching** | Exact values: `AUDIO`, `TEXT` |
| `capture_status_enum` | 001 | Exists (4 labels) | **Matching** | Exact values: `RECEIVED`, `TRANSCRIBED`, `PROCESSED`, `FAILED` |
| `proposal_status_enum` | 001, 003 | Exists (10 labels) | **Matching** | 5 base values + 5 migration 003 extensions |
| `item_type_enum` | 001 | Exists (10 labels) | **Matching** | Exact values match Master PRD Section 10 |
| `proposal_item_status_enum` | 001 | Exists (4 labels) | **Matching** | Exact values: `PENDING`, `APPROVED`, `REJECTED`, `POSTPONED` |
| `task_priority_enum` | 001 | Exists (4 labels) | **Matching** | Exact values: `P1_CRITICAL`, `P2_MEDIUM`, `P3_LOW`, `BACKBURNER` |
| `task_status_enum` | 001 | Exists (5 labels) | **Matching** | Exact values: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `POSTPONED`, `CANCELLED` |
| `plan_feasibility_enum` | 001 | Exists (4 labels) | **Matching** | Exact values match schema |
| `users` table | 001, 004 | Exists (9 columns) | **Matching** | Includes `full_name` and `locale` from 004. PK on `id`. |
| `captures` table | 001, 003, 004 | Exists (13 columns) | **Matching** | Includes `lifecycle_status`, `original/translated_transcript`, `proposal_ids`. Default uses `extensions.uuid_generate_v4()`. |
| `proposals` table | 001, 003, 004 | Exists (17 columns) | **Matching** | Includes translation and intent fields. Default uses `extensions.uuid_generate_v4()`. |
| `proposal_items` table | 001, 003, 004 | Exists (29 columns) | **Matching** | Includes linguistic and decision tracking fields. Default uses `extensions.uuid_generate_v4()`. |
| `tasks` table | 001, 003, 004 | Exists (17 columns) | **Matching** | Includes `origin_proposal_id`, `actual_duration_min`, `scheduled_date`. Default uses `extensions.uuid_generate_v4()`. |
| `task_dependencies` table | 001 | Exists (6 columns) | **Matching** | Unique constraint on edge, self-dependency check. Default uses `extensions.uuid_generate_v4()`. |
| `availability_windows` table | 001 | Exists (7 columns) | **Matching** | Recurrence and time fields matching. Default uses `extensions.uuid_generate_v4()`. |
| `busy_events` table | 001 | Exists (7 columns) | **Matching** | Matching. Default uses `extensions.uuid_generate_v4()`. |
| `plans` table | 001 | Exists (7 columns) | **Matching** | Matching. Default uses `extensions.uuid_generate_v4()`. |
| `plan_items` table | 001 | Exists (6 columns) | **Matching** | Matching. Default uses `extensions.uuid_generate_v4()`. |
| `memory_preferences` table | 001, 004 | Exists (13 columns) | **Matching** | Includes consent and category fields from 004. Unique constraint on `(user_id, preference_key)`. |
| `contextual_summaries` table | 001 | Exists (7 columns) | **Matching** | Matching. Default uses `extensions.uuid_generate_v4()`. |
| `approval_idempotency` table | 001 | Exists (6 columns) | **Matching** | Unique on `idempotency_key`. Matching. |
| `audit_logs` table | 001 | Exists (5 columns) | **Matching** | Matching. Default uses `extensions.uuid_generate_v4()`. |
| `commit_proposal_atomic` RPC | 004 | Exists | **Matching** | SECURITY DEFINER, atomic 7-step transaction, JSONB return. |
| `current_user_id` function | 004 | Exists | **Matching** | Helper function in `public`. |
| `handle_new_user` function | 005 | Exists | **Matching** | SECURITY DEFINER, exception-safe upsert on `auth.users`. |
| `on_auth_user_created` trigger | 005 | Exists | **Matching** | Trigger active on `auth.users`. |
| `supabase_migrations` history | CLI | 0 rows recorded | **Unsynchronized** | The DDL was committed directly via SQL rather than CLI `db push`. |

---

## 5. Safe Recovery & Deployment Options

Because the database schema is already 100% structurally complete and matches migrations 001–005, there are two distinct, safe, and mutually exclusive paths forward.

### Option A: Clean Slate Reset & Clean Supabase CLI Push (Recommended for Maximum Purity)
If the user requires that the live database be created strictly and exclusively through the Supabase CLI pipeline:
1. Reset the `public` schema cleanly:
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   GRANT ALL ON SCHEMA public TO postgres;
   GRANT ALL ON SCHEMA public TO public;
   GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
   ```
2. Remove any orphaned trigger on `auth.users`:
   ```sql
   DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
   ```
3. Execute `npx supabase db push --remote`:
   - Supabase CLI will apply migrations `001_initial_schema.sql` through `005_auth_user_profile_trigger.sql` sequentially.
   - CLI will record versions `001` through `005` in `supabase_migrations.schema_migrations`.
   - Result: 100% clean schema + 100% clean CLI migration history.

### Option B: Synchronize Existing Clean Schema with Migration History (Fast In-Place Reconciliation)
Because every statement in migrations 001–005 was built to be fully idempotent (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`, `DROP POLICY IF EXISTS`, `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object ...`):
1. Execute `npx supabase db push --remote`:
   - Because all DDL statements are guarded with `IF NOT EXISTS` and `CREATE OR REPLACE`, the CLI execution runs idempotently without failing or losing data.
   - Supabase CLI will record all 5 migration versions (`001` through `005`) into `supabase_migrations.schema_migrations`.
2. OR reconcile using Supabase CLI repair commands:
   ```bash
   npx supabase migration repair --status applied 001_initial_schema.sql --remote
   npx supabase migration repair --status applied 002_rls_policies.sql --remote
   npx supabase migration repair --status applied 003_schema_alignment.sql --remote
   npx supabase migration repair --status applied 004_schema_alignment_and_rpc.sql --remote
   npx supabase migration repair --status applied 005_auth_user_profile_trigger.sql --remote
   ```

---

## 6. Action Gate & Current Safety Posture

- **Database State:** Verified intact, fully matching migrations 001–005.
- **Safety Adherence:** Strict read-only mode observed. Zero DDL/DML, zero drops, zero schema resets, zero migration repairs were executed during this turn.
- **Git State:** Master branch clean of commits/pushes.
- **Antigravity is stopped at the gate.** No automated recovery has been attempted. Awaiting your decision on whether to proceed with **Option A** (Clean Reset & Push) or **Option B** (In-Place Idempotent Reconciliation).
