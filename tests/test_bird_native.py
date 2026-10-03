"""Catch changed identifiers/types/keys and incomplete or altered native COPY data."""

import hashlib
import io
import sqlite3
import stat
import zipfile

import pytest

from sqlwarden.data import extract_native_copy, pg_name, read_tables


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_sqlite(path, *, kind="TEXT", name="School Name", target="schools", view=False):
    with sqlite3.connect(path) as conn:
        conn.executescript(
            f'CREATE TABLE schools (CDSCode TEXT PRIMARY KEY, "{name}" {kind}, '
            "Charter INTEGER, Latitude REAL, OpenDate DATE);"
            f"CREATE TABLE frpm (CDSCode TEXT PRIMARY KEY REFERENCES {target}(CDSCode));"
            "CREATE TABLE satscores (cds TEXT PRIMARY KEY REFERENCES schools(CDSCode));"
        )
        if view:
            conn.executescript(
                "DROP TABLE satscores; CREATE VIEW satscores AS SELECT CDSCode FROM schools;"
            )
    return path, digest(path)


def test_native_names_types_and_keys(tmp_path):
    path, checksum = make_sqlite(tmp_path / "source.sqlite")
    tables = read_tables(path, checksum)
    assert [(c["name"], c["type"]) for c in tables["schools"]["columns"]] == [
        ("cdscode", "text"),
        ("School Name", "text"),
        ("charter", "bigint"),
        ("latitude", "real"),
        ("opendate", "date"),
    ]
    assert tables["schools"]["primary_key"] == ["cdscode"]
    assert tables["frpm"]["foreign_key"] == ("cdscode", "schools", "cdscode")
    assert tables["satscores"]["foreign_key"] == ("cds", "schools", "cdscode")
    assert digest(path) == checksum


@pytest.mark.parametrize("problem", ["checksum", "view", "type", "long_name", "foreign_key"])
def test_invalid_source_metadata_is_rejected(tmp_path, problem):
    path, checksum = make_sqlite(
        tmp_path / "source.sqlite",
        kind="BLOB" if problem == "type" else "TEXT",
        name="x" * 64 if problem == "long_name" else "School Name",
        target="other" if problem == "foreign_key" else "schools",
        view=problem == "view",
    )
    with pytest.raises(ValueError):
        read_tables(path, "0" * 64 if problem == "checksum" else checksum)


@pytest.mark.parametrize("name", ["", "bad\x00name", "é" * 32])
def test_invalid_postgres_identifier_is_rejected(name):
    with pytest.raises(ValueError):
        pg_name(name)


TABLES = {
    "schools": {"columns": [{"name": "cdscode"}, {"name": "School Name"}]},
    "frpm": {"columns": [{"name": "cdscode"}]},
    "satscores": {"columns": [{"name": "cds"}]},
}
PAYLOADS = {"schools": b"1\tExample\\tName\n2\t\\N\n", "frpm": b"1\n", "satscores": b"1\n"}


def native_dump():
    return (
        b"DO $$ BEGIN RAISE EXCEPTION 'never execute'; END $$;\n"
        b"COPY public.other_table (value) FROM stdin;\n"
        b'COPY public.schools (cdscode, "School Name") FROM stdin;\n'
        b"not a header inside ignored data\n\\.\n"
        b'COPY public.schools (cdscode, "School Name") FROM stdin;\n'
        + PAYLOADS["schools"]
        + b"\\.\n"
        b"COPY public.frpm (cdscode) FROM stdin;\n" + PAYLOADS["frpm"] + b"\\.\n"
        b"COPY public.satscores (cds) FROM stdin;\n" + PAYLOADS["satscores"] + b"\\.\n"
    )


def expected():
    return {
        name: {"rows": data.count(b"\n"), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in PAYLOADS.items()
    }


def test_native_extractor_preserves_only_selected_copy_bytes(tmp_path):
    output = tmp_path / "native"
    result = extract_native_copy(io.BytesIO(native_dump()), output, TABLES, expected())
    assert set(result) == {"schools", "frpm", "satscores"}
    assert set(p.name for p in output.iterdir()) == {
        "schools.tsv",
        "frpm.tsv",
        "satscores.tsv",
        "manifest.json",
    }
    for name, data in PAYLOADS.items():
        assert (output / f"{name}.tsv").read_bytes() == data
        assert result[name]["rows"] == data.count(b"\n")
        assert result[name]["bytes"] == len(data)


@pytest.mark.parametrize(
    "problem",
    ["missing", "duplicate", "unterminated", "header", "columns", "hash", "rows", "line", "block"],
)
def test_native_failures_never_publish_partial_output(tmp_path, monkeypatch, problem):
    dump = native_dump()
    fingerprints = expected()
    if problem == "missing":
        dump = dump[: dump.index(b"COPY public.satscores")]
    elif problem == "duplicate":
        dump += b"COPY public.frpm (cdscode) FROM stdin;\n1\n\\.\n"
    elif problem == "unterminated":
        dump = dump[:-3]
    elif problem == "header":
        dump = dump.replace(b"COPY public.frpm (cdscode)", b"COPY public.frpm (different)")
    elif problem == "columns":
        dump = dump.replace(b"COPY public.frpm (cdscode)", b"COPY public.frpm (cdscode, cdscode)")
    elif problem == "hash":
        fingerprints["frpm"]["sha256"] = "0" * 64
    elif problem == "rows":
        fingerprints["frpm"]["rows"] = 2
    elif problem == "line":
        monkeypatch.setattr("sqlwarden.data.MAX_LINE_BYTES", 8)
    elif problem == "block":
        monkeypatch.setattr("sqlwarden.data.MAX_BLOCK_BYTES", 8)
    output = tmp_path / "native"
    with pytest.raises(ValueError):
        extract_native_copy(io.BytesIO(dump), output, TABLES, fingerprints)
    assert not output.exists()
    assert not list(tmp_path.glob(".bird-native-*"))


def test_native_extractor_refuses_existing_destination(tmp_path):
    output = tmp_path / "native"
    output.mkdir()
    sentinel = output / "schools.tsv"
    sentinel.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        extract_native_copy(io.BytesIO(native_dump()), output, TABLES, expected())
    assert sentinel.read_bytes() == b"keep"


@pytest.mark.parametrize("problem", [None, "checksum", "missing", "duplicate", "symlink"])
def test_native_archive_entry_point_checks_source_and_member(tmp_path, monkeypatch, problem):
    from scripts import fetch_data

    sqlite_path = tmp_path / "source.sqlite"
    with sqlite3.connect(sqlite_path) as conn:
        conn.executescript(
            'CREATE TABLE schools (CDSCode TEXT PRIMARY KEY, "School Name" TEXT);'
            "CREATE TABLE frpm (CDSCode TEXT PRIMARY KEY REFERENCES schools(CDSCode));"
            "CREATE TABLE satscores (cds TEXT PRIMARY KEY REFERENCES schools(CDSCode));"
        )
    archive_path = tmp_path / "source.zip"
    member = "minidev/MINIDEV_postgresql/BIRD_dev.sql"
    with zipfile.ZipFile(archive_path, "w") as archive:
        if problem != "missing":
            info = zipfile.ZipInfo(member)
            if problem == "symlink":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, native_dump())
        if problem == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(member, native_dump())
    monkeypatch.setattr(
        fetch_data, "ARCHIVE_SHA256", "0" * 64 if problem == "checksum" else digest(archive_path)
    )
    monkeypatch.setattr(fetch_data, "SQLITE_SHA256", digest(sqlite_path), raising=False)
    monkeypatch.setattr(fetch_data, "NATIVE_EXPECTED", expected(), raising=False)
    output = tmp_path / "native"
    if problem is None:
        result = fetch_data.extract_native_archive(archive_path, output, sqlite_path)
        assert result["schools"]["rows"] == 2
        assert (output / "schools.tsv").read_bytes() == PAYLOADS["schools"]
    else:
        with pytest.raises(ValueError):
            fetch_data.extract_native_archive(archive_path, output, sqlite_path)
        assert not output.exists()
