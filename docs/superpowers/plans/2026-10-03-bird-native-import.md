# One BIRD Database Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Native execution is preserved; AGENTS.md forbids parallel implementation without Kunal's request.

**Goal:** Finish G0.5a by loading California Schools into its own PostgreSQL schema and restricted login, without executing downloaded SQL.

**Architecture:** Read only the three selected native PostgreSQL COPY-data blocks from the pinned archive. Generate table definitions from checked SQLite metadata using the reviewed native type/name mapping; import native data through asyncpg in one setup-only transaction. Verify content and direct privileges before any generated SQL.

**Tech Stack:** Python 3.12, uv, PostgreSQL 16, asyncpg, pytest and Python standard library. No new dependency.

**Spec:** [BUILD_SPEC.md](../../BUILD_SPEC.md), sections 5, 8 and 11. Source evidence and fingerprints: [DATA.md](../../DATA.md).

**Status:** Approved by Kunal's “proceed” on 2026-10-03. Execution is in progress; completion evidence belongs in PROGRESS.md.

## Global Constraints

- Workspace: `D:/PROJECTS/SQLWARDEN`. Use the current workspace; do not create a nested `sqlwarden` directory.
- Keep inference local until a hosted configuration is explicitly approved.
- No remote addition or push before the G7 release approval.
- Kunal is the sole author and committer of new project commits.
- Never commit secrets, data downloads, model weights, caches, raw run output or unrelated user changes.
- Use separate restricted dataset logins, conceptually `warden_sandbox_<db_id>`, each with USAGE and SELECT only on its own dataset.
- Real PostgreSQL integration tests must run before database security claims.
- Do not delete the current named volume, overwrite credentials, import unrelated datasets, or execute archive-provided SQL.
- Retain PostgreSQL-native data, identifier behavior and text/bigint/real/date types. This is not a claim of native/SQLite semantic equivalence.

## Review Focus

1. A dump contains other databases, owner changes or executable SQL: extract only data for the three fixed tables; execute none of that SQL.
2. A COPY block is missing, duplicated, unterminated, oversized or altered: fail without publishing partial output or creating database objects.
3. Ordinary SQLite names differ from PostgreSQL names; quoted names and 32-bit real matter: validate the full native header/type mapping, not row counts alone.
4. An existing role/schema/credential or wrong target is encountered: refuse, preserve it and report a sanitized error.
5. A reader changes mutable settings: writes, other datasets, app tables and large-object calls must still be denied by actual privileges.

---

### Task 1: Checked source metadata and native COPY extraction

**Files:**
- Create `src/sqlwarden/data.py` for offline source inspection and extraction.
- Modify `scripts/fetch_data.py` to add `--native` without rerunning or overwriting the existing source selection.
- Create `tests/test_bird_native.py`.

**Interfaces:**
- Consumes the archive and SQLite SHA-256 values in DATA.md, fixed table names schools/frpm/satscores, and native block fingerprints below.
- Produces `read_tables(sqlite_path: Path, expected_sha256: str) -> dict`, returning ordered columns with original name, PostgreSQL name/type, nullability and source keys.
- Produces `extract_native_copy(stream: BinaryIO, destination: Path, tables: dict, expected: dict) -> dict`, returning selected column lists, row counts, byte sizes and SHA-256 values.
- Produces ignored `data/bird_california/native/{schools,frpm,satscores}.tsv` and a metadata manifest; no SQL file is published.

- [ ] **Step 1: Write failing schema/name tests.** Create a SQLite fixture with the three fixed table names. Its schools table includes CDSCode TEXT PRIMARY KEY, `School Name` TEXT, Charter INTEGER, Latitude REAL and OpenDate DATE. Include the two source foreign keys. Compute the fixture hash and call read_tables with that hash.

```python
def test_native_names_types_and_keys(sqlite_fixture):
    path, checksum = sqlite_fixture
    tables = read_tables(path, checksum)
    columns = {c["source_name"]: c for c in tables["schools"]["columns"]}
    assert columns["CDSCode"]["name"] == "cdscode"
    assert columns["School Name"]["name"] == "School Name"
    assert columns["Charter"]["type"] == "bigint"
    assert columns["Latitude"]["type"] == "real"
    assert columns["OpenDate"]["type"] == "date"
    assert tables["schools"]["primary_key"] == ["cdscode"]
    assert tables["frpm"]["foreign_key"] == ("cdscode", "schools", "cdscode")
```

Add parametrized rejection tests for an incorrect checksum, a view replacing a
required table, an unsupported type such as BLOB, a normalized-name collision,
a PostgreSQL identifier exceeding 63 UTF-8 bytes and an unexpected foreign-key
target. Every failure must occur before any PostgreSQL connection is made.

- [ ] **Step 2: Observe RED.**

```powershell
uv run pytest tests/test_bird_native.py -q
```

Expected initial failure: missing sqlwarden.data/read_tables, followed by explicit
assertion failures if mapping or validation is incomplete.

- [ ] **Step 3: Implement the checked metadata mapping.** Use sqlite3 read-only URI
mode, query_only and trusted_schema off. Use fixed table names for PRAGMA calls;
check the file digest before opening it. Read table_info and foreign_key_list,
never execute sqlite_master SQL. Normalize only ASCII ordinary identifiers;
preserve names requiring quotes. Reject collisions and invalid identifier lengths.

```python
TYPE_MAP = {"TEXT": "text", "INTEGER": "bigint", "REAL": "real", "DATE": "date"}
ORDINARY = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")

def pg_name(source_name):
    name = source_name.lower() if ORDINARY.fullmatch(source_name) else source_name
    if not name or "\x00" in name or len(name.encode("utf-8")) > 63:
        raise ValueError("Unsupported source identifier")
    return name

def quote_ident(name):
    return '"' + name.replace('"', '""') + '"'
```

Metadata assertions for the actual source: schools has 49 columns, frpm 29,
satscores 11; primary keys and foreign keys match DATA.md. The generated type/name
sequence must match the reviewed native definitions and full native COPY headers.
PK/NOT NULL/FK constraints come from the checked SQLite metadata and must validate
against the native data; do not silently drop a failing constraint.

- [ ] **Step 4: Write native-block tests and observe RED.** Use BytesIO fixtures,
not an administrative SQL server. All fixture table names remain the three fixed
names, with smaller column lists supplied to the helper only for these unit tests.

```python
def test_native_extractor_keeps_only_data(tmp_path):
    stream = io.BytesIO(
        b"DO $$ BEGIN RAISE EXCEPTION 'never execute'; END $$;\n"
        b"COPY public.other_table (value) FROM stdin;\nprivate-other-row\n\\.\n"
        b"COPY public.schools (cdscode, school) FROM stdin;\n1\tExample\n\\.\n"
        b"COPY public.frpm (cdscode) FROM stdin;\n1\n\\.\n"
        b"COPY public.satscores (cds) FROM stdin;\n1\n\\.\n"
    )
    tables = {
        "schools": {"columns": [{"name": "cdscode"}, {"name": "school"}]},
        "frpm": {"columns": [{"name": "cdscode"}]},
        "satscores": {"columns": [{"name": "cds"}]},
    }
    payloads = {"schools": b"1\tExample\n", "frpm": b"1\n", "satscores": b"1\n"}
    expected = {
        name: {"rows": 1, "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in payloads.items()
    }
    output = tmp_path / "native"
    result = extract_native_copy(stream, output, tables, expected)
    assert set(result) == set(payloads)
    for name, data in payloads.items():
        assert (output / f"{name}.tsv").read_bytes() == data
    assert not (output / "other_table.tsv").exists()
```

Add missing/duplicate/unterminated block, changed header/order, wrong checksum,
over-limit line/block and existing-destination tests. Assert no partial output is
published on failures and existing files are unchanged. Preserve COPY escaping,
NULL markers and LF bytes; do not parse/rewrite row values or treat them as SQL.

- [ ] **Step 5: Implement bounded extraction.** Verify the archive SHA first and
require exactly one ordinary, unencrypted native dump member. Read that member
through zipfile to EOF so CRC validation runs. Read at most 1 MiB per source line;
write at most 32 MiB per selected table. Track every COPY block, including ignored
tables, until its exact terminating backslash-dot LF line. Recognize only the
native `COPY public.<name> (<columns>) FROM stdin;` format. Parse the column list
with csv.reader and compare it with checked metadata. Reject duplicate selected
blocks, invalid format, EOF within a block and content/hash/count mismatches.
Write selected files into a TemporaryDirectory under the destination parent and
rename only after all checks succeed, following the existing extractor pattern.

Production expected block fingerprints:

```python
NATIVE_EXPECTED = {
    "schools": {"rows": 17686, "sha256": "f6f4de19738417ed5bd27d1d2e7935aa3e2b4319a2c366542560514671f38b6a"},
    "frpm": {"rows": 9986, "sha256": "504bc2f6a66e9dfff6c9f04bb6078bcab6196c966b8d992575f88d9ad618f316"},
    "satscores": {"rows": 2269, "sha256": "549f79e4b98bb0660dd9024271e3787ea83cf875fccc8e7a547c38c419a79c0f"},
}
```

- [ ] **Step 6: Run the tests, then actual extraction.**

```powershell
uv run pytest tests/test_bird_extract.py tests/test_bird_native.py -q
uv run python -m scripts.fetch_data --native
```

Expected: unchanged existing source selection; three new native TSVs with exactly
the rows, bytes and hashes in DATA.md. Review the diff, update progress and commit
the independently verified extraction change with owner-only identity.

### Task 2: Setup-only restricted import

**Files:**
- Modify `scripts/init_local.py` with `initialize_bird(root: Path)` and a `--bird` option.
- Create `scripts/load_bird.py` for the fixed California dataset only.
- Extend `tests/test_local_setup.py` and create `tests/test_bird_load.py`.
- Extend the existing PostgreSQL boundary test role mapping only when the actual login exists.

**Interfaces:**
- initialize_bird exclusively creates ignored `.env.california` containing only
  WARDEN_CALIFORNIA_PASSWORD, generated with secrets.token_hex(24). It neither
  reads nor overwrites existing credentials and prints no secret.
- `load_california(conn: asyncpg.Connection, source: Path, password: str) -> dict`
  creates the fixed schema/login and returns counts/fingerprints, not raw data.
- `verify_native_content(conn: asyncpg.Connection, source: Path, tables: dict) -> None`
  is setup-only: load source TSVs into temporary copies of the reviewed table types,
  compare duplicate-preserving results in both directions, and raise ValueError on a difference.
- CLI takes setup credentials only from `.env.setup` and the new dataset file;
  runtime credentials never include the bootstrap credential.

- [ ] **Step 1: Write credential behavior tests and observe RED.**

```python
def test_bird_credentials_are_separate_and_never_overwritten(tmp_path):
    setup = tmp_path / ".env.setup"
    runtime = tmp_path / ".env"
    setup.write_text("existing-setup\n")
    runtime.write_text("existing-runtime\n")
    initialize_bird(tmp_path)
    path = tmp_path / ".env.california"
    original = path.read_bytes()
    assert original.startswith(b"WARDEN_CALIFORNIA_PASSWORD=")
    assert b"BOOTSTRAP" not in original
    with pytest.raises(FileExistsError):
        initialize_bird(tmp_path)
    assert path.read_bytes() == original
    assert setup.read_text() == "existing-setup\n"
    assert runtime.read_text() == "existing-runtime\n"
```

Also verify 48 lowercase hex characters and that captured output contains only the
filename, not its value. Implement using the existing exclusive-create pattern.

- [ ] **Step 2: Write validation and direct database tests before import.** Test
that malformed password, altered native file, missing source manifest or unsupported
schema rejects before database writes. CLI rejects missing WARDEN_TEST_TARGET,
anything other than sqlwarden-local, and ports other than this project's 55432.
Connections are fixed to 127.0.0.1/sqlwarden/warden_bootstrap. Verify PostgreSQL 16
and existing project fixture/ownership markers before writes.

Actual reader tests initially fail because its login/schema does not yet exist.
Use a missing-login failure, not skip, when both dedicated env files are supplied.
Cover SELECT counts for all three tables, own join, owner/flags/memberships,
read-only default and runtime function ACLs. Run forbidden SQL in always-rollback
transactions after disabling the default:

```python
FORBIDDEN_CALIFORNIA_SQL = [
    "UPDATE california_schools.schools SET school = 'not allowed'",
    "DELETE FROM california_schools.frpm",
    "TRUNCATE california_schools.satscores",
    "CREATE TABLE california_schools.forbidden (id int)",
    "CREATE TEMP TABLE forbidden (id int)",
    "SELECT * FROM app.boundary_probe",
    "SELECT * FROM demo_other.canary",
    "SET ROLE warden_owner",
    "SET ROLE warden_app",
    "SELECT pg_catalog.lo_create(0)",
]
```

Existing demo/app readers must also be denied California tables. Include a
setup-only rollback test for future table default grants in the new schema.

- [ ] **Step 3: Implement a single atomic import transaction.** Validate all
source files first against the pinned native fingerprints. Refuse an existing
california_schools schema or warden_sandbox_california_schools role; no drop/reset
or implicit migration path. Generate identifiers with quote_ident and types only
from TYPE_MAP, using read_tables output validated against native headers.

Within conn.transaction(), create the LOGIN with NOINHERIT, NOSUPERUSER,
NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS and connection limit 2.
Require the generated password's exact lowercase-hex format before safely quoting
it; never log role SQL. Grant CONNECT on sqlwarden. Apply the existing reader
settings (read-only on, statement 5s, lock 500ms, idle 5s, work_mem 16MB,
temp_file_limit 64MB) and search_path pg_catalog, california_schools.

Create the schema AUTHORIZATION warden_owner, SET LOCAL ROLE warden_owner, create
its three tables with checked columns/keys, then load only their native TSVs:

```python
for name in ("schools", "frpm", "satscores"):
    await conn.copy_to_table(
        name,
        schema_name="california_schools",
        source=source / f"{name}.tsv",
        columns=[column["name"] for column in tables[name]["columns"]],
        format="text",
        encoding="UTF8",
        timeout=60,
    )
```

Add the two verified foreign keys after all rows are loaded. Grant only USAGE and
SELECT to the fixed reader, plus owner-specific future SELECT defaults in this
schema. No app, other-reader or PUBLIC schema/table grant. Check expected counts
inside the transaction. Restore SET LOCAL ROLE NONE to the setup administrator,
then call verify_native_content before committing. Its source-check tables are
temporary and setup-only; never grant TEMP to a runtime login. A constraint,
COPY, count, content or grant failure rolls the whole import back.
All administrative SQL is generated from reviewed code and fixed metadata,
not read from the downloaded dump. Preserve the existing named volume and fixtures.

The content verifier uses PostgreSQL to decode COPY escaping and native values,
avoiding a second custom parser or arbitrary numeric rounding:

```python
async def verify_native_content(conn, source, tables):
    for name in ("schools", "frpm", "satscores"):
        target = "california_schools." + quote_ident(name)
        temporary = quote_ident("import_check_" + name)
        await conn.execute(f"CREATE TEMP TABLE {temporary} (LIKE {target}) ON COMMIT DROP")
        columns = [column["name"] for column in tables[name]["columns"]]
        await conn.copy_to_table(
            "import_check_" + name, schema_name="pg_temp",
            source=source / f"{name}.tsv", columns=columns,
            format="text", encoding="UTF8", timeout=60,
        )
        projection = ", ".join(quote_ident(column) for column in columns)
        scratch = "pg_temp." + temporary
        different = await conn.fetchval(
            f"SELECT EXISTS("
            f"(SELECT {projection} FROM {target} EXCEPT ALL SELECT {projection} FROM {scratch}) "
            f"UNION ALL "
            f"(SELECT {projection} FROM {scratch} EXCEPT ALL SELECT {projection} FROM {target}))"
        )
        if different:
            raise ValueError("Native source content differs from imported rows")
```

Use bounded setup transaction deadlines/work_mem and container caps. This compares
complete typed row multisets including duplicates and NULL, independent of source
row order. It is an import check, not the official EX comparator. Add a real
always-rollback test that changes one imported value without changing its count
and proves this function raises; the original data must remain unchanged afterward.

- [ ] **Step 4: Verify and import once, then rerun direct tests.**

```powershell
uv run pytest tests/test_local_setup.py tests/test_bird_native.py -q
uv run python -m scripts.init_local --bird
uv run --env-file .env.setup --env-file .env.california python -m scripts.load_bird
uv run --env-file .env.setup --env-file .env.california pytest -q
```

Inspect all actual outputs and run lint/format/lock/diff checks. A repeat import
must refuse without changing data. Record evidence and commit only passing work.

### Task 3: Content and provenance verification / G0.5a handoff

**Files:**
- Extend `tests/test_bird_load.py` for content/type and source-alignment checks.
- Update DATA.md, README.md, PROGRESS.md and DECISIONS.md.
- Create a small versioned `docs/california-import-manifest.json`; no raw rows.

- [ ] **Step 1: Extend the actual content/type checks and record fingerprints.**
The setup-only source replay in Task 2 proves complete typed row agreement, not
just equal counts. Its mutation test must exercise that production function:

```python
async def test_content_check_detects_same_count_changed_values(setup_connection, source_tables):
    async with setup_connection() as conn, rolled_back(conn):
        before = await conn.fetchval("SELECT count(*) FROM california_schools.schools")
        await conn.execute(
            "UPDATE california_schools.schools SET school = coalesce(school, '') || '_probe' "
            "WHERE cdscode = (SELECT cdscode FROM california_schools.schools ORDER BY cdscode LIMIT 1)"
        )
        assert await conn.fetchval("SELECT count(*) FROM california_schools.schools") == before
        with pytest.raises(ValueError, match="content differs"):
            await verify_native_content(conn, Path("data/bird_california/native"), source_tables)
```

setup_connection is a local bootstrap connection using the existing dedicated
target checks; source_tables calls read_tables on the pinned SQLite source.
Use the existing always-rollback helper so the probe and temporary check tables
cannot persist. Also assert that unmodified imported content passes the verifier.

Under the restricted reader, hash streamed COPY query output in source column
order and primary-key order to record a deterministic native data fingerprint.
Do not equate that normalized fingerprint with the raw TSV hash. Add real checks
for date columns, native float4/bigint types, NULL distributions, primary-key
uniqueness and both foreign-key joins. Preserve native precision; never substitute
SQLite values or round differences away. Match descriptions to native names using
the checked mapping, not blind case-folding of every quoted identifier.

- [ ] **Step 2: Verify label alignment by stable IDs.** Recheck pinned file hashes,
reject duplicate/missing IDs or changed db_id, and retain the 30 selected IDs in
DATA.md. The existing full-release question/evidence differences remain recorded;
do not claim all 500 dialect inputs are identical. Gold SQL/results remain
offline-only. No prediction score or gold-validity rate is produced here.

- [ ] **Step 3: Run the full checks and hand off.**

```powershell
uv run --env-file .env.setup --env-file .env.california pytest -q
uv run ruff check .
uv run ruff format --check .
uv lock --check
git diff --check
git check-ignore .env .env.setup .env.california data/raw/minidev_0703.zip
```

The compact import manifest records source revisions/hashes, native row/content
fingerprints, exact mapping/types/keys, import Git state and observed privilege
checks. It contains no credentials or raw source rows. Review the diff and owner
identity before the logical commit; inspect fuller log/body afterward.

Mark G0.5a complete only if the real import/content/privilege checks pass. Next is
G0.6a Qwen endpoint/capability smoke and G0.7a tested guard, bounded executor,
pinned EX comparator and one-database CLI. Do not run generated SQL yet. Full data,
corrected-label conversion, C1 decisions and benchmark scoring remain later tasks.
