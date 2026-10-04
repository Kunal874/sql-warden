# Corrected-label intake and alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Native sequential execution is already selected; no parallel implementation.

**Goal:** Acquire a small, pinned correction release and produce a tested offline alignment report without selecting labels, executing SQL or changing the benchmark.

**Architecture:** Two ordinary setup scripts, using dictionaries and existing libraries. The first verifies local bytes and joins labels by numeric question ID; the second acquires only four fixed HTTPS resources into a new ignored directory. Neither script imports the runtime, reads environment credentials, connects to a database or calls a model.

**Tech Stack:** Python 3.12, uv, stdlib json/hashlib/pathlib/tempfile, existing approved httpx, pytest/ruff. No new dependency.

**Spec:** docs/BUILD_SPEC.md sections 8, 10–12; AGENTS.md; D-032.
This is the first bounded increment of remaining G0.5, not completion of G0.5/C1.

**Status:** Approved 2026-10-05 by Kunal's proceed forward after artifact review.
Native sequential execution; only this plan's two tasks/acquisition scope approved.

Execution schema correction: actual pinned correction sources have null evidence
at IDs 1507/1528 in both sets. Accept null only in corrected evidence; preserve it,
do not coerce it to an empty hint or omit records. Original evidence stays strict.
The test-first correction and rationale/cost are recorded in D-034 and the ledger.

## Global Constraints

- Work in this directory. Implement only the current task; keep a safe thin slice first.
- Python 3.12 with uv; PostgreSQL 16 in Docker; native Ollama; React 18/TypeScript later.
- No parallel implementation unless Kunal asks. Keep the runtime a plain Python state machine.
- Keep inference local until a hosted configuration is explicitly approved.
- No remote addition or push before the G7 release approval.
- Preserve the three original planning files as historical inputs.
- Never commit secrets, downloads, model weights, caches or raw runs.
- Do not print connection credentials or put them in model prompts.
- After a task, run its relevant checks and update progress with truthful results.
- Kunal is the sole author and committer: Kunal <kunalchandrakar2005@gmail.com>.
- Inspect staged changes and the exact message before each Conventional Commit; check author, committer and body after it. Do not change global Git identity.

Approval of this plan authorizes only the two tasks below, downloading their four
fixed resources (645,140 content bytes in total), new ignored correction files,
and cleanup of this acquisition's own temporary staging directory on failure.
It does not authorize reloading any database, changing permissions/passwords,
downloading weights, inference, executing any gold SQL, selecting/excluding
benchmark items, freezing splits, publication or deleting existing artifacts.
Missing/mismatched identities and changed question/evidence text must be reported,
not silently normalized or interpreted as proven ambiguity.

## Inputs already inspected read-only

Upstream revision: fe766045c55b6875a43b30e9ac7683df5582f8cf.
[Release README](https://github.com/uiuc-kang-lab/text_to_sql_benchmarks/blob/fe766045c55b6875a43b30e9ac7683df5582f8cf/README.md)
calls the releases Arcwise-Plat-SQL and Arcwise-Plat; its second JSON filename
still contains full. Original planning inputs are preserved, not renamed.

| Fixed upstream resource | Bytes | SHA-256 |
| --- | ---: | --- |
| data/arcwise_plat_sql_only_with_diff.json | 287718 | e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395 |
| data/arcwise_plat_full_with_diff.json | 332246 | baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8 |
| README.md | 5038 | 7aefaba8da2792a8edde1cb534dde1f89c3228e87ac5b923838ba68bb56cf0f5 |
| LICENSE | 20138 | 28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5 |

The two ignored original files are already present, pinned in DATA.md.
Both corrections have 498 unique decimal-string IDs; canonical labels use
integer IDs. Both omit 119/120 (financial), have no unexpected IDs or database
mismatch, and include variable optional metadata fields. SQL-only differs from
our canonical SQLite questions/evidence on 81/86 IDs (141 either); full differs
on 147/152 (229 either). Between corrected sets 88 questions/98 evidence fields
differ (148 either). These are exact text comparisons, not ambiguity annotations.
Their list order starts at thrombosis_prediction, not canonical California;
never zip lists by position. SQL-only's single difficulty field is ID405,
moderate, consistent with canonical.

The upstream schemas tree is 9cf49139c686a1156491f1859c0a75c91e257897:
75 description CSVs, 76,445 bytes by Git tree metadata. This plan does not acquire,
parse or apply them. Their content mapping and any needed physical-schema changes
remain a separate reviewed increment before C1/conversion claims.

## File map and interfaces

- Create scripts/inspect_labels.py: pinned local reading, strict shape/ID validation,
  stable-ID report without record text. Offline only.
- Create tests/test_labels.py: small synthetic records, no downloaded corpus.
- Create scripts/fetch_labels.py: fixed-resource acquisition with bounded streaming,
  SHA/size checks, exclusive all-or-nothing directory publication.
- Create tests/test_label_fetch.py: synthetic HTTPX streams, no real network.
- Update docs/DATA.md, docs/DECISIONS.md, docs/PROGRESS.md and
  explaination of project/PROJECT_EXPLAINED.md after each checked task.
- At acceptance, create docs/label-alignment-manifest.json from inspected aggregate
  report metadata/ID differences using apply_patch. No question/evidence/SQL values.
  Full generated alignment stays ignored; no active benchmark denominator.

Public script functions:

- decode_labels(raw: bytes, *, corrected: bool) -> dict[int, dict]
- read_pinned(path: Path, size: int, digest: str) -> bytes
- build_report(sources: dict[str, dict[int, dict]]) -> dict
- inspect_local(data_root: Path) -> dict
- fetch_sources(destination: Path, *, transport: httpx.BaseTransport | None = None) -> None

These are setup-only functions, not runtime APIs. Task 2 imports only the fixed
CORRECTION_DIR/REVISION constants from Task 1; it does not add a dynamic provider,
URL selector or database/model integration.

## Review Focus

1. Integer versus decimal-string IDs, duplicates and reordering must never cause
   positional or coercion-based false joins — Task 1 ID/shuffle tests.
2. A corrected question or hint, including SQL-only baseline drift, is not a
   proven ambiguity label — Task 1 exact-difference/undecided-status test.
3. Missing/extra IDs, known-db mismatches and inconsistent optional difficulty
   must be explicit even if most records match — Task 1 mismatch test.
4. Invalid JSON/types/duplicate object keys and changed pinned bytes must not
   produce trusted records — Task 1 malformed/hash tests and Task 2 hash test.
5. Redirects, compression, oversized/slow/partial replies and an existing target
   must not publish a partial release or overwrite old data — Task 2 stream tests.

## Task 1: Strict offline label inspection

**Files:** Create scripts/inspect_labels.py and tests/test_labels.py;
update the four living records after GREEN.

**Interfaces:** Consumes only immutable byte files and dictionaries; produces
the four inspection signatures above, excluding fetch_sources.
A report labels execution_validity as not_run, primary_labels as not_selected,
splits as not_frozen and ambiguity_labels as not_classified. identity_aligned_count
checks ID/database only; it is not verified question or result validity.

- [x] **Step 1: Write all failing tests before source.**

Create tests/test_labels.py:

~~~python
import hashlib
import json

import pytest

from scripts.inspect_labels import LabelError, build_report, decode_labels, read_pinned


def record(identifier=1, **changes):
    row = {
        "question_id": identifier,
        "db_id": "california_schools",
        "question": "How many schools?",
        "evidence": "",
        "SQL": "SELECT COUNT(*) FROM schools",
        "difficulty": "simple",
    }
    row.update(changes)
    return row


def parsed(rows, *, corrected=False):
    if corrected:
        rows = [dict(r, question_id=str(r["question_id"])) for r in rows]
    return decode_labels(json.dumps(rows).encode(), corrected=corrected)


def sources():
    rows = [record(1), record(2)]
    return {
        "bird_sqlite": parsed(rows),
        "bird_pg": parsed(list(reversed(rows))),
        "arcwise_sql": parsed(list(reversed(rows)), corrected=True),
        "arcwise_full": parsed(rows, corrected=True),
    }


def test_ids_join_across_types_and_order():
    report = build_report(sources())
    assert report["original_count"] == 2
    assert report["by_source"]["arcwise_sql"]["identity_aligned_count"] == 2
    assert report["by_source"]["bird_pg"]["missing_ids"] == []


@pytest.mark.parametrize("identifier", [True, -1, 0, 1.0, "1", None])
def test_original_id_types_are_strict(identifier):
    with pytest.raises(LabelError):
        decode_labels(json.dumps([record(identifier)]).encode(), corrected=False)


@pytest.mark.parametrize("identifier", [1, True, "01", "+1", "1.0", " 1", "", "1000000"])
def test_corrected_id_types_are_strict(identifier):
    with pytest.raises(LabelError):
        decode_labels(json.dumps([record(identifier)]).encode(), corrected=True)


def test_duplicate_ids_and_object_keys_are_rejected():
    with pytest.raises(LabelError):
        parsed([record(), record()])
    with pytest.raises(LabelError):
        decode_labels(b'[{"question_id":1,"question_id":2}]', corrected=False)


@pytest.mark.parametrize(
    "change",
    [
        {"db_id": "unknown"},
        {"question": ""},
        {"question": "   "},
        {"SQL": ""},
        {"SQL": "   "},
        {"SQL": False},
        {"evidence": None},
        {"original_SQL": 5},
        {"difficulty": "unknown"},
        {"difficulty": []},
        {"unreviewed_field": "value"},
    ],
)
def test_fields_reject_unreviewed_shapes(change):
    with pytest.raises(LabelError):
        parsed([record(**change)])


@pytest.mark.parametrize(
    "raw",
    [b"null", b"{}", b"[]", b"[NaN]", b"[", b"\xff", b" " * 600001],
    ids=["null", "object", "empty", "constant", "broken", "invalid_utf8", "oversize"],
)
def test_invalid_documents_are_rejected(raw):
    with pytest.raises(LabelError):
        decode_labels(raw, corrected=False)


def test_text_changes_do_not_select_labels_or_classify_ambiguity():
    data = sources()
    data["arcwise_sql"][1]["question"] = "A different question"
    data["arcwise_full"][1]["evidence"] = "A different hint"
    report = build_report(data)
    assert report["by_source"]["arcwise_sql"]["question_difference_ids"] == [1]
    assert report["by_source"]["arcwise_full"]["evidence_difference_ids"] == [1]
    assert report["corrected_pair_text_difference_ids"] == [1]
    assert report["execution_validity"] == "not_run"
    assert report["primary_labels"] == "not_selected"
    assert report["ambiguity_labels"] == "not_classified"
    assert report["splits"] == "not_frozen"
    assert "SELECT COUNT" not in json.dumps(report)
    assert "A different" not in json.dumps(report)


def test_missing_extra_database_and_difficulty_mismatches_are_visible():
    data = sources()
    data["arcwise_sql"].pop(2)
    data["arcwise_sql"][3] = record(3)
    data["arcwise_sql"][1]["db_id"] = "financial"
    data["arcwise_sql"][1]["difficulty"] = "moderate"
    track = build_report(data)["by_source"]["arcwise_sql"]
    assert track["missing_ids"] == [2]
    assert track["unexpected_ids"] == [3]
    assert track["database_mismatch_ids"] == [1]
    assert track["difficulty_mismatch_ids"] == [1]
    assert track["identity_aligned_count"] == 0


def test_original_fields_are_observations_not_trusted_overrides():
    data = sources()
    data["arcwise_full"][1]["original_question"] = "Not our pinned question"
    assert build_report(data)["by_source"]["arcwise_full"]["question_anchor_mismatch_ids"] == [1]


def test_pinned_reader_rejects_bad_size_or_digest(tmp_path):
    path = tmp_path / "labels.json"
    path.write_bytes(b"[]")
    digest = hashlib.sha256(b"[]").hexdigest()
    assert read_pinned(path, 2, digest) == b"[]"
    with pytest.raises(LabelError):
        read_pinned(path, 1, digest)
    with pytest.raises(LabelError):
        read_pinned(path, 2, "0" * 64)


def test_local_inspection_checks_every_pin(tmp_path, monkeypatch):
    import scripts.inspect_labels as module

    pins = {}
    for name in sorted(module.SOURCE_NAMES):
        row = record()
        if name.startswith("arcwise_"):
            row["question_id"] = "1"
        raw = json.dumps([row]).encode()
        filename = name + ".json"
        (tmp_path / filename).write_bytes(raw)
        pins[name] = (filename, len(raw), hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(module, "PINS", pins)
    assert module.inspect_local(tmp_path)["original_count"] == 1
    (tmp_path / pins["bird_pg"][0]).write_bytes(b"corrupt")
    with pytest.raises(LabelError):
        module.inspect_local(tmp_path)
~~~

- [x] **Step 2: Observe RED.**

Run uv run pytest tests/test_labels.py --tb=line.
Expected import/collection failure because scripts.inspect_labels does not exist.
If unrelated import/environment failure occurs, diagnose it rather than treating
it as proof of these assertions.

- [x] **Step 3: Add the minimal complete offline implementation.**

Create scripts/inspect_labels.py:

~~~python
"""Offline correction inspection. Never imported by the SQL runtime."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

REVISION = "fe766045c55b6875a43b30e9ac7683df5582f8cf"
CORRECTION_DIR = "corrections/arcwise-fe766045"
DATABASES = {
    "california_schools", "card_games", "codebase_community",
    "debit_card_specializing", "european_football_2", "financial",
    "formula_1", "student_club", "superhero", "thrombosis_prediction", "toxicology",
}
SOURCE_NAMES = {"bird_sqlite", "bird_pg", "arcwise_sql", "arcwise_full"}
PINS = {
    "bird_sqlite": ("raw/mini_dev_sqlite.json", 278513,
                    "88ceb0710163cae46a256ecea8f0a8c98286599530b60587fda5c3cfe57d45d2"),
    "bird_pg": ("raw/mini_dev_pg.json", 283551,
                "7fa740ef9225389cff6c34432120e8325d0ca3008d73db1ae38731234bc10da7"),
    "arcwise_sql": (CORRECTION_DIR + "/arcwise_plat_sql_only_with_diff.json", 287718,
                    "e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395"),
    "arcwise_full": (CORRECTION_DIR + "/arcwise_plat_full_with_diff.json", 332246,
                     "baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8"),
}
REQUIRED = {"question_id", "db_id", "question", "evidence", "SQL"}
OPTIONAL = {"difficulty", "original_SQL", "original_question", "original_evidence"}


class LabelError(ValueError):
    """Stable offline failure without record text or SQL."""


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LabelError("duplicate JSON field")
        result[key] = value
    return result


def _constant(value):
    raise LabelError("non-standard JSON constant")


def read_pinned(path: Path, size: int, digest: str) -> bytes:
    try:
        if path.is_symlink():
            raise LabelError("source is a symlink")
        with path.open("rb") as stream:
            raw = stream.read(size + 1)
    except OSError:
        raise LabelError("source unavailable") from None
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise LabelError("source pin mismatch")
    return raw


def decode_labels(raw: bytes, *, corrected: bool) -> dict[int, dict]:
    if not raw or len(raw) > 600000:
        raise LabelError("document size rejected")
    try:
        rows = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise LabelError("invalid JSON") from None
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise LabelError("record count rejected")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not REQUIRED <= row.keys():
            raise LabelError("required fields missing")
        if row.keys() - (REQUIRED | OPTIONAL):
            raise LabelError("unreviewed field")
        value = row["question_id"]
        if corrected:
            if not isinstance(value, str) or not re.fullmatch("[1-9][0-9]{0,5}", value):
                raise LabelError("invalid corrected ID")
            identifier = int(value)
        else:
            if type(value) is not int or not 1 <= value <= 999999:
                raise LabelError("invalid original ID")
            identifier = value
        if identifier in result:
            raise LabelError("duplicate ID")
        for field in (REQUIRED | OPTIONAL) - {"question_id", "difficulty"}:
            if (
                field in row
                and not isinstance(row[field], str)
                and not (corrected and field == "evidence" and row[field] is None)
            ):
                raise LabelError("invalid text field")
        if not row["question"].strip() or not row["SQL"].strip() or row["db_id"] not in DATABASES:
            raise LabelError("invalid required value")
        if "difficulty" in row and (
            not isinstance(row["difficulty"], str)
            or row["difficulty"] not in {"simple", "moderate", "challenging"}
        ):
            raise LabelError("invalid difficulty")
        if not corrected and "difficulty" not in row:
            raise LabelError("original difficulty missing")
        result[identifier] = dict(row, question_id=identifier)
    return result


def build_report(sources: dict[str, dict[int, dict]]) -> dict:
    if sources.keys() != SOURCE_NAMES:
        raise LabelError("source set mismatch")
    original = sources["bird_sqlite"]
    by_source = {}
    for name in sorted(sources):
        current = sources[name]
        common = sorted(original.keys() & current.keys())
        database_mismatch = [i for i in common if original[i]["db_id"] != current[i]["db_id"]]
        track = {
            "count": len(current),
            "identity_aligned_count": len(common) - len(database_mismatch),
            "missing_ids": sorted(original.keys() - current.keys()),
            "unexpected_ids": sorted(current.keys() - original.keys()),
            "database_mismatch_ids": database_mismatch,
            "difficulty_mismatch_ids": [
                i for i in common
                if "difficulty" in current[i] and current[i]["difficulty"] != original[i]["difficulty"]
            ],
        }
        for field, label in (("question", "question"), ("evidence", "evidence"), ("SQL", "sql")):
            track[label + "_difference_ids"] = [
                i for i in common if original[i][field] != current[i][field]
            ]
        track["question_anchor_mismatch_ids"] = [
            i for i in common
            if current[i].get("original_question", current[i]["question"]) != original[i]["question"]
        ]
        track["evidence_anchor_mismatch_ids"] = [
            i for i in common
            if current[i].get("original_evidence", current[i]["evidence"]) != original[i]["evidence"]
        ]
        by_source[name] = track
    sql_only, full = sources["arcwise_sql"], sources["arcwise_full"]
    pair = sorted(sql_only.keys() & full.keys())
    return {
        "format_version": 1,
        "original_count": len(original),
        "per_database": dict(sorted(Counter(r["db_id"] for r in original.values()).items())),
        "per_difficulty": dict(sorted(Counter(r["difficulty"] for r in original.values()).items())),
        "by_source": by_source,
        "corrected_pair_missing_from_sql_ids": sorted(full.keys() - sql_only.keys()),
        "corrected_pair_missing_from_full_ids": sorted(sql_only.keys() - full.keys()),
        "corrected_pair_database_mismatch_ids": [
            i for i in pair if sql_only[i]["db_id"] != full[i]["db_id"]
        ],
        "corrected_pair_text_difference_ids": [
            i for i in pair
            if sql_only[i]["question"] != full[i]["question"]
            or sql_only[i]["evidence"] != full[i]["evidence"]
        ],
        "execution_validity": "not_run",
        "primary_labels": "not_selected",
        "ambiguity_labels": "not_classified",
        "splits": "not_frozen",
    }


def inspect_local(data_root: Path) -> dict:
    sources = {
        name: decode_labels(read_pinned(data_root / filename, size, digest),
                            corrected=name.startswith("arcwise_"))
        for name, (filename, size, digest) in PINS.items()
    }
    return build_report(sources)


def main() -> int:
    try:
        report = inspect_local(Path("data"))
    except LabelError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
~~~

- [x] **Step 4: Observe GREEN and run checks.**

Run uv run pytest tests/test_labels.py --tb=line.
Then uv run ruff check . and uv run ruff format . followed by format --check.
Apply formatting only to new files if other user changes appear.
No data acquisition for Task 1; absent correction files are expected until Task 2.
The Step 1 local-file test checks every pin and rejects corruption before a
report is returned; it belongs to the same RED gate as the pure tests.

- [x] **Step 5: Update notebook/progress/decisions, inspect and commit.**

Record actual tests and task-only completion; no G0.5 checkbox completion.
Inspect git diff --check and entire staged diff (only these new files and four
living records), confirm exact message:
feat(data): add strict offline correction alignment
Commit with repository-local identity or git -c user.name=Kunal
-c user.email=kunalchandrakar2005@gmail.com; inspect author/committer/body immediately.

## Task 2: Exclusive pinned correction acquisition and actual offline acceptance

**Files:** Create scripts/fetch_labels.py and tests/test_label_fetch.py;
update DATA/DECISIONS/PROGRESS/notebook and add compact
docs/label-alignment-manifest.json after actual acceptance.

**Interfaces:** Consumes REVISION/CORRECTION_DIR from Task 1.
Produces fetch_sources(destination: Path, *, transport: httpx.BaseTransport | None = None)
-> None. Production has no configurable URLs, redirects, proxy inheritance or
credentials. Optional transport exists only for fake-network tests.
New ignored raw release directory is all-or-nothing; re-running refuses it.

- [x] **Step 1: Write all fake-network tests before source.**

Create tests/test_label_fetch.py:

~~~python
import hashlib

import httpx
import pytest

import scripts.fetch_labels as module


def fake_resources(monkeypatch):
    resources = {
        "data/arcwise_plat_sql_only_with_diff.json": (b"sql", "sql.json"),
        "data/arcwise_plat_full_with_diff.json": (b"full", "full.json"),
        "README.md": (b"readme", "README.md"),
        "LICENSE": (b"license", "LICENSE"),
    }
    monkeypatch.setattr(module, "RESOURCES", {
        path: (filename, len(raw), hashlib.sha256(raw).hexdigest())
        for path, (raw, filename) in resources.items()
    })
    return resources


def transport_for(resources, *, bad=None, calls=None):
    def handle(request):
        if calls is not None:
            calls.append(str(request.url))
        path = request.url.path.split(module.REVISION + "/", 1)[1]
        raw, _ = resources[path]
        assert request.url.scheme == "https"
        assert request.url.host == "raw.githubusercontent.com"
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        if path == "LICENSE" and bad == "redirect":
            return httpx.Response(302, headers={"Location": "https://example.invalid/"})
        headers = {}
        if path == "LICENSE" and bad == "compressed":
            headers["Content-Encoding"] = "gzip"
        if path == "LICENSE" and bad == "oversize":
            raw += b"x"
        if path == "LICENSE" and bad == "hash":
            raw = b"x" * len(raw)
        if path == "LICENSE" and bad == "truncated":
            raw = raw[:-1]
        return httpx.Response(200, headers=headers, stream=httpx.ByteStream(raw))

    return httpx.MockTransport(handle)


def test_exact_release_is_published_once(tmp_path, monkeypatch):
    resources = fake_resources(monkeypatch)
    destination = tmp_path / "release"
    calls = []
    module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 4
    for raw, filename in resources.values():
        assert (destination / filename).read_bytes() == raw
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 4


@pytest.mark.parametrize("bad", ["redirect", "compressed", "oversize", "hash", "truncated"])
def test_failed_last_file_never_publishes_partial_release(tmp_path, monkeypatch, bad):
    resources = fake_resources(monkeypatch)
    destination = tmp_path / "release"
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, bad=bad))
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_timeout_leaves_no_published_release(tmp_path, monkeypatch):
    fake_resources(monkeypatch)

    def fail(request):
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    destination = tmp_path / "release"
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=httpx.MockTransport(fail))
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_command_deadline_is_checked_during_stream(tmp_path, monkeypatch):
    resources = fake_resources(monkeypatch)
    ticks = iter([0.0, 0.0, 121.0])
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks, 121.0))
    destination = tmp_path / "release"
    calls = []
    with pytest.raises(module.IntakeError):
        module.fetch_sources(destination, transport=transport_for(resources, calls=calls))
    assert len(calls) == 1
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []
~~~

- [x] **Step 2: Observe RED.**

Run uv run pytest tests/test_label_fetch.py --tb=line.
Expected import/collection failure from missing scripts.fetch_labels, not unrelated
environment issues.

- [x] **Step 3: Add the complete bounded acquisition script.**

Create scripts/fetch_labels.py:

~~~python
"""Acquire only the approved pinned correction labels and license context."""

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import httpx

from scripts.inspect_labels import CORRECTION_DIR, REVISION

BASE = "https://raw.githubusercontent.com/uiuc-kang-lab/text_to_sql_benchmarks/"
RESOURCES = {
    "data/arcwise_plat_sql_only_with_diff.json": (
        "arcwise_plat_sql_only_with_diff.json", 287718,
        "e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395",
    ),
    "data/arcwise_plat_full_with_diff.json": (
        "arcwise_plat_full_with_diff.json", 332246,
        "baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8",
    ),
    "README.md": (
        "README.md", 5038,
        "7aefaba8da2792a8edde1cb534dde1f89c3228e87ac5b923838ba68bb56cf0f5",
    ),
    "LICENSE": (
        "LICENSE", 20138,
        "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5",
    ),
}


class IntakeError(ValueError):
    """Stable fixed-source acquisition failure."""


def fetch_sources(destination: Path, *, transport: httpx.BaseTransport | None = None) -> None:
    if destination.exists() or destination.is_symlink():
        raise IntakeError("destination already exists")
    deadline = monotonic() + 120
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".label-intake-", dir=destination.parent) as temporary:
            staging = Path(temporary) / "release"
            staging.mkdir()
            with httpx.Client(
                trust_env=False, follow_redirects=False,
                transport=transport or httpx.HTTPTransport(retries=0, trust_env=False),
                headers={"Accept-Encoding": "identity"},
            ) as client:
                for source, (filename, size, digest) in RESOURCES.items():
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise IntakeError("acquisition deadline exceeded")
                    raw = bytearray()
                    url = BASE + REVISION + "/" + source
                    with client.stream("GET", url, timeout=min(20.0, remaining)) as response:
                        if response.status_code != 200:
                            raise IntakeError("source HTTP status rejected")
                        if response.headers.get("content-encoding", "identity").lower() != "identity":
                            raise IntakeError("source encoding rejected")
                        for chunk in response.iter_raw(chunk_size=4096):
                            if monotonic() >= deadline:
                                raise IntakeError("acquisition deadline exceeded")
                            if len(raw) + len(chunk) > size:
                                raise IntakeError("source byte limit exceeded")
                            raw.extend(chunk)
                    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
                        raise IntakeError("source pin mismatch")
                    with (staging / filename).open("xb") as output:
                        output.write(raw)
            if monotonic() >= deadline:
                raise IntakeError("acquisition deadline exceeded")
            if destination.exists() or destination.is_symlink():
                raise IntakeError("destination appeared during acquisition")
            staging.rename(destination)
    except (OSError, httpx.HTTPError):
        raise IntakeError("acquisition failed") from None


def main() -> int:
    try:
        fetch_sources(Path("data") / CORRECTION_DIR)
    except IntakeError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    print(json.dumps({"status": "acquired", "revision": REVISION, "files": len(RESOURCES)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
~~~

Run with uv run python -m scripts.fetch_labels so the sibling script import
resolves from repository root. Inspect likewise with
uv run python -m scripts.inspect_labels. Do not launch either with .env.setup,
.env.california or .env.runtime; they need no secrets.

- [x] **Step 4: Observe GREEN; run the four-file acquisition once after approval.**

Run uv run pytest tests/test_labels.py tests/test_label_fetch.py --tb=line.
Run lint/format and locked sync. Check free disk, fixed URLs/revision/pins,
645,140 total bytes and ignored destination before any acquisition.
Then uv run python -m scripts.fetch_labels, followed by the offline inspector.
Do not silently repin changing bytes, retry via another source, or overwrite a
partly pre-existing release. A pre-existing complete release may instead be
verified with read_pinned for all four files; record reuse, not a new fetch.

For acceptance, inspect the report in memory and assert original/canonical PG
counts 500, both corrections 498, missing [119,120], unexpected [] and database
mismatch [], exact drift counts 81/86 and 147/152, corrected-pair either count148.
A discrepancy is evidence to diagnose/report, not permission to rewrite labels.
Store only the complete generated report in an exclusive ignored output if needed;
do not print questions, evidence, SQL or credentials. A local aggregate acceptance
command (after scripts exist) is:

~~~python
from pathlib import Path
from scripts.inspect_labels import inspect_local

report = inspect_local(Path("data"))
assert report["original_count"] == 500
assert report["by_source"]["bird_pg"]["count"] == 500
for name, question_count, evidence_count in (
    ("arcwise_sql", 81, 86), ("arcwise_full", 147, 152),
):
    track = report["by_source"][name]
    assert track["count"] == 498
    assert track["missing_ids"] == [119, 120]
    assert track["unexpected_ids"] == track["database_mismatch_ids"] == []
    assert len(track["question_difference_ids"]) == question_count
    assert len(track["evidence_difference_ids"]) == evidence_count
assert len(report["corrected_pair_text_difference_ids"]) == 148
assert report["execution_validity"] == "not_run"
print("Pinned offline alignment checks passed; SQL validity and C1 remain undecided.")
~~~

Keep compact manifest provenance, original/per-db/per-difficulty counts,
per-source missing/unexpected/database/difficulty/text-change IDs, pair changes,
question/evidence anchor observations and all four undecided states. Add raw source
URLs/hashes, observed bytes, procedure and check date; never claim conversion
survival from this ID report. Full original/corrected/messy family splits remain
unfrozen; no scoring or runtime prompt construction occurs.

- [x] **Step 5: Run regressions, update all records and commit.**

Run uv sync --locked, uv run pytest --tb=line,
uv run --env-file .env.setup --env-file .env.california pytest --tb=line,
uv run ruff check ., uv run ruff format --check ., git diff --check.
Private tests use --tb=line, never --showlocals; no live inference.
Record actual counts/timings/skips, script pins/results and remaining questions.
Inspect ignored raw files and the exact staged diff; commit exact message:
feat(data): acquire and record pinned correction alignment
Verify both identities/body. Keep everything local, no remote or push.

- [ ] **Step 6: Complete the sole whole-increment review and Handoff.**

After both tasks, use the already selected native workflow's one fresh read-only
final review of this plan's two commits, with all five focus conditions and the
ledger. It may repeat fake-network/offline checks, not inference/download/import.
No parallel implementation. Resolve actionable findings in one tests-first pass,
retain every declined-to-judge ruling/cost, and update notebook/progress.
This review requirement is for approved execution, not preparation now.

Next reviewed increment: inspect all original SQLite/native-dump table layouts and
the 75 corrected description files; plan safe remaining dataset extraction/import
and content/type/key checks. Then conversion/result validity and C1 decisions,
then the second model and E0/C2. Do not mark G0.5 or G0.5b complete here.

## Self-review of this plan (preparation, not implementation evidence)

- Uses the existing approved BUILD_SPEC design; no replacement architecture or
  runtime configuration. Scope is one offline data intake subsystem.
- Section 8 provenance/stable-ID/mismatch/license requirements have tests and
  fixed inputs. Raw source bytes are preserved; no automatic benchmark rewrite.
- Every Review Focus has owning assertion code; network tests are fake, acceptance
  uses real pinned bytes, not synthetic evidence as corpus validation.
- Sources are compared by ID and observed database/question fields, not by order.
  Identity-only counts explicitly do not prove verified question or SQL semantics.
- Function names/constants and Task 2 imports agree; use module launch commands.
- Logical HTTP deadlines are cooperative, not OS process/memory isolation. Fixed
  per-file bounds limit retained bytes; a privileged local file race is outside
  this trusted workspace workflow. No claim of hostile filesystem protection.
- No placeholders or undefined neighboring APIs. Embedded implementation/test
  examples must be checked at execution; this preparation did not run new tests.
- Deferred spec work is explicit: descriptions, remaining database loading, key/
  content equivalence, SQLite/Postgres gold comparison, validity/exclusion policy,
  primary labels, ambiguity classification, family splits and C1 remain unfinished.

## Approval handoff

Please review this exact two-task plan and its four-file acquisition scope.
Does it capture what you want? Native sequential execution remains selected.
Implementation begins only after artifact approval; do not repeat completed CLI
work or ask for a different execution method.
