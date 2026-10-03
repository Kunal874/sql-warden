-- Setup-only, idempotent permissions update; no objects or data are deleted.
-- Call within the bootstrap transaction or with psql --single-transaction.
DO $function_hardening$
DECLARE
  risky record;
BEGIN
  -- These unused functions are outside the read-only dataset/application contract.
  -- Revoke every overload, including the complete large-object API.
  FOR risky IN
    SELECT p.oid::regprocedure AS signature
    FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'pg_catalog' AND p.proname = ANY (ARRAY[
      'pg_sleep', 'pg_sleep_for', 'pg_sleep_until', 'pg_read_file', 'pg_read_binary_file',
      'pg_ls_dir', 'pg_stat_file', 'lo_import', 'lo_export', 'lo_create', 'lo_creat',
      'lo_from_bytea', 'lo_put', 'lowrite', 'lo_unlink', 'lo_truncate', 'lo_truncate64',
      'lo_open', 'lo_close', 'loread', 'lo_get', 'lo_lseek', 'lo_lseek64', 'lo_tell', 'lo_tell64'
    ])
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', risky.signature);
  END LOOP;
END;
$function_hardening$;
