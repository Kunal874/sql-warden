# Full source preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Native sequential execution was already selected; do not reopen that choice or run parallel implementation.

**Goal:** Prepare the complete pinned source release and produce a tested offline layout/description audit before proposing the remaining PostgreSQL imports.

**Architecture:** Three sequential setup-only scripts use a checked-in, fixed metadata manifest. Extract only exact archive members; acquire only fixed-revision CSVs; then read SQLite in immutable read-only mode and stream the native dump for metadata and COPY fingerprints. Existing California import/runtime code remains untouched; no database import, gold query or model request belongs to this batch.

**Tech Stack:** Python 3.12, uv, stdlib zipfile/sqlite3/csv/hashlib/tempfile; already approved httpx and SQLGlot 30.21.0; pytest/ruff.

**Spec:** [BUILD_SPEC](../../BUILD_SPEC.md), especially sections 2, 4 and 8; [original detailed plan](../../../sqlwarden-plan.md) G0.5; [D-036](../../DECISIONS.md); [source pins](../../source-release-pins.json).

**Status:** Prepared 2026-10-05 from clean fc71084. Kunal approved this exact three-task batch on 2026-10-05 after artifact review. The preparation commit contains planning and metadata only; implement all three tasks sequentially without another routine continuation question. Stop on a genuine pin/layout mismatch; do not repin, overwrite or import to get past it.

## Global Constraints

- Kunal is the sole author and committer of new project commits. Never add Codex, OpenAI, Claude, another assistant or a bot as an author, committer, co-author or project contributor. No `Co-Authored-By` trailers, generated-by signatures, assistant credits, contributor entries or assistant package-author metadata.
- No remote creation, remote addition, push, public deployment, tunnel exposure, package publication or model-weight publication until the applicable release approval in G7. Read-only public research/downloads are allowed after execution starts. Never upload proprietary files or secrets.
- Budget: INR 0 recurring. Any one-time spend, at most INR 1,500, needs explicit approval. Never assume a credit card, paid fallback or service signup is authorized.
- Hardware: Windows 11, RTX 4060 Laptop GPU with 8 GB VRAM, 16 GB RAM. Use PowerShell-compatible commands, uv, Docker Desktop and native Ollama. Load one GPU model at a time.
- Implement only files needed by the current task. Do not generate the entire directory tree, empty abstractions, trivial tests or optional features in advance.
- Reuse this checkout, existing dependencies and California helpers. No direct dependency, system install, PostgreSQL mutation, credential operation, inference, gold SQL, primary-label choice, split, exclusion/benchmark denominator change or publication.
- Never launch these scripts with a private env file. Raw source data and audit output stay under ignored `data/`. Copy only reviewed metadata summaries into docs with apply_patch.
- Preserve the existing archive, California extraction/import, correction labels, model files, named PostgreSQL volume and three original planning files. Refuse existing destinations; automatically remove only newly task-owned staging through TemporaryDirectory.
- Bounds are cooperative plus HTTP I/O timeouts, not OS hard kills or crash-durability promises. The fixed manifest and local sources are trusted immutable inputs; no hostile ancestor-link/concurrent-administrator filesystem guarantee.
- The new source extraction occupies 1,493,523,124 bytes; corrected CSV acquisition 76,445 bytes. Reserve an extra 1 GiB before extraction. Fresh preparation saw 46,325,698,560 bytes free on D: and 1,167,319,040 free RAM; recheck before execution. Do not deserialize a large SQLite file into memory.
- Stream the existing native dump from the archive; do not save another 1 GB COPY/dump tree in this preparation. The later reviewed import batch must separately prepare controlled COPY inputs and conversion/content checks.

## Review Focus

1. Duplicate/symlink/oversized archive members or path/case collisions: refuse without exposing a partial new release; Task 1 tests every class and preserves existing artifacts.
2. Redirects, inherited credentials/proxy settings, late raw body chunks or final-source corruption: no unauthorized destination/auth, no deadline bypass or partially published download; Task 2 pins these controls.
3. Legacy encoding, padded/colliding column names and populated unnamed CSV fields: decode only the pinned encoding, reject collisions, preserve source bytes and record anomalies; Task 3 exercises cp1252, padding, unnamed content and malformed records.
4. Quoted/case-sensitive identities, unsupported native layouts, timestamp types and SQLite/native count mismatches: map with existing pg_name rules, verify ordered names, record type differences without claiming value equivalence; Task 3 fixtures exercise case mapping, TIMESTAMP/TIMESTAMPTZ and rejected mismatches.
5. Missing/duplicated/truncated COPY blocks or interrupted audits: never publish a successful manifest, import source SQL or call the result gold-valid; Task 3 corruption/deadline/atomic end-to-end tests enforce this.

## File map and interfaces

- `docs/source-release-pins.json`: reviewed fixed release metadata: archive/dump/metadata pins, 11 SQLite members, 75 original/75 corrected CSV sources, 75 native table definitions/COPY pins, observed anomalies. No descriptions, data cells or gold SQL.
- Create `scripts/prepare_sources.py` and `tests/test_source_prepare.py`: fixed extraction and shared small pin/path checks.
- Create `scripts/fetch_descriptions.py` and `tests/test_description_fetch.py`: bounded one-time corrected CSV acquisition only.
- Create `scripts/audit_sources.py` and `tests/test_source_audit.py`: offline layout/key/count/description audit only.
- Create `docs/source-audit-manifest.json` after the actual Task 3 acceptance, using reviewed metadata only. Do not invent its contents now.
- Update `docs/DATA.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md` and `explaination of project/PROJECT_EXPLAINED.md` after each completed task; no AGENTS/runtime/California module refactor.
- Module APIs accept injected pin dictionaries only for internal deterministic fixtures. Production entry points always read the fixed checked-in manifest; there is no user-configurable release/URL/repinning CLI.

## Task 1: Safely extract the 87 fixed source members

**Files:** Create scripts/prepare_sources.py; test tests/test_source_prepare.py; update the four living records above.

**Interfaces:**
- Consumes `docs/source-release-pins.json` and immutable `data/raw/minidev_0703.zip`.
- Produces `extract_sources(archive_path: Path, destination: Path, *, pins: dict | None = None) -> None` and new ignored `data/source-release/minidev-0703/`.
- Shared `load_pins() -> dict`, `relative_path(value: str) -> Path`, `checked_file(path: Path, pin: dict) -> None`, `new_destination(destination: Path) -> None`, `unique_outputs(entries: list[dict]) -> None`, `selected_member(archive: ZipFile, pin: dict) -> ZipInfo` are consumed by Tasks 2/3.

- [ ] **Step 1: Add the failing tests to tests/test_source_prepare.py.**

```python
import hashlib
import stat
import zipfile
from pathlib import Path

import pytest

from scripts import prepare_sources as prep


def pin(raw, **fields):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), **fields}


def fixture_archive(tmp_path, *, duplicate=False, symlink=False):
    archive_path = tmp_path / "source.zip"
    blobs = {"schema.json": b"{}", "source.sqlite": b"fixture bytes", "source.csv": b"csv"}
    with zipfile.ZipFile(archive_path, "w") as archive:
        for member, raw in blobs.items():
            info = zipfile.ZipInfo(member)
            if symlink and member == "source.csv":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, raw)
        archive.writestr("__MACOSX/source.csv", b"not selected")
        if duplicate:
            with pytest.warns(UserWarning):
                archive.writestr("source.csv", b"csv")
    pins = {
        "archive": pin(archive_path.read_bytes()),
        "metadata": pin(blobs["schema.json"], member="schema.json", output="dev_tables.json"),
        "sqlite_sources": [pin(blobs["source.sqlite"], member="source.sqlite", output="sqlite/db.sqlite")],
        "original_description_sources": [pin(blobs["source.csv"], member="source.csv", output="original/db/table.csv")],
    }
    return archive_path, pins


def test_extracts_only_fixed_members_without_overwrite(tmp_path):
    archive_path, pins = fixture_archive(tmp_path)
    destination = tmp_path / "release"
    prep.extract_sources(archive_path, destination, pins=pins)
    assert sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()) == [
        "dev_tables.json", "original/db/table.csv", "sqlite/db.sqlite"
    ]
    with pytest.raises(ValueError, match="already exists"):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert (destination / "original/db/table.csv").read_bytes() == b"csv"


@pytest.mark.parametrize("mode", ["duplicate", "symlink", "missing", "bytes", "hash", "archive"])
def test_bad_source_never_publishes_partial_tree(tmp_path, mode):
    archive_path, pins = fixture_archive(tmp_path, duplicate=mode == "duplicate", symlink=mode == "symlink")
    if mode == "missing":
        pins["original_description_sources"][0]["member"] = "absent.csv"
    if mode == "bytes":
        pins["original_description_sources"][0]["bytes"] += 1
    if mode == "hash":
        pins["original_description_sources"][0]["sha256"] = "0" * 64
    if mode == "archive":
        pins["archive"]["sha256"] = "0" * 64
    destination = tmp_path / "release"
    with pytest.raises(ValueError):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert not destination.exists()
    assert not list(tmp_path.glob(".source-prep-*"))
    assert archive_path.exists()


@pytest.mark.parametrize("value", ["../x", "/x", "C:/x", "a\\b", "a//b", "a/./b", ""])
def test_unsafe_output_paths_rejected(value):
    with pytest.raises(ValueError, match="output path"):
        prep.relative_path(value)


def test_case_collision_disk_limit_and_deadline(tmp_path, monkeypatch):
    archive_path, pins = fixture_archive(tmp_path)
    pins["original_description_sources"][0]["output"] = "SQLITE/DB.SQLITE"
    with pytest.raises(ValueError, match="collision"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    pins["original_description_sources"][0]["output"] = "original/db/table.csv"
    monkeypatch.setattr(prep.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 0})())
    with pytest.raises(ValueError, match="disk reserve"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    monkeypatch.setattr(prep.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 10**12})())
    ticks = iter([0, 901])
    monkeypatch.setattr(prep, "monotonic", lambda: next(ticks))
    with pytest.raises(ValueError, match="deadline"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    assert not (tmp_path / "release").exists()


def test_refuses_existing_file_and_malformed_pin(tmp_path):
    archive_path, pins = fixture_archive(tmp_path)
    destination = tmp_path / "release"
    destination.write_bytes(b"keep")
    with pytest.raises(ValueError, match="already exists"):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert destination.read_bytes() == b"keep"
    pins["archive"]["bytes"] = True
    with pytest.raises(ValueError, match="invalid source pin"):
        prep.checked_file(archive_path, pins["archive"])
```

- [ ] **Step 2: Run the RED gate.**

Run `uv run pytest tests/test_source_prepare.py -q --tb=line`.
Expected: collection error because scripts.prepare_sources does not exist. Establish that cause; do not weaken a test or run acquisition before GREEN.

- [ ] **Step 3: Add this implementation to scripts/prepare_sources.py.**

```python
"""Fixed, offline source extraction; no source SQL execution."""

import hashlib
import json
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from time import monotonic

from sqlwarden.data import file_sha256

PINS_PATH = Path("docs/source-release-pins.json")
SOURCE_DIR = Path("data/source-release/minidev-0703")
ARCHIVE = Path("data/raw/minidev_0703.zip")


def load_pins() -> dict:
    return json.loads(PINS_PATH.read_text(encoding="utf-8"))


def relative_path(value: str) -> Path:
    if not isinstance(value, str) or "\\" in value or ":" in value:
        raise ValueError("unsupported output path")
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or any(part in {".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise ValueError("unsupported output path")
    return Path(*path.parts)


def checked_file(path: Path, pin: dict) -> None:
    if (
        type(pin["bytes"]) is not int
        or pin["bytes"] < 0
        or re.fullmatch(r"[a-f0-9]{64}", pin["sha256"]) is None
    ):
        raise ValueError("invalid source pin")
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size != pin["bytes"]
        or file_sha256(path) != pin["sha256"]
    ):
        raise ValueError("source pin mismatch")


def new_destination(destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists")


def unique_outputs(entries: list[dict]) -> None:
    outputs = [relative_path(entry["output"]).as_posix().casefold() for entry in entries]
    if len(set(outputs)) != len(outputs):
        raise ValueError("output path collision")


def selected_member(archive: zipfile.ZipFile, pin: dict) -> zipfile.ZipInfo:
    matches = [item for item in archive.infolist() if item.filename == pin["member"]]
    if len(matches) != 1:
        raise ValueError("archive member missing or duplicated")
    item = matches[0]
    if (
        item.is_dir()
        or stat.S_ISLNK(item.external_attr >> 16)
        or item.flag_bits & 1
        or item.file_size != pin["bytes"]
    ):
        raise ValueError("archive member rejected")
    return item


def extract_sources(archive_path: Path, destination: Path, *, pins: dict | None = None) -> None:
    pins = load_pins() if pins is None else pins
    entries = [pins["metadata"], *pins["sqlite_sources"], *pins["original_description_sources"]]
    unique_outputs(entries)
    if len({entry["member"] for entry in entries}) != len(entries):
        raise ValueError("source member collision")
    new_destination(destination)
    checked_file(archive_path, pins["archive"])
    deadline = monotonic() + 900
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(destination.parent).free < sum(e["bytes"] for e in entries) + 2**30:
        raise ValueError("insufficient disk reserve")
    with TemporaryDirectory(prefix=".source-prep-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for entry in entries:
                item = selected_member(archive, entry)
                output = staging / relative_path(entry["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                count = 0
                digest = hashlib.sha256()
                with archive.open(item) as source, output.open("xb") as target:
                    while chunk := source.read(1024 * 1024):
                        if monotonic() >= deadline:
                            raise ValueError("extraction deadline exceeded")
                        count += len(chunk)
                        if count > entry["bytes"]:
                            raise ValueError("member byte limit exceeded")
                        digest.update(chunk)
                        target.write(chunk)
                if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                    raise ValueError("member pin mismatch")
        if monotonic() >= deadline:
            raise ValueError("extraction deadline exceeded")
        new_destination(destination)
        staging.rename(destination)


def main() -> int:
    try:
        extract_sources(ARCHIVE, SOURCE_DIR)
    except (ValueError, OSError, zipfile.BadZipFile):
        print(json.dumps({"status": "failed", "stage": "source extraction"}))
        return 1
    print(json.dumps({"status": "extracted", "files": 87}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify GREEN and formatting.**

Run `uv run pytest tests/test_source_prepare.py -q --tb=line`, `uv run ruff check scripts/prepare_sources.py tests/test_source_prepare.py`, and `uv run ruff format --check scripts/prepare_sources.py tests/test_source_prepare.py`.
If formatting is required, run ruff format on just these files and repeat the checks. Fix actual failures test-first; do not alter size/hash/atomicity controls.

- [ ] **Step 5: Perform the approved one-time actual extraction.**

Without an env file, check `Test-Path data/source-release/minidev-0703` is False, `git check-ignore data/source-release/minidev-0703/sqlite/financial.sqlite` succeeds, and `Get-PSDrive D` has the required free space. Then run `uv run python -m scripts.prepare_sources` once.
Expected status extracted, 87 files: 11 SQLite files, 75 original CSVs, one metadata JSON. All exact byte/hash pins verified before rename. This copies the California source into the complete offline collection; it does not repeat its completed extraction/import or change the existing California destination.
On failure do not retry an existing destination, repin sources or delete prior artifacts automatically.

- [ ] **Step 6: Record and commit this checked logical task.**

Use DATA/PROGRESS to record exact observed file/byte counts, checks and limitations. Add a D-037 entry for approval and actual Task 1 results, with options/rationale/cost. Add a simple notebook entry explaining extraction and temporary staging. Inspect `git diff`, stage only the new module/test and four records, inspect the full staged diff and exact message `feat(data): extract pinned full source release`, then commit.
Check `git log -1 --format=fuller` and `git log -1 --format=%B`; both identities must be Kunal <kunalchandrakar2005@gmail.com>, no trailers/signatures. No source files from data/ are staged.

## Task 2: Acquire the 75 pinned corrected descriptions

**Files:** Create scripts/fetch_descriptions.py; test tests/test_description_fetch.py; update the four living records.

**Interfaces:**
- Consumes `load_pins`, `new_destination`, `relative_path`, `unique_outputs` from scripts.prepare_sources and the already-pinned `REVISION` from scripts.inspect_labels.
- Produces `fetch_descriptions(destination: Path, *, transport: httpx.BaseTransport | None = None, pins: dict | None = None) -> None` and ignored `data/description-corrections/arcwise-fe766045/`.
- No source selection, retries, redirects, credential inheritance or existing-label-directory mutation.

- [ ] **Step 1: Add the failing tests to tests/test_description_fetch.py.**

```python
import hashlib

import httpx
import pytest

from scripts import fetch_descriptions as fetch
from scripts.inspect_labels import REVISION


def fixture_pins(raw=b"fixture"):
    path = "data/schemas/db/database_description/table.csv"
    return {
        "corrected_revision": REVISION,
        "corrected_description_sources": [{
            "path": path, "url": fetch.BASE + REVISION + "/" + path,
            "output": "db/table.csv", "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }],
    }


def test_pinned_download_no_auth_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    requests = []

    def handler(request):
        requests.append(request)
        assert "authorization" not in request.headers
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(200, content=b"fixture")

    destination = tmp_path / "release"
    transport = httpx.MockTransport(handler)
    fetch.fetch_descriptions(destination, transport=transport, pins=fixture_pins())
    assert len(requests) == 1
    assert (destination / "db/table.csv").read_bytes() == b"fixture"
    with pytest.raises(ValueError, match="already exists"):
        fetch.fetch_descriptions(destination, transport=transport, pins=fixture_pins())
    assert len(requests) == 1


@pytest.mark.parametrize("mode", ["redirect", "gzip", "overflow", "truncated", "hash", "timeout"])
def test_rejected_body_leaves_no_published_files(tmp_path, mode):
    def handler(request):
        if mode == "redirect":
            return httpx.Response(302, headers={"location": "https://example.invalid"})
        if mode == "gzip":
            return httpx.Response(200, headers={"content-encoding": "gzip"}, content=b"fixture")
        if mode == "timeout":
            raise httpx.ReadTimeout("test-only", request=request)
        bodies = {"overflow": b"fixture!", "truncated": b"fix", "hash": b"changed"}
        return httpx.Response(200, content=bodies[mode])

    with pytest.raises((ValueError, httpx.HTTPError)):
        fetch.fetch_descriptions(tmp_path / "release", transport=httpx.MockTransport(handler), pins=fixture_pins())
    assert not (tmp_path / "release").exists()
    assert not list(tmp_path.glob(".description-intake-*"))


def test_each_unbuffered_raw_chunk_checks_deadline(tmp_path, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(fetch, "monotonic", lambda: clock[0])

    class LateBody(httpx.SyncByteStream):
        def __iter__(self):
            yield b"f"
            clock[0] = 181.0
            yield b"ixture"

    transport = httpx.MockTransport(lambda _: httpx.Response(200, stream=LateBody()))
    with pytest.raises(ValueError, match="deadline"):
        fetch.fetch_descriptions(tmp_path / "release", transport=transport, pins=fixture_pins())
    assert not (tmp_path / "release").exists()


def test_late_failure_is_atomic_and_old_artifacts_remain(tmp_path):
    pins = fixture_pins()
    second = dict(pins["corrected_description_sources"][0], output="db/other.csv", sha256="0" * 64)
    pins["corrected_description_sources"].append(second)
    old = tmp_path / "old"
    old.mkdir()
    (old / "keep").write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="pin mismatch"):
        fetch.fetch_descriptions(tmp_path / "release", transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"fixture")), pins=pins)
    assert (old / "keep").read_bytes() == b"unchanged"
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize("field,value", [
    ("output", "../escape"), ("url", "https://example.invalid/file"),
    ("bytes", 32769), ("bytes", True),
])
def test_invalid_fixed_source_fails_before_network(tmp_path, field, value):
    pins = fixture_pins()
    pins["corrected_description_sources"][0][field] = value

    def handler(_):
        pytest.fail("network must not be reached")

    with pytest.raises(ValueError):
        fetch.fetch_descriptions(tmp_path / "release", transport=httpx.MockTransport(handler), pins=pins)
```

- [ ] **Step 2: Run the RED gate.**

Run `uv run pytest tests/test_description_fetch.py -q --tb=line`.
Expected: collection error because scripts.fetch_descriptions does not exist.

- [ ] **Step 3: Add this implementation to scripts/fetch_descriptions.py.**

```python
"""Acquire only the 75 reviewed, revision-pinned description CSVs."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import httpx

from scripts.inspect_labels import REVISION
from scripts.prepare_sources import load_pins, new_destination, relative_path, unique_outputs

BASE = "https://raw.githubusercontent.com/uiuc-kang-lab/text_to_sql_benchmarks/"
DESCRIPTION_DIR = Path("data/description-corrections/arcwise-fe766045")


def fetch_descriptions(
    destination: Path, *, transport: httpx.BaseTransport | None = None, pins: dict | None = None
) -> None:
    pins = load_pins() if pins is None else pins
    if pins["corrected_revision"] != REVISION:
        raise ValueError("unapproved revision")
    entries = pins["corrected_description_sources"]
    unique_outputs(entries)
    for entry in entries:
        if (
            entry["url"] != BASE + REVISION + "/" + entry["path"]
            or type(entry["bytes"]) is not int
            or not 0 < entry["bytes"] <= 32768
        ):
            raise ValueError("unapproved description source")
    new_destination(destination)
    deadline = monotonic() + 180
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".description-intake-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        with httpx.Client(
            trust_env=False,
            follow_redirects=False,
            transport=transport or httpx.HTTPTransport(retries=0, trust_env=False),
            headers={"Accept-Encoding": "identity"},
        ) as client:
            for entry in entries:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ValueError("description deadline exceeded")
                raw = bytearray()
                with client.stream("GET", entry["url"], timeout=min(20.0, remaining)) as response:
                    if response.status_code != 200:
                        raise ValueError("description HTTP status rejected")
                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise ValueError("description encoding rejected")
                    for chunk in response.iter_raw():
                        if monotonic() >= deadline:
                            raise ValueError("description deadline exceeded")
                        if len(raw) + len(chunk) > entry["bytes"]:
                            raise ValueError("description byte limit exceeded")
                        raw.extend(chunk)
                if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                    raise ValueError("description pin mismatch")
                output = staging / relative_path(entry["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("xb") as target:
                    target.write(raw)
        if monotonic() >= deadline:
            raise ValueError("description deadline exceeded")
        new_destination(destination)
        staging.rename(destination)


def main() -> int:
    try:
        fetch_descriptions(DESCRIPTION_DIR)
    except (ValueError, OSError, httpx.HTTPError):
        print(json.dumps({"status": "failed", "stage": "description acquisition"}))
        return 1
    print(json.dumps({"status": "acquired", "files": 75, "revision": REVISION}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify GREEN and cumulative extraction controls.**

Run `uv run pytest tests/test_source_prepare.py tests/test_description_fetch.py -q --tb=line`, `uv run ruff check .`, and `uv run ruff format --check .`. Apply ruff formatting only to changed code if needed and repeat.
The delayed-body fixture must genuinely fail without the per-raw-chunk check; this preserves the previous correction-intake deadline fix rather than reintroducing buffered iteration.

- [ ] **Step 5: Perform the approved one-time acquisition.**

Without an env file, verify `Test-Path data/description-corrections/arcwise-fe766045` is False and `git check-ignore data/description-corrections/arcwise-fe766045/financial/account.csv` succeeds. Run `uv run python -m scripts.fetch_descriptions` once.
Expected acquired, 75 files, 76,445 aggregate bytes at revision fe766045c55b6875a43b30e9ac7683df5582f8cf; every size and SHA-256 verified. The existing pinned LICENSE/README from correction intake are retained as local license context; this is not release/distribution clearance.
No additional files, model download or correction-label refetch. A timeout/pin mismatch requires investigation, not relaxed bounds or automatic reattempt.

- [ ] **Step 6: Record and commit this checked logical task.**

Record actual request/file/byte totals and limits in DATA/PROGRESS; add D-038 with options/decision/rationale/cost; append the notebook explanation of fixed-revision downloads and source fingerprints. Inspect/stage only this module/test and those four records. Review the complete staged diff and exact message `feat(data): acquire pinned schema descriptions`, commit and inspect fuller/body identity as in the explicit Kunal identity contract above. Keep data/ ignored.

## Task 3: Audit actual SQLite layouts and description coverage offline

**Files:** Create scripts/audit_sources.py; test tests/test_source_audit.py; create docs/source-audit-manifest.json only after actual acceptance; update the four living records.

**Interfaces:**
- Consumes the fixed pins, Task 1 source tree, Task 2 corrected CSV tree and the immutable original archive.
- Produces `inspect_native(stream: BinaryIO, tables: dict, dump_pin: dict, *, deadline: float) -> dict`, `inspect_sqlite(path: Path, db_id: str, tables: dict, *, deadline: float) -> dict`, `inspect_description(raw: bytes, pin: dict, fields: list[str], columns: list[str]) -> dict`, `inspect_metadata(path: Path, tables: dict) -> None`, and `audit_sources(release: Path, corrected: Path, archive_path: Path, destination: Path, *, pins: dict | None = None) -> dict`.
- Output is a new ignored audit directory containing manifest.json. Its metadata may be copied to docs only after inspection; no raw values, description prose, SQL, credentials or foreign-key row IDs.
- Ordered identifiers, declared source/native types, row counts, primary/foreign-key metadata and violation counts are observations. None establishes representative value equivalence, conversion survival, PostgreSQL isolation for new datasets or primary-description selection.

- [ ] **Step 1: Add the failing tests to tests/test_source_audit.py.**

```python
import csv
import hashlib
import io
import json
import sqlite3
import zipfile

import pytest

from scripts import audit_sources as audit
from scripts.prepare_sources import checked_file, extract_sources
from sqlwarden.data import file_sha256


def pin(raw, **fields):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), **fields}


def native_fixture():
    data = b"1\t2020-01-01\n2\t\\N\n"
    dump = b"CREATE TABLE public.thing (\n    id bigint,\n    happened timestamp with time zone\n);\nCOPY public.thing (id, happened) FROM stdin;\n" + data + b"\\.\n"
    table = {
        "db_id": "db", "source_name": "Thing",
        "columns": [{"name": "id", "type": "BIGINT"}, {"name": "happened", "type": "TIMESTAMPTZ"}],
        "copy": {"rows": 2, **pin(data)},
    }
    return dump, {"thing": table}


def description_bytes(fields, names, *, encoding="utf-8", unnamed=""):
    text = io.StringIO(newline="")
    writer = csv.writer(text)
    writer.writerow(fields)
    for index, name in enumerate(names):
        writer.writerow([name, name.strip(), "café", "", "", *([unnamed if index == 0 else ""] if fields[-1] == "" else [])])
    return text.getvalue().encode(encoding)


def test_native_types_and_blocks_are_metadata_not_execution():
    dump, tables = native_fixture()
    result = audit.inspect_native(io.BytesIO(dump), tables, pin(dump), deadline=float("inf"))
    assert result == {"thing": tables["thing"]["copy"]}


@pytest.mark.parametrize("mode", ["duplicate", "unknown", "truncated", "columns", "types", "row", "line", "digest"])
def test_native_corruption_is_not_an_audit_success(mode):
    dump, tables = native_fixture()
    if mode == "duplicate":
        dump += dump
    elif mode == "unknown":
        dump = dump.replace(b"public.thing", b"public.unknown")
    elif mode == "truncated":
        dump = dump[:-3]
    elif mode == "columns":
        dump = dump.replace(b"(id, happened) FROM", b"(happened, id) FROM")
    elif mode == "types":
        dump = dump.replace(b"id bigint", b"id text")
    elif mode == "row":
        dump = dump.replace(b"1\t2020-01-01", b"1")
    elif mode == "line":
        dump += b"x" * (audit.MAX_LINE_BYTES + 1) + b"\n"
    dump_pin = pin(dump)
    if mode == "digest":
        dump_pin["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        audit.inspect_native(io.BytesIO(dump), tables, dump_pin, deadline=float("inf"))


def test_description_padding_extra_and_unnamed_content_remain_observations():
    fields = ["original_column_name", "column_name", "column_description", "data_format", "value_description"]
    raw = description_bytes(fields + [""], ["id ", "wins "], encoding="cp1252", unnamed="not discarded")
    result = audit.inspect_description(raw, {"encoding": "cp1252", "unnamed_header": True}, fields, ["id"])
    assert result["extra"] == ["wins"]
    assert result["unnamed_nonempty_rows"] == [1]
    assert result["padding_aliases"] == [
        {"source_name": "id ", "mapped_name": "id"}, {"source_name": "wins ", "mapped_name": "wins"}
    ]
    assert "not discarded" not in json.dumps(result)


@pytest.mark.parametrize("mode", ["collision", "short", "extra", "header", "encoding"])
def test_description_malformed_records_fail_closed(mode):
    fields = ["original_column_name", "column_name", "column_description", "data_format", "value_description"]
    raw = description_bytes(fields, ["id", " id "] if mode == "collision" else ["id"])
    if mode == "short":
        raw = b",".join(field.encode() for field in fields) + b"\nid,too-short\n"
    elif mode == "extra":
        raw = b",".join(field.encode() for field in fields) + b"\nid,id,text,,,surplus\n"
    elif mode == "header":
        raw = raw.replace(b"original_column_name", b"unknown")
    elif mode == "encoding":
        raw = description_bytes(fields, ["id"], encoding="cp1252")
    with pytest.raises((ValueError, UnicodeDecodeError, csv.Error)):
        audit.inspect_description(raw, {"encoding": "utf-8-sig", "unnamed_header": False}, fields, ["id"])


def create_sqlite(path, *, extra_table=False, extra_column=False):
    with sqlite3.connect(path) as conn:
        suffix = ", extra TEXT" if extra_column else ""
        conn.execute("CREATE TABLE Thing (id INTEGER PRIMARY KEY, happened TIMESTAMP" + suffix + ")")
        conn.execute("INSERT INTO Thing (id, happened) VALUES (1, '2020-01-01'), (2, NULL)")
        if extra_table:
            conn.execute("CREATE TABLE Unexpected (x TEXT)")


def test_sqlite_actual_layout_rows_keys_without_mutation(tmp_path):
    path = tmp_path / "db.sqlite"
    create_sqlite(path)
    _, tables = native_fixture()
    before = file_sha256(path)
    report = audit.inspect_sqlite(path, "db", tables, deadline=float("inf"))
    assert report["tables"]["thing"]["rows"] == 2
    assert report["tables"]["thing"]["primary_key"] == ["id"]
    column = report["tables"]["thing"]["columns"][1]
    assert (column["source_type"], column["native_type"]) == ("TIMESTAMP", "TIMESTAMPTZ")
    assert report["foreign_key_violation_count"] == 0
    assert file_sha256(path) == before



def test_foreign_key_metadata_and_violations_are_reported_not_hidden(tmp_path):
    path = tmp_path / "db.sqlite"
    create_sqlite(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE Child (pid INTEGER REFERENCES Thing(id))")
        conn.execute("INSERT INTO Child VALUES (99)")
    _, tables = native_fixture()
    tables["child"] = {
        "db_id": "db", "source_name": "Child",
        "columns": [{"name": "pid", "type": "BIGINT"}], "copy": {"rows": 1},
    }
    report = audit.inspect_sqlite(path, "db", tables, deadline=float("inf"))
    assert report["foreign_key_violation_count"] == 1
    key = report["tables"]["child"]["foreign_keys"][0]
    assert (key["parent_table"], key["column"], key["parent_column"]) == ("Thing", "pid", "id")
    assert "99" not in json.dumps(report)


@pytest.mark.parametrize("mode", ["table", "column", "count", "deadline"])
def test_sqlite_layout_count_or_deadline_mismatch_is_not_validity(tmp_path, mode):
    path = tmp_path / "db.sqlite"
    create_sqlite(path, extra_table=mode == "table", extra_column=mode == "column")
    _, tables = native_fixture()
    if mode == "count":
        tables["thing"]["copy"]["rows"] = 3
    with pytest.raises((ValueError, sqlite3.OperationalError)):
        audit.inspect_sqlite(path, "db", tables, deadline=0 if mode == "deadline" else float("inf"))


def test_metadata_layout_mismatch_rejected(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps([{"db_id": "wrong", "table_names_original": ["Thing"],
        "column_names_original": [[-1, "*"], [0, "id"], [0, "happened"]]}]), encoding="utf-8")
    _, tables = native_fixture()
    with pytest.raises(ValueError, match="metadata layout"):
        audit.inspect_metadata(path, tables)


def test_atomic_end_to_end_source_audit_has_no_gold_validity_claim(tmp_path):
    sqlite_path = tmp_path / "db.sqlite"
    create_sqlite(sqlite_path)
    dump, tables = native_fixture()
    fields = ["original_column_name", "column_name", "column_description", "data_format", "value_description"]
    raw = description_bytes(fields, ["id", "happened"])
    metadata = json.dumps([{"db_id": "db", "table_names_original": ["Thing"],
        "column_names_original": [[-1, "*"], [0, "id"], [0, "happened"]]}]).encode()
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("db.sqlite", sqlite_path.read_bytes())
        archive.writestr("original.csv", raw)
        archive.writestr("metadata.json", metadata)
        archive.writestr("native.sql", dump)
    description = {"db_id": "db", "native_table": "thing", "encoding": "utf-8-sig", "unnamed_header": False}
    pins = {
        "archive": pin(archive_path.read_bytes()),
        "metadata": pin(metadata, member="metadata.json", output="dev_tables.json"),
        "native_dump": pin(dump, member="native.sql"),
        "sqlite_sources": [pin(sqlite_path.read_bytes(), db_id="db", member="db.sqlite", output="sqlite/db.sqlite")],
        "original_description_sources": [pin(raw, **description, member="original.csv", output="original/db/thing.csv")],
        "corrected_description_sources": [pin(raw, **description, output="db/thing.csv")],
        "tables": tables, "csv_fields": fields, "corrected_revision": "fixture-only",
        "observations": {"original_unmapped_columns": []},
    }
    release = tmp_path / "release"
    corrected = tmp_path / "corrected"
    (corrected / "db").mkdir(parents=True)
    (corrected / "db/thing.csv").write_bytes(raw)
    extract_sources(archive_path, release, pins=pins)
    destination = tmp_path / "audit"
    report = audit.audit_sources(release, corrected, archive_path, destination, pins=pins)
    assert json.loads((destination / "manifest.json").read_text()) == report
    assert report["conversion_validity"] == "not checked"
    assert report["typed_content_equivalence"] == "not checked"
    checked_file(sqlite_path, pins["sqlite_sources"][0])
    with pytest.raises(ValueError, match="already exists"):
        audit.audit_sources(release, corrected, archive_path, destination, pins=pins)
    pins["corrected_description_sources"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source pin mismatch"):
        audit.audit_sources(release, corrected, archive_path, tmp_path / "bad-audit", pins=pins)
    assert not (tmp_path / "bad-audit").exists()
```

- [ ] **Step 2: Run the RED gate.**

Run `uv run pytest tests/test_source_audit.py -q --tb=line`.
Expected: collection error because scripts.audit_sources does not exist. Real SQLite test fixtures must run once implemented; native source SQL is never executed.

- [ ] **Step 3: Add this implementation to scripts/audit_sources.py.**

```python
"""Read-only source/layout audit; not a PostgreSQL import or gold-validity check."""

import csv
import hashlib
import io
import json
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import BinaryIO

import sqlglot
from sqlglot import exp

from scripts.fetch_descriptions import DESCRIPTION_DIR
from scripts.prepare_sources import (
    ARCHIVE,
    SOURCE_DIR,
    checked_file,
    load_pins,
    new_destination,
    relative_path,
    selected_member,
)
from sqlwarden.data import COPY_HEADER, MAX_LINE_BYTES, pg_name, quote_ident

AUDIT_DIR = Path("data/source-audit/minidev-0703-fe766045")


def inspect_native(stream: BinaryIO, tables: dict, dump_pin: dict, *, deadline: float) -> dict:
    definitions = {}
    blocks = {}
    ddl = []
    active = None
    dump_digest = hashlib.sha256()
    dump_bytes = 0
    checksum = None
    while line := stream.readline(MAX_LINE_BYTES + 1):
        if monotonic() >= deadline:
            raise ValueError("audit deadline exceeded")
        dump_bytes += len(line)
        if len(line) > MAX_LINE_BYTES or not line.endswith(b"\n") or dump_bytes > dump_pin["bytes"]:
            raise ValueError("native line or dump byte limit exceeded")
        dump_digest.update(line)
        if active is not None:
            if line == b"\\.\n":
                blocks[active]["sha256"] = checksum.hexdigest()
                if blocks[active] != tables[active]["copy"]:
                    raise ValueError("native block pin mismatch")
                active = None
            else:
                block = blocks[active]
                block["rows"] += 1
                block["bytes"] += len(line)
                if (
                    block["rows"] > tables[active]["copy"]["rows"]
                    or block["bytes"] > tables[active]["copy"]["bytes"]
                    or line.count(b"\t") + 1 != len(tables[active]["columns"])
                ):
                    raise ValueError("native row shape or block budget exceeded")
                checksum.update(line)
            continue
        if ddl:
            ddl.append(line)
            if sum(map(len, ddl)) > 65536:
                raise ValueError("native definition byte limit exceeded")
            if line == b");\n":
                statement = sqlglot.parse_one(b"".join(ddl).decode("utf-8"), read="postgres")
                if not isinstance(statement, exp.Create) or not isinstance(statement.this, exp.Schema):
                    raise ValueError("unsupported native definition")
                table = statement.this.this
                if table.db != "public" or table.name not in tables or table.name in definitions:
                    raise ValueError("native table identity mismatch")
                if any(not isinstance(c, exp.ColumnDef) for c in statement.this.expressions):
                    raise ValueError("unsupported native definition member")
                columns = [{"name": c.this.name, "type": c.kind.sql(dialect="postgres")} for c in statement.this.expressions]
                if columns != tables[table.name]["columns"]:
                    raise ValueError("native definition differs")
                definitions[table.name] = columns
                ddl = []
            continue
        if line.startswith(b"CREATE TABLE "):
            if not line.startswith(b"CREATE TABLE public."):
                raise ValueError("unsupported native table schema")
            ddl = [line]
        elif line.startswith(b"COPY "):
            match = COPY_HEADER.fullmatch(line)
            if match is None:
                raise ValueError("unsupported native COPY header")
            active = next(csv.reader([match[1].decode("utf-8")], strict=True))[0]
            if active not in tables or active in blocks or active not in definitions:
                raise ValueError("native COPY identity mismatch")
            columns = next(csv.reader([match[2].decode("utf-8")], skipinitialspace=True, strict=True))
            if columns != [c["name"] for c in tables[active]["columns"]]:
                raise ValueError("native COPY columns differ")
            blocks[active] = {"rows": 0, "bytes": 0}
            checksum = hashlib.sha256()
    if ddl or active is not None or set(blocks) != set(tables) or set(definitions) != set(tables):
        raise ValueError("native release incomplete")
    if dump_bytes != dump_pin["bytes"] or dump_digest.hexdigest() != dump_pin["sha256"]:
        raise ValueError("native dump pin mismatch")
    return blocks


def inspect_sqlite(path: Path, db_id: str, tables: dict, *, deadline: float) -> dict:
    expected = {name: table for name, table in tables.items() if table["db_id"] == db_id}
    result = {}
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        conn.execute("PRAGMA cache_size=-8192")
        conn.set_progress_handler(lambda: int(monotonic() >= deadline), 10000)
        if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("SQLite quick check failed")
        physical = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'")]
        mapped = {pg_name(name): name for name in physical}
        if len(mapped) != len(physical) or set(mapped) != set(expected):
            raise ValueError("SQLite table identity mismatch")
        violations = 0
        for _ in conn.execute("PRAGMA foreign_key_check"):
            violations += 1
            if monotonic() >= deadline:
                raise ValueError("audit deadline exceeded")
        for name, table in expected.items():
            physical_name = mapped[name]
            columns = conn.execute(f"PRAGMA table_info({quote_ident(physical_name)})").fetchall()
            names = [pg_name(row[1]) for row in columns]
            if len(set(names)) != len(names) or names != [c["name"] for c in table["columns"]]:
                raise ValueError("SQLite columns differ")
            count = conn.execute(f"SELECT COUNT(*) FROM {quote_ident(physical_name)}").fetchone()[0]
            if count != table["copy"]["rows"]:
                raise ValueError("SQLite/native row counts differ")
            result[name] = {
                "source_name": physical_name,
                "rows": count,
                "columns": [
                    {"name": pg_name(row[1]), "source_name": row[1], "source_type": row[2],
                     "native_type": native["type"], "declared_not_null": bool(row[3]),
                     "primary_key_position": row[5]}
                    for row, native in zip(columns, table["columns"], strict=True)
                ],
                "primary_key": [pg_name(row[1]) for row in sorted(columns, key=lambda r: r[5]) if row[5]],
                "foreign_keys": [
                    {"id": row[0], "sequence": row[1], "parent_table": row[2],
                     "column": row[3], "parent_column": row[4],
                     "on_update": row[5], "on_delete": row[6], "match": row[7]}
                    for row in conn.execute(f"PRAGMA foreign_key_list({quote_ident(physical_name)})")
                ],
            }
            if monotonic() >= deadline:
                raise ValueError("audit deadline exceeded")
    return {"tables": result, "foreign_key_violation_count": violations}


def inspect_description(raw: bytes, pin: dict, fields: list[str], columns: list[str]) -> dict:
    expected_fields = fields + ([""] if pin["unnamed_header"] else [])
    reader = csv.DictReader(io.StringIO(raw.decode(pin["encoding"], errors="strict"), newline=""), strict=True)
    if reader.fieldnames != expected_fields:
        raise ValueError("description header differs")
    names = []
    aliases = []
    unnamed = []
    for index, row in enumerate(reader, 1):
        if None in row or any(not isinstance(value, str) for value in row.values()):
            raise ValueError("description field count differs")
        original = row["original_column_name"]
        name = pg_name(original.strip())
        if name in names:
            raise ValueError("description column collision")
        names.append(name)
        if original != original.strip():
            aliases.append({"source_name": original, "mapped_name": name})
        if row.get(""):
            unnamed.append(index)
    return {
        "rows": len(names), "missing": sorted(set(columns) - set(names)),
        "extra": sorted(set(names) - set(columns)), "padding_aliases": aliases,
        "unnamed_nonempty_rows": unnamed,
    }


def inspect_metadata(path: Path, tables: dict) -> None:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    observed = {}
    for database in metadata:
        for index, source_name in enumerate(database["table_names_original"]):
            name = pg_name(source_name)
            if name in observed:
                raise ValueError("metadata table collision")
            observed[name] = {
                "db_id": database["db_id"],
                "columns": [pg_name(column) for table_id, column in database["column_names_original"] if table_id == index],
            }
    expected = {
        name: {"db_id": table["db_id"], "columns": [c["name"] for c in table["columns"]]}
        for name, table in tables.items()
    }
    if observed != expected:
        raise ValueError("metadata layout differs")


def audit_sources(
    release: Path, corrected: Path, archive_path: Path, destination: Path, *, pins: dict | None = None
) -> dict:
    pins = load_pins() if pins is None else pins
    new_destination(destination)
    deadline = monotonic() + 1200
    checked_file(archive_path, pins["archive"])
    checked_file(release / relative_path(pins["metadata"]["output"]), pins["metadata"])
    inspect_metadata(release / relative_path(pins["metadata"]["output"]), pins["tables"])
    report = {
        "format_version": 1, "status": "source layout audit only",
        "conversion_validity": "not checked", "typed_content_equivalence": "not checked",
        "primary_descriptions": "not selected", "databases": {}, "descriptions": {},
        "source_archive_sha256": pins["archive"]["sha256"],
        "corrected_revision": pins["corrected_revision"],
    }
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(selected_member(archive, pins["native_dump"])) as stream:
            report["native_blocks"] = inspect_native(stream, pins["tables"], pins["native_dump"], deadline=deadline)
    for entry in pins["sqlite_sources"]:
        path = release / relative_path(entry["output"])
        checked_file(path, entry)
        report["databases"][entry["db_id"]] = inspect_sqlite(path, entry["db_id"], pins["tables"], deadline=deadline)
    for source, root, entries in [
        ("original", release, pins["original_description_sources"]),
        ("corrected", corrected, pins["corrected_description_sources"]),
    ]:
        for entry in entries:
            if monotonic() >= deadline:
                raise ValueError("audit deadline exceeded")
            path = root / relative_path(entry["output"])
            checked_file(path, entry)
            columns = [c["name"] for c in pins["tables"][entry["native_table"]]["columns"]]
            description = inspect_description(path.read_bytes(), entry, pins["csv_fields"], columns)
            allowed_extra = [
                observation["mapped_name"] for observation in pins["observations"]["original_unmapped_columns"]
                if source == "original" and observation["db_id"] == entry["db_id"]
                and observation["table"] == entry["native_table"]
            ]
            if description["missing"] or description["extra"] != sorted(allowed_extra):
                raise ValueError("description/native column coverage differs")
            report["descriptions"][source + "/" + entry["db_id"] + "/" + entry["native_table"]] = description
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".source-audit-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "report"
        staging.mkdir()
        (staging / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if monotonic() >= deadline:
            raise ValueError("audit deadline exceeded")
        new_destination(destination)
        staging.rename(destination)
    return report


def main() -> int:
    try:
        report = audit_sources(SOURCE_DIR, DESCRIPTION_DIR, ARCHIVE, AUDIT_DIR)
    except (ValueError, OSError, sqlite3.Error, csv.Error, zipfile.BadZipFile, sqlglot.errors.ParseError):
        print(json.dumps({"status": "failed", "stage": "offline source audit"}))
        return 1
    print(json.dumps({"status": "audited", "databases": len(report["databases"]), "tables": len(report["native_blocks"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify GREEN and the complete deterministic batch.**

Run `uv run pytest tests/test_source_prepare.py tests/test_description_fetch.py tests/test_source_audit.py -q --tb=line`; run ruff check/format checks and fix actual issues test-first. Add focused reproductions before changing behavior if real source bytes expose an unanticipated condition; keep pins and the benchmark definition unchanged.

- [ ] **Step 5: Perform the approved actual offline audit.**

Without an env file, check `Test-Path data/source-audit/minidev-0703-fe766045` is False and `git check-ignore data/source-audit/minidev-0703-fe766045/manifest.json` succeeds. Run `uv run python -m scripts.audit_sources` once.
Expected: audited, 11 databases, 75 tables. Rechecked metadata/native definitions and all ordered columns must cover 798 columns; COPY data-line total 3,898,114 must equal actual SQLite table-count total before a successful report. Full native dump and each COPY block must match pins.
Original descriptions contain 799 records: preserve/report formula_1 constructors' unknown wins record. Corrected descriptions cover 798 columns with no missing/extra/duplicate matches. Preserve/report 89 original padding aliases and the populated unnamed financial/account field at one-based data row 3 in both sources. Four original/three corrected encoding exceptions are explicit pins, not automatic fallback.
Inspect actual FK counts/layout and all declared types before proposing import mappings; do not silently waive a mismatch or treat a count match as content validity. The 11 native TIMESTAMPTZ columns require later timezone/conversion policy.

- [ ] **Step 6: Save reviewed metadata, fresh regressions, records and commit.**

Read the ignored report, verify that it contains metadata only, and use apply_patch to add its actual content to docs/source-audit-manifest.json. Add execution date/Git state and clearly retain conversion/content validity not checked and primary descriptions not selected. Do not fabricate expected results on failure.
Run `uv sync --locked`, `uv run pytest -q --tb=line`, `uv run --env-file .env.setup --env-file .env.california pytest -q --tb=line`, `uv run ruff check .`, `uv run ruff format --check .`, and `git diff --check`. Private envs are used for tests only; the existing 165 PostgreSQL checks must actually run.
Update DATA/PROGRESS, D-039 and notebook with actual checks and source findings. G0 remains 7/12; this completes three new nested G0.5 preparation tasks, not full imports/conversion/C1. Stage only module/test, checked metadata and four records. Inspect the complete staged diff and exact message `feat(data): audit full source layouts and descriptions`, commit, and inspect fuller/body author and committer.

## Batch completion and next checkpoint

- [ ] Complete one fresh final read-only review of the whole approved batch after all three tasks, using requesting-code-review/executing-plans; no parallel implementation or repeated per-component review.
- [ ] Resolve Important/Critical findings in one test-first pass under the same scope, record every ruling/cost and actual regressions. No automatic second review. If scope must change, pause.
- [ ] Keep the checked branch local, update Handoff/notebook, report actual commits, tests and three completed nested checklist items.
- [ ] Prepare the next separate controlled COPY/import/content/conversion plan from the actual audit; obtain its artifact/operation review before administrative writes, passwords or gold queries. C1 still needs labels/layout/conversion/ambiguity decisions before any benchmark freeze.

## Self-review (preparation, not execution)

Spec coverage: this deliberately implements only the next offline G0.5 source-preparation boundary. PostgreSQL imports, typed/content equivalence, result conversion, validity/exclusions, label/description policy, split/E0/second model and C1 are explicit subsequent gated work, not missing promised features.
File/API consistency: all helpers used by Tasks 2/3 are defined in Task 1; outputs consumed by Task 3 match fixed directories/member/output paths; existing California code is unchanged.
Review Focus: each of the five classes maps to the named fixture tests above. Trusted immutable pins/Windows filesystem and cooperative hard-interruption limitations are explicit.
Code blocks will be syntax-parsed without executing proposed implementation or claiming its tests GREEN during preparation. Ruff formatting is a mechanical execution step, not a reason to adjust boundaries.
No fresh implementation/review agent is dispatched for preparing this plan.
