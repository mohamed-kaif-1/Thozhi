-- ====================================================================
-- THOZHI MASTER CLOUD DEPLOYMENT SCRIPT: MIGRATIONS 001 THROUGH 005
-- Target Supabase Project: bwzqudaaxfubtbgwmevo
-- Version: 5.1.0 (Production Consolidated Idempotent Deployment Script)
-- Invariant: "The AI proposes. The user decides."
-- ====================================================================

-- --------------------------------------------------------------------
-- PHASE 1: MIGRATION 001 — INITIAL SCHEMA & BASE ENTITIES
-- --------------------------------------------------------------------
BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;

-- 1. ENUMS (Idempotent creation via exception handling)
DO $$ BEGIN
    CREATE TYPE input_type_enum AS ENUM ('AUDIO', 'TEXT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE capture_status_enum AS ENUM ('RECEIVED', 'TRANSCRIBED', 'PROCESSED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE proposal_status_enum AS ENUM ('DRAFT', 'PRESENTED', 'APPROVED', 'REJECTED', 'EXPIRED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE item_type_enum AS ENUM (
        'TASK', 'COMMITMENT', 'IDEA', 'WISH', 'CONDITIONAL_INTENTION',
        'QUESTION', 'REMINDER', 'COMPLETED', 'CANCELLED', 'INFORMATIONAL'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE proposal_item_status_enum AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'POSTPONED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE task_priority_enum AS ENUM ('P1_CRITICAL', 'P2_MEDIUM', 'P3_LOW', 'BACKBURNER');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE task_status_enum AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'POSTPONED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE plan_feasibility_enum AS ENUM ('FEASIBLE', 'INFEASIBLE', 'NEEDS_CLARIFICATION', 'INCOMPLETE_INFORMATION');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 2. USERS / PROFILES
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(64) DEFAULT 'Asia/Kolkata' NOT NULL,
    default_start_time TIME DEFAULT '09:00:00' NOT NULL,
    default_end_time TIME DEFAULT '18:00:00' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 3. CAPTURES
CREATE TABLE IF NOT EXISTS captures (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    input_type input_type_enum NOT NULL,
    transcript_text TEXT NOT NULL,
    detected_language VARCHAR(64) DEFAULT 'Tanglish' NOT NULL,
    processing_status capture_status_enum DEFAULT 'RECEIVED' NOT NULL,
    provider_metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
    retention_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 4. PROPOSALS
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    capture_id UUID REFERENCES captures(id) ON DELETE SET NULL,
    status proposal_status_enum DEFAULT 'DRAFT' NOT NULL,
    model_provider VARCHAR(64) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days') NOT NULL
);

-- 5. PROPOSAL_ITEMS
CREATE TABLE IF NOT EXISTS proposal_items (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_type item_type_enum NOT NULL,
    proposed_title VARCHAR(255) NOT NULL,
    description TEXT,
    deadline TIMESTAMPTZ,
    earliest_start TIMESTAMPTZ,
    estimated_duration_min INT DEFAULT 30,
    duration_source VARCHAR(64) DEFAULT 'MODEL_ESTIMATE' NOT NULL,
    priority task_priority_enum DEFAULT 'P2_MEDIUM' NOT NULL,
    confidence FLOAT DEFAULT 0.85 NOT NULL,
    uncertainty_flags TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
    source_reference TEXT NOT NULL,
    status proposal_item_status_enum DEFAULT 'PENDING' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 6. TASKS
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_proposal_item_id UUID REFERENCES proposal_items(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    deadline TIMESTAMPTZ,
    estimated_duration_min INT DEFAULT 30 NOT NULL,
    priority task_priority_enum DEFAULT 'P2_MEDIUM' NOT NULL,
    status task_status_enum DEFAULT 'PENDING' NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 7. TASK_DEPENDENCIES
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    predecessor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    successor_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(64) DEFAULT 'FINISH_TO_START' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT chk_no_self_dependency CHECK (predecessor_task_id != successor_task_id),
    CONSTRAINT uq_task_edge UNIQUE (predecessor_task_id, successor_task_id)
);

-- 8. AVAILABILITY_WINDOWS
CREATE TABLE IF NOT EXISTS availability_windows (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    recurrence_rule VARCHAR(64) DEFAULT 'DAILY_WEEKDAYS' NOT NULL,
    timezone VARCHAR(64) DEFAULT 'Asia/Kolkata' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 9. BUSY_EVENTS
CREATE TABLE IF NOT EXISTS busy_events (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    source VARCHAR(64) DEFAULT 'MANUAL' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 10. PLANS
CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    feasibility_status plan_feasibility_enum NOT NULL,
    total_allocated_minutes INT DEFAULT 0 NOT NULL,
    capacity_deficit_minutes INT DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 11. PLAN_ITEMS
CREATE TABLE IF NOT EXISTS plan_items (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    allocated_start TIMESTAMPTZ NOT NULL,
    allocated_end TIMESTAMPTZ NOT NULL,
    status VARCHAR(64) DEFAULT 'PROPOSED' NOT NULL
);

-- 12. MEMORY_PREFERENCES
CREATE TABLE IF NOT EXISTS memory_preferences (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(64) NOT NULL,
    preference_value JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_user_pref UNIQUE (user_id, preference_key)
);

-- 13. CONTEXTUAL_SUMMARIES
CREATE TABLE IF NOT EXISTS contextual_summaries (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_type VARCHAR(64) NOT NULL,
    summary_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 14. APPROVAL_IDEMPOTENCY
CREATE TABLE IF NOT EXISTS approval_idempotency (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    response_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 15. AUDIT_LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_captures_user_created ON captures(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_proposals_user_status ON proposals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_prop_items_proposal_id ON proposal_items(proposal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_date_status ON tasks(user_id, deadline, status);
CREATE INDEX IF NOT EXISTS idx_plans_user_date ON plans(user_id, plan_date);
CREATE INDEX IF NOT EXISTS idx_plan_items_plan_id ON plan_items(plan_id);

COMMIT;

-- --------------------------------------------------------------------
-- PHASE 2: MIGRATION 002 — ROW LEVEL SECURITY ACTIVATION
-- --------------------------------------------------------------------
BEGIN;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposal_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE availability_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE busy_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE plan_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextual_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_idempotency ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        auth.uid(),
        NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Idempotent baseline policy application
DROP POLICY IF EXISTS users_self ON users;
CREATE POLICY users_self ON users FOR ALL USING (id = current_user_id());

DROP POLICY IF EXISTS captures_self ON captures;
CREATE POLICY captures_self ON captures FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS proposals_self ON proposals;
CREATE POLICY proposals_self ON proposals FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS proposal_items_self ON proposal_items;
CREATE POLICY proposal_items_self ON proposal_items FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS tasks_self ON tasks;
CREATE POLICY tasks_self ON tasks FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS dependencies_self ON task_dependencies;
CREATE POLICY dependencies_self ON task_dependencies FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS availability_self ON availability_windows;
CREATE POLICY availability_self ON availability_windows FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS busy_self ON busy_events;
CREATE POLICY busy_self ON busy_events FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS plans_self ON plans;
CREATE POLICY plans_self ON plans FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS memory_self ON memory_preferences;
CREATE POLICY memory_self ON memory_preferences FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS summaries_self ON contextual_summaries;
CREATE POLICY summaries_self ON contextual_summaries FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS idempotency_self ON approval_idempotency;
CREATE POLICY idempotency_self ON approval_idempotency FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS audit_self ON audit_logs;
CREATE POLICY audit_self ON audit_logs FOR ALL USING (user_id = current_user_id());

DROP POLICY IF EXISTS plan_items_self ON plan_items;
CREATE POLICY plan_items_self ON plan_items FOR ALL USING (
    EXISTS (SELECT 1 FROM plans WHERE plans.id = plan_items.plan_id AND plans.user_id = current_user_id())
);

COMMIT;

-- --------------------------------------------------------------------
-- PHASE 3: MIGRATION 003 — ENUM EXTENSIONS & LINGUISTIC FIELDS
-- Note: Enum values MUST be committed before being referenced in Phase 4.
-- --------------------------------------------------------------------
BEGIN;

DO $$ BEGIN
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PROCESSING';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PENDING_REVIEW';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'COMMITTED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'FAILED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'ARCHIVED';
EXCEPTION WHEN duplicate_object THEN null; END $$;

ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS locale VARCHAR(64);

ALTER TABLE captures ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(64) DEFAULT 'PENDING_REVIEW' NOT NULL;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS original_transcript TEXT;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS translated_transcript TEXT;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS proposal_ids UUID[] DEFAULT '{}'::UUID[] NOT NULL;

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS transcript_text TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS original_transcript TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translated_transcript TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS display_language VARCHAR(32) DEFAULT 'original' NOT NULL;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translation_status VARCHAR(32) DEFAULT 'ORIGINAL' NOT NULL;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS intent_summary TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS original_intent_summary TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translated_intent_summary TEXT;

ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS action VARCHAR(255);
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS object VARCHAR(255);
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS original_title TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS original_description TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS translated_title TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS translated_description TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS intent_confidence FLOAT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS action_confidence FLOAT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS object_confidence FLOAT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS deadline_confidence FLOAT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS condition_trigger TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE proposal_items ADD COLUMN IF NOT EXISTS decision_state VARCHAR(64) DEFAULT 'PENDING' NOT NULL;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS origin_proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS duration_source VARCHAR(64) DEFAULT 'UNSPECIFIED' NOT NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_language VARCHAR(32);

ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS category VARCHAR(64) DEFAULT 'GENERAL' NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 1.0 NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_granted BOOLEAN DEFAULT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_level VARCHAR(64) DEFAULT 'UNKNOWN' NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_status VARCHAR(64) DEFAULT 'UNCONFIRMED' NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

CREATE INDEX IF NOT EXISTS idx_captures_user_lifecycle ON captures(user_id, lifecycle_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_proposals_user_status_created ON proposals(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_prefs_user_cat ON memory_preferences(user_id, category);
CREATE INDEX IF NOT EXISTS idx_memory_prefs_consent ON memory_preferences(user_id, consent_status);

COMMIT;

-- --------------------------------------------------------------------
-- PHASE 4: MIGRATION 004 — INTEGRITY, RPC & RLS MODERNIZATION
-- --------------------------------------------------------------------
BEGIN;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_duration_min INT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS scheduled_date DATE;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS clarifications JSONB DEFAULT '[]'::JSONB NOT NULL;

-- Priority Nullability Alignment (SEC-02 Remediation)
ALTER TABLE proposal_items ALTER COLUMN priority DROP NOT NULL;
ALTER TABLE proposal_items ALTER COLUMN priority DROP DEFAULT;
ALTER TABLE tasks ALTER COLUMN priority DROP NOT NULL;
ALTER TABLE tasks ALTER COLUMN priority DROP DEFAULT;

-- Composite Candidate Key on Tasks
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_tasks_id_user_id'
    ) THEN
        ALTER TABLE tasks ADD CONSTRAINT uq_tasks_id_user_id UNIQUE (id, user_id);
    END IF;
END $$;

-- Drop obsolete single-column foreign keys safely
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'task_dependencies_predecessor_task_id_fkey'
    ) THEN
        ALTER TABLE task_dependencies DROP CONSTRAINT task_dependencies_predecessor_task_id_fkey;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'task_dependencies_successor_task_id_fkey'
    ) THEN
        ALTER TABLE task_dependencies DROP CONSTRAINT task_dependencies_successor_task_id_fkey;
    END IF;
END $$;

-- Composite Foreign Keys for strict multi-tenant isolation
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_task_deps_predecessor_tenant'
    ) THEN
        ALTER TABLE task_dependencies
            ADD CONSTRAINT fk_task_deps_predecessor_tenant
            FOREIGN KEY (predecessor_task_id, user_id)
            REFERENCES tasks (id, user_id)
            ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_task_deps_successor_tenant'
    ) THEN
        ALTER TABLE task_dependencies
            ADD CONSTRAINT fk_task_deps_successor_tenant
            FOREIGN KEY (successor_task_id, user_id)
            REFERENCES tasks (id, user_id)
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
    ON tasks (source_proposal_item_id)
    WHERE source_proposal_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_user_scheduled_date
    ON tasks (user_id, scheduled_date);

-- Privilege Hardening on Append-Only / Idempotency Tables
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM authenticated, anon;
GRANT SELECT ON TABLE audit_logs TO authenticated;
GRANT ALL ON TABLE audit_logs TO service_role;

REVOKE UPDATE, DELETE, TRUNCATE ON TABLE approval_idempotency FROM authenticated, anon;
GRANT SELECT, INSERT ON TABLE approval_idempotency TO authenticated, service_role;

-- RLS Updates with auth.uid()
DROP POLICY IF EXISTS captures_self ON captures;
DROP POLICY IF EXISTS captures_select ON captures;
DROP POLICY IF EXISTS captures_insert ON captures;
DROP POLICY IF EXISTS captures_update ON captures;
DROP POLICY IF EXISTS captures_delete ON captures;

CREATE POLICY captures_select ON captures FOR SELECT USING (user_id = auth.uid());
CREATE POLICY captures_insert ON captures FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY captures_update ON captures FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY captures_delete ON captures FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS proposals_self ON proposals;
DROP POLICY IF EXISTS proposals_select ON proposals;
DROP POLICY IF EXISTS proposals_insert ON proposals;
DROP POLICY IF EXISTS proposals_update ON proposals;
DROP POLICY IF EXISTS proposals_delete ON proposals;

CREATE POLICY proposals_select ON proposals FOR SELECT USING (user_id = auth.uid());
CREATE POLICY proposals_insert ON proposals FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY proposals_update ON proposals FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY proposals_delete ON proposals FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS proposal_items_self ON proposal_items;
DROP POLICY IF EXISTS proposal_items_select ON proposal_items;
DROP POLICY IF EXISTS proposal_items_insert ON proposal_items;
DROP POLICY IF EXISTS proposal_items_update ON proposal_items;
DROP POLICY IF EXISTS proposal_items_delete ON proposal_items;

CREATE POLICY proposal_items_select ON proposal_items FOR SELECT USING (user_id = auth.uid());
CREATE POLICY proposal_items_insert ON proposal_items FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY proposal_items_update ON proposal_items FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY proposal_items_delete ON proposal_items FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS tasks_self ON tasks;
DROP POLICY IF EXISTS tasks_select ON tasks;
DROP POLICY IF EXISTS tasks_insert ON tasks;
DROP POLICY IF EXISTS tasks_update ON tasks;
DROP POLICY IF EXISTS tasks_delete ON tasks;

CREATE POLICY tasks_select ON tasks FOR SELECT USING (user_id = auth.uid());
CREATE POLICY tasks_insert ON tasks FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY tasks_update ON tasks FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY tasks_delete ON tasks FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS memory_self ON memory_preferences;
DROP POLICY IF EXISTS memory_select ON memory_preferences;
DROP POLICY IF EXISTS memory_insert ON memory_preferences;
DROP POLICY IF EXISTS memory_update ON memory_preferences;
DROP POLICY IF EXISTS memory_delete ON memory_preferences;

CREATE POLICY memory_select ON memory_preferences FOR SELECT USING (user_id = auth.uid());
CREATE POLICY memory_insert ON memory_preferences FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY memory_update ON memory_preferences FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY memory_delete ON memory_preferences FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS dependencies_self ON task_dependencies;
DROP POLICY IF EXISTS dependencies_select ON task_dependencies;
DROP POLICY IF EXISTS dependencies_insert ON task_dependencies;
DROP POLICY IF EXISTS dependencies_delete ON task_dependencies;

CREATE POLICY dependencies_select ON task_dependencies FOR SELECT USING (user_id = auth.uid());
CREATE POLICY dependencies_insert ON task_dependencies FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY dependencies_delete ON task_dependencies FOR DELETE USING (user_id = auth.uid());

DROP POLICY IF EXISTS audit_self ON audit_logs;
DROP POLICY IF EXISTS audit_select ON audit_logs;
DROP POLICY IF EXISTS audit_insert ON audit_logs;

CREATE POLICY audit_select ON audit_logs FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS idempotency_self ON approval_idempotency;
DROP POLICY IF EXISTS idempotency_select ON approval_idempotency;
DROP POLICY IF EXISTS idempotency_insert ON approval_idempotency;

CREATE POLICY idempotency_select ON approval_idempotency FOR SELECT USING (user_id = auth.uid());
CREATE POLICY idempotency_insert ON approval_idempotency FOR INSERT WITH CHECK (user_id = auth.uid());

-- Upgrade remaining tables to auth.uid() for 100% policy consistency
DROP POLICY IF EXISTS users_self ON users;
CREATE POLICY users_self ON users FOR ALL USING (id = auth.uid()) WITH CHECK (id = auth.uid());

DROP POLICY IF EXISTS availability_self ON availability_windows;
CREATE POLICY availability_self ON availability_windows FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS busy_self ON busy_events;
CREATE POLICY busy_self ON busy_events FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS plans_self ON plans;
CREATE POLICY plans_self ON plans FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS plan_items_self ON plan_items;
CREATE POLICY plan_items_self ON plan_items FOR ALL USING (
    EXISTS (SELECT 1 FROM plans WHERE plans.id = plan_items.plan_id AND plans.user_id = auth.uid())
);

DROP POLICY IF EXISTS summaries_self ON contextual_summaries;
CREATE POLICY summaries_self ON contextual_summaries FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Stored Procedure: commit_proposal_atomic
CREATE OR REPLACE FUNCTION commit_proposal_atomic(
    p_user_id UUID,
    p_proposal_id UUID,
    p_idempotency_key VARCHAR(255),
    p_item_decisions JSONB
) RETURNS JSONB AS $$
DECLARE
    v_caller_role TEXT;
    v_auth_uid UUID;
    v_effective_user_id UUID;
    v_cached_response JSONB;
    v_proposal RECORD;
    v_item JSONB;
    v_item_id UUID;
    v_prop_item RECORD;
    v_is_approved BOOLEAN;
    v_task_id UUID;
    v_target_date DATE;
    v_target_priority task_priority_enum;
    v_db_item_count INT;
    v_decision_count INT;
    v_approved_count INT := 0;
    v_rejected_count INT := 0;
    v_created_task_ids UUID[] := '{}';
    v_seen_item_ids UUID[] := '{}';
    v_now TIMESTAMPTZ := NOW();
    v_result JSONB;
BEGIN
    v_caller_role := COALESCE(
        NULLIF(current_setting('request.jwt.claim.role', true), ''),
        NULLIF(auth.role(), '')
    );
    v_auth_uid := auth.uid();

    IF v_caller_role = 'authenticated' THEN
        IF v_auth_uid IS NULL THEN
            RAISE EXCEPTION 'Access denied: authenticated token missing sub claim' USING ERRCODE = '42501';
        END IF;
        IF v_auth_uid != p_user_id THEN
            RAISE EXCEPTION 'Access denied: authenticated caller % does not match target user_id %',
                v_auth_uid, p_user_id USING ERRCODE = '42501';
        END IF;
        v_effective_user_id := v_auth_uid;

    ELSIF v_caller_role = 'service_role' OR session_user = 'postgres' THEN
        v_effective_user_id := p_user_id;

    ELSE
        RAISE EXCEPTION 'Access denied: authentication required to commit proposals' USING ERRCODE = '42501';
    END IF;

    SELECT response_payload INTO v_cached_response
    FROM approval_idempotency
    WHERE user_id = v_effective_user_id AND idempotency_key = p_idempotency_key;

    IF v_cached_response IS NOT NULL THEN
        RETURN v_cached_response;
    END IF;

    SELECT * INTO v_proposal
    FROM proposals
    WHERE id = p_proposal_id AND user_id = v_effective_user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal % not found for user %', p_proposal_id, v_effective_user_id
            USING ERRCODE = 'P0002';
    END IF;

    IF v_proposal.status IN ('APPROVED', 'COMMITTED') THEN
        SELECT response_payload INTO v_cached_response
        FROM approval_idempotency
        WHERE user_id = v_effective_user_id AND idempotency_key = p_idempotency_key;

        IF v_cached_response IS NOT NULL THEN
            RETURN v_cached_response;
        END IF;

        RAISE EXCEPTION 'Proposal % has already been committed', p_proposal_id
            USING ERRCODE = '23505';
    END IF;

    IF v_proposal.status = 'REJECTED' THEN
        RAISE EXCEPTION 'Proposal % has already been rejected', p_proposal_id
            USING ERRCODE = '22023';
    END IF;

    IF p_item_decisions IS NULL THEN
        RAISE EXCEPTION 'Decisions payload cannot be NULL' USING ERRCODE = '22023';
    END IF;

    IF jsonb_typeof(p_item_decisions) != 'array' THEN
        RAISE EXCEPTION 'Decisions payload must be a JSON array, got %', jsonb_typeof(p_item_decisions)
            USING ERRCODE = '22023';
    END IF;

    SELECT COUNT(*) INTO v_db_item_count
    FROM proposal_items
    WHERE proposal_id = p_proposal_id AND user_id = v_effective_user_id;

    v_decision_count := jsonb_array_length(p_item_decisions);

    IF v_db_item_count > 0 AND v_decision_count = 0 THEN
        RAISE EXCEPTION 'Proposal % contains % items, but received 0 decisions',
            p_proposal_id, v_db_item_count USING ERRCODE = '22023';
    END IF;

    IF v_decision_count != v_db_item_count THEN
        RAISE EXCEPTION 'Incomplete decisions: proposal contains % items, but received % decisions',
            v_db_item_count, v_decision_count USING ERRCODE = '22023';
    END IF;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_item_decisions)
    LOOP
        v_item_id := (v_item->>'id')::UUID;
        v_is_approved := COALESCE((v_item->>'is_approved')::BOOLEAN, TRUE);

        IF v_item_id = ANY(v_seen_item_ids) THEN
            RAISE EXCEPTION 'Duplicate decision for item % in approval payload', v_item_id
                USING ERRCODE = '22023';
        END IF;
        v_seen_item_ids := array_append(v_seen_item_ids, v_item_id);

        SELECT * INTO v_prop_item
        FROM proposal_items
        WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Proposal item % does not belong to proposal % or user %',
                v_item_id, p_proposal_id, v_effective_user_id USING ERRCODE = 'P0002';
        END IF;

        IF v_is_approved THEN
            v_task_id := gen_random_uuid();

            v_target_date := NULL;
            IF v_item->>'scheduled_date' IS NOT NULL THEN
                v_target_date := (v_item->>'scheduled_date')::DATE;
            ELSIF v_prop_item.deadline IS NOT NULL THEN
                v_target_date := (v_prop_item.deadline AT TIME ZONE 'UTC')::DATE;
            ELSE
                v_target_date := (v_now AT TIME ZONE 'UTC')::DATE;
            END IF;

            v_target_priority := NULL;
            IF v_item->>'priority' IS NOT NULL AND v_item->>'priority' NOT IN ('UNSPECIFIED', '', 'null') THEN
                v_target_priority := (v_item->>'priority')::task_priority_enum;
            ELSIF v_prop_item.priority IS NOT NULL THEN
                v_target_priority := v_prop_item.priority;
            ELSE
                v_target_priority := NULL;
            END IF;

            INSERT INTO tasks (
                id,
                user_id,
                source_proposal_item_id,
                origin_proposal_id,
                title,
                description,
                deadline,
                scheduled_date,
                estimated_duration_min,
                duration_source,
                priority,
                status,
                source_language,
                created_at,
                updated_at
            ) VALUES (
                v_task_id,
                v_effective_user_id,
                v_item_id,
                p_proposal_id,
                COALESCE(v_item->>'proposed_title', v_prop_item.proposed_title),
                v_prop_item.description,
                v_prop_item.deadline,
                v_target_date,
                COALESCE((v_item->>'estimated_duration_min')::INT, v_prop_item.estimated_duration_min, 30),
                'USER_APPROVED',
                v_target_priority,
                'PENDING',
                'en',
                v_now,
                v_now
            );

            UPDATE proposal_items
            SET status = 'APPROVED',
                decision_state = 'COMMITTED'
            WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id;

            v_approved_count := v_approved_count + 1;
            v_created_task_ids := array_append(v_created_task_ids, v_task_id);
        ELSE
            UPDATE proposal_items
            SET status = 'REJECTED',
                decision_state = 'REJECTED',
                rejection_reason = COALESCE(v_item->>'rejection_reason', 'User rejected item')
            WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id;

            v_rejected_count := v_rejected_count + 1;
        END IF;
    END LOOP;

    UPDATE proposals
    SET status = 'COMMITTED'
    WHERE id = p_proposal_id AND user_id = v_effective_user_id;

    IF v_proposal.capture_id IS NOT NULL THEN
        UPDATE captures
        SET lifecycle_status = 'COMMITTED'
        WHERE id = v_proposal.capture_id AND user_id = v_effective_user_id;
    END IF;

    v_result := jsonb_build_object(
        'proposal_id', p_proposal_id,
        'approved_tasks_count', v_approved_count,
        'rejected_items_count', v_rejected_count,
        'created_task_ids', to_jsonb(v_created_task_ids),
        'message', 'Human decision recorded atomically. Tasks explicitly committed to schedule.'
    );

    INSERT INTO approval_idempotency (
        id,
        user_id,
        idempotency_key,
        proposal_id,
        response_payload,
        created_at
    ) VALUES (
        gen_random_uuid(),
        v_effective_user_id,
        p_idempotency_key,
        p_proposal_id,
        v_result,
        v_now
    );

    INSERT INTO audit_logs (
        id,
        user_id,
        event_type,
        metadata,
        created_at
    ) VALUES (
        gen_random_uuid(),
        v_effective_user_id,
        'PROPOSAL_COMMITTED',
        jsonb_build_object(
            'proposal_id', p_proposal_id,
            'approved_count', v_approved_count,
            'rejected_count', v_rejected_count,
            'idempotency_key', p_idempotency_key
        ),
        v_now
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql
   SECURITY DEFINER
   SET search_path = public, extensions, pg_temp;

REVOKE ALL ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) TO authenticated, service_role;

COMMIT;

-- --------------------------------------------------------------------
-- PHASE 5: MIGRATION 005 — AUTH TO PUBLIC USER PROFILE TRIGGER
-- --------------------------------------------------------------------
BEGIN;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $$
DECLARE
    v_email TEXT;
    v_full_name TEXT;
    v_timezone TEXT;
BEGIN
    v_email := COALESCE(new.email, 'user_' || replace(new.id::text, '-', '') || '@thozhi.ai');
    v_full_name := COALESCE(new.raw_user_meta_data->>'full_name', 'THOZHI User');
    v_timezone := COALESCE(new.raw_user_meta_data->>'timezone', 'Asia/Kolkata');

    BEGIN
        INSERT INTO public.users (
            id,
            email,
            full_name,
            timezone,
            default_start_time,
            default_end_time,
            created_at,
            updated_at
        )
        VALUES (
            new.id,
            v_email,
            v_full_name,
            v_timezone,
            '09:00:00',
            '18:00:00',
            NOW(),
            NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            full_name = COALESCE(EXCLUDED.full_name, public.users.full_name),
            updated_at = NOW();

    EXCEPTION
        WHEN unique_violation THEN
            -- If email uniqueness conflicts with an existing different user profile,
            -- fallback to collision-free synthetic email based on new.id to guarantee profile creation
            INSERT INTO public.users (
                id,
                email,
                full_name,
                timezone,
                default_start_time,
                default_end_time,
                created_at,
                updated_at
            )
            VALUES (
                new.id,
                'user_' || replace(new.id::text, '-', '') || '@thozhi.ai',
                v_full_name,
                v_timezone,
                '09:00:00',
                '18:00:00',
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                full_name = COALESCE(EXCLUDED.full_name, public.users.full_name),
                updated_at = NOW();
    END;

    RETURN new;
END;
$$;

REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role, postgres;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Safe backfill handling duplicate emails
INSERT INTO public.users (id, email, full_name, timezone, default_start_time, default_end_time, created_at, updated_at)
SELECT
    u.id,
    COALESCE(u.email, 'user_' || replace(u.id::text, '-', '') || '@thozhi.ai'),
    COALESCE(u.raw_user_meta_data->>'full_name', 'THOZHI User'),
    'Asia/Kolkata',
    '09:00:00',
    '18:00:00',
    u.created_at,
    NOW()
FROM auth.users u
WHERE NOT EXISTS (
    SELECT 1 FROM public.users p WHERE p.id = u.id OR (u.email IS NOT NULL AND p.email = u.email)
)
ON CONFLICT (id) DO NOTHING;

-- --------------------------------------------------------------------
-- NOTIFY POSTGREST SCHEMA RELOAD & COMMIT
-- --------------------------------------------------------------------
NOTIFY pgrst, 'reload schema';

COMMIT;
