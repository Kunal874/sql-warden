"""Offline, bounded cross-dialect gold validation; never used by the runtime."""

import argparse
import asyncio
import hashlib
import json
import math
import os
import re
import sqlite3
from collections import Counter
from contextlib import closing, contextmanager, suppress
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import monotonic

import asyncpg
from sqlglot import exp, parse
from sqlglot.errors import SqlglotError as SQLGlotError

from scripts.inspect_labels import DATABASES, PINS, LabelError, decode_labels, read_pinned
from scripts.prepare_import_bundle import load_specs

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PINS = ROOT / "docs/source-release-pins.json"
SQLITE_ROOT = ROOT / "data/source-release/minidev-0703"
MAX_ROWS = 100_000
MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_CELL_BYTES = 1024 * 1024
QUERY_TIMEOUT_SECONDS = 10
TRACK_TIMEOUT_SECONDS = 30 * 60
_SQLITE_DEADLINES: dict[int, float] = {}

STATUSES = frozenset({"matched", "mismatched", "failed", "excluded"})
REASONS = frozenset(
    {
        "database_mismatch",
        "unexpected_id",
        "missing_id",
        "statement_refused",
        "transpile_error",
        "sqlite_error",
        "postgres_error",
        "postgres_syntax_error",
        "undefined_object",
        "arithmetic_error",
        "data_error",
        "permission_error",
        "query_error",
        "query_timeout",
        "track_timeout",
        "row_limit",
        "result_bytes",
        "cell_bytes",
        "result_mismatch",
        "cell_type_refused",
    }
)


class ValidationError(ValueError):
    """Stable validation refusal that never embeds SQL, results, or credentials."""


class LimitExceeded(ValidationError):
    """A stable resource-limit classification."""


class TrackDeadline:
    def __init__(self, *, seconds: float = TRACK_TIMEOUT_SECONDS):
        self.deadline = monotonic() + seconds

    def remaining(self) -> float:
        return self.deadline - monotonic()

    def check(self) -> None:
        if self.remaining() <= 0:
            raise LimitExceeded("track_timeout")


def load_tracks(data_root: Path) -> dict[str, dict[int, dict]]:
    try:
        return {
            name: decode_labels(
                read_pinned(data_root / filename, size, digest),
                corrected=name.startswith("arcwise_"),
            )
            for name, (filename, size, digest) in PINS.items()
        }
    except LabelError as error:
        raise ValidationError(str(error)) from None


def align_track(original: dict[int, dict], candidate: dict[int, dict]):
    aligned = []
    rejected = {}
    for identifier in sorted(candidate):
        if identifier not in original:
            rejected[identifier] = "unexpected_id"
        elif candidate[identifier]["db_id"] != original[identifier]["db_id"]:
            rejected[identifier] = "database_mismatch"
        else:
            aligned.append((identifier, original[identifier], candidate[identifier]))
    return aligned, rejected


@contextmanager
def open_sqlite(path: Path, *, timeout_seconds: float = QUERY_TIMEOUT_SECONDS):
    try:
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_file():
            raise ValidationError("SQLite source refused")
    except OSError:
        raise ValidationError("SQLite source unavailable") from None
    deadline = monotonic() + timeout_seconds
    uri = resolved.as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA cache_size=-8192")
        _SQLITE_DEADLINES[id(connection)] = deadline
        connection.set_progress_handler(lambda: int(monotonic() >= deadline), 10_000)
        try:
            yield connection
        finally:
            _SQLITE_DEADLINES.pop(id(connection), None)


def _query(sql: str, *, dialect: str):
    try:
        statements = parse(sql, read=dialect)
    except SQLGlotError:
        raise ValidationError("statement refused") from None
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        raise ValidationError("statement refused")
    return statements[0]


def _native_identifier(name: str, *, table: bool = False) -> exp.Identifier:
    reserved_table = table and name in {"order"}
    quoted = reserved_table or re.fullmatch(r"[a-z_][a-z0-9_]*", name) is None
    return exp.to_identifier(name, quoted=quoted)


def _adapt_identifiers(statement: exp.Expression, tables: dict) -> exp.Expression:
    table_names = {}
    column_candidates: dict[str, set[str]] = {}
    for native_name, table in tables.items():
        for name in {native_name, table["source_name"]}:
            table_names[name.casefold()] = native_name
        for column in table["columns"]:
            for name in {column["name"], column["source_name"]}:
                column_candidates.setdefault(name.casefold(), set()).add(column["name"])
    column_names = {
        name: next(iter(candidates))
        for name, candidates in column_candidates.items()
        if len(candidates) == 1
    }

    def adapt(node):
        if isinstance(node, exp.Table):
            native = table_names.get(node.name.casefold())
            if native:
                node.set("this", _native_identifier(native, table=True))
        elif isinstance(node, exp.Column):
            native = column_names.get(node.name.casefold())
            if native:
                node.set("this", _native_identifier(native))
            if node.table:
                native_table = table_names.get(node.table.casefold())
                if native_table:
                    node.set("table", _native_identifier(native_table, table=True))
        return node

    return statement.transform(adapt, copy=False)


def _adapt_sqlite_semantics(statement: exp.Expression, tables: dict) -> exp.Expression:
    table_columns = {
        table_name: {
            column["name"].casefold(): column.get("native_type") for column in table["columns"]
        }
        for table_name, table in tables.items()
    }
    aliases = {
        table.alias_or_name.casefold(): table.name
        for table in statement.find_all(exp.Table)
        if table.alias_or_name
    }
    global_types: dict[str, set[str]] = {}
    for columns in table_columns.values():
        for name, native_type in columns.items():
            if native_type:
                global_types.setdefault(name, set()).add(native_type)

    def column_type(node):
        if not isinstance(node, exp.Column):
            return None
        if node.table:
            table_name = aliases.get(node.table.casefold(), node.table)
            return table_columns.get(table_name, {}).get(node.name.casefold())
        candidates = global_types.get(node.name.casefold(), set())
        return next(iter(candidates)) if len(candidates) == 1 else None

    def numeric(value):
        return exp.cast(value.copy(), "DECIMAL")

    boolean = (exp.Predicate, exp.And, exp.Or)
    comparisons = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)

    def adapt(node):
        if isinstance(node, exp.Date) and isinstance(node.args.get("zone"), exp.Literal):
            modifier = node.args["zone"].this.strip()
            match = re.fullmatch(r"([+-]?\d+)\s+(day|month|year)s?", modifier, re.I)
            if match:
                added = exp.DateAdd(
                    this=node.this.copy(),
                    expression=exp.Literal.number(match.group(1)),
                    unit=exp.Var(this=match.group(2).upper()),
                )
                return exp.cast(exp.cast(added, "DATE"), "TEXT")
            return exp.cast(exp.cast(node.this.copy(), "DATE"), "TEXT")
        if isinstance(node, exp.Anonymous) and node.name.upper() == "JULIANDAY":
            arguments = node.expressions
            if len(arguments) == 1:
                epoch = exp.Extract(
                    this=exp.Var(this="EPOCH"),
                    expression=exp.cast(arguments[0].copy(), "TIMESTAMP"),
                )
                return exp.Add(
                    this=exp.Div(this=epoch, expression=exp.Literal.number(86400)),
                    expression=exp.Literal.number("2440587.5"),
                )
        if isinstance(node, exp.Sum) and isinstance(node.this, boolean):
            node.set("this", exp.cast(node.this.copy(), "INT"))
        elif (isinstance(node, exp.Round) and node.args.get("decimals") is not None) or (
            isinstance(node, exp.Avg) and column_type(node.this) == "TEXT"
        ):
            node.set("this", numeric(node.this))
        elif isinstance(node, exp.GroupConcat):
            if isinstance(node.this, exp.Distinct):
                node.this.set(
                    "expressions",
                    [exp.cast(value.copy(), "TEXT") for value in node.this.expressions],
                )
            else:
                node.set("this", exp.cast(node.this.copy(), "TEXT"))
        elif isinstance(node, exp.Like):
            node.set("this", exp.cast(node.this.copy(), "TEXT"))
        elif isinstance(node, exp.Sub):
            if column_type(node.this) == "TEXT" or isinstance(node.this, exp.TimeToStr):
                node.set("this", numeric(node.this))
            if column_type(node.expression) == "TEXT" or isinstance(node.expression, exp.TimeToStr):
                node.set("expression", numeric(node.expression))
        elif isinstance(node, comparisons):
            if (
                column_type(node.this) == "TEXT"
                and isinstance(node.expression, exp.Literal)
                and not node.expression.is_string
            ):
                node.set("expression", exp.cast(node.expression.copy(), "TEXT"))
            if (
                column_type(node.expression) == "TEXT"
                and isinstance(node.this, exp.Literal)
                and not node.this.is_string
            ):
                node.set("this", exp.cast(node.this.copy(), "TEXT"))
        return node

    statement = statement.transform(adapt, copy=False)
    for select in statement.find_all(exp.Select):
        projections = []
        for projection in select.expressions:
            value = projection.this if isinstance(projection, exp.Alias) else projection
            if isinstance(value, exp.Column) and column_type(value) == "DATE":
                value = exp.cast(value.copy(), "TEXT")
                if isinstance(projection, exp.Alias):
                    projection = exp.Alias(this=value, alias=projection.args["alias"].copy())
                else:
                    projection = value
            projections.append(projection)
        select.set("expressions", projections)
    return statement


def transpile_corrected(sql: str, *, tables: dict | None = None) -> str:
    statement = _query(sql, dialect="sqlite")
    if tables is not None:
        statement = _adapt_identifiers(statement, tables)
        statement = _adapt_sqlite_semantics(statement, tables)
    try:
        return statement.sql(dialect="postgres")
    except SQLGlotError:
        raise ValidationError("transpile error") from None


def validate_postgres_query(sql: str) -> str:
    return _query(sql, dialect="postgres").sql(dialect="postgres")


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValidationError("cell type refused")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text.startswith("-0."):
        return "-" + text[2:]
    if text.startswith("0."):
        return text
    return text.lstrip("0") or "0"


def canonical_cell(value):
    if value is None:
        return ("null", "")
    if isinstance(value, bool):
        return ("bool", "true" if value else "false")
    if type(value) is int:
        return ("number", str(value))
    if isinstance(value, Decimal):
        return ("number", _decimal_text(value))
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError("cell type refused")
        try:
            return ("number", _decimal_text(Decimal(str(value))))
        except InvalidOperation:
            raise ValidationError("cell type refused") from None
    if isinstance(value, str):
        return ("text", value)
    if isinstance(value, bytes):
        return ("bytes", value.hex())
    if isinstance(value, datetime):
        return ("datetime", value.isoformat())
    if isinstance(value, date):
        return ("date", value.isoformat())
    if isinstance(value, time):
        return ("time", value.isoformat())
    raise ValidationError("cell type refused")


def canonical_row(row):
    return tuple(canonical_cell(value) for value in row)


def canonical_rows(rows):
    return sorted(canonical_row(row) for row in rows)


def _cell_bytes(value) -> int:
    if value is None:
        return 0
    if isinstance(value, bytes):
        return len(value)
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    tag, text = canonical_cell(value)
    return len(tag) + len(text.encode("utf-8"))


def collect_rows(
    rows,
    *,
    max_rows: int = MAX_ROWS,
    max_result_bytes: int = MAX_RESULT_BYTES,
    max_cell_bytes: int = MAX_CELL_BYTES,
):
    collected = []
    total_bytes = 0
    for row in rows:
        if len(collected) >= max_rows:
            raise LimitExceeded("row_limit")
        current = tuple(row)
        for value in current:
            size = _cell_bytes(value)
            if size > max_cell_bytes:
                raise LimitExceeded("cell_bytes")
            total_bytes += size
            if total_bytes > max_result_bytes:
                raise LimitExceeded("result_bytes")
        collected.append(current)
    return collected


def execute_sqlite(connection, sql: str, *, progress_steps: int = 10_000):
    deadline_reached = False
    deadline = _SQLITE_DEADLINES.get(id(connection), monotonic() + QUERY_TIMEOUT_SECONDS)

    def bounded_progress():
        nonlocal deadline_reached
        deadline_reached = monotonic() >= deadline
        return int(deadline_reached)

    connection.set_progress_handler(bounded_progress, progress_steps)
    try:
        return collect_rows(connection.execute(sql))
    except sqlite3.OperationalError:
        if deadline_reached:
            raise LimitExceeded("query_timeout") from None
        raise ValidationError("sqlite_error") from None
    finally:
        connection.set_progress_handler(None, 0)


def public_outcome(identifier: int, db_id: str, status: str, reason: str | None):
    if (
        type(identifier) is not int
        or db_id not in DATABASES
        or status not in STATUSES
        or (reason is not None and reason not in REASONS)
        or (status == "matched" and reason is not None)
        or (status != "matched" and reason is None)
    ):
        raise ValidationError("classification refused")
    result = {"question_id": identifier, "db_id": db_id, "status": status}
    if reason is not None:
        result["reason"] = reason
    return result


def summarize(outcomes: list[dict]) -> dict:
    return {
        "total": len(outcomes),
        "status_counts": dict(sorted(Counter(item["status"] for item in outcomes).items())),
        "reason_counts": dict(
            sorted(Counter(item["reason"] for item in outcomes if "reason" in item).items())
        ),
        "per_database": dict(sorted(Counter(item["db_id"] for item in outcomes).items())),
    }


def publish_manifest(path: Path, manifest: dict) -> None:
    if path.is_symlink():
        raise ValidationError("target is a symlink")
    if path.exists():
        raise ValidationError("target exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ValidationError("temporary target exists")
    payload = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    except OSError:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise ValidationError("manifest publication failed") from None


def _ids_for(outcomes: list[dict], *, status: str | None = None, reason: str | None = None):
    return [
        item["question_id"]
        for item in outcomes
        if (status is None or item["status"] == status)
        and (reason is None or item.get("reason") == reason)
    ]


def build_c1_manifest(
    validation_report: dict,
    label_report: dict,
    original: dict[int, dict],
    *,
    evidence_sha256: str,
    evidence_path: str,
    decision_source: str,
) -> dict:
    if not re.fullmatch(r"[a-f0-9]{64}", evidence_sha256):
        raise ValidationError("evidence hash refused")
    try:
        track = validation_report["tracks"]["arcwise_full"]
        outcomes = track["outcomes"]
        label_alignment = label_report["alignment"]
        label_track = label_alignment["by_source"]["arcwise_full"]
        original_count = label_alignment["original_count"]
        aligned_count = label_track["identity_aligned_count"]
    except (KeyError, TypeError):
        raise ValidationError("manifest input mismatch") from None
    if not isinstance(outcomes, list) or original_count != len(original):
        raise ValidationError("manifest input mismatch")
    by_id = {}
    for item in outcomes:
        identifier = item.get("question_id")
        if identifier not in original or identifier in by_id:
            raise ValidationError("manifest input mismatch")
        public_outcome(identifier, item.get("db_id"), item.get("status"), item.get("reason"))
        by_id[identifier] = item
    usable = [item for item in outcomes if item["status"] == "matched"]
    if len(usable) != track["summary"]["status_counts"].get("matched", 0):
        raise ValidationError("manifest input mismatch")
    text_difference_ids = set(label_track["question_difference_ids"]) | set(
        label_track["evidence_difference_ids"]
    )
    usable_items = []
    for item in sorted(usable, key=lambda row: row["question_id"]):
        source = original[item["question_id"]]
        if source["db_id"] != item["db_id"]:
            raise ValidationError("manifest input mismatch")
        usable_items.append(
            {
                "question_id": item["question_id"],
                "db_id": item["db_id"],
                "difficulty": source["difficulty"],
                "ambiguity_candidate": item["question_id"] in text_difference_ids,
            }
        )
    candidate_ids = [item["question_id"] for item in usable_items if item["ambiguity_candidate"]]
    negative_ids = [item["question_id"] for item in usable_items if not item["ambiguity_candidate"]]
    survival = Decimal(len(usable)) / Decimal(aligned_count)
    return {
        "format_version": 1,
        "checked_on": "2026-10-08",
        "primary_track": "arcwise_full",
        "primary_labels": "arcwise_full_verified_corrected_pool",
        "primary_descriptions": "corrected",
        "alternate_descriptions": "original",
        "decision_source": decision_source,
        "evidence": {
            "ignored_path": evidence_path,
            "sha256": evidence_sha256,
            "contains": "question IDs, database IDs and bounded outcome classes only",
            "excludes": ["question text", "SQL", "result cells", "credentials"],
        },
        "limits": validation_report["limits"],
        "validity": {
            "original_count": original_count,
            "candidate_count": track["summary"]["total"],
            "aligned_count": aligned_count,
            "usable_count": len(usable),
            "automatic_threshold": "95.00%",
            "automatic_threshold_met": False,
            "survival_rate": f"{survival * 100:.2f}%",
            "status_counts": track["summary"]["status_counts"],
            "reason_counts": track["summary"]["reason_counts"],
            "per_database_original": label_alignment["per_database"],
            "per_database_usable": dict(
                sorted(Counter(item["db_id"] for item in usable_items).items())
            ),
            "per_difficulty_usable": dict(
                sorted(Counter(item["difficulty"] for item in usable_items).items())
            ),
            "missing_ids": label_track["missing_ids"],
            "unusable_ids_by_reason": {
                reason: _ids_for(outcomes, reason=reason)
                for reason in sorted(track["summary"]["reason_counts"])
            },
        },
        "ambiguity_policy": {
            "candidate_ids": candidate_ids,
            "negative_control_ids": negative_ids,
            "status": "literal_text_difference_only_not_semantic_review",
        },
        "usable_items": usable_items,
        "label_source_revisions": {
            "original": label_report.get("original_revision"),
            "correction": label_report.get("correction_revision"),
        },
        "splits": "not_frozen",
    }


def _source_pins() -> dict[str, dict]:
    try:
        raw = SOURCE_PINS.read_bytes()
        if len(raw) > 256 * 1024:
            raise ValidationError("source pins refused")
        document = json.loads(raw)
        sources = document["sqlite_sources"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        raise ValidationError("source pins refused") from None
    result = {}
    for item in sources:
        if set(item) < {"db_id", "output", "bytes", "sha256"} or item["db_id"] in result:
            raise ValidationError("source pins refused")
        result[item["db_id"]] = item
    if set(result) != DATABASES:
        raise ValidationError("source pins refused")
    return result


def checked_sqlite_path(db_id: str) -> Path:
    pin = _source_pins().get(db_id)
    if pin is None:
        raise ValidationError("SQLite source refused")
    path = SQLITE_ROOT / pin["output"]
    try:
        if path.is_symlink() or path.stat().st_size != pin["bytes"]:
            raise ValidationError("SQLite source pin mismatch")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise ValidationError("SQLite source unavailable") from None
    if digest != pin["sha256"]:
        raise ValidationError("SQLite source pin mismatch")
    return path


def postgres_options(db_id: str, values: dict[str, str]) -> dict:
    if db_id not in DATABASES:
        raise ValidationError("database refused")
    key = (
        "WARDEN_CALIFORNIA_PASSWORD"
        if db_id == "california_schools"
        else "WARDEN_DATASET_" + db_id.upper() + "_PASSWORD"
    )
    password = values.get(key, "")
    if not isinstance(password, str) or len(password) != 48:
        raise ValidationError("restricted credential unavailable")
    return {
        "host": "127.0.0.1",
        "port": 55432,
        "database": "sqlwarden",
        "user": "warden_sandbox_" + db_id,
        "password": password,
        "timeout": 5,
        "command_timeout": QUERY_TIMEOUT_SECONDS,
    }


def classify_postgres_error(error: asyncpg.PostgresError) -> str:
    if isinstance(error, asyncpg.PostgresSyntaxError):
        return "postgres_syntax_error"
    if isinstance(
        error,
        (
            asyncpg.UndefinedTableError,
            asyncpg.UndefinedColumnError,
            asyncpg.UndefinedFunctionError,
            asyncpg.InvalidSchemaNameError,
        ),
    ):
        return "undefined_object"
    if isinstance(error, asyncpg.DivisionByZeroError):
        return "arithmetic_error"
    if isinstance(error, (asyncpg.InsufficientPrivilegeError, asyncpg.ReadOnlySQLTransactionError)):
        return "permission_error"
    if isinstance(error, asyncpg.DataError):
        return "data_error"
    return "postgres_error"


async def execute_postgres(connection, sql: str):
    rows = []
    total_bytes = 0
    try:
        async with asyncio.timeout(QUERY_TIMEOUT_SECONDS), connection.transaction(readonly=True):
            await connection.execute(
                "SET LOCAL statement_timeout='10s'; SET LOCAL lock_timeout='500ms'; "
                "SET LOCAL idle_in_transaction_session_timeout='12s'; "
                "SET LOCAL work_mem='16MB'; SET LOCAL timezone='UTC'; "
                "SET LOCAL DateStyle='ISO,YMD'"
            )
            async for record in connection.cursor(sql, prefetch=100):
                if len(rows) >= MAX_ROWS:
                    raise LimitExceeded("row_limit")
                current = tuple(record)
                for value in current:
                    size = _cell_bytes(value)
                    if size > MAX_CELL_BYTES:
                        raise LimitExceeded("cell_bytes")
                    total_bytes += size
                    if total_bytes > MAX_RESULT_BYTES:
                        raise LimitExceeded("result_bytes")
                rows.append(current)
    except LimitExceeded:
        raise
    except TimeoutError:
        raise LimitExceeded("query_timeout") from None
    except asyncpg.PostgresError as error:
        raise ValidationError(classify_postgres_error(error)) from None
    except OSError:
        raise ValidationError("postgres_error") from None
    return rows


def _reason(error: ValidationError, default: str) -> str:
    reason = str(error).replace(" ", "_")
    return reason if reason in REASONS else default


async def validate_pair(connection, sqlite_path: Path, sqlite_sql: str, postgres_sql: str):
    try:
        sqlite_query = _query(sqlite_sql, dialect="sqlite").sql(dialect="sqlite")
        postgres_query = validate_postgres_query(postgres_sql)
    except ValidationError as error:
        return "failed", _reason(error, "statement_refused")
    try:
        with open_sqlite(sqlite_path) as sqlite:
            sqlite_rows = execute_sqlite(sqlite, sqlite_query)
    except LimitExceeded as error:
        return "excluded", _reason(error, "query_timeout")
    except ValidationError:
        return "failed", "sqlite_error"
    try:
        postgres_rows = await execute_postgres(connection, postgres_query)
    except LimitExceeded as error:
        return "excluded", _reason(error, "query_timeout")
    except ValidationError as error:
        return "failed", _reason(error, "postgres_error")
    try:
        if canonical_rows(sqlite_rows) == canonical_rows(postgres_rows):
            return "matched", None
    except ValidationError:
        return "excluded", "cell_type_refused"
    return "mismatched", "result_mismatch"


async def validate_track(name: str, tracks: dict[str, dict], values: dict[str, str]):
    track_deadline = TrackDeadline()
    original = tracks["bird_sqlite"]
    candidate = tracks[name]
    aligned, rejected = align_track(original, candidate)
    outcomes = [
        public_outcome(identifier, candidate[identifier]["db_id"], "failed", reason)
        for identifier, reason in sorted(rejected.items())
    ]
    if name != "bird_sqlite":
        for identifier in sorted(original.keys() - candidate.keys()):
            outcomes.append(
                public_outcome(identifier, original[identifier]["db_id"], "failed", "missing_id")
            )
    grouped = {db_id: [] for db_id in DATABASES}
    _, audit = load_specs()
    for item in aligned:
        grouped[item[1]["db_id"]].append(item)
    for db_id in sorted(DATABASES):
        if not grouped[db_id]:
            continue
        path = checked_sqlite_path(db_id)
        connection = await asyncpg.connect(**postgres_options(db_id, values))
        try:
            identity = await connection.fetchrow("SELECT current_database(), current_user")
            if tuple(identity) != ("sqlwarden", "warden_sandbox_" + db_id):
                raise ValidationError("restricted identity differs")
            for identifier, source, item in grouped[db_id]:
                track_deadline.check()
                sqlite_sql = item["SQL"] if name.startswith("arcwise_") else source["SQL"]
                try:
                    postgres_sql = (
                        transpile_corrected(item["SQL"], tables=audit["databases"][db_id]["tables"])
                        if name.startswith("arcwise_")
                        else tracks["bird_pg"][identifier]["SQL"]
                    )
                    status, reason = await validate_pair(connection, path, sqlite_sql, postgres_sql)
                except ValidationError as error:
                    status, reason = "failed", _reason(error, "transpile_error")
                outcomes.append(public_outcome(identifier, db_id, status, reason))
        finally:
            await connection.close()
    outcomes.sort(key=lambda item: item["question_id"])
    return {"track": name, "summary": summarize(outcomes), "outcomes": outcomes}


async def validate_all(data_root: Path, values: dict[str, str], tracks_to_run: list[str]):
    tracks = load_tracks(data_root)
    reports = {}
    for name in tracks_to_run:
        if name not in {"bird_pg", "arcwise_sql", "arcwise_full"}:
            raise ValidationError("track refused")
        reports[name] = await validate_track(name, tracks, values)
    return {
        "format_version": 1,
        "limits": {
            "query_seconds": QUERY_TIMEOUT_SECONDS,
            "rows": MAX_ROWS,
            "result_bytes": MAX_RESULT_BYTES,
            "cell_bytes": MAX_CELL_BYTES,
            "track_seconds": TRACK_TIMEOUT_SECONDS,
        },
        "tracks": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--track",
        action="append",
        choices=("bird_pg", "arcwise_sql", "arcwise_full"),
        required=True,
    )
    args = parser.parse_args()
    try:
        report = asyncio.run(validate_all(ROOT / "data", dict(os.environ), args.track))
        publish_manifest(args.output, report)
    except ValidationError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    except (OSError, ValueError, asyncpg.PostgresError, TimeoutError):
        print(json.dumps({"status": "failed", "reason": "validation runtime error"}))
        return 1
    print(json.dumps({"status": "complete", "output": str(args.output), "tracks": args.track}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
