# Remaining native dataset imports — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task-by-task, natively and sequentially, with one fresh whole-batch read-only reviewer. No parallel implementation. Steps use checkbox syntax.

**Goal:** Import the ten remaining pinned datasets with separate restricted logins and verified native typed content, representative SQLite values, keys and actual access denials, without editing sources or benchmark policy.

**Architecture:** Extend the existing offline COPY auditor and setup-only California importer with backward-compatible optional arguments. New setup tools select only fixed IDs, pinned metadata and the dedicated local PostgreSQL target. One transaction per dataset; no source dump statements, model or gold SQL.

**Tech Stack:** Python 3.12/uv, PostgreSQL 16/Docker, existing asyncpg and stdlib; no direct dependency additions.

**Spec:** docs/BUILD_SPEC.md sections 2–8/11, preserved sqlwarden-plan.md G0.5, actual source-audit-manifest.json and D-036–D-040. Reuse the already approved architecture.

**Status:** Prepared 2026-10-05 from clean 3f4b61f. NOT approved or implemented. Kunal requests trying to finish G0 in one run; this does not approve a new artifact, ten new credentials, source-key policy or benchmark choices. After artifact/operation approval execute all four tasks without routine continuation questions; pause only for genuine failures or new required decisions.

## Understanding and alternatives

Finish foundation work efficiently, preserve the first working local demo, and record evidence Kunal can explain. Do not repeat completed setup/intake/California/source-preparation tasks or their reviews.

1. Recommended: preserve all source rows/native types, enforce verified primary keys, retain all foreign keys as explicitly unenforced metadata in the ten new datasets. No silent data repair/dropping.
2. Enforce every original FK: cannot finish with known violations and European Football's invalid parent-key definition.
3. Repair/drop source rows or keys: changes the corpus and needs a different reviewed data/benchmark policy.

Approval of this plan includes option 1. It does not establish referential validity or change California's existing enforced FKs. C1 reviews implications for labels/conversion later.

## Global constraints and exact proposed operations

- Work in D:/PROJECTS/SQLWARDEN on feat/foundation. Kunal <kunalchandrakar2005@gmail.com> is sole author/committer; inspect staged diff/exact Conventional Commit message first and identity/body afterward. No bot credits/trailers.
- No remote, push, publication, hosted inference, account/spend, model download/inference, new dependency or runtime redesign.
- Preserve historical planning inputs, raw sources, California objects, .env.setup/.env.california/.env.runtime, PostgreSQL 17 and sqlwarden_pg16_data. Never print credentials or put them in reports/prompts.
- Create only absent data/import-release/minidev-0703/native and .env.datasets. Raw payloads/credentials/evidence stay ignored. Existing paths/schemas/roles refuse changes; no drop/truncate/rotation or automatic recovery.
- Generate ten separate restricted-login passwords in setup/test-only .env.datasets; no bootstrap/app/California keys. New logins are warden_sandbox_<db_id> for fixed DB_IDS. No runtime credential wiring.
- Setup writes: warden_bootstrap at 127.0.0.1:55432/sqlwarden, PostgreSQL major 16 and existing ownership markers. Setup/test envs never launch runtime/model.
- Create 72 tables/709 columns using native TEXT/BIGINT/REAL/DATE/TIMESTAMPTZ; source NOT NULL and 69 checked PKs enforced. Retain 103 remaining FK component records as metadata; zero new FK constraints. Do not call relationships valid.
- Setup timezone UTC/ISO,YMD. Representative DATETIME text without a zone assumes UTC; REAL uses float4. These are explicit native-domain sample adaptations, not a changed EX comparator/full SQLite equivalence.
- COPY preparation: 1200s cooperative envelope, 1 MiB line bound, exact full archive/dump/block pins, 1 GiB D: reserve above 991363484 payload bytes. Publish only after all 72 saved payloads recheck.
- Each import: one connection/transaction/dataset, 900s async transaction envelope (not a hard total including prior file hashing), 120s setup command/statement/COPY, 500ms lock, 16MB work_mem, setup-only 2GB temp_file_limit and 30s idle transaction. Reader defaults stay 5s/500ms/16MB/64MB, connection limit 2. Docker remains 768 MiB/1 CPU; no resource-limit expansion.
- Actual import attempts: 3600s aggregate envelope checked before starting each; no retry or automatic timeout increase.
- Writes limited to new schemas/logins/grants and named rollback-only probes: sqlwarden_import_probe/warden_sandbox_sqlwarden_import_probe, future_grant_probe and one-row toxicology mutation. These never persist and do not authorize unrelated changes.
- Dataset transactions are individually atomic, not one all-ten transaction. On failure preserve verified completed datasets, stop and record exact IDs. Existing targets are refusal, not authority to auto-skip/reset/reimport.
- Tests first for credential/refusal/DDL/rollback/content/security boundaries. Actual PostgreSQL checks precede isolation claims. Private commands always --tb=line; never --showlocals.
- Update DATA/PROGRESS/DECISIONS and explaination of project/PROJECT_EXPLAINED.md after completed subtasks. G0.5/C1 remain unfinished until real conversion/policy completion.

## Observed read-only preflight

Only California schema/login exist. PostgreSQL 16 identity/ownership markers pass; database 20585495 bytes. COPY destination and .env.datasets absent.
Remaining: 72 tables/709 columns/3868173 rows/991363484 COPY bytes. Largest block European match 280029547 bytes.
All 72 source PKs have no null key rows or duplicate key groups; California owns three. Three no-PK tables: examination, hero_attribute, hero_power. All 11 codebase DATETIME columns contain text/null storage only; not value/answer validation.
Known FK issues: 779 formula_1/88 card_games/88 codebase_community records, European schema_mismatch/null.
D: free 44817014784 bytes; C: free 661347966976; Docker volume filesystem available 1008069328896 (virtual, not physical capacity guarantee). RAM free 1511016 KiB; NVIDIA sampled 7956 MiB free/0 MiB used. No model loaded by preparation.
No acquisition/source rewrite/new schema/role/credential/model/gold/benchmark action occurred.

## Review focus

1. Arbitrary IDs/roles/passwords/external targets: reject before writes; fixed IDs/local identity/version/ownership markers required. Task 2 refusal tests plus existing target tests/Task 3 real controls.
2. Altered/truncated/partial COPY/metadata/repeated outputs: no success/publication/overwrite. Task 1 pin/sink/refusal and Task 2 rollback tests.
3. Same-count changed values, NULLs/float4/dates/timezones/interruption: native EXCEPT ALL and explicit representative mappings; no full SQLite/gold claim. Task 2 sample tests and Task 3 actual mutation/partial-COPY rollback.
4. PUBLIC/default/future/cross-schema/cluster/SET ROLE access after disabling read-only defaults: real direct denials. Task 3/4 matrix, old-reader/future/cluster/function checks.
5. Source FK defects/no-PK/quoted identities/native failure: preserve rows/metadata; no quiet validity claim. Task 2 DDL/report tests and Task 3 ordered-layout/PK/content acceptance.

## Task 1 — controlled remaining COPY bundle

**Files:** Modify scripts/audit_sources.py; create scripts/prepare_import_bundle.py/tests/test_import_bundle.py; living records.
**Interfaces:** inspect_native(...,deadline,copy_outputs=None) defaults unchanged. prepare_bundle(archive,destination) stages/publishes fixed COPY files; validate_bundle(source,db_id) returns checked table metadata; load_specs()->pins/audit. DB_IDS/BUNDLE feed later tasks exactly.

- [ ] Write tests/test_import_bundle.py first:

```python
import io
import json
import zipfile
from types import SimpleNamespace

import pytest
from test_source_audit import native_fixture, pin

from scripts import audit_sources as audit
from scripts import prepare_import_bundle as bundle

@pytest.fixture
def fixture(tmp_path, monkeypatch):
    dump, tables = native_fixture()
    tables["thing"]["db_id"] = "card_games"
    archive = tmp_path / "source.zip"
    member = "native.sql"
    with zipfile.ZipFile(archive, "w") as target:
        target.writestr(member, dump)
    pins = {"archive": pin(archive.read_bytes()), "native_dump": pin(dump, member=member), "tables": tables}
    columns = [
        {"name": c["name"], "native_type": c["type"], "declared_not_null": False, "primary_key_position": 0}
        for c in tables["thing"]["columns"]
    ]
    metadata = {"tables": {"thing": {"columns": columns, "primary_key": []}}}
    audit_doc = {"databases": {i: metadata if i == "card_games" else {"tables": {}} for i in bundle.DB_IDS}}
    monkeypatch.setattr(bundle, "load_specs", lambda: (pins, audit_doc))
    return archive, pins

def test_native_copy_sink_is_optional_and_exact():
    dump, tables = native_fixture()
    sink = io.BytesIO()
    blocks = audit.inspect_native(io.BytesIO(dump), tables, pin(dump), deadline=float("inf"), copy_outputs={"thing": sink})
    assert blocks["thing"] == tables["thing"]["copy"]
    assert sink.getvalue() == b"1\t2020-01-01\n2\t\\N\n"

def test_bundle_is_pinned_and_never_executes_source_sql(fixture, tmp_path):
    archive, pins = fixture
    destination = tmp_path / "native"
    bundle.prepare_bundle(archive, destination)
    assert (destination / "card_games/thing.tsv").read_bytes() == b"1\t2020-01-01\n2\t\\N\n"
    assert json.loads((destination / "manifest.json").read_text()) == bundle.bundle_metadata(pins)
    assert set(bundle.validate_bundle(destination, "card_games")) == {"thing"}
    assert not list(tmp_path.glob(".release-copy-*"))

@pytest.mark.parametrize("mode", ["existing", "disk", "archive", "block", "metadata", "payload", "deadline"])
def test_bundle_refuses_or_keeps_failed_outputs_private(fixture, tmp_path, monkeypatch, mode):
    archive, pins = fixture
    destination = tmp_path / "native"
    if mode == "existing":
        destination.mkdir()
        (destination / "keep").write_bytes(b"unchanged")
    elif mode == "disk":
        monkeypatch.setattr(bundle.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    elif mode == "archive":
        pins["archive"]["sha256"] = "0" * 64
    elif mode == "block":
        pins["tables"]["thing"]["copy"]["sha256"] = "0" * 64
    elif mode == "deadline":
        monkeypatch.setattr(audit, "monotonic", lambda: float("inf"))
    if mode in {"metadata", "payload"}:
        bundle.prepare_bundle(archive, destination)
        if mode == "metadata":
            (destination / "manifest.json").write_text("{}")
        else:
            (destination / "card_games/thing.tsv").write_bytes(b"changed")
        with pytest.raises(ValueError):
            bundle.validate_bundle(destination, "card_games")
    else:
        with pytest.raises((ValueError, FileExistsError)):
            bundle.prepare_bundle(archive, destination)
        if mode == "existing":
            assert (destination / "keep").read_bytes() == b"unchanged"
        else:
            assert not destination.exists()
        assert not list(tmp_path.glob(".release-copy-*"))

def test_california_and_unrecognized_import_targets_refused(tmp_path):
    for db_id in ("california_schools", "app", "../other", "hosted"):
        with pytest.raises(ValueError):
            bundle.validate_bundle(tmp_path, db_id)

def test_reviewed_metadata_hash_checked_before_use(tmp_path, monkeypatch):
    metadata = tmp_path / "pins.json"
    metadata.write_text("{}")
    monkeypatch.setattr(bundle, "PINS_PATH", metadata)
    with pytest.raises(ValueError, match="metadata fingerprint"):
        bundle.load_specs()
```


- [ ] Run uv run pytest tests/test_import_bundle.py -q --tb=line. Expected missing module RED; no actual extraction.
- [ ] Extend the existing auditor signature and append only the two sink lines after checksum.update(line) in its active COPY data branch; preserve all validation before writing:

```python
def inspect_native(stream: BinaryIO, tables: dict, dump_pin: dict, *, deadline: float, copy_outputs: dict[str, BinaryIO] | None = None) -> dict:
```

```python
                if copy_outputs is not None and active in copy_outputs:
                    copy_outputs[active].write(line)
```


Never write headers/terminators/surrounding SQL; the caller owns unpublished staged streams. None leaves the completed metadata-only audit unchanged.
- [ ] Create scripts/prepare_import_bundle.py:

```python
"""Setup-only extraction of pinned native COPY payloads for ten new datasets."""
import json
import shutil
import zipfile
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from scripts.audit_sources import inspect_native
from scripts.prepare_sources import (
    ARCHIVE, PINS_PATH, checked_file, load_pins, new_destination,
    relative_path, selected_member,
)
from sqlwarden.data import file_sha256

AUDIT_PATH = Path("docs/source-audit-manifest.json")
PINS_SHA = "f8c61dbc426deab580174c965fbd1883192e98ec30253e8d2b6aa85eb7114f7c"
AUDIT_SHA = "f52ecfd71c53fb470bb85e899e4b97178df304e0b30f66cba32518fa7f286c31"
BUNDLE = Path("data/import-release/minidev-0703/native")
DB_IDS = (
    "toxicology", "thrombosis_prediction", "superhero", "student_club",
    "debit_card_specializing", "formula_1", "financial", "card_games",
    "codebase_community", "european_football_2",
)

def load_specs():
    for path, expected in ((PINS_PATH, PINS_SHA), (AUDIT_PATH, AUDIT_SHA)):
        if path.stat().st_size > 256 * 1024 or file_sha256(path) != expected:
            raise ValueError("Reviewed metadata fingerprint differs")
    pins = load_pins()
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    return pins, audit

def bundle_metadata(pins):
    return {
        "format_version": 1, "source_pins_sha256": PINS_SHA,
        "source_audit_sha256": AUDIT_SHA,
        "tables": {
            name: {"db_id": t["db_id"], "columns": t["columns"], **t["copy"]}
            for name, t in pins["tables"].items() if t["db_id"] in DB_IDS
        },
    }

def validate_bundle(source, db_id):
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    pins, audit = load_specs()
    manifest = source / "manifest.json"
    if manifest.stat().st_size > 256 * 1024:
        raise ValueError("COPY manifest exceeds budget")
    if json.loads(manifest.read_text(encoding="utf-8")) != bundle_metadata(pins):
        raise ValueError("COPY metadata differs")
    tables = audit["databases"][db_id]["tables"]
    wanted = {n: t for n, t in pins["tables"].items() if t["db_id"] == db_id}
    if set(tables) != set(wanted):
        raise ValueError("Dataset table metadata differs")
    for name, table in wanted.items():
        checked_file(source / relative_path(db_id + "/" + name + ".tsv"), table["copy"])
        if [{"name": c["name"], "type": c["native_type"]} for c in tables[name]["columns"]] != table["columns"]:
            raise ValueError("Dataset columns differ")
    return tables

def prepare_bundle(archive_path, destination):
    pins, _audit = load_specs()
    new_destination(destination)
    checked_file(archive_path, pins["archive"])
    selected = bundle_metadata(pins)["tables"]
    deadline = monotonic() + 1200
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(destination.parent).free < sum(t["bytes"] for t in selected.values()) + 2**30:
        raise ValueError("Insufficient COPY disk reserve")
    with TemporaryDirectory(prefix=".release-copy-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "native"
        staging.mkdir()
        with ExitStack() as outputs, zipfile.ZipFile(archive_path) as archive:
            sinks = {}
            for name, table in selected.items():
                path = staging / relative_path(table["db_id"] + "/" + name + ".tsv")
                path.parent.mkdir(parents=True, exist_ok=True)
                sinks[name] = outputs.enter_context(path.open("xb"))
            with archive.open(selected_member(archive, pins["native_dump"])) as stream:
                inspect_native(stream, pins["tables"], pins["native_dump"], deadline=deadline, copy_outputs=sinks)
        (staging / "manifest.json").write_text(json.dumps(bundle_metadata(pins), indent=2) + "\n", encoding="utf-8")
        for db_id in DB_IDS:
            validate_bundle(staging, db_id)
        if monotonic() >= deadline:
            raise ValueError("COPY preparation deadline exceeded")
        new_destination(destination)
        staging.rename(destination)

def main():
    try:
        prepare_bundle(ARCHIVE, BUNDLE)
    except Exception as error:
        print(json.dumps({"status": "failed", "stage": "COPY preparation", "error_type": type(error).__name__}))
        return 1
    print(json.dumps({"status": "prepared", "datasets": 10, "tables": 72}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```


- [ ] Run uv run pytest tests/test_import_bundle.py tests/test_source_audit.py tests/test_bird_native.py -q --tb=line. Expected GREEN including existing controls. Apply planned Ruff formatting/checks.
- [ ] Recheck destination absence/ignore/pins/reserve without envs. Run uv run python -m scripts.prepare_import_bundle once. Expected ten datasets/72 payloads/991363484 bytes, all saved pins match; California excluded. No completed destination rerun.
- [ ] Update DATA/PROGRESS/D-042/notebook with real bytes/limits/tests. Run no-env suite/lint/format/whitespace; inspect staged/exact message feat(data): prepare remaining native copy inputs, commit/verify identity/body. Task-done uses combined deterministic checks above.

## Task 2 — fixed-target importer and credential tool

**Files:** Create scripts/load_release.py/tests/test_release_load.py; modify scripts/load_bird.py content helper only via backward-compatible optional arguments; living records.
**Interfaces:** initialize_credentials(root) creates .env.datasets once; password_key(db_id) server-owned mapping; load_dataset(conn,source,db_id,password)->checked metadata or rollback. native_sample_value/verify_sqlite_samples are setup-only; import_one(db_id) uses fixed local target.

- [ ] Write tests/test_release_load.py first:

```python
import re
from contextlib import asynccontextmanager

import pytest

from scripts import load_release as loader

TABLE = {
    "columns": [
        {"name": "id", "native_type": "BIGINT", "declared_not_null": False, "primary_key_position": 1},
        {"name": "when", "native_type": "TIMESTAMPTZ", "declared_not_null": False, "primary_key_position": 0},
    ], "primary_key": ["id"],
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
    assert loader.table_definition(TABLE) == '"id" BIGINT NOT NULL, "when" TIMESTAMPTZ, PRIMARY KEY ("id")'
    changed = {**TABLE, "columns": [{**TABLE["columns"][0], "native_type": "TEXT; DROP SCHEMA app"}]}
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
    source_audit = {"databases": {"toxicology": {"foreign_key_check_status": "schema_mismatch", "foreign_key_violation_count": None}}}
    monkeypatch.setattr(loader, "load_specs", lambda: ({"tables": {"sample": {"copy": {"rows": 1}}}}, source_audit))
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
    conn = Connection(exists=mode == "existing", bad_count=mode == "count", fail_copy=mode == "copy")
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

@pytest.mark.parametrize("value,kind,wanted", [
    (None, "REAL", None), (3, "INTEGER", 3), ("literal", "TEXT", "literal"),
    (1.00000001, "REAL", 1.0),
])
def test_native_sample_conversion_is_explicit(value, kind, wanted):
    assert loader.native_sample_value(value, kind) == wanted

def test_date_and_datetime_samples_use_iso_and_explicit_utc():
    from datetime import date, datetime, timezone
    assert loader.native_sample_value("2020-01-01", "DATE") == date(2020, 1, 1)
    assert loader.native_sample_value("2020-01-01 12:30:00", "DATETIME") == datetime(2020, 1, 1, 12, 30, tzinfo=timezone.utc)
    assert loader.native_sample_value("2020-01-01T14:30:00+02:00", "DATETIME") == datetime(2020, 1, 1, 12, 30, tzinfo=timezone.utc)

@pytest.mark.parametrize("value,kind", [(True, "INTEGER"), ("3", "INTEGER"), (float("nan"), "REAL"), (float("inf"), "REAL"), ("not-a-date", "DATE"), (b"bytes", "TEXT"), (1, "BLOB")])
def test_unreviewed_sample_values_refuse(value, kind):
    with pytest.raises(ValueError):
        loader.native_sample_value(value, kind)

@pytest.mark.parametrize("bad", [False, True])
async def test_sqlite_representative_first_middle_last_nulls_and_mismatch(tmp_path, monkeypatch, bad):
    import hashlib
    import sqlite3
    path = tmp_path / "sqlite/source.sqlite"
    path.parent.mkdir()
    with sqlite3.connect(path) as sqlite:
        sqlite.executescript("CREATE TABLE Thing (id INTEGER PRIMARY KEY, value REAL); INSERT INTO Thing VALUES (1,1.00000001),(2,NULL),(3,2.5);")
    pins = {
        "sqlite_sources": [{"db_id": "toxicology", "output": "sqlite/source.sqlite", "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}],
        "tables": {"thing": {"copy": {"rows": 3}}},
    }
    tables = {"thing": {"source_name": "Thing", "columns": [
        {"name": "id", "source_name": "id", "source_type": "INTEGER", "primary_key_position": 1},
        {"name": "value", "source_name": "value", "source_type": "REAL", "primary_key_position": 0},
    ]}}
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
        assert conn.values == [(1,1.0), (2,None), (3,2.5)]

@pytest.mark.parametrize("db_id", ["california_schools", "app", "../escape", "hosted"])
async def test_unapproved_dataset_rejected_before_connection(tmp_path, db_id):
    with pytest.raises(ValueError):
        await loader.load_dataset(object(), tmp_path, db_id, "a" * 48)
```


- [ ] Run uv run pytest tests/test_release_load.py -q --tb=line. Expected missing load_release RED.
- [ ] Generalize only the completed content helper's schema/names/COPY timeout; old defaults/callers unchanged:

```python
async def verify_native_content(conn: asyncpg.Connection, source: Path, tables: dict, *, schema: str = SCHEMA, names: tuple[str, ...] = TABLE_NAMES, copy_timeout: float = 60) -> None:
```


Inside this function replace for name in TABLE_NAMES with for name in names; target = SCHEMA + ... becomes target = quote_ident(schema) + "." + quote_ident(name); its COPY timeout=60 becomes timeout=copy_timeout. Keep EXCEPT ALL, projections/scratch tables/duplicates and California loader unchanged.
- [ ] Create scripts/load_release.py:

```python
"""Fixed-target setup importer; no inference, gold SQL or runtime credential wiring."""
import argparse
import asyncio
import json
import math
import os
import sqlite3
import struct
from contextlib import closing
from datetime import date, datetime, timezone
from time import monotonic
from pathlib import Path
from secrets import token_hex

import asyncpg

from scripts.load_bird import PASSWORD, setup_connection_options, verify_local_database, verify_native_content
from scripts.prepare_import_bundle import BUNDLE, DB_IDS, load_specs, validate_bundle
from scripts.prepare_sources import SOURCE_DIR, checked_file, relative_path
from sqlwarden.data import quote_ident

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TYPES = {"TEXT", "BIGINT", "REAL", "DATE", "TIMESTAMPTZ"}

def password_key(db_id):
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    return "WARDEN_DATASET_" + db_id.upper() + "_PASSWORD"

def initialize_credentials(root):
    with (root / ".env.datasets").open("x", encoding="utf-8", newline="\n") as file:
        file.write("".join(password_key(db_id) + "=" + token_hex(24) + "\n" for db_id in DB_IDS))

def table_definition(table):
    columns = []
    for column in table["columns"]:
        if column["native_type"] not in ALLOWED_TYPES:
            raise ValueError("Unsupported reviewed native type")
        columns.append(
            quote_ident(column["name"]) + " " + column["native_type"] +
            (" NOT NULL" if column["declared_not_null"] or column["primary_key_position"] else "")
        )
    if table["primary_key"]:
        columns.append("PRIMARY KEY (" + ", ".join(map(quote_ident, table["primary_key"])) + ")")
    return ", ".join(columns)

def native_sample_value(value, source_type):
    if value is None:
        return None
    if source_type == "TEXT" and isinstance(value, str):
        return value
    if source_type == "INTEGER" and type(value) is int:
        return value
    if source_type == "REAL" and type(value) in (int, float) and math.isfinite(value):
        return struct.unpack("!f", struct.pack("!f", value))[0]
    if source_type == "DATE" and isinstance(value, str):
        return date.fromisoformat(value)
    if source_type == "DATETIME" and isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    raise ValueError("Unsupported SQLite representative value")

async def verify_sqlite_samples(conn, db_id, tables, pins):
    source = next(p for p in pins["sqlite_sources"] if p["db_id"] == db_id)
    path = SOURCE_DIR / relative_path(source["output"])
    checked_file(path, source)
    deadline = monotonic() + 120
    verified = {}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)) as sqlite:
        sqlite.execute("PRAGMA query_only=ON")
        sqlite.execute("PRAGMA trusted_schema=OFF")
        sqlite.execute("PRAGMA cache_size=-8192")
        sqlite.set_progress_handler(lambda: int(monotonic() >= deadline), 10000)
        for name, table in tables.items():
            columns = table["columns"]
            projection = ", ".join(quote_ident(c["source_name"]) for c in columns)
            source_keys = [c["source_name"] for c in sorted(columns, key=lambda c: c["primary_key_position"]) if c["primary_key_position"]]
            ordering = ", ".join(map(quote_ident, source_keys)) if source_keys else "rowid"
            count = pins["tables"][name]["copy"]["rows"]
            offsets = sorted({0, count // 2, count - 1}) if count else []
            verified[name] = 0
            for offset in offsets:
                raw = sqlite.execute(
                    f"SELECT {projection} FROM {quote_ident(table['source_name'])} ORDER BY {ordering} LIMIT 1 OFFSET ?", (offset,)
                ).fetchone()
                if raw is None or sum(len(v.encode("utf-8")) for v in raw if isinstance(v, str)) > 1024 * 1024:
                    raise ValueError("SQLite representative row missing or over budget")
                values = [native_sample_value(v, c["source_type"]) for v, c in zip(raw, columns, strict=True)]
                predicate = " AND ".join(quote_ident(c["name"]) + " IS NOT DISTINCT FROM $" + str(i) for i, c in enumerate(columns, 1))
                if not await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM {quote_ident(db_id)}.{quote_ident(name)} WHERE {predicate})", *values):
                    raise ValueError("SQLite/native representative comparison differs")
                verified[name] += 1
                if monotonic() >= deadline:
                    raise ValueError("SQLite representative deadline exceeded")
    return verified

async def load_dataset(conn, source, db_id, password):
    if not isinstance(password, str) or not PASSWORD.fullmatch(password):
        raise ValueError("Invalid dataset password")
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    tables = validate_bundle(source, db_id)
    definitions = {name: table_definition(t) for name, t in tables.items()}
    pins, audit = load_specs()
    role_name = "warden_sandbox_" + db_id
    role, schema = quote_ident(role_name), quote_ident(db_id)
    async with asyncio.timeout(900), conn.transaction():
        await verify_local_database(conn)
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) "
            "OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)", db_id, role_name,
        )
        if exists:
            raise FileExistsError("Dataset schema or login exists; refusing changes")
        await conn.execute(
            "SET LOCAL statement_timeout='120s'; SET LOCAL lock_timeout='500ms'; "
            "SET LOCAL work_mem='16MB'; SET LOCAL temp_file_limit='2GB'; "
            "SET LOCAL idle_in_transaction_session_timeout='30s'; "
            "SET LOCAL timezone='UTC'; SET LOCAL DateStyle='ISO,YMD'"
        )
        await conn.execute(
            f"CREATE ROLE {role} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
            f"NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 2 PASSWORD '{password}'"
        )
        await conn.execute(f"GRANT CONNECT ON DATABASE sqlwarden TO {role}")
        for key, value in {
            "default_transaction_read_only": "on", "statement_timeout": "5s",
            "lock_timeout": "500ms", "idle_in_transaction_session_timeout": "5s",
            "work_mem": "16MB", "temp_file_limit": "64MB",
        }.items():
            await conn.execute(f"ALTER ROLE {role} SET {key}='{value}'")
        await conn.execute(f"ALTER ROLE {role} SET search_path=pg_catalog, {schema}")
        await conn.execute(f"CREATE SCHEMA {schema} AUTHORIZATION warden_owner")
        await conn.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        await conn.execute("SET LOCAL ROLE warden_owner")
        for name, table in tables.items():
            await conn.execute(f"CREATE TABLE {schema}.{quote_ident(name)} ({definitions[name]})")
            await conn.copy_to_table(
                name, schema_name=db_id, source=source / db_id / (name + ".tsv"),
                columns=[c["name"] for c in table["columns"]],
                format="text", encoding="UTF8", timeout=120,
            )
        await conn.execute(f"GRANT USAGE ON SCHEMA {schema} TO {role}")
        await conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {role}")
        await conn.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE warden_owner IN SCHEMA {schema} "
            f"GRANT SELECT ON TABLES TO {role}"
        )
        counts = {}
        for name in tables:
            counts[name] = await conn.fetchval(f"SELECT count(*) FROM {schema}.{quote_ident(name)}")
            if counts[name] != pins["tables"][name]["copy"]["rows"]:
                raise ValueError("Imported row count differs")
        await conn.execute("SET LOCAL ROLE NONE")
        await verify_native_content(
            conn, source / db_id, tables, schema=db_id, names=tuple(tables), copy_timeout=120,
        )
        samples = await verify_sqlite_samples(conn, db_id, tables, pins)
    return {
        "db_id": db_id, "rows": counts, "typed_native_content_verified": True,
        "sqlite_full_content_equivalence": "not established",
        "gold_conversion_validity": "not checked",
        "primary_descriptions": "not selected",
        "sqlite_representative_samples": samples,
        "sqlite_sample_policy": "native REAL=float4; DATE=ISO; DATETIME=UTC; no gold comparator change",
        "primary_key_tables": sum(bool(t["primary_key"]) for t in tables.values()),
        "foreign_key_enforcement": "metadata only; not installed",
        "source_foreign_key_check_status": audit["databases"][db_id]["foreign_key_check_status"],
        "source_foreign_key_violation_count": audit["databases"][db_id]["foreign_key_violation_count"],
    }

async def import_one(db_id):
    options = setup_connection_options(dict(os.environ))
    options["command_timeout"] = 120
    password = os.environ.get(password_key(db_id), "")
    if not PASSWORD.fullmatch(password):
        raise ValueError("Separate dataset credentials required")
    validate_bundle(BUNDLE, db_id)
    conn = await asyncpg.connect(**options)
    try:
        result = await load_dataset(conn, BUNDLE, db_id, password)
    finally:
        await conn.close()
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--init-credentials", action="store_true")
    choice.add_argument("--db", choices=DB_IDS)
    args = parser.parse_args()
    try:
        if args.init_credentials:
            initialize_credentials(ROOT)
            result = {"status": "credentials created; values private", "datasets": len(DB_IDS)}
        else:
            result = asyncio.run(import_one(args.db))
    except Exception as error:
        print(json.dumps({"status": "failed", "stage": "dataset import", "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```


- [ ] Run uv run pytest tests/test_release_load.py tests/test_import_bundle.py tests/test_bird_load.py -q --tb=line. Expected deterministic GREEN; unconfigured PG skips explicit. Run existing configured California suite to verify helper compatibility; no new imports yet.
- [ ] Tests above first verify tmp_path credential refusal. Recheck .env.datasets absent/ignored, then run uv run python -m scripts.load_release --init-credentials once without envs. Expected ten distinct restricted-only secrets, no values printed. No login created yet; never overwrite interrupted file.
- [ ] Update D-043/records/notebook with actual checks/file creation, never values. Run locked/no-env/old configured suite/lint/format/whitespace. Inspect staged/exact message feat(data): add fixed remaining dataset importer, commit/verify identity; task-done deterministic checks. No runtime wiring/inference/gold.


## Task 3 — toxicology thin slice and real acceptance boundary

**Files:** Create tests/test_release_postgres.py; ignored evidence; docs/toxicology-import-manifest.json; living records.
**Interfaces:** dataset_connected(db_id) fixed restricted login. capture_metadata(db_ids) reports metadata/null counts/keys only; save_metadata(destination,db_ids) refuses repeats. Named real rollback probes never persist.

- [ ] Write the actual database tests first:

```python
"""Real restricted-login and rollback checks; private values are never reported."""
import os
from contextlib import asynccontextmanager

import asyncpg
import pytest
from test_postgres_boundary import LARGE_OBJECT_FUNCTIONS, connected, rolled_back

from scripts import load_release as loader
from scripts.load_bird import verify_native_content
from scripts.prepare_import_bundle import BUNDLE, DB_IDS, load_specs, validate_bundle
from sqlwarden.data import quote_ident

pytestmark = pytest.mark.integration

@asynccontextmanager
async def dataset_connected(db_id):
    key = loader.password_key(db_id)
    if os.environ.get("WARDEN_TEST_TARGET") != "sqlwarden-local" or not os.environ.get(key):
        pytest.skip("Supply dedicated setup and dataset test environments")
    if os.environ.get("WARDEN_PG_PORT") != "55432":
        pytest.fail("Fixed local test port required", pytrace=False)
    conn = None
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1", port=55432, database="sqlwarden",
            user="warden_sandbox_" + db_id, password=os.environ[key],
            timeout=5, command_timeout=10,
        )
    except (OSError, asyncpg.PostgresError):
        pytest.fail("Configured dataset login unavailable", pytrace=False)
    try:
        yield conn
    finally:
        if conn is not None:
            await conn.close()

@pytest.mark.parametrize("db_id", DB_IDS)
async def test_dataset_counts_owned_tables_types_keys_and_null_counts(db_id):
    pins, audit = load_specs()
    wanted = audit["databases"][db_id]["tables"]
    async with dataset_connected(db_id) as conn, conn.transaction(readonly=True):
        for name, table in wanted.items():
            target = quote_ident(db_id) + "." + quote_ident(name)
            assert await conn.fetchval(f"SELECT count(*) FROM {target}") == pins["tables"][name]["copy"]["rows"]
            actual = await conn.fetch(
                "SELECT attname,format_type(atttypid,atttypmod),attnotnull "
                "FROM pg_attribute WHERE attrelid=$1::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum", target,
            )
            expected_types = {"TEXT":"text", "BIGINT":"bigint", "REAL":"real", "DATE":"date", "TIMESTAMPTZ":"timestamp with time zone"}
            assert [tuple(r) for r in actual] == [
                (c["name"], expected_types[c["native_type"]], bool(c["declared_not_null"] or c["primary_key_position"]))
                for c in table["columns"]
            ]
            keys = await conn.fetch(
                "SELECT a.attname FROM pg_constraint p "
                "CROSS JOIN LATERAL unnest(p.conkey) WITH ORDINALITY k(attnum,pos) "
                "JOIN pg_attribute a ON a.attrelid=p.conrelid AND a.attnum=k.attnum "
                "WHERE p.conrelid=$1::regclass AND p.contype='p' ORDER BY k.pos", target,
            )
            assert [r["attname"] for r in keys] == table["primary_key"]
            nulls = await conn.fetchrow("SELECT " + ",".join(
                "count(*) FILTER (WHERE " + quote_ident(c["name"]) + " IS NULL)" for c in table["columns"]
            ) + " FROM " + target)
            assert all(n == 0 for n,c in zip(nulls,table["columns"],strict=True) if c["declared_not_null"] or c["primary_key_position"])
        assert await conn.fetchval(
            "SELECT count(*) FROM pg_constraint p JOIN pg_namespace n ON n.oid=p.connamespace "
            "WHERE n.nspname=$1 AND p.contype='f'", db_id,
        ) == 0  # Proposed metadata-only FKs; not a claim of clean source keys.
        assert await conn.fetchval(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname=$1 AND c.relkind='r' AND r.rolname='warden_owner'", db_id,
        ) == len(wanted)

@pytest.mark.parametrize("db_id", DB_IDS)
async def test_dataset_reader_privileges_memberships_defaults_and_function_acls(db_id):
    async with dataset_connected(db_id) as conn:
        role = await conn.fetchrow(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit,rolconnlimit "
            "FROM pg_roles WHERE rolname=current_user"
        )
        assert tuple(role) == (False, False, False, False, False, False, 2)
        assert await conn.fetchval("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)") == 0
        assert await conn.fetchval("SHOW default_transaction_read_only") == "on"
        assert list(await conn.fetchval("SELECT current_schemas(false)")) == ["pg_catalog", db_id]
        for setting, expected in [("statement_timeout","5s"),("lock_timeout","500ms"),("work_mem","16MB"),("temp_file_limit","64MB")]:
            assert await conn.fetchval("SHOW " + setting) == expected
        names = [*LARGE_OBJECT_FUNCTIONS, "pg_read_file", "pg_sleep", "pg_ls_dir"]
        assert await conn.fetchval(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname='pg_catalog' AND p.proname=ANY($1::text[]) AND has_function_privilege(current_user,p.oid,'EXECUTE')", names,
        ) == 0

@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize("operation", ["update", "delete", "create", "temp", "app", "peer", "owner", "app_role", "california_role", "function"])
async def test_direct_denial_after_read_only_default_disabled(db_id, operation):
    pins, _audit = load_specs()
    name, table = next((n,t) for n,t in pins["tables"].items() if t["db_id"] == db_id)
    target = quote_ident(db_id) + "." + quote_ident(name)
    column = quote_ident(table["columns"][0]["name"])
    statements = {
        "update": f"UPDATE {target} SET {column}={column}",
        "delete": f"DELETE FROM {target}",
        "create": f"CREATE TABLE {quote_ident(db_id)}.forbidden_probe (id int)",
        "temp": "CREATE TEMP TABLE forbidden_probe (id int)",
        "app": "SELECT * FROM app.boundary_probe",
        "peer": "SELECT count(*) FROM california_schools.schools",
        "owner": "SET ROLE warden_owner",
        "app_role": "SET ROLE warden_app",
        "california_role": "SET ROLE warden_sandbox_california_schools",
        "function": "SELECT pg_catalog.lo_create(0)",
    }
    async with dataset_connected(db_id) as conn:
        await conn.execute("SET default_transaction_read_only=off")
        async with rolled_back(conn):
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(statements[operation])

@pytest.mark.parametrize("db_id,other", [(a,b) for a in DB_IDS for b in DB_IDS if a != b])
async def test_all_datasets_cross_read_and_role_denials(db_id, other):
    pins, _audit = load_specs()
    table = next(n for n,t in pins["tables"].items() if t["db_id"] == other)
    async with dataset_connected(db_id) as conn:
        for sql in (
            f"SELECT 1 FROM {quote_ident(other)}.{quote_ident(table)} LIMIT 1",
            "SET ROLE " + quote_ident("warden_sandbox_" + other),
        ):
            async with rolled_back(conn):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await conn.execute(sql)

async def test_mid_copy_failure_rolls_back_named_synthetic_import_probe(tmp_path, monkeypatch):
    db_id = "sqlwarden_import_probe"
    role = "warden_sandbox_" + db_id
    source = tmp_path / db_id
    source.mkdir()
    for name in ("first", "second"):
        (source / (name + ".tsv")).write_bytes(b"1\n")
    table = {"columns":[{"name":"id","native_type":"BIGINT","declared_not_null":False,"primary_key_position":1}], "primary_key":["id"]}
    monkeypatch.setattr(loader, "DB_IDS", (db_id,))
    monkeypatch.setattr(loader, "validate_bundle", lambda path, ident: {"first":table,"second":table})
    monkeypatch.setattr(loader, "load_specs", lambda: ({}, {}))
    class InterruptAfterFirstCopy:
        def __init__(self, conn):
            self.conn, self.calls = conn, 0
        def __getattr__(self, name):
            return getattr(self.conn, name)
        async def copy_to_table(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 2:
                raise ValueError("injected mid-COPY interruption")
            return await self.conn.copy_to_table(*args, **kwargs)
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        assert not await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)", db_id, role)
        proxy = InterruptAfterFirstCopy(conn)
        with pytest.raises(ValueError, match="mid-COPY"):
            await loader.load_dataset(proxy, tmp_path, db_id, "a" * 48)
        assert proxy.calls == 2
        assert not await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=$1) OR EXISTS(SELECT 1 FROM pg_roles WHERE rolname=$2)", db_id, role)

@pytest.mark.parametrize("db_id", DB_IDS)
async def test_repeat_import_refuses_and_preserves_counts(db_id):
    async with dataset_connected(db_id):
        pass
    async with connected("warden_bootstrap") as conn:
        pins, _audit = load_specs()
        name = next(n for n,t in pins["tables"].items() if t["db_id"] == db_id)
        target = quote_ident(db_id) + "." + quote_ident(name)
        before = await conn.fetchval("SELECT count(*) FROM " + target)
        with pytest.raises(FileExistsError):
            await loader.load_dataset(conn,BUNDLE,db_id,os.environ[loader.password_key(db_id)])
        assert await conn.fetchval("SELECT count(*) FROM " + target) == before

@pytest.mark.parametrize("db_id", DB_IDS)
async def test_future_owner_defaults_are_dataset_specific(db_id):
    async with dataset_connected(db_id):
        pass
    async with connected("warden_bootstrap") as conn, rolled_back(conn):
        await conn.execute("SET LOCAL ROLE warden_owner")
        target = quote_ident(db_id) + ".future_grant_probe"
        await conn.execute("CREATE TABLE " + target + " (id int)")
        own = "warden_sandbox_" + db_id
        assert await conn.fetchval("SELECT has_table_privilege($1,$2,'SELECT')", own, target)
        assert not await conn.fetchval("SELECT has_table_privilege($1,$2,'INSERT')", own, target)
        roles = await conn.fetch("SELECT rolname FROM pg_roles WHERE (rolname LIKE 'warden_sandbox_%' OR rolname='warden_app') AND rolname<>$1", own)
        for role in (r["rolname"] for r in roles):
            assert not await conn.fetchval("SELECT has_table_privilege($1,$2,'SELECT')", role, target)

async def test_toxicology_same_count_mutation_is_detected_and_rolled_back():
    async with dataset_connected("toxicology"):
        pass
    tables = validate_bundle(BUNDLE, "toxicology")
    name, table = next((n,t) for n,t in tables.items() if t["primary_key"] and any(c["native_type"]=="TEXT" and not c["primary_key_position"] for c in t["columns"]))
    field = next(c["name"] for c in table["columns"] if c["native_type"]=="TEXT" and not c["primary_key_position"])
    key = table["primary_key"][0]
    target = '"toxicology".' + quote_ident(name)
    async with connected("warden_bootstrap") as conn:
        before = await conn.fetchval("SELECT count(*) FROM " + target)
        async with rolled_back(conn):
            await conn.execute("SET LOCAL statement_timeout='120s'; SET LOCAL temp_file_limit='2GB'")
            value = await conn.fetchval("SELECT " + quote_ident(key) + " FROM " + target + " ORDER BY " + quote_ident(key) + " LIMIT 1")
            await conn.execute("UPDATE " + target + " SET " + quote_ident(field) + "=coalesce(" + quote_ident(field) + ",'') || '_verification_probe' WHERE " + quote_ident(key) + "=$1", value)
            assert await conn.fetchval("SELECT count(*) FROM " + target) == before
            with pytest.raises(ValueError,match="content differs"):
                await verify_native_content(conn,BUNDLE/"toxicology",tables,schema="toxicology",names=tuple(tables),copy_timeout=120)
        assert await conn.fetchval("SELECT count(*) FROM " + target) == before
        async with rolled_back(conn):
            await conn.execute("SET LOCAL statement_timeout='120s'; SET LOCAL temp_file_limit='2GB'")
            await verify_native_content(conn,BUNDLE/"toxicology",tables,schema="toxicology",names=tuple(tables),copy_timeout=120)

async def capture_metadata(db_ids=DB_IDS):
    pins, audit = load_specs()
    report = {
        "format_version":1,"track":"native PostgreSQL import preparation",
        "gold_conversion_validity":"not checked","sqlite_full_content_equivalence":"not established",
        "primary_descriptions":"not selected","datasets":{},
    }
    for db_id in db_ids:
        tables = validate_bundle(BUNDLE, db_id)
        actual = {}
        async with dataset_connected(db_id) as conn, conn.transaction(readonly=True):
            for name, table in tables.items():
                target = quote_ident(db_id) + "." + quote_ident(name)
                rows = await conn.fetchval("SELECT count(*) FROM " + target)
                assert rows == pins["tables"][name]["copy"]["rows"]
                nulls = await conn.fetchrow("SELECT " + ",".join("count(*) FILTER (WHERE " + quote_ident(c["name"]) + " IS NULL)" for c in table["columns"]) + " FROM " + target)
                actual[name] = {
                    "rows":rows,"null_counts":list(nulls),"columns":table["columns"],
                    "primary_key":table["primary_key"],"source_foreign_keys":table["foreign_keys"],
                    "foreign_key_enforcement":"metadata only; not installed",
                    "native_source":pins["tables"][name]["copy"],
                }
        report["datasets"][db_id] = {
            "tables":actual,
            "source_foreign_key_check_status":audit["databases"][db_id]["foreign_key_check_status"],
            "source_foreign_key_violation_count":audit["databases"][db_id]["foreign_key_violation_count"],
        }
    return report

@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize("role", ["warden_app", "warden_sandbox_demo_schools", "warden_sandbox_demo_other", "warden_sandbox_california_schools"])
async def test_existing_runtime_logins_cannot_read_new_dataset(db_id, role):
    async with dataset_connected(db_id):
        pass
    pins, _audit = load_specs()
    table = next(n for n,t in pins["tables"].items() if t["db_id"]==db_id)
    async with connected(role) as conn, rolled_back(conn):
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetchval("SELECT count(*) FROM " + quote_ident(db_id) + "." + quote_ident(table))

@pytest.mark.parametrize("db_id", DB_IDS)
@pytest.mark.parametrize("database", ["postgres", "template1"])
async def test_new_reader_cannot_connect_to_unused_cluster_databases(db_id, database):
    async with dataset_connected(db_id):
        pass
    conn = None
    try:
        try:
            conn = await asyncpg.connect(host="127.0.0.1",port=55432,database=database,user="warden_sandbox_"+db_id,password=os.environ[loader.password_key(db_id)],timeout=5)
        except asyncpg.InsufficientPrivilegeError:
            return
        except (OSError, asyncpg.PostgresError):
            pytest.fail("Unexpected connection result; private details suppressed",pytrace=False)
        pytest.fail("Reader connected to unused cluster database",pytrace=False)
    finally:
        if conn is not None:
            await conn.close()

async def save_metadata(destination, db_ids=DB_IDS):
    import json
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Evidence destination exists")
    report = await capture_metadata(db_ids)
    raw = json.dumps(report,indent=2)+"\n"
    if len(raw.encode("utf-8")) > 512*1024:
        raise ValueError("Evidence metadata exceeds budget")
    with destination.open("x",encoding="utf-8",newline="\n") as file:
        file.write(raw)
    return {"status":"metadata captured","datasets":len(report["datasets"])}
```


- [ ] Before import run uv run --env-file .env.setup --env-file .env.california --env-file .env.datasets pytest tests/test_release_postgres.py -k 'toxicology and not all_datasets' -q --tb=line. Expected controlled Configured dataset login unavailable RED, no credential details. Run test_mid_copy_failure_rolls_back_named_synthetic_import_probe separately: expected GREEN, actual first COPY/injected second failure/no durable probe schema or login.
- [ ] Recheck source pins, absent toxicology schema/login, disk/volume health and preserved California counts. Start the 3600s actual-import clock. Run uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db toxicology once.
Expected four tables/36922 rows; typed native multiset and up to three representative SQLite rows/table match before commit; explicit not-gold-valid markers. Any mismatch/timeout stops without data repair or relaxed checks.
- [ ] Run toxicology selection and the real rollback probe; run original actual PostgreSQL checks. Expected GREEN: owned reads/counts/types/PKs/defaults; denied writes/temp/app/California/old readers/SET ROLE/functions/unused databases; repeat refusal preserves counts; same-count mutation is detected/rolled back. No isolation claim before actual GREEN.
- [ ] Capture metadata with no rows/passwords printed:

```powershell
uv run --env-file .env.setup --env-file .env.datasets python -c "import asyncio,sys; from pathlib import Path; sys.path.insert(0,'tests'); from test_release_postgres import save_metadata; print(asyncio.run(save_metadata(Path('data/import-release/minidev-0703/toxicology-evidence.json'),('toxicology',))))"
```


Inspect ignored evidence and actual importer result; copy checked metadata with apply_patch into docs/toxicology-import-manifest.json, adding actual success/sample counts, date/Git state, source pin paths/hash and procedure. No raw cells/SQL/prose/secrets. Native typed equivalence is not full SQLite/gold equivalence.
- [ ] Update D-044/records/notebook, run actual selection/old regression/lint/format/whitespace. Inspect staged/exact message test(data): verify toxicology import and isolation, commit/verify identity/body. Task-done uses toxicology selection plus rollback probe. Preserve this verified dataset if later imports fail.

## Task 4 — nine further sequential imports and final evidence

**Files:** Implemented tools/tests; ignored full evidence; docs/remaining-import-manifest.json; living records.
**Interfaces:** same fixed importer/credential/pin schema; no new format/auto-skip. Full cross-new-reader matrix runs only after all new targets exist.

- [ ] Confirm Task 3 done, elapsed import attempt clock below 3600s, no running model/import, and each next target absent. Run exact commands in order; stop at nonzero exit or exhausted envelope:

```powershell
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db thrombosis_prediction
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db superhero
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db student_club
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db debit_card_specializing
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db formula_1
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db financial
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db card_games
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db codebase_community
uv run --env-file .env.setup --env-file .env.datasets python -m scripts.load_release --db european_football_2
```


Expected overall new totals ten datasets/72 tables/709 columns/3868173 rows/69 enforced PKs, complete typed native comparisons and representative samples match. Existing role/schema is refusal, not an auto-skip. No new FK enforcement/repair; European count remains null.
- [ ] Run uv run --env-file .env.setup --env-file .env.california --env-file .env.datasets pytest tests/test_release_postgres.py -q --tb=line. Expected actual GREEN/zero skips, including 90 ordered new-reader pairs checking both cross-read and SET ROLE denial, existing reader/unused cluster/future grant denials. Record actual check count.
- [ ] Capture full metadata:

```powershell
uv run --env-file .env.setup --env-file .env.datasets python -c "import asyncio,sys; from pathlib import Path; sys.path.insert(0,'tests'); from test_release_postgres import save_metadata; print(asyncio.run(save_metadata(Path('data/import-release/minidev-0703/remaining-evidence.json'))))"
```


Inspect evidence and each actual import result. Use apply_patch for docs/remaining-import-manifest.json with actual pins/typed comparison/sample counts/method/date/Git state, metadata-only FK policy and unselected descriptions/not-checked gold validity. No raw run/cell/prose/secrets committed.
- [ ] Run uv sync --locked; uv run pytest -q --tb=line; uv run --env-file .env.setup --env-file .env.california --env-file .env.datasets pytest -q --tb=line; uv run ruff check .; uv run ruff format --check .; git diff --check. Expected all configured tests/zero skips, preserved California; record actual counts/timing.
- [ ] Update D-045/records/notebook from actual acceptance. G0.5 stays unfinished until conversions/descriptions/C1 decisions. Inspect staged/exact message docs(data): record remaining checked native imports, commit/verify identity/body; task-done runs complete actual release tests.
- [ ] One fresh final read-only whole-four-task reviewer, no per-task or parallel implementation reviews. Grade by user effect; fix Important/Critical once test-first plus full suite; no automatic re-review. Record every declined judgment/cost and deferred Minor.
- [ ] Keep branch local and ignored scratch unless cleanup separately approved; truthful Handoff and actual completed IDs/commits/tests/limits.

## Rest of G0 — later required checkpoints, not implicit approval

| Item | Work remaining | Required checkpoint |
| --- | --- | --- |
| G0.5 | Bounded source SQLite/restricted PostgreSQL original/corrected gold validation, exact mismatches/survivors/exclusions and descriptions | Separate reviewed gold/adaptation plan; no quiet corpus edits |
| G0.5b / C1 | Layout, primary labels/descriptions, conversion survival and ambiguity audit policy | Review actual evidence; below 95% corrected survival needs explicit options |
| G0.6 | Pin Arctic availability/license/GGUF/template and bounded local smoke, one GPU model | Review exact artifact/size/limits before download/probe; absence explicit |
| G0.7 | Deduplicated family-consistent seeded 100-item development and actual held-out IDs, full-schema budgets, small safe smoke then E0 | Approve benchmark protocol/input/evidence/denominator choices before scoring |
| G0.8 / C2 | Development model/slice/helper choices from actual speed/memory/capabilities | Review measured results, not guessed performance |
| Interview drill | Original three questions | Offer when G0 actually finishes; Kunal can skip |

Do not mark G0 done after imports alone or score predictions before validity/split freezes. Missing optional model is reported, not an indefinite blocker for Qwen's working slice. Batch completion permits read-only next-artifact preparation, not automatic gold/model/benchmark operations.

## Self-review of this preparation

Scope: already approved architecture reused; setup-only changes preserve California defaults. Planning is not implementation, mocks are not isolation proof, samples are not complete conversion validity.
Interfaces: bundle metadata/table names/constants feed fixed loader; optional content helper preserves existing callers; Task 3 selection avoids cross-new-schema matrix until Task 4.
All five Review Focus cases map to concrete fixture/direct tests. Refusal/pins/partial rollback/value mutations/keys/samples/grants/readers/cluster covered. Imported source SQL/gold/model work absent.
Limits: cooperative not hard interruption; trusted immutable local files, no crash-durable credential/report recovery. Setup spill cap is not a RAM cap; Docker/runtime limits unchanged. No universal catalog/function/security claim.
Before approval syntax-parse proposed Python blocks without running them, inspect interface consistency/placeholder/spec coverage, run existing regressions and record actual output. No new implementation tests/import acceptance claimed.
