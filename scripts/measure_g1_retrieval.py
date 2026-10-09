"""Read-only G1 retrieval measurement on the frozen development split."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "results" / "G1_retrieval" / "summary.json"
TOP_KS = (8, 16, 24, 32)


def referenced_tables(sql: str) -> set[str]:
    try:
        tree = sqlglot.parse_one(sql, read="postgres")
    except sqlglot.errors.ParseError:
        return set()
    cte_names = {cte.alias.casefold() for cte in tree.find_all(exp.CTE) if cte.alias}
    return {
        table.name.casefold()
        for table in tree.find_all(exp.Table)
        if table.name and not (not table.db and table.name.casefold() in cte_names)
    }


def measure() -> dict:
    from scripts import run_e0
    from sqlwarden.schema import SchemaCatalog

    _, audit = run_e0.load_specs()
    schemas: dict[str, SchemaCatalog] = {}
    rows = {k: {"items": 0, "table_recall_sum": 0.0, "full_table_hits": 0} for k in TOP_KS}
    for item in run_e0.build_items():
        db_id = item["db_id"]
        schemas.setdefault(
            db_id, SchemaCatalog.from_mapping(db_id, run_e0.load_schema(db_id, audit))
        )
        expected = referenced_tables(item["gold_sql"])
        if not expected:
            continue
        for top_k in TOP_KS:
            scope = schemas[db_id].retrieve(item["question"], top_k=top_k)
            actual = {table.name.casefold() for table in scope.tables}
            recall = len(expected & actual) / len(expected)
            rows[top_k]["items"] += 1
            rows[top_k]["table_recall_sum"] += recall
            rows[top_k]["full_table_hits"] += int(expected <= actual)
    results = {}
    for top_k, row in rows.items():
        items = row["items"]
        results[str(top_k)] = {
            "items": items,
            "mean_table_recall": round(row["table_recall_sum"] / items, 6) if items else None,
            "full_table_recall": round(row["full_table_hits"] / items, 6) if items else None,
        }
    return {
        "format_version": 1,
        "protocol": "g1-retrieval-c3-dev-v1",
        "split": "docs/e0-protocol.json development IDs only",
        "retriever": "stdlib BM25-style lexical over table/column names and descriptions",
        "top_k_columns": results,
        "chosen": {
            "retrieve_columns": 24,
            "candidates": 3,
            "max_repairs": 1,
            "helper_setup": (
                "no general helper in the core loop; clarification/explanation use a bounded "
                "helper seam with fake-LLM tests until a local helper is separately measured"
            ),
        },
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(measure(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
