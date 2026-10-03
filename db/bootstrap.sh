#!/usr/bin/env bash
set -Eeuo pipefail

psql --no-psqlrc --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set ON_ERROR_STOP=1 \
  --set app_password="$WARDEN_APP_PASSWORD" \
  --set schools_password="$WARDEN_SCHOOLS_PASSWORD" \
  --set other_password="$WARDEN_OTHER_PASSWORD" \
  --file /opt/sqlwarden/bootstrap.sql
