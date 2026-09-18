-- Creates the three cluster-level database roles from LLD section 2.1 / ADR-0001.
-- Run once per PostgreSQL cluster, as a superuser, before any Alembic migration.
--
-- kritvo_owner  - runs Alembic migrations only; ends up owning every table.
-- kritvo_app    - the API, gateway and tenant-scoped worker tasks use this at runtime.
--                 NOBYPASSRLS so it can never skip the tenant-isolation policies, even
--                 though it owns no tables and has no DDL rights.
-- kritvo_system - platform-only code paths (billing, signup, the scheduler). Bypasses RLS;
--                 every connection made with it must be from a platform_* module.
--
-- Local dev: mounted into postgres:16's /docker-entrypoint-initdb.d by docker-compose, so it
-- runs automatically on first startup with the placeholder passwords below.
-- Everywhere else: run by deployment tooling with real, generated passwords from a secrets
-- manager. Never reuse the placeholder passwords outside local development.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kritvo_owner') THEN
    CREATE ROLE kritvo_owner LOGIN PASSWORD 'change-me';
  END IF;

  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kritvo_app') THEN
    CREATE ROLE kritvo_app LOGIN PASSWORD 'change-me' NOBYPASSRLS;
  END IF;

  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kritvo_system') THEN
    CREATE ROLE kritvo_system LOGIN PASSWORD 'change-me' BYPASSRLS;
  END IF;
END
$$;

ALTER DATABASE kritvo OWNER TO kritvo_owner;

GRANT CONNECT ON DATABASE kritvo TO kritvo_app, kritvo_system;
GRANT USAGE ON SCHEMA public TO kritvo_app, kritvo_system;

-- Tables and sequences that kritvo_owner creates from here on (i.e. every Alembic
-- migration) are readable/writable by the runtime roles by default, with no DDL rights.
ALTER DEFAULT PRIVILEGES FOR ROLE kritvo_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO kritvo_app, kritvo_system;
ALTER DEFAULT PRIVILEGES FOR ROLE kritvo_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO kritvo_app, kritvo_system;
