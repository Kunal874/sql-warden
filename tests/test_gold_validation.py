import json
import sqlite3
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import asyncpg
import pytest

from scripts import freeze_c1, validate_gold


def test_load_tracks_refuses_unpinned_input(tmp_path):
    source = tmp_path / "raw" / "mini_dev_sqlite.json"
    source.parent.mkdir()
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(validate_gold.ValidationError, match="source pin mismatch"):
        validate_gold.load_tracks(tmp_path)


def test_align_tracks_uses_id_and_database_not_list_position():
    original = {
        2: {"question_id": 2, "db_id": "financial"},
        1: {"question_id": 1, "db_id": "california_schools"},
    }
    candidate = {
        1: {"question_id": 1, "db_id": "california_schools"},
        2: {"question_id": 2, "db_id": "wrong"},
        3: {"question_id": 3, "db_id": "financial"},
    }

    aligned, rejected = validate_gold.align_track(original, candidate)

    assert aligned == [(1, original[1], candidate[1])]
    assert rejected == {
        2: "database_mismatch",
        3: "unexpected_id",
    }


def test_sqlite_connection_is_immutable_and_query_only(tmp_path):
    database = tmp_path / "sample.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE item(value INTEGER)")
        connection.execute("INSERT INTO item VALUES (1)")

    with validate_gold.open_sqlite(database) as connection:
        assert connection.execute("PRAGMA query_only").fetchone() == (1,)
        assert connection.execute("SELECT value FROM item").fetchone() == (1,)
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO item VALUES (2)")


@pytest.mark.parametrize(
    ("sql", "fragment"),
    [
        ("SELECT strftime('%Y', d) FROM t", "TO_CHAR"),
        ("SELECT x FROM t LIMIT 2", "LIMIT 2"),
    ],
)
def test_corrected_sql_is_transpiled_from_sqlite_to_postgres(sql, fragment):
    converted = validate_gold.transpile_corrected(sql)
    assert fragment in converted.upper()


def test_corrected_identifiers_use_reviewed_native_names_without_changing_aliases():
    tables = {
        "patient": {
            "source_name": "Patient",
            "columns": [
                {"source_name": "ID", "name": "id"},
                {"source_name": "Given Name", "name": "Given Name"},
            ],
        }
    }

    converted = validate_gold.transpile_corrected(
        'SELECT p."ID", p."Given Name" FROM "Patient" AS p', tables=tables
    )

    assert converted == 'SELECT p.id, p."Given Name" FROM patient AS p'
    assert (
        validate_gold.transpile_corrected('SELECT "Patient"."ID" FROM "Patient"', tables=tables)
        == "SELECT patient.id FROM patient"
    )


def test_reviewed_reserved_table_name_remains_quoted():
    tables = {
        "order": {
            "source_name": "Order",
            "columns": [{"source_name": "id", "name": "id", "native_type": "BIGINT"}],
        }
    }

    converted = validate_gold.transpile_corrected("SELECT id FROM `Order`", tables=tables)

    assert converted == 'SELECT id FROM "order"'


def test_sqlite_numeric_date_and_aggregate_semantics_are_made_explicit():
    tables = {
        "sample": {
            "source_name": "Sample",
            "columns": [
                {"source_name": "d", "name": "d", "native_type": "DATE"},
                {"source_name": "txt", "name": "txt", "native_type": "TEXT"},
                {"source_name": "n", "name": "n", "native_type": "BIGINT"},
                {"source_name": "r", "name": "r", "native_type": "REAL"},
            ],
        }
    }
    sql = (
        "SELECT d, DATE(d, '+1 year'), JULIANDAY(d), SUM(n > 1), ROUND(r, 2), "
        "AVG(txt), GROUP_CONCAT(n, ','), GROUP_CONCAT(DISTINCT n), "
        "d LIKE '2026%', txt = 3, txt - txt, "
        "STRFTIME('%Y', d) - STRFTIME('%Y', d) FROM Sample"
    )

    converted = validate_gold.transpile_corrected(sql, tables=tables)

    assert converted.startswith("SELECT CAST(d AS TEXT), CAST(CAST(d + INTERVAL '+1 YEAR'")
    assert "EXTRACT(EPOCH FROM CAST(d AS TIMESTAMP))" in converted
    assert "/ 86400 + 2440587.5" in converted
    assert "SUM(CAST(n > 1 AS INT))" in converted
    assert "ROUND(CAST(r AS DECIMAL), 2)" in converted
    assert "AVG(CAST(txt AS DECIMAL))" in converted
    assert "STRING_AGG(CAST(n AS TEXT), ',')" in converted
    assert "STRING_AGG(DISTINCT CAST(n AS TEXT), ',')" in converted
    assert "CAST(d AS TEXT) LIKE '2026%'" in converted
    assert "txt = CAST(3 AS TEXT)" in converted
    assert "CAST(txt AS DECIMAL) - CAST(txt AS DECIMAL)" in converted
    assert "CAST(TO_CHAR" in converted


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM t",
        "CREATE TABLE x(a INT)",
        "SELECT 1; SELECT 2",
        "PRAGMA table_info(t)",
    ],
)
def test_non_query_or_multiple_statements_are_refused(sql):
    with pytest.raises(validate_gold.ValidationError, match="statement refused"):
        validate_gold.transpile_corrected(sql)


def test_typed_canonicalization_is_lossless_and_preserves_duplicate_rows():
    rows = [
        (
            None,
            True,
            7,
            Decimal("1.2300"),
            2.5,
            "Text",
            b"\x00\xff",
            date(2026, 10, 8),
            time(12, 30, 1),
            datetime(2026, 10, 8, 12, 30, tzinfo=UTC),
        ),
        ("duplicate",),
        ("duplicate",),
    ]
    reversed_rows = list(reversed(rows))

    canonical = validate_gold.canonical_rows(rows)

    assert canonical == validate_gold.canonical_rows(reversed_rows)
    assert canonical.count(validate_gold.canonical_row(("duplicate",))) == 2
    assert validate_gold.canonical_cell(1) != validate_gold.canonical_cell(True)
    assert validate_gold.canonical_cell(Decimal("1.2300")) == ("number", "1.23")
    assert validate_gold.canonical_cell(Decimal("1.00000000000000000000000000001")) != (
        validate_gold.canonical_cell(Decimal("1.00000000000000000000000000002"))
    )
    assert validate_gold.canonical_cell(-0.0) == ("number", "0")


def test_track_deadline_is_enforced_before_each_pair(monkeypatch):
    ticks = iter([0.0, 1.0, 1801.0])
    monkeypatch.setattr(validate_gold, "monotonic", lambda: next(ticks, 1801.0))
    deadline = validate_gold.TrackDeadline(seconds=1800)

    deadline.check()
    with pytest.raises(validate_gold.LimitExceeded, match="track_timeout"):
        deadline.check()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object()])
def test_unsupported_or_nonfinite_cells_are_refused(value):
    with pytest.raises(validate_gold.ValidationError, match="cell type refused"):
        validate_gold.canonical_cell(value)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (asyncpg.PostgresSyntaxError("detail"), "postgres_syntax_error"),
        (asyncpg.UndefinedFunctionError("detail"), "undefined_object"),
        (asyncpg.DivisionByZeroError("detail"), "arithmetic_error"),
        (asyncpg.DataError("detail"), "data_error"),
        (asyncpg.InsufficientPrivilegeError("detail"), "permission_error"),
        (asyncpg.PostgresError("detail"), "postgres_error"),
    ],
)
def test_postgres_failure_classification_is_bounded_and_drops_detail(error, reason):
    assert validate_gold.classify_postgres_error(error) == reason
    assert "detail" not in validate_gold.classify_postgres_error(error)


def test_collect_rows_enforces_row_cell_and_result_byte_limits():
    with pytest.raises(validate_gold.LimitExceeded, match="row_limit"):
        validate_gold.collect_rows([(1,), (2,)], max_rows=1)
    with pytest.raises(validate_gold.LimitExceeded, match="cell_bytes"):
        validate_gold.collect_rows([("abcd",)], max_cell_bytes=3)
    with pytest.raises(validate_gold.LimitExceeded, match="result_bytes"):
        validate_gold.collect_rows([("abc",), ("def",)], max_result_bytes=5)


def test_sqlite_deadline_interrupts_long_query(tmp_path, monkeypatch):
    database = tmp_path / "sample.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE item(value INTEGER)")
        connection.executemany("INSERT INTO item VALUES (?)", [(i,) for i in range(50)])
    ticks = iter([0.0, 11.0])
    monkeypatch.setattr(validate_gold, "monotonic", lambda: next(ticks, 11.0))

    with (
        validate_gold.open_sqlite(database, timeout_seconds=10) as connection,
        pytest.raises(validate_gold.LimitExceeded, match="query_timeout"),
    ):
        validate_gold.execute_sqlite(
            connection,
            "SELECT a.value FROM item a, item b, item c",
            progress_steps=1,
        )


def test_public_outcome_contains_only_bounded_classification():
    outcome = validate_gold.public_outcome(
        identifier=7,
        db_id="financial",
        status="failed",
        reason="query_error",
    )
    assert outcome == {
        "question_id": 7,
        "db_id": "financial",
        "status": "failed",
        "reason": "query_error",
    }
    with pytest.raises(validate_gold.ValidationError, match="classification refused"):
        validate_gold.public_outcome(7, "financial", "failed", "SELECT secret")


def test_postgres_options_map_california_and_release_dataset_credentials():
    california = "a" * 48
    financial = "b" * 48
    values = {
        "WARDEN_CALIFORNIA_PASSWORD": california,
        "WARDEN_DATASET_FINANCIAL_PASSWORD": financial,
    }

    california_options = validate_gold.postgres_options("california_schools", values)
    financial_options = validate_gold.postgres_options("financial", values)

    assert california_options["user"] == "warden_sandbox_california_schools"
    assert california_options["password"] == california
    assert financial_options["user"] == "warden_sandbox_financial"
    assert financial_options["password"] == financial


@pytest.mark.asyncio
async def test_postgres_execution_keeps_admin_only_temp_limit_from_restricted_role():
    class Transaction:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

    class Records:
        def __init__(self):
            self._items = iter([(1,)])

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self._items)
            except StopIteration:
                raise StopAsyncIteration from None

    class Connection:
        def transaction(self, *, readonly):
            assert readonly is True
            return Transaction()

        async def execute(self, sql):
            assert "temp_file_limit" not in sql

        def cursor(self, sql, *, prefetch):
            assert sql == "SELECT 1"
            assert prefetch == 100
            return Records()

    assert await validate_gold.execute_postgres(Connection(), "SELECT 1") == [(1,)]


def test_summarize_counts_statuses_and_reasons_without_payloads():
    outcomes = [
        validate_gold.public_outcome(1, "financial", "matched", None),
        validate_gold.public_outcome(2, "financial", "failed", "query_error"),
        validate_gold.public_outcome(3, "formula_1", "excluded", "row_limit"),
    ]

    summary = validate_gold.summarize(outcomes)

    assert summary == {
        "total": 3,
        "status_counts": {"excluded": 1, "failed": 1, "matched": 1},
        "reason_counts": {"query_error": 1, "row_limit": 1},
        "per_database": {"financial": 2, "formula_1": 1},
    }
    assert "SELECT" not in json.dumps(summary)


def test_publish_manifest_is_atomic_and_refuses_overwrite_or_symlink(tmp_path):
    target = tmp_path / "manifest.json"
    manifest = {"format_version": 1, "status": "complete"}

    validate_gold.publish_manifest(target, manifest)

    assert json.loads(target.read_text(encoding="utf-8")) == manifest
    assert not list(tmp_path.glob("*.tmp"))
    with pytest.raises(validate_gold.ValidationError, match="target exists"):
        validate_gold.publish_manifest(target, manifest)

    real = tmp_path / "real.json"
    link = tmp_path / "link.json"
    real.write_text("{}", encoding="utf-8")
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(validate_gold.ValidationError, match="target is a symlink"):
        validate_gold.publish_manifest(link, manifest)


def test_c1_manifest_freezes_corrected_pool_without_payload_text():
    validation_report = {
        "format_version": 1,
        "limits": {"query_seconds": 10, "rows": 100000, "result_bytes": 1, "cell_bytes": 1},
        "tracks": {
            "arcwise_full": {
                "track": "arcwise_full",
                "summary": {
                    "total": 3,
                    "status_counts": {"failed": 1, "matched": 2},
                    "reason_counts": {"missing_id": 1},
                    "per_database": {"financial": 2, "toxicology": 1},
                },
                "outcomes": [
                    {"question_id": 1, "db_id": "financial", "status": "matched"},
                    {
                        "question_id": 2,
                        "db_id": "financial",
                        "status": "failed",
                        "reason": "missing_id",
                    },
                    {"question_id": 3, "db_id": "toxicology", "status": "matched"},
                ],
            }
        },
    }
    label_report = {
        "correction_revision": "revision",
        "original_revision": "original",
        "alignment": {
            "original_count": 3,
            "per_database": {"financial": 2, "toxicology": 1},
            "by_source": {
                "arcwise_full": {
                    "identity_aligned_count": 2,
                    "missing_ids": [2],
                    "question_difference_ids": [1],
                    "evidence_difference_ids": [],
                }
            },
        },
    }
    original = {
        1: {
            "db_id": "financial",
            "difficulty": "simple",
            "question": "private-question",
            "SQL": "SELECT private_sql",
        },
        2: {
            "db_id": "financial",
            "difficulty": "moderate",
            "question": "missing",
            "SQL": "SELECT missing",
        },
        3: {
            "db_id": "toxicology",
            "difficulty": "challenging",
            "question": "clear",
            "SQL": "SELECT clear",
        },
    }

    manifest = validate_gold.build_c1_manifest(
        validation_report,
        label_report,
        original,
        evidence_sha256="a" * 64,
        evidence_path=".tools/gold-validation/recovery-final.json",
        decision_source="test decision",
    )

    assert manifest["primary_track"] == "arcwise_full"
    assert manifest["primary_labels"] == "arcwise_full_verified_corrected_pool"
    assert manifest["primary_descriptions"] == "corrected"
    assert manifest["validity"]["usable_count"] == 2
    assert manifest["validity"]["aligned_count"] == 2
    assert manifest["validity"]["survival_rate"] == "100.00%"
    assert manifest["usable_items"] == [
        {
            "question_id": 1,
            "db_id": "financial",
            "difficulty": "simple",
            "ambiguity_candidate": True,
        },
        {
            "question_id": 3,
            "db_id": "toxicology",
            "difficulty": "challenging",
            "ambiguity_candidate": False,
        },
    ]
    assert manifest["ambiguity_policy"] == {
        "candidate_ids": [1],
        "negative_control_ids": [3],
        "status": "literal_text_difference_only_not_semantic_review",
    }
    rendered = json.dumps(manifest)
    assert "private-question" not in rendered
    assert "private_sql" not in rendered


def test_c1_manifest_refuses_untrusted_or_inconsistent_inputs():
    base = {
        "tracks": {
            "arcwise_full": {
                "summary": {"total": 1, "status_counts": {"matched": 1}, "reason_counts": {}},
                "outcomes": [{"question_id": 1, "db_id": "financial", "status": "matched"}],
            }
        }
    }
    labels = {
        "alignment": {
            "original_count": 1,
            "per_database": {"financial": 1},
            "by_source": {
                "arcwise_full": {
                    "identity_aligned_count": 1,
                    "missing_ids": [],
                    "question_difference_ids": [],
                    "evidence_difference_ids": [],
                }
            },
        }
    }

    with pytest.raises(validate_gold.ValidationError, match="evidence hash refused"):
        validate_gold.build_c1_manifest(
            base,
            labels,
            {1: {"db_id": "financial", "difficulty": "simple"}},
            evidence_sha256="bad",
            evidence_path="x",
            decision_source="d",
        )
    with pytest.raises(validate_gold.ValidationError, match="manifest input mismatch"):
        validate_gold.build_c1_manifest(
            base, labels, {}, evidence_sha256="a" * 64, evidence_path="x", decision_source="d"
        )


def test_freeze_c1_records_relative_evidence_paths_from_absolute_or_relative_inputs(tmp_path):
    root = tmp_path.resolve()
    evidence = root / ".tools" / "gold-validation" / "report.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}", encoding="utf-8")

    assert freeze_c1.project_relative(evidence, root=root) == ".tools/gold-validation/report.json"
    assert freeze_c1.project_relative(Path(".tools/gold-validation/report.json"), root=root) == (
        ".tools/gold-validation/report.json"
    )
