# 58 — Safe Supabase Migration History Repair Preparation

**Project Reference:** `bwzqudaaxfubtbgwmevo`
**Host:** `aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres` (PostgreSQL 17.11)
**Date:** November 8, 2026
**Status:** **PREPARATION ONLY** (Zero remote repairs or mutations executed; holding at final approval gate)

---

## 1. Executive Summary

A comprehensive read-only audit of the production Supabase database confirmed that the live `public` schema already embodies 100% of the cumulative structural, linguistic, security, RPC, and trigger specifications defined in migrations `001` through `005`.

However, because the DDL was established via direct PostgreSQL connection during the dry-run/transactional testing of `deploy_all_migrations.sql`, the Supabase CLI internal migration tracker `supabase_migrations.schema_migrations` currently contains **0 records**.

This document outlines the exact, safe procedure to perform **in-place migration history reconciliation** using `npx supabase migration repair --status applied`. This operation:
- Updates strictly metadata in `supabase_migrations.schema_migrations`.
- **Executes ZERO migration SQL or DDL against public tables**.
- Synchronizes the Supabase CLI so that future `db push` or migration audits recognize the project as fully up to date.

---

## 2. CLI Help & Command Syntax Analysis

Invoking `npx supabase migration repair --help` on Supabase CLI v3.0.0 yields:

```text
DESCRIPTION
  Repair the migration history table.

TARGET
  Local by default. Pass --remote for the linked project, or --remote=<ref|branch|url>.

USAGE
  supabase migration repair [flags] [<version...>]

ARGUMENTS
  version... string    Migration version(s) to repair. (optional)

FLAGS
  --status choice                Version status to update. (choices: applied, reverted)
  --remote[=<ref|branch|url>]    Target a remote database: the linked project, or --remote=<ref|branch|url>.
  --password, -p string          Database password for the project selected with --remote.
```

### Key Technical Properties
1. **Target Table:** Only touches `supabase_migrations.schema_migrations`.
2. **Behavior under `--status applied`:** Inserts the specified migration version(s) into the history table without reading or running the SQL files.
3. **Arguments:** Accepts one or more version strings (`<version...>`).

---

## 3. Version Mapping & Verification Evidence

Querying the live remote project with `npx supabase migration list --remote` produced the following ground-truth JSON output:

```json
{
  "migrations": [
    {"local": "001", "remote": "", "time": "001"},
    {"local": "002", "remote": "", "time": "002"},
    {"local": "003", "remote": "", "time": "003"},
    {"local": "004", "remote": "", "time": "004"},
    {"local": "005", "remote": "", "time": "005"}
  ],
  "message": "Migrations listed",
  "target": {
    "kind": "linked",
    "project_ref": "bwzqudaaxfubtbgwmevo",
    "project_name": "mohamedkaif.sa@gmail.com's Project",
    "environment": "production"
  }
}
```

### Version Mapping Table
| Local File Name | Supabase Version Identifier | Remote Status in Tracker | Target Repair Status |
| :--- | :-: | :-: | :-: |
| `supabase/migrations/001_initial_schema.sql` | `001` | Unrecorded (`""`) | `applied` |
| `supabase/migrations/002_rls_policies.sql` | `002` | Unrecorded (`""`) | `applied` |
| `supabase/migrations/003_schema_alignment.sql` | `003` | Unrecorded (`""`) | `applied` |
| `supabase/migrations/004_schema_alignment_and_rpc.sql` | `004` | Unrecorded (`""`) | `applied` |
| `supabase/migrations/005_auth_user_profile_trigger.sql` | `005` | Unrecorded (`""`) | `applied` |

---

## 4. Live Production Schema Verification Summary

Direct read-only catalog queries confirmed the live presence and integrity of all cumulative objects:

1. **Base Tables (Migration 001):** 14 of 14 tables present (`users`, `captures`, `proposals`, `proposal_items`, `tasks`, `task_dependencies`, `availability_windows`, `busy_events`, `plans`, `plan_items`, `memory_preferences`, `contextual_summaries`, `approval_idempotency`, `audit_logs`).
2. **Row Level Security (Migration 002):** Active on all 14 tables (`rowsecurity = true`) with 32 strict tenant-isolation policies.
3. **Enums & Linguistic Fields (Migration 003):** All 5 modern `proposal_status_enum` extensions (`PROCESSING`, `PENDING_REVIEW`, `COMMITTED`, `FAILED`, `ARCHIVED`) present; linguistic/translation columns present across `captures`, `proposals`, `proposal_items`, and `tasks`.
4. **Modern Schema & Atomic RPC (Migration 004):** `commit_proposal_atomic` RPC installed as `SECURITY DEFINER` with fixed search_path `public, extensions`; `memory_preferences` consent/category columns and unique constraint present.
5. **Auth Trigger (Migration 005):** `handle_new_user` function installed as `SECURITY DEFINER`; trigger `on_auth_user_created` active on `auth.users`.
6. **UUID Resolution:** All 13 table primary key defaults resolve through `extensions.uuid_generate_v4()`.

---

## 5. Migration History Table State

Direct catalog query against `supabase_migrations.schema_migrations`:
- **Table exists:** `TRUE`
- **Columns:**
  - `version (text, NOT NULL, PRIMARY KEY)`
  - `statements (ARRAY / text[], NULLABLE)`
  - `name (text, NULLABLE)`
- **Current Row Count:** **0**
- **Conflicting or Corrupted Entries:** **0**

---

## 6. Exact CLI Repair Commands Prepared

Once authorized, the migration history table will be repaired using either of the following commands:

### Consolidated Single Command:
```bash
npx supabase migration repair --status applied 001 002 003 004 005 --remote
```

### Sequential Per-Version Commands (Alternative):
```bash
npx supabase migration repair --status applied 001 --remote
npx supabase migration repair --status applied 002 --remote
npx supabase migration repair --status applied 003 --remote
npx supabase migration repair --status applied 004 --remote
npx supabase migration repair --status applied 005 --remote
```

*Authentication environment: `SUPABASE_ACCESS_TOKEN` and `SUPABASE_DB_PASSWORD` exported in execution subshell.*

---

## 7. Expected Changes from Repair

1. **In `supabase_migrations.schema_migrations`:** 5 records will be inserted corresponding to versions `001`, `002`, `003`, `004`, and `005`.
2. **In `public` schema:** **0 changes** (no tables, rows, columns, or policies modified).
3. **In `npx supabase migration list --remote`:** All 5 migrations will display with status `remote: "001"`, `remote: "002"`, etc.
4. **In `npx supabase db push --remote`:** Will report `Already up to date` without attempting to execute DDL.

---

## 8. Risks & Rollback Considerations

- **Risk of Data Loss:** **Zero**. `migration repair` does not execute DDL or DML against application tables.
- **Rollback Procedure:** If needed, any or all versions can be reverted in the migration tracker using:
  ```bash
  npx supabase migration repair --status reverted 001 002 003 004 005 --remote
  ```
  which cleanly deletes the entries from `supabase_migrations.schema_migrations` without touching any tables.

---

## 9. Final Safety Confirmation

- **No remote changes were made during this turn.**
- **No repair command was executed.**
- **No Git commits or pushes were made.**
- **Antigravity is holding at the gate awaiting your explicit approval to execute the repair.**
