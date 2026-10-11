"""E7 on the frozen self-authored set: ask, simulated reply, final answer.

The simulated user may only return the item's frozen intended meaning; it never sees
candidate SQL or results. Raw records go to ignored results/G3_matrix/raw/e7/.
uv run --env-file .env.california --env-file .env.datasets python -m scripts.run_e7_self_authored
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import statistics
from typing import Any

from scripts.run_e0 import _git_commit, _git_dirty
from scripts.run_matrix import CACHE, RAW, result_sha, run_item
from scripts.validate_self_authored import SET, gold_sql, run_sql
from sqlwarden.cache import JsonDiskCache
from sqlwarden.evaluation import EvaluationError, append_jsonl_record, load_jsonl_records
from sqlwarden.ollama import ARCTIC, QWEN
from sqlwarden.prompts import PROMPT_VERSIONS, template_sha256

OUTPUT = RAW / "e7" / "self_authored.jsonl"
FROZEN_SHA = "ee149a94aa1436c2"


def pseudo_item(index: int, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": index,
        "db_id": item["db_id"],
        "difficulty": item["kind"],
        "ambiguity_candidate": item["kind"] == "ambiguous",
        "input_changed": False,
        "corrected_text": item["question"],
        "original_text": item["question"],
        "gold_corrected": gold_sql(item),
        "gold_original": None,
        "original_label_status": "not_applicable",
    }


def matched_reading(selected_sha: str | None, reading_shas: dict[str, str | None]) -> str | None:
    if selected_sha is None:
        return None
    return next((rid for rid, sha in reading_shas.items() if sha == selected_sha), "neither")


async def run() -> int:
    if not hashlib.sha256(SET.read_bytes()).hexdigest().startswith(FROZEN_SHA):
        raise EvaluationError("self-authored set changed after freezing")
    values = dict(os.environ)
    data = json.loads(SET.read_text(encoding="utf-8"))
    manifest_path = OUTPUT.with_name("self_authored.manifest.json")
    if not manifest_path.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "set_sha256": hashlib.sha256(SET.read_bytes()).hexdigest(),
            "config": "retrieval 24, 3 candidates, 1 repair, clarify on abstain (Qwen helper)",
            "models": {model.name: model.digest for model in (ARCTIC, QWEN)},
            "prompts": {kind: [v, template_sha256(kind)] for kind, v in PROMPT_VERSIONS.items()},
            "git": {"commit": _git_commit(), "dirty": _git_dirty()},
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    done = {r["id"] for r in load_jsonl_records(OUTPUT)}
    cache, lock = JsonDiskCache(CACHE), asyncio.Lock()
    for index, item in enumerate(data["items"]):
        if item["id"] in done:
            continue
        pseudo = pseudo_item(index, item)
        reading_shas = {}
        if item["kind"] == "ambiguous":
            for reading in item["readings"]:
                reading_shas[reading["id"]] = result_sha(
                    await run_sql(item["db_id"], reading["sql"], values)
                )
        first = await run_item(pseudo, "self_authored", values, cache, lock, clarify=True)
        record = {
            "id": item["id"],
            "partition": item["partition"],
            "kind": item["kind"],
            "category": item.get("category"),
            "first_status": first["status"],
            "first_reason": first["reason"],
            "first_correct": first["final_ex_corrected"] == 1,
            "first_reading": matched_reading(first["selected_result_sha256"], reading_shas),
            "asked": first["status"] == "needs_clarification",
            "helper_options": len((first.get("clarification") or {}).get("options") or []),
            "helper_calls": [c for c in first["calls"] if c["role"] == "clarify"],
            "seconds": first["seconds"],
            "usage": first["usage"],
        }
        final = first
        if record["asked"]:
            question = f"{item['question']}\nClarification: {item['reply']}"
            final = await run_item(pseudo, "self_authored", values, cache, lock, question=question)
            record |= {"resume_seconds": final["seconds"], "resume_usage": final["usage"]}
        record |= {
            "final_status": final["status"],
            "final_correct": final["final_ex_corrected"] == 1,
            "final_reading": matched_reading(final["selected_result_sha256"], reading_shas),
        }
        append_jsonl_record(OUTPUT, record)
        print(json.dumps({k: record[k] for k in ("id", "first_status", "asked", "final_correct")}))
    return len(data["items"])


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Ask rates, false asks and outcomes per partition and kind (non-oracle simulation)."""
    out: dict[str, Any] = {}
    for partition in ("tuning", "evaluation"):
        for kind in ("ambiguous", "clear"):
            rows = [r for r in records if r["partition"] == partition and r["kind"] == kind]
            if not rows:
                continue
            asked = [r for r in rows if r["asked"]]
            helper = [c["seconds"] for r in asked for c in r["helper_calls"] if c.get("seconds")]
            entry = {
                "n": len(rows),
                "asked": len(asked),
                "answered_without_asking": sum(r["first_status"] == "answered" for r in rows),
                "correct_without_asking": sum(r["first_correct"] for r in rows),
                "correct_final": sum(r["final_correct"] for r in rows),
                "asked_then_correct": sum(r["final_correct"] for r in asked),
                "asked_then_wrong": sum(not r["final_correct"] for r in asked),
                "helper_valid_options": sum(r["helper_options"] > 0 for r in asked),
                "helper_median_seconds": round(statistics.median(helper), 3) if helper else None,
            }
            if kind == "ambiguous":
                entry["first_reading"] = _counts(r["first_reading"] for r in rows)
                entry["final_reading"] = _counts(r["final_reading"] for r in rows)
            out[f"{partition}_{kind}"] = entry
    return out


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    print(json.dumps({"status": "complete", "items": asyncio.run(run())}))
