-- ====================================================================
-- THOZHI MASTER MIGRATION 001: INITIAL SCHEMA
-- Aligned 100% with Masterprd.md Section 10 & 06_DATABASE_ARCHITECTURE.md
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;

-- 1. ENUMS
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

-- 6. TASKS (Approved items)
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
