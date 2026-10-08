import json
import sqlite3
from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest

from scripts import validate_gold


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
    assert validate_gold.canonical_cell(-0.0) == ("number", "0")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object()])
def test_unsupported_or_nonfinite_cells_are_refused(value):
    with pytest.raises(validate_gold.ValidationError, match="cell type refused"):
        validate_gold.canonical_cell(value)


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
