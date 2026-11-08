-- ====================================================================
-- THOZHI MASTER MIGRATION 005: AUTH USER TO PUBLIC USER PROFILE TRIGGER
-- Version: 5.1.0 (PostgreSQL 15+ / Supabase GoTrue Auth)
-- Status: Production Migration File
-- Objective: Ensure reliable automatic creation of public.users profile
--            for every registered Supabase Auth identity to satisfy
--            relational foreign key constraints across all child tables.
-- ====================================================================

-- 1. Create or replace the profile creation trigger function
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

-- Revoke default public execution; restrict to service_role and postgres
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role, postgres;

-- 2. Bind trigger to auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. Safely backfill any existing auth users into public.users
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

-- 4. Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';
