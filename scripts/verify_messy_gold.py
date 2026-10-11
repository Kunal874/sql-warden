"""E4 check: gold SQL rewritten to messy names and back must return the same rows.

Writes compact counts and failing IDs only (no SQL, no rows) to
results/G3_matrix/messy-gold-check.json. Restricted evaluation credentials only:
uv run --env-file .env.california --env-file .env.datasets python -m scripts.verify_messy_gold
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter

from scripts.messy_schema import SEED, build_mapping, leaked_names, messy_catalog, translate
from scripts.run_matrix import RESULTS, build_items, ex, gold_rows
from sqlwarden.catalog import load_catalog
from sqlwarden.executor import QueryResult
from sqlwarden.schema import SchemaCatalog

OUTPUT = RESULTS / "messy-gold-check.json"


async def check() -> dict:
    values = dict(os.environ)
    items = build_items("dev") + build_items("held_out")
    outcomes: Counter[str] = Counter()
    failing = []
    for item in items:
        mapping = build_mapping(load_catalog(item["db_id"]))
        try:
            restored = translate(translate(item["gold_corrected"], mapping), mapping.reverse())
        except Exception:
            outcomes["translate_error"] += 1
            failing.append(item["question_id"])
            continue
        original = await gold_rows(item["db_id"], item["gold_corrected"], values)
        rewritten = await gold_rows(item["db_id"], restored, values)
        if original is None:
            outcomes["gold_unavailable"] += 1
            continue
        result = (
            None
            if rewritten is None
            else QueryResult("ok", "ok", rows=tuple(map(tuple, rewritten)))
        )
        if ex(result, original) == 1:
            outcomes["same_rows"] += 1
        else:
            outcomes["different_rows"] += 1
            failing.append(item["question_id"])
    leakage = {}
    for db_id in sorted({item["db_id"] for item in items}):
        catalog = load_catalog(db_id)
        text = SchemaCatalog.serialize(
            messy_catalog(catalog, build_mapping(catalog)).scope_all(), max_bytes=10**6
        )
        leakage[db_id] = leaked_names(text, catalog)
    return {
        "format_version": 1,
        "seed": SEED,
        "items": len(items),
        "outcomes": dict(sorted(outcomes.items())),
        "failing_question_ids": sorted(failing),
        "leaked_distinctive_names_by_db": leakage,
        "excludes": ["sql", "rows", "credentials"],
    }


def main() -> int:
    report = asyncio.run(check())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("items", "outcomes")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
