-- ====================================================================
-- THOZHI MASTER MIGRATION 003: SCHEMA ALIGNMENT & DATA INTEGRITY RECTIFICATION
-- Version: 3.1.0 (PostgreSQL 15+ / Supabase PostgREST)
-- Status: Forward-only, additive, non-destructive migration
-- Core Invariant: Never fabricate user consent, approval, or provenance.
-- ====================================================================

-- 1. EXTEND PROPOSAL STATUS ENUM SAFELY
-- Preserves historical statuses: DRAFT, PRESENTED, APPROVED, REJECTED, EXPIRED
-- Extends with workflow states: PROCESSING, PENDING_REVIEW, COMMITTED, FAILED, ARCHIVED
DO $$ BEGIN
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PROCESSING';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'PENDING_REVIEW';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'COMMITTED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'FAILED';
    ALTER TYPE proposal_status_enum ADD VALUE IF NOT EXISTS 'ARCHIVED';
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- 2. EXTEND USERS TABLE
-- Neutral locale: Nullable without language assumption; application prompts user on onboarding.
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS locale VARCHAR(64); -- NULL = unconfigured/inherit device locale

-- 3. EXTEND CAPTURES TABLE
-- processing_status (enum in 001) tracks technical ingestion (RECEIVED, TRANSCRIBED, COMPLETED, FAILED)
-- lifecycle_status (varchar) tracks human governance (PENDING_REVIEW, COMMITTED, REJECTED, EXPIRED, NO_PROPOSALS)
ALTER TABLE captures ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(64) DEFAULT 'PENDING_REVIEW' NOT NULL;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS original_transcript TEXT;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS translated_transcript TEXT;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS proposal_ids UUID[] DEFAULT '{}'::UUID[] NOT NULL;

-- 4. EXTEND PROPOSALS TABLE
-- Multi-language transcripts and intent deconstruction metadata
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS transcript_text TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS original_transcript TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translated_transcript TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS display_language VARCHAR(32) DEFAULT 'original' NOT NULL;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translation_status VARCHAR(32) DEFAULT 'ORIGINAL' NOT NULL;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS intent_summary TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS original_intent_summary TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS translated_intent_summary TEXT;

-- 5. EXTEND PROPOSAL_ITEMS TABLE
-- Linguistic decomposition (Subject-Object-Verb), confidence metrics, and human review states
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

-- 6. EXTEND TASKS TABLE
-- Provenance tracking: Default is UNSPECIFIED, never fabricating 'USER_APPROVED' for legacy rows.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS origin_proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS duration_source VARCHAR(64) DEFAULT 'UNSPECIFIED' NOT NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_language VARCHAR(32);

-- 7. EXTEND MEMORY_PREFERENCES TABLE
-- Consent Integrity: Consent must be explicitly granted by the user.
-- Defaults to consent_status='UNCONFIRMED', consent_granted=NULL, consent_level='UNKNOWN'.
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS category VARCHAR(64) DEFAULT 'GENERAL' NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 1.0 NOT NULL;
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_granted BOOLEAN DEFAULT NULL; -- NULL = unrecorded, TRUE = granted, FALSE = withdrawn
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_level VARCHAR(64) DEFAULT 'UNKNOWN' NOT NULL; -- 'UNKNOWN', 'USER_EXPLICIT', 'INFERRED'
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS consent_status VARCHAR(64) DEFAULT 'UNCONFIRMED' NOT NULL; -- 'NOT_RECORDED', 'UNCONFIRMED', 'GRANTED', 'WITHDRAWN'
ALTER TABLE memory_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- 8. PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_captures_user_lifecycle ON captures(user_id, lifecycle_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_proposals_user_status_created ON proposals(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_memory_prefs_user_cat ON memory_preferences(user_id, category);
CREATE INDEX IF NOT EXISTS idx_memory_prefs_consent ON memory_preferences(user_id, consent_status);
