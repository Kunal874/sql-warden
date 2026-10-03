"""Setup validation and direct real-PostgreSQL checks for the California import."""

import csv
import hashlib
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
import pytest
from test_postgres_boundary import LARGE_OBJECT_FUNCTIONS, connected, rolled_back

from scripts import load_bird
from sqlwarden.data import pg_name, quote_ident

CALIFORNIA_ROLE = "warden_sandbox_california_schools"
SOURCE = Path("data/bird_california/native")
IMPORT_MANIFEST = Path("docs/california-import-manifest.json")


@pytest.mark.parametrize(
    "target,port", [(None, "55432"), ("hosted", "55432"), ("sqlwarden-local", "5432")]
)
def test_setup_target_rejects_missing_marker_wrong_project_and_port(target, port):
    values = {"WARDEN_PG_PORT": port, "WARDEN_BOOTSTRAP_PASSWORD": "a" * 48}
    if target is not None:
        values["WARDEN_TEST_TARGET"] = target
    with pytest.raises(ValueError):
        load_bird.setup_connection_options(values)


def test_setup_target_has_only_the_fixed_local_connection():
    options = load_bird.setup_connection_options(
        {
            "WARDEN_TEST_TARGET": "sqlwarden-local",
            "WARDEN_PG_PORT": "55432",
            "WARDEN_BOOTSTRAP_PASSWORD": "a" * 48,
        }
    )
    assert (options["host"], options["port"], options["database"], options["user"]) == (
        "127.0.0.1",
        55432,
        "sqlwarden",
        "warden_bootstrap",
    )


@pytest.mark.parametrize("password", ["", "short", "A" * 48, "'" * 48, "a" * 47])
async def test_bad_password_rejects_before_accessing_connection(tmp_path, password):
    with pytest.raises(ValueError, match="password"):
        await load_bird.load_california(object(), tmp_path, password)


@pytest.fixture
def source_fixture(tmp_path, monkeypatch):
    source = tmp_path / "native"
    source.mkdir()
    sqlite_path = tmp_path / "california_schools.sqlite"
    with sqlite3.connect(sqlite_path) as conn:
        conn.executescript(
            "CREATE TABLE schools (CDSCode TEXT PRIMARY KEY);"
            "CREATE TABLE frpm (CDSCode TEXT PRIMARY KEY REFERENCES schools(CDSCode));"
            "CREATE TABLE satscores (cds TEXT PRIMARY KEY REFERENCES schools(CDSCode));"
        )
    monkeypatch.setattr(
        load_bird, "SQLITE_SHA256", hashlib.sha256(sqlite_path.read_bytes()).hexdigest()
    )
    expected = {}
    for name in ["schools", "frpm", "satscores"]:
        (source / f"{name}.tsv").write_bytes(b"1\n")
        expected[name] = {"rows": 1, "bytes": 2, "sha256": hashlib.sha256(b"1\n").hexdigest()}
    monkeypatch.setattr(load_bird, "NATIVE_EXPECTED", expected)
    manifest = {
        name: {**entry, "columns": ["cds" if name == "satscores" else "cdscode"]}
        for name, entry in expected.items()
    }
    (source / "manifest.json").write_text(json.dumps(manifest))
    return source


def test_valid_source_is_rechecked_from_bytes_and_metadata(source_fixture):
    tables = load_bird.validate_source(source_fixture)
    assert tables["satscores"]["primary_key"] == ["cds"]


@pytest.mark.parametrize("problem", ["missing_manifest", "changed_file", "schema", "rows"])
async def test_bad_source_rejects_before_accessing_connection(source_fixture, problem):
    manifest_path = source_fixture / "manifest.json"
    if problem == "missing_manifest":
        manifest_path.unlink()
    elif problem == "changed_file":
        (source_fixture / "schools.tsv").write_bytes(b"2\n")
    else:
        manifest = json.loads(manifest_path.read_text())
        if problem == "schema":
            manifest["schools"]["columns"] = ["different"]
        else:
            manifest["schools"]["rows"] = 2
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        await load_bird.load_california(object(), source_fixture, "a" * 48)


@asynccontextmanager
async def california_connected():
    if os.environ.get("WARDEN_TEST_TARGET") != "sqlwarden-local" or not os.environ.get(
        "WARDEN_CALIFORNIA_PASSWORD"
    ):
        pytest.skip("Supply the dedicated .env.setup and .env.california for real import checks")
    if os.environ.get("WARDEN_PG_PORT") != "55432":
        pytest.fail("California checks require the fixed dedicated local port")
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=55432,
            database="sqlwarden",
            user=CALIFORNIA_ROLE,
            password=os.environ["WARDEN_CALIFORNIA_PASSWORD"],
            timeout=5,
        )
    except (OSError, asyncpg.InvalidAuthorizationSpecificationError):
        pytest.fail("The actual California login must exist and authenticate", pytrace=False)
    try:
        yield conn
    finally:
        await conn.close()


@pytest.mark.integration
async def test_california_reader_counts_and_own_join():
    async with california_connected() as conn:
        for name, count in [("schools", 17686), ("frpm", 9986), ("satscores", 2269)]:
            assert await conn.fetchval(f"SELECT count(*) FROM california_schools.{name}") == count
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM california_schools.frpm f "
                "JOIN california_schools.schools s USING (cdscode)"
            )
            == 9986
        )
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM california_schools.satscores t "
                "JOIN california_schools.schools s ON s.cdscode=t.cds"
            )
            == 2269
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE california_schools.schools SET school='not allowed'",
        "DELETE FROM california_schools.frpm",
        "TRUNCATE california_schools.satscores",
        "CREATE TABLE california_schools.forbidden (id int)",
        "CREATE TEMP TABLE forbidden (id int)",
        "SELECT * FROM app.boundary_probe",
        "SELECT * FROM demo_other.canary",
        "SET ROLE warden_owner",
        "SET ROLE warden_app",
        "SELECT pg_catalog.lo_create(0)",
    ],
)
async def test_california_direct_denials_survive_read_only_setting_changes(sql):
    async with california_connected() as conn:
        await conn.execute("SET default_transaction_read_only=off")
        async with rolled_back(conn):
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(sql)


@pytest.mark.integration
async def test_california_role_owner_defaults_and_risky_function_acls():
    async with california_connected() as conn:
        role = await conn.fetchrow(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit,"
            "rolconnlimit FROM pg_roles WHERE rolname=current_user"
        )
        assert tuple(role) == (False, False, False, False, False, False, 2)
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_auth_members WHERE member="
                "(SELECT oid FROM pg_roles WHERE rolname=current_user)"
            )
            == 0
        )
        assert await conn.fetchval("SHOW default_transaction_read_only") == "on"
        assert await conn.fetchval("SHOW search_path") == "pg_catalog, california_schools"
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='california_schools' "
                "AND c.relkind='r' AND r.rolname='warden_owner'"
            )
            == 3
        )
        names = [*LARGE_OBJECT_FUNCTIONS, "pg_read_file", "pg_sleep", "pg_ls_dir"]
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='pg_catalog' AND p.proname=ANY($1::text[]) "
                "AND has_function_privilege(current_user,p.oid,'EXECUTE')",
                names,
            )
            == 0
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "role", ["warden_sandbox_demo_schools", "warden_sandbox_demo_other", "warden_app"]
)
async def test_other_runtime_logins_cannot_read_california(role):
    async with connected(role) as conn, rolled_back(conn):
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetchval("SELECT count(*) FROM california_schools.schools")


@pytest.mark.integration
async def test_california_future_owner_grants_stay_dataset_specific():
    async with california_connected():
        pass
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        await conn.execute("SET LOCAL ROLE warden_owner")
        await conn.execute("CREATE TABLE california_schools.future_probe (id int)")
        assert await conn.fetchval(
            "SELECT has_table_privilege($1,'california_schools.future_probe','SELECT')",
            CALIFORNIA_ROLE,
        )
        for role in ["warden_sandbox_demo_other", "warden_sandbox_demo_schools", "warden_app"]:
            assert not await conn.fetchval(
                "SELECT has_table_privilege($1,'california_schools.future_probe','SELECT')", role
            )
        assert not await conn.fetchval(
            "SELECT has_table_privilege($1,'california_schools.future_probe','INSERT')",
            CALIFORNIA_ROLE,
        )


@pytest.mark.integration
async def test_repeat_import_preserves_existing_schema_role_and_counts():
    async with california_connected():
        pass
    async with connected("warden_bootstrap") as conn:
        before = await conn.fetchval("SELECT count(*) FROM california_schools.schools")
        with pytest.raises(FileExistsError):
            await load_bird.load_california(conn, SOURCE, os.environ["WARDEN_CALIFORNIA_PASSWORD"])
        assert await conn.fetchval("SELECT count(*) FROM california_schools.schools") == before


@pytest.mark.integration
async def test_unmodified_native_content_passes_complete_typed_comparison():
    async with california_connected():
        pass
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        await load_bird.verify_native_content(conn, SOURCE, load_bird.validate_source(SOURCE))


@pytest.mark.integration
async def test_content_verifier_detects_same_count_changed_values_and_probe_rolls_back():
    async with california_connected():
        pass
    async with connected("warden_bootstrap") as conn:
        row = await conn.fetchrow(
            "SELECT cdscode,school FROM california_schools.schools ORDER BY cdscode LIMIT 1"
        )
        before = await conn.fetchval("SELECT count(*) FROM california_schools.schools")
        async with rolled_back(conn):
            await conn.execute(
                "UPDATE california_schools.schools SET school=coalesce(school,'') || '_probe' "
                "WHERE cdscode=$1",
                row["cdscode"],
            )
            assert await conn.fetchval("SELECT count(*) FROM california_schools.schools") == before
            with pytest.raises(ValueError, match="content differs"):
                await load_bird.verify_native_content(
                    conn, SOURCE, load_bird.validate_source(SOURCE)
                )
        assert (
            await conn.fetchval(
                "SELECT school FROM california_schools.schools WHERE cdscode=$1", row["cdscode"]
            )
            == row["school"]
        )


async def capture_import_evidence():
    """Test utility: record only metadata/hashes, never credentials, gold SQL or rows."""
    tables = load_bird.validate_source(SOURCE)
    evidence = {}
    async with california_connected() as conn, conn.transaction(readonly=True):
        await conn.execute(
            "SET LOCAL extra_float_digits=3; SET LOCAL DateStyle='ISO,YMD'; "
            "SET LOCAL timezone='UTC'"
        )
        for name, table in tables.items():
            columns = [c["name"] for c in table["columns"]]
            target = "california_schools." + quote_ident(name)
            primary_key = quote_ident(table["primary_key"][0])
            checksum = hashlib.sha256()
            byte_count = 0

            async def consume(data, checksum=checksum):
                nonlocal byte_count
                byte_count += len(data)
                if byte_count > 32 * 1024 * 1024:
                    raise ValueError("Native evidence export exceeded budget")
                checksum.update(data)

            projection = ",".join(map(quote_ident, columns))
            status = await conn.copy_from_query(
                f'SELECT {projection} FROM {target} ORDER BY {primary_key} COLLATE "C"',
                output=consume,
                format="text",
                encoding="UTF8",
                timeout=15,
            )
            nulls = await conn.fetchrow(
                "SELECT "
                + ",".join(
                    f"count(*) FILTER (WHERE {quote_ident(column)} IS NULL)" for column in columns
                )
                + " FROM "
                + target
            )
            types = await conn.fetch(
                "SELECT column_name,data_type,is_nullable FROM information_schema.columns "
                "WHERE table_schema='california_schools' AND table_name=$1 "
                "ORDER BY ordinal_position",
                name,
            )
            actual = [(r["column_name"], r["data_type"], r["is_nullable"] == "NO") for r in types]
            wanted = [(c["name"], c["type"], c["not_null"]) for c in table["columns"]]
            assert actual == wanted
            with (SOURCE.parent / f"{name}.csv").open(encoding="utf-8-sig", newline="") as file:
                descriptions = list(csv.DictReader(file))
            description_names = [
                pg_name(row["original_column_name"].strip()) for row in descriptions
            ]
            assert len(description_names) == len(columns)
            assert set(description_names) == set(columns)
            evidence[name] = {
                "rows": int(status.split()[1]),
                "ordered_copy_bytes": byte_count,
                "ordered_copy_sha256": checksum.hexdigest(),
                "null_counts": list(nulls),
                "columns": [
                    [c["source_name"], c["name"], c["type"], c["not_null"]]
                    for c in table["columns"]
                ],
                "primary_key": table["primary_key"],
                "foreign_key": list(table["foreign_key"]) if table["foreign_key"] else None,
                "description_name_adaptations": {
                    row["original_column_name"]: row["original_column_name"].strip()
                    for row in descriptions
                    if row["original_column_name"] != row["original_column_name"].strip()
                },
                "native_source": load_bird.NATIVE_EXPECTED[name],
            }
    return evidence


@pytest.mark.integration
async def test_recorded_import_matches_live_ordered_content_types_nulls_and_descriptions():
    async with california_connected():
        pass
    manifest = json.loads(IMPORT_MANIFEST.read_text(encoding="utf-8"))
    assert await capture_import_evidence() == manifest["tables"]


@pytest.mark.integration
async def test_native_date_float4_bigint_and_key_constraints_are_preserved():
    async with california_connected() as conn:
        observed = dict(
            await conn.fetch(
                "SELECT attname,format_type(atttypid,atttypmod) FROM pg_attribute "
                "WHERE attrelid='california_schools.schools'::regclass AND attname=ANY($1::text[])",
                ["opendate", "closeddate", "lastupdate", "latitude", "longitude", "charter"],
            )
        )
        assert observed == {
            "opendate": "date",
            "closeddate": "date",
            "lastupdate": "date",
            "latitude": "real",
            "longitude": "real",
            "charter": "bigint",
        }
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace "
                "WHERE n.nspname='california_schools' AND c.contype='p'"
            )
            == 3
        )
        assert (
            await conn.fetchval(
                "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace "
                "WHERE n.nspname='california_schools' AND c.contype='f' AND c.convalidated"
            )
            == 2
        )
        for table, key in [("schools", "cdscode"), ("frpm", "cdscode"), ("satscores", "cds")]:
            assert await conn.fetchval(
                f"SELECT count(*)=count(DISTINCT {key}) FROM california_schools.{table}"
            )


@pytest.mark.integration
async def test_pinned_sources_and_labels_match_by_unique_ids_not_position():
    async with california_connected():
        pass
    manifest = json.loads(IMPORT_MANIFEST.read_text(encoding="utf-8"))
    for name, expected in manifest["source_files"].items():
        path = Path(name)
        with path.open("rb") as file:
            assert hashlib.file_digest(file, "sha256").hexdigest() == expected["sha256"]
        assert path.stat().st_size == expected["bytes"]
    dialects = [
        json.loads(Path("data/raw/mini_dev_" + dialect + ".json").read_text(encoding="utf-8"))
        for dialect in ("sqlite", "pg")
    ]
    indexed = [{row["question_id"]: row for row in rows} for rows in dialects]
    assert len(indexed[0]) == len(dialects[0]) == len(indexed[1]) == len(dialects[1]) == 500
    assert set(indexed[0]) == set(indexed[1])
    assert all(indexed[0][i]["db_id"] == indexed[1][i]["db_id"] for i in indexed[0])
    for field in ("question", "evidence"):
        different = sorted(i for i in indexed[0] if indexed[0][i][field] != indexed[1][i][field])
        assert different == manifest["label_alignment"][field + "_different_ids"]
    selected = sorted(i for i, row in indexed[0].items() if row["db_id"] == "california_schools")
    assert selected == [
        5,
        11,
        12,
        17,
        23,
        24,
        25,
        26,
        27,
        28,
        31,
        32,
        36,
        37,
        39,
        40,
        41,
        45,
        46,
        47,
        48,
        50,
        62,
        72,
        77,
        79,
        82,
        83,
        85,
        87,
    ]
    assert selected == manifest["label_alignment"]["california_question_ids"]
    assert all(
        indexed[0][i][field] == indexed[1][i][field]
        for i in selected
        for field in ("question", "evidence")
    )
