# THOZHI — Database & SQL Migration Audit

## 1. Executive Summary

- **Database Engine:** PostgreSQL 15+ (Supabase Managed PostgreSQL)
- **Current Migrations:**
  - `001_initial_schema.sql` (15 tables, 8 enums, 6 indexes)
  - `002_rls_policies.sql` (RLS policies on 14 tables via `current_user_id()`)
- **Status:** **CRITICAL SCHEMA DRIFT DETECTED**
- **Root Cause:** As THOZHI evolved across Stages 6, 7, 8, 9, and the Recent Capture & Approval Queue overhaul, the Pydantic schemas in `backend/app/schemas/` were expanded with essential fields (`lifecycle_status`, multi-language fields, `full_name`, consent levels), but no subsequent migration (`003_...`) was written to update the PostgreSQL DDL.

---

## 2. Table-by-Table Schema Divergence Analysis

| PostgreSQL Table | Columns in `001_initial_schema.sql` | Missing Columns Required by Backend Schemas | Severity |
|---|---|---|:---:|
| **`captures`** | `id`, `user_id`, `input_type`, `transcript_text`, `detected_language`, `processing_status`, `provider_metadata`, `retention_expires_at`, `created_at` | `lifecycle_status VARCHAR(64) DEFAULT 'PENDING_REVIEW'`, `original_transcript TEXT`, `translated_transcript TEXT`, `proposal_ids UUID[]` | **P0** |
| **`proposals`** | `id`, `user_id`, `capture_id`, `status (enum: DRAFT, PRESENTED, APPROVED, REJECTED, EXPIRED)`, `model_provider`, `model_version`, `created_at`, `expires_at` | `transcript_text TEXT`, `original_transcript TEXT`, `translated_transcript TEXT`, `display_language VARCHAR(32) DEFAULT 'original'`, `translation_status VARCHAR(32) DEFAULT 'ORIGINAL'`, `intent_summary TEXT`, `original_intent_summary TEXT`, `translated_intent_summary TEXT`. Enum `proposal_status_enum` missing `'PROCESSING'`, `'PENDING_REVIEW'`, `'COMMITTED'`, `'FAILED'`, `'ARCHIVED'`. | **P0** |
| **`proposal_items`** | `id`, `proposal_id`, `user_id`, `item_type`, `proposed_title`, `description`, `deadline`, `earliest_start`, `estimated_duration_min`, `duration_source`, `priority`, `confidence`, `uncertainty_flags`, `source_reference`, `status`, `created_at` | `action VARCHAR(255)`, `object VARCHAR(255)`, `original_title TEXT`, `original_description TEXT`, `translated_title TEXT`, `translated_description TEXT`, `intent_confidence FLOAT`, `action_confidence FLOAT`, `object_confidence FLOAT`, `deadline_confidence FLOAT`, `condition_trigger TEXT`, `rejection_reason TEXT`, `decision_state VARCHAR(64) DEFAULT 'PENDING'` | **P0** |
| **`users`** | `id`, `email`, `timezone`, `default_start_time`, `default_end_time`, `created_at`, `updated_at` | `full_name VARCHAR(255)` / `display_name VARCHAR(255)`, `locale VARCHAR(64) DEFAULT 'ta-IN'` | **P1** |
| **`memory_preferences`** | `id`, `user_id`, `preference_key`, `preference_value`, `is_active`, `updated_at` | `category VARCHAR(64) DEFAULT 'WORK_HOURS'`, `description TEXT`, `confidence_score FLOAT DEFAULT 1.0`, `consent_granted BOOLEAN DEFAULT TRUE`, `consent_level VARCHAR(64) DEFAULT 'EXPLICIT_USER'`, `created_at TIMESTAMPTZ DEFAULT NOW()` | **P1** |
| **`tasks`** | `id`, `user_id`, `source_proposal_item_id`, `title`, `description`, `deadline`, `estimated_duration_min`, `priority`, `status`, `completed_at`, `created_at`, `updated_at` | `origin_proposal_id UUID REFERENCES proposals(id)`, `duration_source VARCHAR(64) DEFAULT 'USER_APPROVED'`, `source_language VARCHAR(32)` | **P2** |

---

## 3. Detailed Database Findings

### Finding DB-01: Divergence of `proposal_status_enum` Between SQL and Application
- **Severity:** `P0 — Critical`
- **Exact File Paths:**
  - [`supabase/migrations/001_initial_schema.sql:18-19`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/supabase/migrations/001_initial_schema.sql#L18-L19)
  - [`backend/app/schemas/proposal.py:93`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/schemas/proposal.py#L93)
  - [`backend/app/db/repository.py:166`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/db/repository.py#L166)
- **Evidence:**
  - SQL definition:
    ```sql
    CREATE TYPE proposal_status_enum AS ENUM ('DRAFT', 'PRESENTED', 'APPROVED', 'REJECTED', 'EXPIRED');
    ```
  - Backend runtime lifecycle values:
    `'PROCESSING'`, `'PENDING_REVIEW'`, `'APPROVED'`, `'COMMITTED'`, `'REJECTED'`, `'FAILED'`, `'ARCHIVED'`.
- **Actual Problem:**
  - If Supabase PostgreSQL is connected, inserting a proposal with `status="PENDING_REVIEW"` or updating to `status="COMMITTED"` will throw PostgreSQL error `22P02: invalid input value for enum proposal_status_enum`.
- **Recommended Correction:**
  - Update `proposal_status_enum` or convert column to `VARCHAR(64)` with check constraint to permit modern lifecycle states:
    ```sql
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PROCESSING';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PENDING_REVIEW';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'COMMITTED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'FAILED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'ARCHIVED';
    ```
- **Code Change Necessary:** Yes (requires new migration file).

---

### Finding DB-02: Missing Capture Lifecycle & Multi-Language Fields in `captures` Table
- **Severity:** `P0 — Critical`
- **Exact File Paths:**
  - [`supabase/migrations/001_initial_schema.sql:56-66`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/supabase/migrations/001_initial_schema.sql#L56-L66)
  - [`backend/app/schemas/capture.py:12-25`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/backend/app/schemas/capture.py#L12-L25)
- **Evidence:** Backend `CaptureResponse` requires `lifecycle_status`, `original_transcript`, and `translated_transcript`. None of these exist in the SQL DDL for `captures`.
- **Actual Problem:** Any attempt by a Supabase persistence layer to insert or query `Capture` records will fail.
- **Recommended Correction:** Add columns to `captures` table in migration `003_schema_alignment.sql`:
  ```sql
  ALTER TABLE captures ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(64) DEFAULT 'PENDING_REVIEW' NOT NULL;
  ALTER TABLE captures ADD COLUMN IF NOT EXISTS original_transcript TEXT;
  ALTER TABLE captures ADD COLUMN IF NOT EXISTS translated_transcript TEXT;
  ALTER TABLE captures ADD COLUMN IF NOT EXISTS proposal_ids UUID[] DEFAULT '{}'::UUID[];
  ```
- **Code Change Necessary:** Yes (new migration).

---

### Finding DB-03: Missing Index on `captures.lifecycle_status` & `proposals.status`
- **Severity:** `P1 — High`
- **Exact File Path:** [`supabase/migrations/001_initial_schema.sql:213-219`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/supabase/migrations/001_initial_schema.sql#L213-L219)
- **Evidence:** `001_initial_schema.sql` only creates `idx_captures_user_created ON captures(user_id, created_at DESC)`.
- **Actual Problem:** Queries filtering by `lifecycle_status = 'PENDING_REVIEW'` (used on every visit to `/capture` and `/`) will perform sequential scans on `captures`.
- **Recommended Correction:**
  ```sql
  CREATE INDEX IF NOT EXISTS idx_captures_user_lifecycle ON captures(user_id, lifecycle_status, created_at DESC);
  CREATE INDEX IF NOT EXISTS idx_proposals_user_status_created ON proposals(user_id, status, created_at DESC);
  ```
- **Code Change Necessary:** Yes (in migration 003).

---

### Finding DB-04: Row Level Security (RLS) Policy Audit
- **Severity:** `INFO — Verified Compliant`
- **Exact File Path:** [`supabase/migrations/002_rls_policies.sql`](file:///c:/Users/moham/OneDrive%20-%20ELCOT/Projects/Thozhi/supabase/migrations/002_rls_policies.sql)
- **Audit Assessment:** All 14 tables have RLS enabled and enforce `USING (user_id = current_user_id())`. `plan_items` correctly verifies parent ownership via `EXISTS (SELECT 1 FROM plans WHERE ...)`.
- **Recommendation:** When new tables or views are added, ensure RLS is enabled by default.
