# G2.5 grants and direct-permission evidence

Date: 2026-10-09

## Scope

Record the existing real PostgreSQL evidence for effective grants, default grants
and direct-connection permission denials. Do not change database objects,
credentials, guard policy, benchmark rules, model settings or source files.

## Test-first check

1. Add a manifest-contract test requiring
   `docs/grants-permission-manifest.json`.
2. Watch that test fail because the manifest is missing.
3. Add the compact manifest with only fixed test names, expected protection
   labels and exclusion rules.
4. Run the manifest test, focused security-contract tests, the real PostgreSQL
   release permission checks, lint, format and whitespace checks.

## Completion condition

G2.5 is complete only if the real direct-connection checks run against local
PostgreSQL with the restricted dataset logins and pass.
