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


def inspect_native(
    stream: BinaryIO,
    tables: dict,
    dump_pin: dict,
    *,
    deadline: float,
    copy_outputs: dict[str, BinaryIO] | None = None,
) -> dict:
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
                if copy_outputs is not None and active in copy_outputs:
                    copy_outputs[active].write(line)
            continue
        if ddl:
            ddl.append(line)
            if sum(map(len, ddl)) > 65536:
                raise ValueError("native definition byte limit exceeded")
            if line == b");\n":
                statement = sqlglot.parse_one(b"".join(ddl).decode("utf-8"), read="postgres")
                if not isinstance(statement, exp.Create) or not isinstance(
                    statement.this, exp.Schema
                ):
                    raise ValueError("unsupported native definition")
                table = statement.this.this
                if table.db != "public" or table.name not in tables or table.name in definitions:
                    raise ValueError("native table identity mismatch")
                if any(not isinstance(c, exp.ColumnDef) for c in statement.this.expressions):
                    raise ValueError("unsupported native definition member")
                columns = [
                    {"name": c.this.name, "type": c.kind.sql(dialect="postgres")}
                    for c in statement.this.expressions
                ]
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
            columns = next(
                csv.reader([match[2].decode("utf-8")], skipinitialspace=True, strict=True)
            )
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
        physical = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'"
            )
        ]
        mapped = {pg_name(name): name for name in physical}
        if len(mapped) != len(physical) or set(mapped) != set(expected):
            raise ValueError("SQLite table identity mismatch")
        violations = 0
        foreign_key_status = "completed"
        try:
            for _ in conn.execute("PRAGMA foreign_key_check"):
                violations += 1
                if monotonic() >= deadline:
                    raise ValueError("audit deadline exceeded")
        except sqlite3.OperationalError as error:
            if not str(error).startswith("foreign key mismatch - "):
                raise
            foreign_key_status = "schema_mismatch"
            violations = None
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
                    {
                        "name": pg_name(row[1]),
                        "source_name": row[1],
                        "source_type": row[2],
                        "native_type": native["type"],
                        "declared_not_null": bool(row[3]),
                        "primary_key_position": row[5],
                    }
                    for row, native in zip(columns, table["columns"], strict=True)
                ],
                "primary_key": [
                    pg_name(row[1]) for row in sorted(columns, key=lambda r: r[5]) if row[5]
                ],
                "foreign_keys": [
                    {
                        "id": row[0],
                        "sequence": row[1],
                        "parent_table": row[2],
                        "column": row[3],
                        "parent_column": row[4],
                        "on_update": row[5],
                        "on_delete": row[6],
                        "match": row[7],
                    }
                    for row in conn.execute(
                        f"PRAGMA foreign_key_list({quote_ident(physical_name)})"
                    )
                ],
            }
            if monotonic() >= deadline:
                raise ValueError("audit deadline exceeded")
    return {
        "tables": result,
        "foreign_key_check_status": foreign_key_status,
        "foreign_key_violation_count": violations,
    }


def inspect_description(raw: bytes, pin: dict, fields: list[str], columns: list[str]) -> dict:
    expected_fields = fields + ([""] if pin["unnamed_header"] else [])
    reader = csv.DictReader(
        io.StringIO(raw.decode(pin["encoding"], errors="strict"), newline=""), strict=True
    )
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
        "rows": len(names),
        "missing": sorted(set(columns) - set(names)),
        "extra": sorted(set(names) - set(columns)),
        "padding_aliases": aliases,
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
                "columns": [
                    pg_name(column)
                    for table_id, column in database["column_names_original"]
                    if table_id == index
                ],
            }
    expected = {
        name: {"db_id": table["db_id"], "columns": [c["name"] for c in table["columns"]]}
        for name, table in tables.items()
    }
    if observed != expected:
        raise ValueError("metadata layout differs")


def audit_sources(
    release: Path,
    corrected: Path,
    archive_path: Path,
    destination: Path,
    *,
    pins: dict | None = None,
) -> dict:
    pins = load_pins() if pins is None else pins
    new_destination(destination)
    deadline = monotonic() + 1200
    checked_file(archive_path, pins["archive"])
    checked_file(release / relative_path(pins["metadata"]["output"]), pins["metadata"])
    inspect_metadata(release / relative_path(pins["metadata"]["output"]), pins["tables"])
    report = {
        "format_version": 1,
        "status": "source layout audit only",
        "conversion_validity": "not checked",
        "typed_content_equivalence": "not checked",
        "primary_descriptions": "not selected",
        "constraint_validity": "not established; source issues recorded",
        "databases": {},
        "descriptions": {},
        "source_archive_sha256": pins["archive"]["sha256"],
        "corrected_revision": pins["corrected_revision"],
    }
    with (
        zipfile.ZipFile(archive_path) as archive,
        archive.open(selected_member(archive, pins["native_dump"])) as stream,
    ):
        report["native_blocks"] = inspect_native(
            stream, pins["tables"], pins["native_dump"], deadline=deadline
        )
    for entry in pins["sqlite_sources"]:
        path = release / relative_path(entry["output"])
        checked_file(path, entry)
        report["databases"][entry["db_id"]] = inspect_sqlite(
            path, entry["db_id"], pins["tables"], deadline=deadline
        )
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
                observation["mapped_name"]
                for observation in pins["observations"]["original_unmapped_columns"]
                if source == "original"
                and observation["db_id"] == entry["db_id"]
                and observation["table"] == entry["native_table"]
            ]
            if description["missing"] or description["extra"] != sorted(allowed_extra):
                raise ValueError("description/native column coverage differs")
            report["descriptions"][source + "/" + entry["db_id"] + "/" + entry["native_table"]] = (
                description
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".source-audit-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "report"
        staging.mkdir()
        (staging / "manifest.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        if monotonic() >= deadline:
            raise ValueError("audit deadline exceeded")
        new_destination(destination)
        staging.rename(destination)
    return report


def main() -> int:
    try:
        report = audit_sources(SOURCE_DIR, DESCRIPTION_DIR, ARCHIVE, AUDIT_DIR)
    except (
        ValueError,
        OSError,
        sqlite3.Error,
        csv.Error,
        zipfile.BadZipFile,
        sqlglot.errors.ParseError,
    ):
        print(json.dumps({"status": "failed", "stage": "offline source audit"}))
        return 1
    print(
        json.dumps(
            {
                "status": "audited",
                "databases": len(report["databases"]),
                "tables": len(report["native_blocks"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
