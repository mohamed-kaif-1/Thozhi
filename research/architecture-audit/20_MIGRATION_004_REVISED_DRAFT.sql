-- ====================================================================
-- THOZHI MASTER MIGRATION 004 (REVISED DRAFT — POST-SECURITY REVIEW)
-- Schema Alignment, Relational Multi-Tenant Integrity, and Atomic Commitment
-- Version: 4.1.0 (PostgreSQL 15+ / Supabase PostgREST 12+)
-- Status: REVIEW DRAFT — NOT EXECUTED AGAINST LIVE DATABASE
-- Target: Forward-only, additive, non-destructive migration
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. ENUM EXTENSIONS (Top-Level Statement, No Subtransaction)
-- --------------------------------------------------------------------
-- Standalone DDL avoids subtransaction savepoints in migration runners.
ALTER TYPE capture_status_enum ADD VALUE IF NOT EXISTS 'COMPLETED';

-- --------------------------------------------------------------------
-- 2. TABLE EXTENSIONS (TASKS & PROPOSALS)
-- --------------------------------------------------------------------
-- Track actual task duration in minutes
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS actual_duration_min INT;

-- Track explicit calendar scheduling date
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS scheduled_date DATE;

-- Persist AI-generated clarification questions
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS clarifications JSONB DEFAULT '[]'::JSONB NOT NULL;

-- --------------------------------------------------------------------
-- 3. RELATIONAL MULTI-TENANT INTEGRITY (COMPOSITE FOREIGN KEYS)
-- --------------------------------------------------------------------
-- 3.1 Composite Candidate Key on Tasks
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_tasks_id_user_id'
    ) THEN
        ALTER TABLE tasks ADD CONSTRAINT uq_tasks_id_user_id UNIQUE (id, user_id);
    END IF;
END $$;

-- 3.2 Composite Foreign Keys on Task Dependencies (Cross-Tenant Edge Prevention)
-- Guarantees that predecessor and successor tasks MUST belong to the same user as the dependency row.
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

-- --------------------------------------------------------------------
-- 4. PARTIAL UNIQUE INDEX (DUPLICATE TASK COMMITMENT PREVENTION)
-- --------------------------------------------------------------------
-- Note: Must be executed after preflight deduplication (see Document 22)
CREATE UNIQUE INDEX IF NOT EXISTS uq_task_source_proposal_item
    ON tasks (source_proposal_item_id)
    WHERE source_proposal_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_user_scheduled_date
    ON tasks (user_id, scheduled_date);

-- --------------------------------------------------------------------
-- 5. TABLE-LEVEL PRIVILEGE HARDENING (AUDIT TRAIL IMMUTABILITY)
-- --------------------------------------------------------------------
-- Revoke mutation rights from client-facing roles on audit_logs.
-- Only SECURITY DEFINER functions and service_role can append records.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM authenticated, anon;
GRANT SELECT ON TABLE audit_logs TO authenticated;
GRANT ALL ON TABLE audit_logs TO service_role;

REVOKE UPDATE, DELETE, TRUNCATE ON TABLE approval_idempotency FROM authenticated, anon;
GRANT SELECT, INSERT ON TABLE approval_idempotency TO authenticated, service_role;

-- --------------------------------------------------------------------
-- 6. ROW-LEVEL SECURITY (RLS) POLICIES
-- --------------------------------------------------------------------
-- CAPTURES
DROP POLICY IF EXISTS captures_self ON captures;
DROP POLICY IF EXISTS captures_select ON captures;
DROP POLICY IF EXISTS captures_insert ON captures;
DROP POLICY IF EXISTS captures_update ON captures;
DROP POLICY IF EXISTS captures_delete ON captures;

CREATE POLICY captures_select ON captures FOR SELECT USING (user_id = auth.uid());
CREATE POLICY captures_insert ON captures FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY captures_update ON captures FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY captures_delete ON captures FOR DELETE USING (user_id = auth.uid());

-- PROPOSALS
DROP POLICY IF EXISTS proposals_self ON proposals;
DROP POLICY IF EXISTS proposals_select ON proposals;
DROP POLICY IF EXISTS proposals_insert ON proposals;
DROP POLICY IF EXISTS proposals_update ON proposals;
DROP POLICY IF EXISTS proposals_delete ON proposals;

CREATE POLICY proposals_select ON proposals FOR SELECT USING (user_id = auth.uid());
CREATE POLICY proposals_insert ON proposals FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY proposals_update ON proposals FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY proposals_delete ON proposals FOR DELETE USING (user_id = auth.uid());

-- PROPOSAL ITEMS
DROP POLICY IF EXISTS proposal_items_self ON proposal_items;
DROP POLICY IF EXISTS proposal_items_select ON proposal_items;
DROP POLICY IF EXISTS proposal_items_insert ON proposal_items;
DROP POLICY IF EXISTS proposal_items_update ON proposal_items;
DROP POLICY IF EXISTS proposal_items_delete ON proposal_items;

CREATE POLICY proposal_items_select ON proposal_items FOR SELECT USING (user_id = auth.uid());
CREATE POLICY proposal_items_insert ON proposal_items FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY proposal_items_update ON proposal_items FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY proposal_items_delete ON proposal_items FOR DELETE USING (user_id = auth.uid());

-- TASKS
DROP POLICY IF EXISTS tasks_self ON tasks;
DROP POLICY IF EXISTS tasks_select ON tasks;
DROP POLICY IF EXISTS tasks_insert ON tasks;
DROP POLICY IF EXISTS tasks_update ON tasks;
DROP POLICY IF EXISTS tasks_delete ON tasks;

CREATE POLICY tasks_select ON tasks FOR SELECT USING (user_id = auth.uid());
CREATE POLICY tasks_insert ON tasks FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY tasks_update ON tasks FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY tasks_delete ON tasks FOR DELETE USING (user_id = auth.uid());

-- MEMORY PREFERENCES
DROP POLICY IF EXISTS memory_self ON memory_preferences;
DROP POLICY IF EXISTS memory_select ON memory_preferences;
DROP POLICY IF EXISTS memory_insert ON memory_preferences;
DROP POLICY IF EXISTS memory_update ON memory_preferences;
DROP POLICY IF EXISTS memory_delete ON memory_preferences;

CREATE POLICY memory_select ON memory_preferences FOR SELECT USING (user_id = auth.uid());
CREATE POLICY memory_insert ON memory_preferences FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY memory_update ON memory_preferences FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY memory_delete ON memory_preferences FOR DELETE USING (user_id = auth.uid());

-- TASK DEPENDENCIES
DROP POLICY IF EXISTS dependencies_self ON task_dependencies;
DROP POLICY IF EXISTS dependencies_select ON task_dependencies;
DROP POLICY IF EXISTS dependencies_insert ON task_dependencies;
DROP POLICY IF EXISTS dependencies_delete ON task_dependencies;

CREATE POLICY dependencies_select ON task_dependencies FOR SELECT USING (user_id = auth.uid());
CREATE POLICY dependencies_insert ON task_dependencies FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY dependencies_delete ON task_dependencies FOR DELETE USING (user_id = auth.uid());

-- AUDIT LOGS (Read-Only for Authenticated Users)
DROP POLICY IF EXISTS audit_self ON audit_logs;
DROP POLICY IF EXISTS audit_select ON audit_logs;
DROP POLICY IF EXISTS audit_insert ON audit_logs;

CREATE POLICY audit_select ON audit_logs FOR SELECT USING (user_id = auth.uid());

-- APPROVAL IDEMPOTENCY
DROP POLICY IF EXISTS idempotency_self ON approval_idempotency;
DROP POLICY IF EXISTS idempotency_select ON approval_idempotency;
DROP POLICY IF EXISTS idempotency_insert ON approval_idempotency;

CREATE POLICY idempotency_select ON approval_idempotency FOR SELECT USING (user_id = auth.uid());
CREATE POLICY idempotency_insert ON approval_idempotency FOR INSERT WITH CHECK (user_id = auth.uid());

-- --------------------------------------------------------------------
-- 7. REVISED ATOMIC PROPOSAL APPROVAL STORED PROCEDURE (RPC)
-- --------------------------------------------------------------------
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
    v_db_item_count INT;
    v_decision_count INT;
    v_approved_count INT := 0;
    v_rejected_count INT := 0;
    v_created_task_ids UUID[] := '{}';
    v_seen_item_ids UUID[] := '{}';
    v_now TIMESTAMPTZ := NOW();
    v_result JSONB;
BEGIN
    -- 1. Multi-Tier Identity Verification
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
        -- Authorized administrative / backend test runner mode
        v_effective_user_id := p_user_id;

    ELSE
        -- Deny anonymous callers (anon) and unauthenticated contexts
        RAISE EXCEPTION 'Access denied: authentication required to commit proposals' USING ERRCODE = '42501';
    END IF;

    -- 2. Fast-Path Idempotency Cache Check
    SELECT response_payload INTO v_cached_response
    FROM approval_idempotency
    WHERE user_id = v_effective_user_id AND idempotency_key = p_idempotency_key;

    IF v_cached_response IS NOT NULL THEN
        RETURN v_cached_response;
    END IF;

    -- 3. Lock Proposal Row (Serializes concurrent requests & eliminates race conditions)
    SELECT * INTO v_proposal
    FROM proposals
    WHERE id = p_proposal_id AND user_id = v_effective_user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal % not found for user %', p_proposal_id, v_effective_user_id
            USING ERRCODE = 'P0002';
    END IF;

    -- Validate Proposal State
    IF v_proposal.status IN ('APPROVED', 'COMMITTED') THEN
        -- Re-check idempotency cache under lock (handles concurrent race that committed moments ago)
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

    -- 4. Strict Full-Coverage Item Decisions Validation
    SELECT COUNT(*) INTO v_db_item_count
    FROM proposal_items
    WHERE proposal_id = p_proposal_id AND user_id = v_effective_user_id;

    v_decision_count := jsonb_array_length(p_item_decisions);

    IF v_decision_count != v_db_item_count THEN
        RAISE EXCEPTION 'Incomplete decisions: proposal contains % items, but received % decisions',
            v_db_item_count, v_decision_count USING ERRCODE = '22023';
    END IF;

    -- 5. Process Item Decisions Under Lock
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_item_decisions)
    LOOP
        v_item_id := (v_item->>'id')::UUID;
        v_is_approved := COALESCE((v_item->>'is_approved')::BOOLEAN, TRUE);

        -- Prevent duplicate decision IDs in input array
        IF v_item_id = ANY(v_seen_item_ids) THEN
            RAISE EXCEPTION 'Duplicate decision for item % in approval payload', v_item_id
                USING ERRCODE = '22023';
        END IF;
        v_seen_item_ids := array_append(v_seen_item_ids, v_item_id);

        -- Lock and validate proposal item
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

            -- Resolve scheduled date
            v_target_date := NULL;
            IF v_item->>'scheduled_date' IS NOT NULL THEN
                v_target_date := (v_item->>'scheduled_date')::DATE;
            ELSIF v_prop_item.deadline IS NOT NULL THEN
                v_target_date := (v_prop_item.deadline AT TIME ZONE 'UTC')::DATE;
            ELSE
                v_target_date := (v_now AT TIME ZONE 'UTC')::DATE;
            END IF;

            -- Insert approved Task
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
                COALESCE((v_item->>'priority')::task_priority_enum, v_prop_item.priority, 'P2_MEDIUM'::task_priority_enum),
                'PENDING',
                'en',
                v_now,
                v_now
            );

            -- Update proposal item
            UPDATE proposal_items
            SET status = 'APPROVED',
                decision_state = 'COMMITTED'
            WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id;

            v_approved_count := v_approved_count + 1;
            v_created_task_ids := array_append(v_created_task_ids, v_task_id);
        ELSE
            -- Rejected proposal item
            UPDATE proposal_items
            SET status = 'REJECTED',
                decision_state = 'REJECTED',
                rejection_reason = COALESCE(v_item->>'rejection_reason', 'User rejected item')
            WHERE id = v_item_id AND proposal_id = p_proposal_id AND user_id = v_effective_user_id;

            v_rejected_count := v_rejected_count + 1;
        END IF;
    END LOOP;

    -- 6. Update Proposal Status
    UPDATE proposals
    SET status = 'COMMITTED'
    WHERE id = p_proposal_id AND user_id = v_effective_user_id;

    -- 7. Update Capture Lifecycle Status if linked
    IF v_proposal.capture_id IS NOT NULL THEN
        UPDATE captures
        SET lifecycle_status = 'COMMITTED'
        WHERE id = v_proposal.capture_id AND user_id = v_effective_user_id;
    END IF;

    -- 8. Build Typed API Response Payload
    v_result := jsonb_build_object(
        'proposal_id', p_proposal_id,
        'approved_tasks_count', v_approved_count,
        'rejected_items_count', v_rejected_count,
        'created_task_ids', to_jsonb(v_created_task_ids),
        'message', 'Human decision recorded atomically. Tasks explicitly committed to schedule.'
    );

    -- 9. Record Idempotency Cache
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

    -- 10. Record Immutable Audit Log
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

-- Revoke default public execution; grant explicitly to authenticated and service_role
REVOKE ALL ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION commit_proposal_atomic(UUID, UUID, VARCHAR, JSONB) TO authenticated, service_role;
