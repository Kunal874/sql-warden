"""Compact guard acceptance audit for the corrected usable gold pool."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLD = ROOT / "docs" / "gold-validity-manifest.json"
DATA = ROOT / "data"
DEFAULT_OUTPUT = ROOT / "docs" / "guard-gold-audit-manifest.json"


def guard_case_inventory() -> dict[str, int]:
    path = ROOT / "tests" / "test_guard.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    safe = unsafe = other = 0
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            names = {target.id for target in node.targets if isinstance(target, ast.Name)}
            count = _count_sql_literals(node.value)
            if "SAFE" in names:
                safe += count
            if "UNSAFE" in names:
                unsafe += count
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                count = _parametrize_sql_cases(decorator)
                if node.name.startswith("test_supported"):
                    safe += count
                elif count:
                    other += count
    return {
        "safe_cases": safe,
        "unsafe_cases": unsafe,
        "other_guard_cases": other,
        "total_cases": safe + unsafe + other,
    }


def summarize(records: list[dict[str, Any]], *, source_sha256: str) -> dict[str, Any]:
    status_counts = Counter(record["status"] for record in records)
    reason_counts = Counter(
        record["reason"] for record in records if record.get("status") == "blocked"
    )
    by_db: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        by_db[record["db_id"]][record["status"]] += 1
    return {
        "format_version": 1,
        "source": "docs/gold-validity-manifest.json usable_items",
        "source_sha256": source_sha256,
        "items": len(records),
        "status_counts": dict(sorted(status_counts.items())),
        "blocked_reason_counts": dict(sorted(reason_counts.items())),
        "by_db": {
            db_id: {
                "accepted": counts.get("accepted", 0),
                "blocked": counts.get("blocked", 0),
                "transpile_failed": counts.get("transpile_failed", 0),
            }
            for db_id, counts in sorted(by_db.items())
        },
        "contains": "counts, database IDs, status categories and reason counts only",
        "excludes": ["SQL text", "question text", "result rows", "credentials", "model prompts"],
    }


def _count_sql_literals(node: ast.AST) -> int:
    if isinstance(node, (ast.List, ast.Tuple)):
        return sum(_count_sql_literals(item) for item in node.elts)
    return int(isinstance(node, ast.Constant) and isinstance(node.value, str))


def _parametrize_sql_cases(node: ast.AST) -> int:
    if not isinstance(node, ast.Call) or len(node.args) < 2:
        return 0
    marker = node.func
    if (
        not isinstance(marker, ast.Attribute)
        or marker.attr != "parametrize"
        or not isinstance(node.args[0], ast.Constant)
    ):
        return 0
    names = str(node.args[0].value)
    if "sql" not in names:
        return 0
    values = node.args[1]
    if not isinstance(values, (ast.List, ast.Tuple)):
        return 0
    return len(values.elts)


def audit() -> dict[str, Any]:
    from scripts.prepare_import_bundle import load_specs
    from scripts.validate_gold import load_tracks, transpile_corrected
    from sqlwarden.guard import DATASET_POLICIES, guard_sql

    manifest = json.loads(GOLD.read_text(encoding="utf-8"))
    tracks = load_tracks(DATA)
    _, native = load_specs()
    source_sha256 = hashlib.sha256(GOLD.read_bytes()).hexdigest()
    records = []
    for item in manifest["usable_items"]:
        identifier = item["question_id"]
        db_id = item["db_id"]
        try:
            sql = transpile_corrected(
                tracks["arcwise_full"][identifier]["SQL"],
                tables=native["databases"][db_id]["tables"],
            )
        except Exception:
            records.append(
                {"question_id": identifier, "db_id": db_id, "status": "transpile_failed"}
            )
            continue
        decision = guard_sql(sql, DATASET_POLICIES[db_id])
        records.append(
            {
                "question_id": identifier,
                "db_id": db_id,
                "status": "accepted" if decision.accepted else "blocked",
                **({} if decision.accepted else {"reason": decision.reason}),
            }
        )
    return summarize(records, source_sha256=source_sha256) | {
        "guard_case_inventory": guard_case_inventory()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
