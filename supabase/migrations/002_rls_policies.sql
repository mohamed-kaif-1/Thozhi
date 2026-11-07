-- ====================================================================
-- THOZHI MASTER MIGRATION 002: ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

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

-- Dynamic auth user check function
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('request.jwt.claim.sub', true), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE;

-- POLICIES
CREATE POLICY users_self ON users FOR ALL USING (id = current_user_id());
CREATE POLICY captures_self ON captures FOR ALL USING (user_id = current_user_id());
CREATE POLICY proposals_self ON proposals FOR ALL USING (user_id = current_user_id());
CREATE POLICY proposal_items_self ON proposal_items FOR ALL USING (user_id = current_user_id());
CREATE POLICY tasks_self ON tasks FOR ALL USING (user_id = current_user_id());
CREATE POLICY dependencies_self ON task_dependencies FOR ALL USING (user_id = current_user_id());
CREATE POLICY availability_self ON availability_windows FOR ALL USING (user_id = current_user_id());
CREATE POLICY busy_self ON busy_events FOR ALL USING (user_id = current_user_id());
CREATE POLICY plans_self ON plans FOR ALL USING (user_id = current_user_id());
CREATE POLICY memory_self ON memory_preferences FOR ALL USING (user_id = current_user_id());
CREATE POLICY summaries_self ON contextual_summaries FOR ALL USING (user_id = current_user_id());
CREATE POLICY idempotency_self ON approval_idempotency FOR ALL USING (user_id = current_user_id());
CREATE POLICY audit_self ON audit_logs FOR ALL USING (user_id = current_user_id());

CREATE POLICY plan_items_self ON plan_items FOR ALL USING (
    EXISTS (SELECT 1 FROM plans WHERE plans.id = plan_items.plan_id AND plans.user_id = current_user_id())
);

