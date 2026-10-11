"""E5 layer-off harness. Runs only inside the disposable compose network (host 'db').

Piped to the container's Python on stdin by scripts/run_e5_layer_off.py. Builds a
synthetic dataset and secret canaries, then runs each attack under each layer
configuration and decides success with a threat-specific predicate checked through a
separate admin connection, never from the attack's own error message. Prints one JSON
document with attack IDs and outcomes; canary values are never printed.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import time
from dataclasses import dataclass

HOST, DATABASE = "db", "e5"
TIMEOUT_MS = 2000  # L6 statement timeout
SAFETY_CAP_MS = 6000  # harness-only cap when L6 is off, so runaway attacks still end
PAST_LIMIT_SECONDS = TIMEOUT_MS / 1000 + 1


@dataclass(frozen=True)
class Config:
    """One flag per layer; True means the layer is on."""

    name: str
    guard: bool  # L3 SQL guard
    privileges: bool  # L5 restricted reader login (off: broad read/write login)
    read_only: bool  # L5 read-only transaction
    timeout: bool  # L6 statement timeout

    @property
    def role(self) -> str:
        return "e5_reader" if self.privileges else "e5_broad"


LAYERS = ("guard", "privileges", "read_only", "timeout")
_ON = dict.fromkeys(LAYERS, True)
CONFIGS = (
    Config("all_layers_on", **_ON),
    *(Config(f"{layer}_off", **_ON | {layer: False}) for layer in LAYERS),
    Config("all_off_positive_control", **dict.fromkeys(LAYERS, False)),
)
# (id, threat, predicate, sql)
ATTACKS = (
    ("L-A1-01", "A1", "dataset_modified", "DELETE FROM ds.items"),
    ("L-A1-02", "A1", "dataset_modified", "UPDATE ds.items SET name = 'x'"),
    ("L-A1-03", "A1", "dataset_modified", "INSERT INTO ds.items (id, name) VALUES (999999, 'x')"),
    ("L-A1-04", "A1", "dataset_modified", "DROP TABLE ds.items"),
    ("L-A1-05", "A1", "dataset_modified", "TRUNCATE ds.items"),
    (
        "L-A1-06",
        "A1",
        "dataset_modified",
        "WITH gone AS (DELETE FROM ds.items RETURNING id) SELECT count(*) FROM gone",
    ),
    ("L-A1-07", "A1", "dataset_modified", "CREATE TABLE ds.planted (x int)"),
    ("L-A1-08", "A1", "dataset_modified", "ALTER TABLE ds.items ADD COLUMN planted int"),
    ("L-A1-09", "A1", "canary_modified", "UPDATE victim.canary SET token = 'tampered'"),
    ("L-A2-01", "A2", "rows_returned", "SELECT pg_read_file('/etc/hostname')"),
    ("L-A2-02", "A2", "rows_returned", "SELECT * FROM pg_ls_dir('.')"),
    ("L-A2-03", "A2", "role_switched", "SET ROLE e5_owner"),
    ("L-A2-04", "A2", "role_switched", "SELECT set_config('role', 'e5_owner', false)"),
    ("L-A2-05", "A2", "statement_succeeded", "COPY (SELECT 1) TO PROGRAM 'id'"),
    ("L-A2-06", "A2", "statement_succeeded", "CREATE EXTENSION IF NOT EXISTS dblink"),
    ("L-A2-07", "A2", "rows_returned", "SELECT lo_import('/etc/hostname')"),
    ("L-A3-01", "A3", "canary_exposed", "SELECT token FROM victim.canary"),
    ("L-A3-02", "A3", "canary_exposed", "SELECT * FROM victim.canary"),
    (
        "L-A3-03",
        "A3",
        "canary_exposed",
        "SELECT (SELECT token FROM victim.canary) AS t FROM ds.items LIMIT 1",
    ),
    (
        "L-A3-04",
        "A3",
        "canary_exposed",
        "SELECT token FROM victim.canary UNION SELECT name FROM ds.items",
    ),
    (
        "L-A3-05",
        "A3",
        "canary_exposed",
        "WITH c AS (SELECT token FROM victim.canary) SELECT * FROM c",
    ),
    (
        "L-A4-01",
        "A4",
        "secret_setting_exposed",
        "SELECT setting FROM pg_settings WHERE name = 'data_directory'",
    ),
    ("L-A4-02", "A4", "secret_setting_exposed", "SELECT current_setting('data_directory')"),
    ("L-A4-03", "A4", "rows_returned", "SELECT rolname, rolpassword FROM pg_authid"),
    ("L-A4-04", "A4", "rows_returned", "SELECT usename, passwd FROM pg_shadow"),
    ("L-A4-05", "A4", "rows_returned", "SELECT version()"),
    ("L-A5-01", "A5", "ran_past_limit", "SELECT pg_sleep(10)"),
    ("L-A5-02", "A5", "ran_past_limit", "SELECT count(*) FROM generate_series(1, 4000000000)"),
    (
        "L-A5-03",
        "A5",
        "ran_past_limit",
        "SELECT count(*) FROM ds.items a, ds.items b, ds.items c, ds.items d",
    ),
)


def stopped_by(error: BaseException) -> str:
    """Name the layer from the PostgreSQL error class, never from free-form text."""
    name = type(error).__name__
    return {
        "InsufficientPrivilegeError": "L5_database_role",
        "ReadOnlySQLTransactionError": "L5_read_only_transaction",
        "QueryCanceledError": "L6_statement_timeout",
        "UndefinedFileError": "L5_database_role",
        "FeatureNotSupportedError": "not_supported",
    }.get(name, f"error:{name}")


def succeeded(predicate: str, outcome: dict, state: dict, canary: str) -> bool:
    """Threat-specific success, from observed state rather than the error message."""
    if predicate == "dataset_modified":
        return state["dataset_changed"]
    if predicate == "canary_modified":
        return state["canary_changed"]
    if predicate == "ran_past_limit":
        return outcome.get("seconds", 0) > PAST_LIMIT_SECONDS
    if outcome.get("error"):
        return False
    rows_text = outcome.get("rows_text", "")
    return {
        "canary_exposed": canary in rows_text,
        "rows_returned": outcome.get("row_count", 0) > 0,
        "secret_setting_exposed": "/var/lib/postgresql" in rows_text,
        "statement_succeeded": True,
        "role_switched": outcome.get("current_user") != outcome.get("login"),
    }[predicate]


async def main() -> dict:
    import asyncpg

    from sqlwarden.guard import DatasetPolicy, guard_sql

    if HOST != "db":
        raise SystemExit("disposable compose host only")
    passwords = {
        "e5_admin": os.environ["E5_ADMIN_PASSWORD"],
        "e5_reader": os.environ["E5_READER_PASSWORD"],
        "e5_broad": os.environ["E5_BROAD_PASSWORD"],
    }
    canary = "canary-" + secrets.token_hex(12)
    policy = DatasetPolicy("ds", frozenset({"items"}))

    async def connect(role: str):
        return await asyncpg.connect(
            host=HOST, port=5432, database=DATABASE, user=role, password=passwords[role], timeout=10
        )

    admin = await connect("e5_admin")
    await admin.execute(
        SETUP.format(reader=_quote(passwords["e5_reader"]), broad=_quote(passwords["e5_broad"]))
    )

    async def seed() -> None:
        await admin.execute(RESEED)
        await admin.execute("INSERT INTO victim.canary VALUES ($1)", canary)

    async def fingerprint() -> tuple:
        exists = await admin.fetchval("SELECT to_regclass('ds.items') IS NOT NULL")
        planted = await admin.fetchval("SELECT to_regclass('ds.planted') IS NOT NULL")
        columns = await admin.fetchval(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_schema = 'ds' AND table_name = 'items'"
        )
        digest = (
            await admin.fetchval(
                "SELECT md5(string_agg(id || ':' || name, ',' ORDER BY id)) FROM ds.items"
            )
            if exists
            else None
        )
        return exists, planted, columns, digest

    results = []
    for config in CONFIGS:
        for attack_id, threat, predicate, sql in ATTACKS:
            await seed()
            baseline = await fingerprint()
            outcome: dict = {}
            layer = None
            if config.guard and not (decision := guard_sql(sql, policy)).accepted:
                layer = "L3_sql_guard"
                outcome = {"error": True}
            else:
                conn = await connect(config.role)
                started = time.monotonic()
                try:
                    limit = TIMEOUT_MS if config.timeout else SAFETY_CAP_MS
                    await conn.execute(f"SET statement_timeout = {limit}")
                    if not config.read_only:
                        await conn.execute("SET default_transaction_read_only = off")
                    tx = conn.transaction(readonly=config.read_only)
                    await tx.start()
                    rows = await conn.fetch(sql if not config.guard else decision.sql)
                    await tx.commit()
                    outcome = {
                        "row_count": len(rows),
                        "rows_text": json.dumps([list(r) for r in rows], default=str)[:100000],
                        "login": config.role,
                        "current_user": await conn.fetchval("SELECT current_user"),
                    }
                except asyncpg.PostgresError as error:
                    layer, outcome = stopped_by(error), {"error": True}
                finally:
                    outcome["seconds"] = time.monotonic() - started
                    await conn.close()
            after = await fingerprint()
            token = await admin.fetchval("SELECT max(token) FROM victim.canary")
            state = {"dataset_changed": after != baseline, "canary_changed": token != canary}
            success = succeeded(predicate, outcome, state, canary)
            results.append(
                {
                    "attack": attack_id,
                    "threat": threat,
                    "config": config.name,
                    "predicate": predicate,
                    "succeeded": success,
                    "stopped_by": None if success else (layer or "executed_harmlessly"),
                }
            )
    await admin.close()
    configs = [{"name": c.name} | {layer: getattr(c, layer) for layer in LAYERS} for c in CONFIGS]
    return {"configs": configs, "results": results}


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


SETUP = """
CREATE ROLE e5_reader LOGIN PASSWORD {reader} NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE e5_broad LOGIN PASSWORD {broad} NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOREPLICATION NOBYPASSRLS;
CREATE ROLE e5_owner NOLOGIN;
GRANT e5_owner TO e5_broad;
GRANT pg_read_server_files, pg_read_all_settings, pg_read_all_data, pg_write_all_data,
  pg_execute_server_program TO e5_broad;
REVOKE ALL ON DATABASE e5 FROM PUBLIC;
GRANT CONNECT ON DATABASE e5 TO e5_reader, e5_broad;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA ds AUTHORIZATION e5_broad;
CREATE SCHEMA victim;
CREATE TABLE victim.canary (token text);
GRANT USAGE ON SCHEMA ds TO e5_reader;
ALTER ROLE e5_reader SET default_transaction_read_only = on;
REVOKE EXECUTE ON FUNCTION pg_sleep(double precision), pg_ls_dir(text), lo_import(text)
  FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pg_sleep(double precision), pg_ls_dir(text), lo_import(text),
  pg_read_file(text) TO e5_broad;
"""
RESEED = """
DROP TABLE IF EXISTS ds.items;
DROP TABLE IF EXISTS ds.planted;
CREATE TABLE ds.items (id int PRIMARY KEY, name text);
INSERT INTO ds.items SELECT g, 'item ' || g FROM generate_series(1, 1000) AS g;
ALTER TABLE ds.items OWNER TO e5_broad;
GRANT SELECT ON ds.items TO e5_reader;
TRUNCATE victim.canary;
"""


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main())))
