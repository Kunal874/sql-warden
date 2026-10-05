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
    dump = (
        b"CREATE TABLE public.thing (\n    id bigint,\n"
        b"    happened timestamp with time zone\n);\n"
        b"COPY public.thing (id, happened) FROM stdin;\n" + data + b"\\.\n"
    )
    table = {
        "db_id": "db",
        "source_name": "Thing",
        "columns": [{"name": "id", "type": "BIGINT"}, {"name": "happened", "type": "TIMESTAMPTZ"}],
        "copy": {"rows": 2, **pin(data)},
    }
    return dump, {"thing": table}


def description_bytes(fields, names, *, encoding="utf-8", unnamed=""):
    text = io.StringIO(newline="")
    writer = csv.writer(text)
    writer.writerow(fields)
    for index, name in enumerate(names):
        writer.writerow(
            [
                name,
                name.strip(),
                "café",
                "",
                "",
                *([unnamed if index == 0 else ""] if fields[-1] == "" else []),
            ]
        )
    return text.getvalue().encode(encoding)


def test_native_types_and_blocks_are_metadata_not_execution():
    dump, tables = native_fixture()
    result = audit.inspect_native(io.BytesIO(dump), tables, pin(dump), deadline=float("inf"))
    assert result == {"thing": tables["thing"]["copy"]}


@pytest.mark.parametrize(
    "mode", ["duplicate", "unknown", "truncated", "columns", "types", "row", "line", "digest"]
)
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
    fields = [
        "original_column_name",
        "column_name",
        "column_description",
        "data_format",
        "value_description",
    ]
    raw = description_bytes(
        fields + [""], ["id ", "wins "], encoding="cp1252", unnamed="not discarded"
    )
    result = audit.inspect_description(
        raw, {"encoding": "cp1252", "unnamed_header": True}, fields, ["id"]
    )
    assert result["extra"] == ["wins"]
    assert result["unnamed_nonempty_rows"] == [1]
    assert result["padding_aliases"] == [
        {"source_name": "id ", "mapped_name": "id"},
        {"source_name": "wins ", "mapped_name": "wins"},
    ]
    assert "not discarded" not in json.dumps(result)


@pytest.mark.parametrize("mode", ["collision", "short", "extra", "header", "encoding"])
def test_description_malformed_records_fail_closed(mode):
    fields = [
        "original_column_name",
        "column_name",
        "column_description",
        "data_format",
        "value_description",
    ]
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
        audit.inspect_description(
            raw, {"encoding": "utf-8-sig", "unnamed_header": False}, fields, ["id"]
        )


def create_sqlite(path, *, extra_table=False, extra_column=False):
    with sqlite3.connect(path) as conn:
        suffix = ", extra TEXT" if extra_column else ""
        conn.execute(
            "CREATE TABLE Thing (id INTEGER PRIMARY KEY, happened TIMESTAMP" + suffix + ")"
        )
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
        "db_id": "db",
        "source_name": "Child",
        "columns": [{"name": "pid", "type": "BIGINT"}],
        "copy": {"rows": 1},
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
    path.write_text(
        json.dumps(
            [
                {
                    "db_id": "wrong",
                    "table_names_original": ["Thing"],
                    "column_names_original": [[-1, "*"], [0, "id"], [0, "happened"]],
                }
            ]
        ),
        encoding="utf-8",
    )
    _, tables = native_fixture()
    with pytest.raises(ValueError, match="metadata layout"):
        audit.inspect_metadata(path, tables)


def test_invalid_foreign_key_definition_is_explicitly_uncheckable(tmp_path):
    path = tmp_path / "db.sqlite"
    create_sqlite(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE Child (pid TIMESTAMP REFERENCES Thing(happened))")
        conn.execute("INSERT INTO Child VALUES (NULL)")
    _, tables = native_fixture()
    tables["child"] = {
        "db_id": "db",
        "source_name": "Child",
        "columns": [{"name": "pid", "type": "TIMESTAMPTZ"}],
        "copy": {"rows": 1},
    }
    before = file_sha256(path)
    report = audit.inspect_sqlite(path, "db", tables, deadline=float("inf"))
    assert report["foreign_key_check_status"] == "schema_mismatch"
    assert report["foreign_key_violation_count"] is None
    assert sum(table["rows"] for table in report["tables"].values()) == 3
    key = report["tables"]["child"]["foreign_keys"][0]
    assert key["parent_column"] == "happened"
    assert file_sha256(path) == before


def test_unrelated_sqlite_operational_error_is_not_a_schema_warning(tmp_path, monkeypatch):
    path = tmp_path / "db.sqlite"
    create_sqlite(path)
    _, tables = native_fixture()
    real_connect = sqlite3.connect

    class InterruptedCheck:
        def __init__(self, connection):
            self.connection = connection

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def execute(self, statement, *args):
            if statement == "PRAGMA foreign_key_check":
                raise sqlite3.OperationalError("interrupted")
            return self.connection.execute(statement, *args)

    monkeypatch.setattr(
        audit.sqlite3,
        "connect",
        lambda *args, **kwargs: InterruptedCheck(real_connect(*args, **kwargs)),
    )
    with pytest.raises(sqlite3.OperationalError, match="interrupted"):
        audit.inspect_sqlite(path, "db", tables, deadline=float("inf"))


def test_atomic_end_to_end_source_audit_has_no_gold_validity_claim(tmp_path):
    sqlite_path = tmp_path / "db.sqlite"
    create_sqlite(sqlite_path)
    dump, tables = native_fixture()
    fields = [
        "original_column_name",
        "column_name",
        "column_description",
        "data_format",
        "value_description",
    ]
    raw = description_bytes(fields, ["id", "happened"])
    metadata = json.dumps(
        [
            {
                "db_id": "db",
                "table_names_original": ["Thing"],
                "column_names_original": [[-1, "*"], [0, "id"], [0, "happened"]],
            }
        ]
    ).encode()
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("db.sqlite", sqlite_path.read_bytes())
        archive.writestr("original.csv", raw)
        archive.writestr("metadata.json", metadata)
        archive.writestr("native.sql", dump)
    description = {
        "db_id": "db",
        "native_table": "thing",
        "encoding": "utf-8-sig",
        "unnamed_header": False,
    }
    pins = {
        "archive": pin(archive_path.read_bytes()),
        "metadata": pin(metadata, member="metadata.json", output="dev_tables.json"),
        "native_dump": pin(dump, member="native.sql"),
        "sqlite_sources": [
            pin(sqlite_path.read_bytes(), db_id="db", member="db.sqlite", output="sqlite/db.sqlite")
        ],
        "original_description_sources": [
            pin(raw, **description, member="original.csv", output="original/db/thing.csv")
        ],
        "corrected_description_sources": [pin(raw, **description, output="db/thing.csv")],
        "tables": tables,
        "csv_fields": fields,
        "corrected_revision": "fixture-only",
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
