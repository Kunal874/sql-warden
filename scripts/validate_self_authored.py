"""Check and freeze the E7 self-authored set before any model run on it.

Every reading and gold query must pass the guard, run on the dataset's restricted
login and return rows; the two readings of an ambiguous item must differ. Writes
results/G3_matrix/e7-self-authored-check.json with the set's SHA-256 (the freeze).
uv run --env-file .env.california --env-file .env.datasets python -m scripts.validate_self_authored
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from sqlwarden.comparator import compare_ex
from sqlwarden.executor import QueryResult, dataset_password_key, open_dataset_executor
from sqlwarden.guard import DATASET_POLICIES, guard_sql

ROOT = Path(__file__).resolve().parents[1]
SET = ROOT / "docs/e7-self-authored.json"
OUTPUT = ROOT / "results/G3_matrix/e7-self-authored-check.json"


def load_set() -> dict[str, Any]:
    return json.loads(SET.read_text(encoding="utf-8"))


def gold_sql(item: dict[str, Any]) -> str:
    if item["kind"] == "clear":
        return item["gold_sql"]
    return next(r["sql"] for r in item["readings"] if r["id"] == item["intended"])


async def run_sql(db_id: str, sql: str, values: dict[str, str]) -> QueryResult:
    decision = guard_sql(sql, DATASET_POLICIES[db_id])
    if not decision.accepted:
        return QueryResult("blocked", decision.reason)
    async with open_dataset_executor(db_id, values[dataset_password_key(db_id)]) as executor:
        return await executor.execute(decision.sql)


async def check() -> dict[str, Any]:
    values = dict(os.environ)
    data = load_set()
    rows, problems = [], []
    for item in data["items"]:
        sqls = [gold_sql(item)] if item["kind"] == "clear" else [r["sql"] for r in item["readings"]]
        results = [await run_sql(item["db_id"], sql, values) for sql in sqls]
        ok = all(r.status == "ok" and r.rows for r in results)
        differ = None
        if item["kind"] == "ambiguous" and ok:
            differ = compare_ex(results[0], results[1]).score == 0
        if not ok or differ is False:
            problems.append(item["id"])
        rows.append(
            {
                "id": item["id"],
                "kind": item["kind"],
                "statuses": [f"{r.status}:{r.reason}" for r in results],
                "row_counts": [len(r.rows) for r in results],
                "readings_differ": differ,
            }
        )
    return {
        "format_version": 1,
        "set_sha256": hashlib.sha256(SET.read_bytes()).hexdigest(),
        "items": len(rows),
        "ambiguous": sum(1 for r in rows if r["kind"] == "ambiguous"),
        "clear": sum(1 for r in rows if r["kind"] == "clear"),
        "problems": problems,
        "checks": rows,
    }


def main() -> int:
    report = asyncio.run(check())
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("items", "ambiguous", "clear", "problems")}))
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
