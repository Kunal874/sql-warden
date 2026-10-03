-- Setup-only, idempotent migration for this dedicated local PostgreSQL cluster.
-- Runtime logins use sqlwarden only; default databases have independent catalogs.
-- Keep the databases and their data, but remove PUBLIC connection/temp privileges.
REVOKE CONNECT, TEMPORARY ON DATABASE postgres, template1 FROM PUBLIC;
