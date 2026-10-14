-- Run this once in the Supabase SQL Editor AFTER schema.sql.
-- Creates a login that can only READ, for AI-generated queries.
-- Change the password before running, and never commit the real one.

CREATE ROLE ai_readonly WITH LOGIN PASSWORD 'CHANGE-ME-to-a-strong-password';
GRANT USAGE ON SCHEMA public TO ai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_readonly;
ALTER ROLE ai_readonly SET default_transaction_read_only = on;  -- blocks writes even if the AI tries
ALTER ROLE ai_readonly SET statement_timeout = '5s';            -- stops runaway queries

-- Turn on row-level security everywhere, then allow only ai_readonly to SELECT.
-- (The admin "postgres" login bypasses RLS, so seeding still works.)
DO $$
DECLARE t text;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY ai_readonly_select ON public.%I FOR SELECT TO ai_readonly USING (true)', t);
  END LOOP;
END $$;

-- Make the views respect those rules too
ALTER VIEW vendor_ratings SET (security_invoker = on);
ALTER VIEW event_budget_summary SET (security_invoker = on);
