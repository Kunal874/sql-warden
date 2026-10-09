-- Setup-only bootstrap. Synthetic fixtures are NOT BIRD benchmark data.
-- Credentials are safely quoted psql variables, never literals in this file.
BEGIN;

CREATE ROLE warden_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE warden_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 4 PASSWORD :'app_password';
CREATE ROLE warden_sandbox_demo_schools LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD :'schools_password';
CREATE ROLE warden_sandbox_demo_other LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD :'other_password';
CREATE ROLE warden_sandbox_tenant_demo_a LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD :'tenant_a_password';
CREATE ROLE warden_sandbox_tenant_demo_b LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD :'tenant_b_password';

REVOKE ALL ON DATABASE sqlwarden FROM PUBLIC;
\ir cluster_hardening.sql
GRANT CONNECT ON DATABASE sqlwarden TO
  warden_app, warden_sandbox_demo_schools, warden_sandbox_demo_other,
  warden_sandbox_tenant_demo_a, warden_sandbox_tenant_demo_b;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA app AUTHORIZATION warden_owner;
CREATE SCHEMA demo_schools AUTHORIZATION warden_owner;
CREATE SCHEMA demo_other AUTHORIZATION warden_owner;
CREATE SCHEMA tenant_demo AUTHORIZATION warden_owner;
REVOKE ALL ON SCHEMA app, demo_schools, demo_other, tenant_demo FROM PUBLIC;

CREATE TABLE demo_schools.schools (
  id integer PRIMARY KEY,
  "School Name" text NOT NULL,
  enrollment integer NOT NULL
);
INSERT INTO demo_schools.schools VALUES (1, 'Sample North', 120), (2, 'Sample South', 80);
ALTER TABLE demo_schools.schools OWNER TO warden_owner;

CREATE TABLE demo_other.canary (value text NOT NULL);
INSERT INTO demo_other.canary VALUES ('synthetic-other-dataset');
ALTER TABLE demo_other.canary OWNER TO warden_owner;

CREATE TABLE app.boundary_probe (value text NOT NULL);
INSERT INTO app.boundary_probe VALUES ('synthetic-app-private');
ALTER TABLE app.boundary_probe OWNER TO warden_owner;

CREATE TABLE tenant_demo.orders (
  tenant_id text NOT NULL,
  order_id integer NOT NULL,
  item text NOT NULL,
  PRIMARY KEY (tenant_id, order_id)
);
INSERT INTO tenant_demo.orders VALUES
  ('tenant_a', 1, 'tenant-a-visible'),
  ('tenant_b', 1, 'tenant-b-visible');
ALTER TABLE tenant_demo.orders OWNER TO warden_owner;
ALTER TABLE tenant_demo.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_demo.orders FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_demo_a_read ON tenant_demo.orders
  FOR SELECT TO warden_sandbox_tenant_demo_a
  USING (tenant_id = 'tenant_a');
CREATE POLICY tenant_demo_b_read ON tenant_demo.orders
  FOR SELECT TO warden_sandbox_tenant_demo_b
  USING (tenant_id = 'tenant_b');

GRANT USAGE ON SCHEMA app TO warden_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO warden_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO warden_app;
GRANT USAGE ON SCHEMA demo_schools TO warden_sandbox_demo_schools;
GRANT SELECT ON ALL TABLES IN SCHEMA demo_schools TO warden_sandbox_demo_schools;
GRANT USAGE ON SCHEMA demo_other TO warden_sandbox_demo_other;
GRANT SELECT ON ALL TABLES IN SCHEMA demo_other TO warden_sandbox_demo_other;
GRANT USAGE ON SCHEMA tenant_demo TO
  warden_sandbox_tenant_demo_a, warden_sandbox_tenant_demo_b;
GRANT SELECT ON tenant_demo.orders TO
  warden_sandbox_tenant_demo_a, warden_sandbox_tenant_demo_b;

ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO warden_app;
ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA app
  GRANT USAGE, SELECT ON SEQUENCES TO warden_app;
ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA demo_schools
  GRANT SELECT ON TABLES TO warden_sandbox_demo_schools;
ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA demo_other
  GRANT SELECT ON TABLES TO warden_sandbox_demo_other;

ALTER ROLE warden_app SET search_path = pg_catalog, app;
ALTER ROLE warden_sandbox_demo_schools SET search_path = pg_catalog, demo_schools;
ALTER ROLE warden_sandbox_demo_other SET search_path = pg_catalog, demo_other;
ALTER ROLE warden_sandbox_tenant_demo_a SET search_path = pg_catalog, tenant_demo;
ALTER ROLE warden_sandbox_tenant_demo_b SET search_path = pg_catalog, tenant_demo;

DO $hardening$
DECLARE
  reader text;
BEGIN
  FOREACH reader IN ARRAY ARRAY[
    'warden_sandbox_demo_schools',
    'warden_sandbox_demo_other',
    'warden_sandbox_tenant_demo_a',
    'warden_sandbox_tenant_demo_b'
  ]
  LOOP
    EXECUTE format('ALTER ROLE %I SET default_transaction_read_only = on', reader);
    EXECUTE format('ALTER ROLE %I SET statement_timeout = %L', reader, '5s');
    EXECUTE format('ALTER ROLE %I SET lock_timeout = %L', reader, '500ms');
    EXECUTE format('ALTER ROLE %I SET idle_in_transaction_session_timeout = %L', reader, '5s');
    EXECUTE format('ALTER ROLE %I SET work_mem = %L', reader, '16MB');
    EXECUTE format('ALTER ROLE %I SET temp_file_limit = %L', reader, '64MB');
  END LOOP;
END;
$hardening$;

-- The same idempotent grants update also supports existing local volumes.
\ir function_hardening.sql

COMMIT;
