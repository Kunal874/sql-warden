import re
from contextlib import asynccontextmanager
from datetime import UTC

import pytest

from scripts import load_release as loader

TABLE = {
    "columns": [
        {
            "name": "id",
            "native_type": "BIGINT",
            "declared_not_null": False,
            "primary_key_position": 1,
        },
        {
            "name": "when",
            "native_type": "TIMESTAMPTZ",
            "declared_not_null": False,
            "primary_key_position": 0,
        },
    ],
    "primary_key": ["id"],
}


def test_credentials_are_private_complete_and_refuse_overwrite(tmp_path):
    loader.initialize_credentials(tmp_path)
    file = tmp_path / ".env.datasets"
    before = file.read_bytes()
    rows = dict(line.split("=", 1) for line in before.decode().splitlines())
    assert set(rows) == {loader.password_key(i) for i in loader.DB_IDS}
    assert all(re.fullmatch("[a-f0-9]{48}", p) for p in rows.values())
    assert len(set(rows.values())) == len(loader.DB_IDS)
    assert "BOOTSTRAP" not in rows and "CALIFORNIA" not in rows
    with pytest.raises(FileExistsError):
        loader.initialize_credentials(tmp_path)
    assert file.read_bytes() == before


def test_ddl_uses_only_reviewed_types_and_key_metadata():
    assert (
        loader.table_definition(TABLE)
        == '"id" BIGINT NOT NULL, "when" TIMESTAMPTZ, PRIMARY KEY ("id")'
    )
    changed = {
        **TABLE,
        "columns": [{**TABLE["columns"][0], "native_type": "TEXT; DROP SCHEMA app"}],
    }
    with pytest.raises(ValueError):
        loader.table_definition(changed)


@pytest.mark.parametrize("password", ["", "a" * 47, "A" * 48, "'" * 48])
async def test_invalid_password_refuses_before_connection(tmp_path, password):
    with pytest.raises(ValueError):
        await loader.load_dataset(object(), tmp_path, "toxicology", password)


class Connection:
    def __init__(self, *, exists=False, bad_count=False, fail_copy=False):
        self.exists, self.bad_count, self.fail_copy = exists, bad_count, fail_copy
        self.commands, self.events, self.copies = [], [], []

    @asynccontextmanager
    async def transaction(self):
        self.events.append("begin")
        try:
            yield
        except BaseException:
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")

    async def execute(self, sql):
        self.commands.append(sql)

    async def fetchval(self, sql, *args):
        if sql.startswith("SELECT EXISTS"):
            return self.exists
        return 0 if self.bad_count else 1

    async def copy_to_table(self, name, **kwargs):
        if self.fail_copy:
            raise ValueError("injected COPY failure")
        self.copies.append((name, kwargs))


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(loader, "validate_bundle", lambda source, db_id: {"sample": TABLE})
    source_audit = {
        "databases": {
            "toxicology": {
                "foreign_key_check_status": "schema_mismatch",
                "foreign_key_violation_count": None,
            }
        }
    }
    monkeypatch.setattr(
        loader, "load_specs", lambda: ({"tables": {"sample": {"copy": {"rows": 1}}}}, source_audit)
    )

    async def identity(conn):
        conn.events.append("verified local")

    async def content(conn, source, tables, **kwargs):
        conn.events.append(("content checked", kwargs))

    monkeypatch.setattr(loader, "verify_local_database", identity)
    monkeypatch.setattr(loader, "verify_native_content", content)

    async def samples(*args):
        return {"sample": 1}

    monkeypatch.setattr(loader, "verify_sqlite_samples", samples)


async def test_fixed_role_settings_scoped_grants_and_content_before_commit(setup, tmp_path):
    conn = Connection()
    result = await loader.load_dataset(conn, tmp_path, "toxicology", "a" * 48)
    joined = "\n".join(conn.commands)
    assert "NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE" in joined
    assert "NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2" in joined
    assert 'CREATE SCHEMA "toxicology" AUTHORIZATION warden_owner' in joined
    assert 'REVOKE ALL ON SCHEMA "toxicology" FROM PUBLIC' in joined
    assert 'GRANT SELECT ON ALL TABLES IN SCHEMA "toxicology"' in joined
    assert "default_transaction_read_only" in joined and "search_path=pg_catalog" in joined
    assert "FOREIGN KEY" not in joined and "california_schools" not in joined
    assert conn.events[0:2] == ["begin", "verified local"]
    assert conn.events[-2][0] == "content checked" and conn.events[-1] == "commit"
    assert result["typed_native_content_verified"] is True
    assert result["source_foreign_key_violation_count"] is None
    assert result["gold_conversion_validity"] == "not checked"


@pytest.mark.parametrize("mode", ["existing", "count", "copy", "identity", "content", "sample"])
async def test_failures_do_not_commit(setup, tmp_path, monkeypatch, mode):
    conn = Connection(
        exists=mode == "existing", bad_count=mode == "count", fail_copy=mode == "copy"
    )

    async def fail(*args, **kwargs):
        raise ValueError("injected failure")

    if mode == "identity":
        monkeypatch.setattr(loader, "verify_local_database", fail)
    if mode == "content":
        monkeypatch.setattr(loader, "verify_native_content", fail)
    if mode == "sample":
        monkeypatch.setattr(loader, "verify_sqlite_samples", fail)
    with pytest.raises((ValueError, FileExistsError)):
        await loader.load_dataset(conn, tmp_path, "toxicology", "a" * 48)
    assert conn.events[-1] == "rollback" and "commit" not in conn.events
    if mode in {"identity", "existing"}:
        assert not conn.commands


async def test_cancel_rolls_back(setup, tmp_path, monkeypatch):
    import asyncio

    conn = Connection()

    async def cancel(*args, **kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(loader, "verify_native_content", cancel)
    with pytest.raises(asyncio.CancelledError):
        await loader.load_dataset(conn, tmp_path, "toxicology", "a" * 48)
    assert conn.events[-1] == "rollback"


@pytest.mark.parametrize(
    "value,kind,wanted",
    [
        (None, "REAL", None),
        (3, "INTEGER", 3),
        ("literal", "TEXT", "literal"),
        (1.00000001, "REAL", 1.0),
    ],
)
def test_native_sample_conversion_is_explicit(value, kind, wanted):
    assert loader.native_sample_value(value, kind) == wanted


def test_date_and_datetime_samples_use_iso_and_explicit_utc():
    from datetime import date, datetime

    assert loader.native_sample_value("2020-01-01", "DATE") == date(2020, 1, 1)
    assert loader.native_sample_value("2020-01-01 12:30:00", "DATETIME") == datetime(
        2020, 1, 1, 12, 30, tzinfo=UTC
    )
    assert loader.native_sample_value("2020-01-01T14:30:00+02:00", "DATETIME") == datetime(
        2020, 1, 1, 12, 30, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "value,kind",
    [
        (True, "INTEGER"),
        ("3", "INTEGER"),
        (float("nan"), "REAL"),
        (float("inf"), "REAL"),
        ("not-a-date", "DATE"),
        (b"bytes", "TEXT"),
        (1, "BLOB"),
    ],
)
def test_unreviewed_sample_values_refuse(value, kind):
    with pytest.raises(ValueError):
        loader.native_sample_value(value, kind)


@pytest.mark.parametrize("bad", [False, True])
async def test_sqlite_representative_first_middle_last_nulls_and_mismatch(
    tmp_path, monkeypatch, bad
):
    import hashlib
    import sqlite3

    path = tmp_path / "sqlite/source.sqlite"
    path.parent.mkdir()
    with sqlite3.connect(path) as sqlite:
        sqlite.executescript(
            "CREATE TABLE Thing (id INTEGER PRIMARY KEY, value REAL); "
            "INSERT INTO Thing VALUES (1,1.00000001),(2,NULL),(3,2.5);"
        )
    pins = {
        "sqlite_sources": [
            {
                "db_id": "toxicology",
                "output": "sqlite/source.sqlite",
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        ],
        "tables": {"thing": {"copy": {"rows": 3}}},
    }
    tables = {
        "thing": {
            "source_name": "Thing",
            "columns": [
                {
                    "name": "id",
                    "source_name": "id",
                    "source_type": "INTEGER",
                    "primary_key_position": 1,
                },
                {
                    "name": "value",
                    "source_name": "value",
                    "source_type": "REAL",
                    "primary_key_position": 0,
                },
            ],
        }
    }
    monkeypatch.setattr(loader, "SOURCE_DIR", tmp_path)

    class Probe:
        def __init__(self):
            self.values = []

        async def fetchval(self, sql, *values):
            self.values.append(values)
            assert '"toxicology"."thing"' in sql
            assert '"value" IS NOT DISTINCT FROM $2' in sql
            return not bad

    conn = Probe()
    if bad:
        with pytest.raises(ValueError, match="representative comparison"):
            await loader.verify_sqlite_samples(conn, "toxicology", tables, pins)
    else:
        assert await loader.verify_sqlite_samples(conn, "toxicology", tables, pins) == {"thing": 3}
        assert conn.values == [(1, 1.0), (2, None), (3, 2.5)]


@pytest.mark.parametrize("db_id", ["california_schools", "app", "../escape", "hosted"])
async def test_unapproved_dataset_rejected_before_connection(tmp_path, db_id):
    with pytest.raises(ValueError):
        await loader.load_dataset(object(), tmp_path, db_id, "a" * 48)
