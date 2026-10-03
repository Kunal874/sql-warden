"""Offline, fixed-dataset metadata and native-data extraction; never execute dump SQL."""

import csv
import hashlib
import json
import re
import sqlite3
import tempfile
from contextlib import ExitStack, closing
from pathlib import Path
from typing import BinaryIO

TABLE_NAMES = ("schools", "frpm", "satscores")
TYPE_MAP = {"TEXT": "text", "INTEGER": "bigint", "REAL": "real", "DATE": "date"}
ORDINARY = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
COPY_HEADER = re.compile(
    rb'COPY public\.([a-z_][a-z_0-9]*|"(?:[^"]|"")+") \((.*)\) FROM stdin;\n\Z'
)
MAX_LINE_BYTES = 1024 * 1024
MAX_BLOCK_BYTES = 32 * 1024 * 1024
SQLITE_SHA256 = "c0903eec662e63068fd1d14403d3d6c1d473287fc10c4356333ea58f878db983"
NATIVE_EXPECTED = {
    "schools": {
        "rows": 17686,
        "bytes": 7728755,
        "sha256": "f6f4de19738417ed5bd27d1d2e7935aa3e2b4319a2c366542560514671f38b6a",
    },
    "frpm": {
        "rows": 9986,
        "bytes": 2481961,
        "sha256": "504bc2f6a66e9dfff6c9f04bb6078bcab6196c966b8d992575f88d9ad618f316",
    },
    "satscores": {
        "rows": 2269,
        "bytes": 197389,
        "sha256": "549f79e4b98bb0660dd9024271e3787ea83cf875fccc8e7a547c38c419a79c0f",
    },
}


def file_sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def pg_name(source_name: str) -> str:
    name = source_name.lower() if ORDINARY.fullmatch(source_name) else source_name
    if not name or "\x00" in name or len(name.encode("utf-8")) > 63:
        raise ValueError("Unsupported source identifier")
    return name


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def read_tables(sqlite_path: Path, expected_sha256: str) -> dict:
    if file_sha256(sqlite_path) != expected_sha256:
        raise ValueError("SQLite source checksum differs")
    tables = {}
    with closing(sqlite3.connect(sqlite_path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        for name in TABLE_NAMES:
            kind = conn.execute("SELECT type FROM sqlite_master WHERE name=?", (name,)).fetchone()
            if kind != ("table",):
                raise ValueError("Required source table is missing or is a view")
            columns = []
            primary_key = []
            for _cid, source_name, kind, not_null, _default, pk in conn.execute(
                f"PRAGMA table_info({name})"
            ):
                if kind not in TYPE_MAP:
                    raise ValueError("Unsupported source column type")
                mapped = pg_name(source_name)
                columns.append(
                    {
                        "source_name": source_name,
                        "name": mapped,
                        "type": TYPE_MAP[kind],
                        "not_null": bool(not_null or pk),
                    }
                )
                if pk:
                    primary_key.append((pk, mapped))
            if not columns or len({c["name"] for c in columns}) != len(columns):
                raise ValueError("Missing or colliding source columns")
            primary_key = [column for _position, column in sorted(primary_key)]
            if primary_key != (["cds"] if name == "satscores" else ["cdscode"]):
                raise ValueError("Unexpected source primary key")
            keys = list(conn.execute(f"PRAGMA foreign_key_list({name})"))
            foreign_key = None
            if name == "schools":
                if keys:
                    raise ValueError("Unexpected source foreign key")
            else:
                expected_key = ("cds" if name == "satscores" else "cdscode", "schools", "cdscode")
                if len(keys) != 1:
                    raise ValueError("Unexpected source foreign key")
                key = keys[0]
                foreign_key = (pg_name(key[3]), key[2], pg_name(key[4]))
                if key[1] != 0 or foreign_key != expected_key:
                    raise ValueError("Unexpected source foreign key")
            tables[name] = {
                "columns": columns,
                "primary_key": primary_key,
                "foreign_key": foreign_key,
            }
    return tables


def extract_native_copy(stream: BinaryIO, destination: Path, tables: dict, expected: dict) -> dict:
    if destination.exists():
        raise FileExistsError("Refusing to overwrite native source data")
    if set(tables) != set(TABLE_NAMES) or set(expected) != set(TABLE_NAMES):
        raise ValueError("Unsupported source table selection")
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = {}
    active = None
    output = None
    checksum = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix=".bird-native-", dir=destination.parent) as work:
        staging = Path(work)
        with ExitStack() as files:
            while line := stream.readline(MAX_LINE_BYTES + 1):
                if len(line) > MAX_LINE_BYTES or not line.endswith(b"\n"):
                    raise ValueError("Source line exceeds budget or lacks LF ending")
                if active is not None:
                    if line == b"\\.\n":
                        if output is not None:
                            entry = result[active]
                            entry["sha256"] = checksum.hexdigest()
                            if any(entry[key] != value for key, value in expected[active].items()):
                                raise ValueError("Native COPY data fingerprint differs")
                        active = None
                        output = None
                    elif output is not None:
                        entry["rows"] += 1
                        entry["bytes"] += len(line)
                        if entry["bytes"] > MAX_BLOCK_BYTES:
                            raise ValueError("Selected native block exceeds budget")
                        checksum.update(line)
                        output.write(line)
                    continue
                if not line.startswith(b"COPY "):
                    continue
                match = COPY_HEADER.fullmatch(line)
                if match is None:
                    raise ValueError("Unsupported native COPY header")
                active = match[1].decode("utf-8")
                if active not in tables:
                    continue
                if active in result:
                    raise ValueError("Duplicated selected native COPY block")
                columns = next(
                    csv.reader([match[2].decode("utf-8")], skipinitialspace=True, strict=True)
                )
                wanted = [column["name"] for column in tables[active]["columns"]]
                if columns != wanted or len(set(columns)) != len(columns):
                    raise ValueError("Native COPY columns differ from checked metadata")
                result[active] = entry = {"columns": columns, "rows": 0, "bytes": 0}
                checksum = hashlib.sha256()
                output = files.enter_context((staging / f"{active}.tsv").open("xb"))
            if active is not None or set(result) != set(TABLE_NAMES):
                raise ValueError("Selected native COPY blocks are incomplete")
        (staging / "manifest.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        staging.rename(destination)
    return result
