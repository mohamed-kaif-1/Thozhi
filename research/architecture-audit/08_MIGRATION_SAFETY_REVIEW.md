# 08 — MIGRATION SAFETY AND DATA PROVENANCE REVIEW

**Document:** MIGRATION SAFETY & PROVENANCE SPECIFICATION
**Migration Target:** `supabase/migrations/003_schema_alignment.sql` (v3.1.0)
**Author:** PostgreSQL Database Architect & Security Auditor
**Date:** 2026-11-08
**Status:** APPROVED FOR STAGING / LIVE DRY-RUN

---

## 1. Migration Baseline & Status

### 1.1 Local vs. Remote State
- **Migration 001 (`001_initial_schema.sql`):** Establishes base 14 tables, enums, foreign keys, and indexes. Fully declared in local repository.
- **Migration 002 (`002_rls_policies.sql`):** Enables RLS and attaches row policies using `current_setting('request.jwt.claim.sub', true)::UUID`. Fully declared in local repository.
- **Migration 003 (`003_schema_alignment.sql`):** Newly created alignment migration. **Not yet applied to any remote or live Supabase database.**
- **Verification Note:** Live Supabase database credentials are not connected in CI/test environments; live application status is pending human review and explicit authorization.

---

## 2. Detailed Schema Diff (Migration 001/002 vs. Rectified 003)

| Table | Column Added | Type | Old (Draft 003) | Rectified (v3.1.0) | Rationale & Safety Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `users` | `locale` | `VARCHAR(64)` | `DEFAULT 'ta-IN' NOT NULL` | `NULL` (nullable) | Eliminates forced language assumption on users without evidence. |
| `tasks` | `duration_source` | `VARCHAR(64)` | `DEFAULT 'USER_APPROVED' NOT NULL` | `DEFAULT 'UNSPECIFIED' NOT NULL` | Prevents fabricating that historical task durations were verified by humans. |
| `memory_preferences` | `consent_granted` | `BOOLEAN` | `DEFAULT TRUE NOT NULL` | `DEFAULT NULL` | Distinguishes unrecorded consent (`NULL`) from granted (`TRUE`) or withdrawn (`FALSE`). |
| `memory_preferences` | `consent_level` | `VARCHAR(64)` | `DEFAULT 'EXPLICIT_USER' NOT NULL` | `DEFAULT 'UNKNOWN' NOT NULL` | Requires deliberate user action before recording explicit user consent. |
| `memory_preferences` | `consent_status` | `VARCHAR(64)` | *(Not present)* | `DEFAULT 'UNCONFIRMED' NOT NULL` | Explicit state machine: `'NOT_RECORDED'`, `'UNCONFIRMED'`, `'GRANTED'`, `'WITHDRAWN'`. |
| `captures` | `lifecycle_status` | `VARCHAR(64)` | `DEFAULT 'PENDING_REVIEW' NOT NULL` | `DEFAULT 'PENDING_REVIEW' NOT NULL` | Tracks human approval lifecycle; decoupled from technical `processing_status`. |
| `proposals` | translation fields | `TEXT` | `original_transcript`, etc. | Retained | Supports display language switching without destructive reprocessing. |
| `proposal_items` | linguistic fields | `VARCHAR/TEXT` | `action`, `object`, etc. | Retained | Persists semantic deconstruction (SOV) for human inspection and editing. |

---

## 3. Backfill Strategy for Pre-Existing Records

When applying migration 003 to an existing database with historical records:

```sql
-- 1. Tasks: Mark existing tasks with unknown duration source as LEGACY_UNSPECIFIED
UPDATE tasks
SET duration_source = 'LEGACY_UNSPECIFIED'
WHERE duration_source = 'UNSPECIFIED' AND created_at < NOW();

-- 2. Memory Preferences: Ensure historical preferences are marked UNCONFIRMED
UPDATE memory_preferences
SET consent_status = 'UNCONFIRMED', consent_level = 'UNKNOWN', consent_granted = NULL
WHERE consent_status IS NULL OR consent_status = 'UNCONFIRMED';

-- 3. Users: Leave locale as NULL so the frontend onboarding prompts for preference
UPDATE users
SET locale = NULL
WHERE locale = 'ta-IN' AND id NOT IN (
    SELECT user_id FROM memory_preferences WHERE preference_key = 'preferred_locale'
);
```

---

## 4. Rollback Plan

All statements in `003_schema_alignment.sql` are purely additive (`ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). If a rollback is ever mandated:

```sql
-- DOWN MIGRATION (003 Rollback):
DROP INDEX IF EXISTS idx_memory_prefs_consent;
DROP INDEX IF EXISTS idx_memory_prefs_user_cat;
DROP INDEX IF EXISTS idx_tasks_user_status;
DROP INDEX IF EXISTS idx_proposals_user_status_created;
DROP INDEX IF EXISTS idx_captures_user_lifecycle;

ALTER TABLE memory_preferences
    DROP COLUMN IF EXISTS consent_status,
    DROP COLUMN IF EXISTS consent_level,
    DROP COLUMN IF EXISTS consent_granted,
    DROP COLUMN IF EXISTS confidence_score,
    DROP COLUMN IF EXISTS description,
    DROP COLUMN IF EXISTS category;

ALTER TABLE tasks
    DROP COLUMN IF EXISTS source_language,
    DROP COLUMN IF EXISTS duration_source,
    DROP COLUMN IF EXISTS origin_proposal_id;

ALTER TABLE proposal_items
    DROP COLUMN IF EXISTS decision_state,
    DROP COLUMN IF EXISTS rejection_reason,
    DROP COLUMN IF EXISTS condition_trigger,
    DROP COLUMN IF EXISTS deadline_confidence,
    DROP COLUMN IF EXISTS object_confidence,
    DROP COLUMN IF EXISTS action_confidence,
    DROP COLUMN IF EXISTS intent_confidence,
    DROP COLUMN IF EXISTS translated_description,
    DROP COLUMN IF EXISTS translated_title,
    DROP COLUMN IF EXISTS original_description,
    DROP COLUMN IF EXISTS original_title,
    DROP COLUMN IF EXISTS object,
    DROP COLUMN IF EXISTS action;

ALTER TABLE proposals
    DROP COLUMN IF EXISTS translated_intent_summary,
    DROP COLUMN IF EXISTS original_intent_summary,
    DROP COLUMN IF EXISTS intent_summary,
    DROP COLUMN IF EXISTS translation_status,
    DROP COLUMN IF EXISTS display_language,
    DROP COLUMN IF EXISTS translated_transcript,
    DROP COLUMN IF EXISTS original_transcript,
    DROP COLUMN IF EXISTS transcript_text;

ALTER TABLE captures
    DROP COLUMN IF EXISTS proposal_ids,
    DROP COLUMN IF EXISTS translated_transcript,
    DROP COLUMN IF EXISTS original_transcript,
    DROP COLUMN IF EXISTS lifecycle_status;

ALTER TABLE users
    DROP COLUMN IF EXISTS locale,
    DROP COLUMN IF EXISTS full_name;
```

---

## 5. Unresolved Risks & Operational Guardrails

1. **Transaction Isolation:** In PostgreSQL, adding values to an enum (`ALTER TYPE ... ADD VALUE`) cannot be rolled back inside a transaction block if subsequent statements fail. Therefore, the enum extension is isolated in a standalone block.
2. **PostgREST Schema Cache Reload:** After applying migration 003, PostgREST must be instructed to reload its schema cache via `NOTIFY pgrst, 'reload schema'` or by restarting the Supabase container, otherwise newly added columns will return HTTP 400 `Column not found in schema cache`.
3. **Sovereignty Invariant:** No background process may automatically flip `consent_granted` to `TRUE`. Only an authenticated HTTP request from the user's session with explicit consent payloads may update `consent_granted = TRUE`.
