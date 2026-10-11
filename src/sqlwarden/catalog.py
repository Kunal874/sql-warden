"""Dataset schema catalogs from the tracked audit manifest and local corrected descriptions."""

from __future__ import annotations

import csv
import hashlib
import json
from functools import cache
from pathlib import Path
from typing import Any

from sqlwarden.schema import SchemaCatalog, SchemaError

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "docs/source-audit-manifest.json"
AUDIT_SHA = "f52ecfd71c53fb470bb85e899e4b97178df304e0b30f66cba32518fa7f286c31"
DESCRIPTIONS = ROOT / "data/description-corrections/arcwise-fe766045"


def load_audit() -> dict[str, Any]:
    data = AUDIT_PATH.read_bytes()
    if len(data) > 256 * 1024 or hashlib.sha256(data).hexdigest() != AUDIT_SHA:
        raise SchemaError("reviewed metadata fingerprint differs")
    return json.loads(data)


def schema_mapping(
    db_id: str, audit: dict[str, Any], *, descriptions_root: Path = DESCRIPTIONS
) -> dict[str, Any]:
    """Tables, keys and corrected column descriptions; no sample values."""
    descriptions = {
        path.stem: read_description_csv(path) for path in (descriptions_root / db_id).glob("*.csv")
    }
    tables = {}
    for table_name, table in audit["databases"][db_id]["tables"].items():
        tables[table_name] = {
            "description": "",
            "primary_key": table.get("primary_key", []),
            "foreign_keys": [
                {
                    "columns": [foreign_key["column"].casefold()],
                    "references": f"{foreign_key['parent_table'].casefold()}."
                    f"{(foreign_key.get('parent_column') or '').casefold()}",
                }
                for foreign_key in table.get("foreign_keys", [])
                if foreign_key.get("column") and foreign_key.get("parent_table")
            ],
            "columns": [
                {
                    "name": column["name"],
                    "type": column["native_type"],
                    "description": descriptions.get(table_name, {}).get(column["source_name"], ""),
                }
                for column in table["columns"]
            ],
        }
    return {"tables": tables}


def read_description_csv(path: Path) -> dict[str, str]:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with path.open("r", encoding=encoding, newline="") as stream:
                return {
                    row["original_column_name"]: row.get("column_description", "")
                    for row in csv.DictReader(stream)
                    if row.get("original_column_name")
                }
        except UnicodeDecodeError:
            continue
    raise SchemaError("description encoding refused")


@cache
def load_catalog(db_id: str) -> SchemaCatalog:
    return SchemaCatalog.from_mapping(db_id, schema_mapping(db_id, load_audit()))
