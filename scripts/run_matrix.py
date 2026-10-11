"""Run one E1-E8 matrix condition under inference contract v2 (D-075).

Raw per-item records (they contain generated SQL) go to ignored
`results/G3_matrix/raw/<split>/<condition>.jsonl`; tracked summaries come from
`scripts/build_matrix_report.py`. Gold SQL is executed only after the agent finishes,
for offline scoring. Use restricted evaluation credentials only, never `.env.setup`:

uv run --env-file .env.california --env-file .env.datasets \
    python -m scripts.run_matrix --condition ret_n3_k1 --split dev --resume
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import asyncpg

from scripts.messy_schema import SEED, build_mapping, leaked_names, messy_catalog, translate
from scripts.prepare_import_bundle import load_specs
from scripts.run_e0 import _git_commit, _git_dirty
from scripts.validate_gold import (
    execute_postgres,
    load_tracks,
    postgres_options,
    transpile_corrected,
)
from sqlwarden.agent import AgentConfig, run_agent
from sqlwarden.cache import JsonDiskCache
from sqlwarden.catalog import AUDIT_SHA, load_catalog
from sqlwarden.comparator import compare_ex
from sqlwarden.evaluation import (
    EvaluationError,
    append_jsonl_record,
    extract_final_sql,
    load_jsonl_records,
    write_atomic_record,
)
from sqlwarden.executor import QueryResult, dataset_password_key, open_dataset_executor
from sqlwarden.guard import DATASET_POLICIES
from sqlwarden.ollama import ARCTIC, QWEN, OllamaAgentProvider
from sqlwarden.prompts import PROMPT_VERSIONS, template_sha256
from sqlwarden.schema import SchemaCatalog
from sqlwarden.voting import CandidateResult, vote

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/G3_matrix"
RAW = RESULTS / "raw"
CACHE = RESULTS / "cache"
PROTOCOL = ROOT / "docs/e0-protocol.json"
GOLD = ROOT / "docs/gold-validity-manifest.json"
ORIGINAL_VALIDITY = ROOT / ".tools/gold-validation/evidence.json"

BASE = AgentConfig(
    candidates=1,
    max_repairs=0,
    retrieve_columns=24,
    clarify_on_abstain=False,
    explain=False,
    total_timeout_seconds=600,
)
VOTED = replace(BASE, candidates=3, max_repairs=1)
CONDITIONS: dict[str, dict[str, Any]] = {
    "full_n1": {"config": replace(BASE, full_schema=True), "input": "corrected"},
    "ret_n3_k1": {"config": VOTED, "input": "corrected"},
    "orig_n3_k1": {"config": VOTED, "input": "original"},
    "messy_n1": {"config": BASE, "input": "corrected", "messy": True},
    "ret_n3_k1_replay": {"config": VOTED, "input": "corrected", "replay": True},
    "clarify_oracle": {"config": VOTED, "input": "original", "base": "orig_n3_k1"},
    "self_authored": {"config": VOTED, "input": "corrected"},
}


def text_of(question: str, evidence: str) -> str:
    """Contract v2 input: corrected BIRD evidence followed by the question."""
    question, evidence = question.strip(), (evidence or "").strip()
    return f"{evidence}\n{question}" if evidence else question


def build_items(split: str) -> list[dict[str, Any]]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    ids = protocol["split"]["dev_ids" if split == "dev" else "held_out_ids"]
    usable = {
        item["question_id"]: item
        for item in json.loads(GOLD.read_text(encoding="utf-8"))["usable_items"]
    }
    validity = {
        outcome["question_id"]: outcome["status"]
        for outcome in json.loads(ORIGINAL_VALIDITY.read_text(encoding="utf-8"))["tracks"][
            "bird_pg"
        ]["outcomes"]
    }
    tracks = load_tracks(ROOT / "data")
    _, audit = load_specs()
    items = []
    for question_id in ids:
        meta = usable[question_id]
        db_id = meta["db_id"]
        source = tracks["bird_sqlite"][question_id]
        corrected = tracks["arcwise_full"][question_id]
        corrected_text = text_of(
            corrected.get("question") or source["question"], corrected.get("evidence")
        )
        original_text = text_of(source["question"], source.get("evidence"))
        items.append(
            {
                "question_id": question_id,
                "db_id": db_id,
                "difficulty": meta["difficulty"],
                "ambiguity_candidate": meta["ambiguity_candidate"],
                "corrected_text": corrected_text,
                "original_text": original_text,
                "input_changed": corrected_text != original_text,
                "gold_corrected": transpile_corrected(
                    corrected["SQL"], tables=audit["databases"][db_id]["tables"]
                ),
                "gold_original": tracks["bird_pg"][question_id]["SQL"]
                if validity.get(question_id) == "matched"
                else None,
                "original_label_status": validity.get(question_id, "missing"),
            }
        )
    return items


class TranslatingProvider:
    """E4: the model writes messy names; real names reach the guard and executor."""

    def __init__(self, inner: OllamaAgentProvider, mapping) -> None:
        self.inner = inner
        self.mapping = mapping
        self.translated = 0
        self.untranslated = 0

    async def complete(self, messages, *, model_config):
        response = await self.inner.complete(messages, model_config=model_config)
        try:
            sql = translate(extract_final_sql(response["content"]), self.mapping)
        except Exception:
            self.untranslated += 1
            return response
        self.translated += 1
        return response | {"content": f"```sql\n{sql}\n```"}


async def gold_rows(db_id: str, sql: str | None, values: dict[str, str]):
    if sql is None:
        return None
    connection = await asyncpg.connect(**postgres_options(db_id, values))
    try:
        return await execute_postgres(connection, sql)
    except Exception:
        return None
    finally:
        await connection.close()


def ex(result: QueryResult | None, gold) -> int | None:
    if gold is None:
        return None
    if result is None:
        return 0
    reference = QueryResult("ok", "ok", rows=tuple(tuple(row) for row in gold))
    return compare_ex(result, reference).score


def result_sha(result: QueryResult) -> str | None:
    if result.status != "ok":
        return None
    text = json.dumps([list(result.columns), [list(row) for row in result.rows]], default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def derived_outcomes(candidates: list[CandidateResult], gold_c, gold_o) -> dict[str, Any]:
    """Re-score the same generations as smaller loop settings (same-input ablation)."""

    def outcome(chosen: list[tuple[int, QueryResult]]) -> dict[str, Any]:
        voted = vote(
            [
                CandidateResult(index, "ok" if r.status == "ok" else "failed", r.reason, result=r)
                for index, r in chosen
            ],
            requested=len(chosen),
        )
        selected = voted.selected.result if voted.status == "answered" else None
        return {
            "status": voted.status,
            "reason": voted.reason,
            "agreement": voted.agreement,
            "ex_corrected": ex(selected, gold_c),
            "ex_original": ex(selected, gold_o),
        }

    first = [(c.index, c.attempts[0][1]) for c in candidates if c.attempts]
    final = [(c.index, c.attempts[-1][1]) for c in candidates if c.attempts]
    if len(first) != len(candidates):
        return {}
    derived = {"n1_k0": outcome(first[:1]), "n1_k1": outcome(final[:1])}
    if len(candidates) > 1:
        derived |= {"n3_k0": outcome(first), "n3_k1": outcome(final)}
    return derived


async def run_item(
    item: dict[str, Any],
    condition: str,
    values: dict[str, str],
    cache: JsonDiskCache,
    lock: asyncio.Lock,
    *,
    question: str | None = None,
    clarify: bool = False,
) -> dict[str, Any]:
    spec = CONDITIONS[condition]
    db_id = item["db_id"]
    catalog = load_catalog(db_id)
    provider = OllamaAgentProvider(
        fingerprints=(catalog.fingerprint(), AUDIT_SHA),
        cache=cache,
        helper=QWEN if clarify else None,
        lock=lock,
        timeout_seconds=300,
    )
    agent_catalog: SchemaCatalog = catalog
    agent_provider: Any = provider
    extra: dict[str, Any] = {}
    if spec.get("messy"):
        mapping = build_mapping(catalog)
        agent_catalog = messy_catalog(catalog, mapping)
        provider.schema_sha256 = agent_catalog.fingerprint()
        agent_provider = TranslatingProvider(provider, mapping.reverse())
        extra["messy_leaked_names"] = leaked_names(
            SchemaCatalog.serialize(agent_catalog.scope_all(), max_bytes=10**6), catalog
        )
    config = replace(spec["config"], clarify_on_abstain=clarify)
    text = question or item[f"{spec['input']}_text"]
    started = time.perf_counter()
    async with open_dataset_executor(db_id, values[dataset_password_key(db_id)]) as executor:
        result = await run_agent(
            text,
            catalog=agent_catalog,
            provider=agent_provider,
            executor=executor,
            policy=DATASET_POLICIES[db_id],
            config=config,
            model=ARCTIC.name,
        )
    seconds = round(time.perf_counter() - started, 3)
    gold_c = await gold_rows(db_id, item["gold_corrected"], values)
    gold_o = await gold_rows(db_id, item["gold_original"], values)
    selected = (
        result.vote.selected.result
        if result.status == "answered" and result.vote and result.vote.selected
        else None
    )
    if isinstance(agent_provider, TranslatingProvider):
        extra |= {
            "translated": agent_provider.translated,
            "untranslated": agent_provider.untranslated,
        }
    return {
        "question_id": item["question_id"],
        "db_id": db_id,
        "difficulty": item["difficulty"],
        "ambiguity_candidate": item["ambiguity_candidate"],
        "input_changed": item["input_changed"],
        "condition": condition,
        "status": result.status,
        "reason": result.reason,
        "vote": None
        if result.vote is None
        else {
            "status": result.vote.status,
            "reason": result.vote.reason,
            "agreement": result.vote.agreement,
        },
        "clarification": result.clarification,
        "final_ex_corrected": ex(selected, gold_c),
        "selected_result_sha256": result_sha(selected) if selected else None,
        "final_ex_original": ex(selected, gold_o),
        "gold_corrected_valid": gold_c is not None,
        "gold_original_valid": gold_o is not None,
        "original_label_status": item["original_label_status"],
        "derived": derived_outcomes(list(result.candidates), gold_c, gold_o),
        "candidates": [
            {
                "index": c.index,
                "status": c.status,
                "reason": c.reason,
                "repairs": c.repairs,
                "attempts": [
                    {
                        "sql": sql,
                        "status": r.status,
                        "reason": r.reason,
                        "rows": len(r.rows),
                        "result_sha256": result_sha(r),
                        "ex_corrected": ex(r, gold_c),
                        "ex_original": ex(r, gold_o),
                    }
                    for sql, r in c.attempts
                ],
            }
            for c in result.candidates
        ],
        "trace": [[event.step, event.status, event.reason] for event in result.trace],
        "usage": provider.summary(),
        "calls": provider.calls,
        "seconds": seconds,
        **extra,
    }


def manifest_for(condition: str, split: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    spec = CONDITIONS[condition]
    manifest = {
        "format_version": 1,
        "contract": "v2",
        "condition": condition,
        "split": split,
        "config": asdict(spec["config"]),
        "input": spec["input"],
        "messy_seed": SEED if spec.get("messy") else None,
        "item_id_sha256": _sha([item["question_id"] for item in items]),
        "models": {model.name: model.digest for model in (ARCTIC, QWEN)},
        "prompts": {kind: [v, template_sha256(kind)] for kind, v in PROMPT_VERSIONS.items()},
        "protocol_sha256": _file_sha(PROTOCOL),
        "gold_manifest_sha256": _file_sha(GOLD),
        "original_validity_sha256": _file_sha(ORIGINAL_VALIDITY),
        "audit_sha256": AUDIT_SHA,
        "git": {"commit": _git_commit(), "dirty": _git_dirty()},
        "excludes_from_tracked_outputs": ["sql", "question text", "rows", "credentials"],
    }
    return manifest | {"fingerprint": _sha(manifest)}


async def run_condition(condition: str, split: str, *, limit: int | None, resume: bool) -> int:
    values = dict(os.environ)
    items = build_items(split)[:limit]
    path = RAW / split / f"{condition}.jsonl"
    manifest_path = RAW / split / f"{condition}.manifest.json"
    manifest = manifest_for(condition, split, items)
    if resume and manifest_path.exists():
        recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
        if recorded["fingerprint"] != manifest["fingerprint"]:
            raise EvaluationError("resume manifest mismatch")
    elif path.exists() or manifest_path.exists():
        raise EvaluationError("run records exist")
    else:
        write_atomic_record(manifest_path, manifest)
    done = {record["question_id"] for record in load_jsonl_records(path)}
    cache = JsonDiskCache(CACHE)
    lock = asyncio.Lock()
    spec = CONDITIONS[condition]
    base = (
        {r["question_id"]: r for r in load_jsonl_records(RAW / split / f"{spec['base']}.jsonl")}
        if spec.get("base")
        else {}
    )
    for item in items:
        if item["question_id"] in done:
            continue
        if spec.get("base"):
            record = await clarify_oracle_item(
                item, base.get(item["question_id"]), values, cache, lock
            )
        else:
            record = await run_item(item, condition, values, cache, lock)
        if spec.get("replay"):
            # The cache refuses outputs containing secret/gold terms, so a few
            # questions cannot be replayed; record that instead of hiding it.
            record["fully_replayed"] = record["usage"]["live_calls"] == 0
        append_jsonl_record(path, record)
        print(
            json.dumps(
                {
                    "id": item["question_id"],
                    "status": record["status"],
                    "ex": record.get("final_ex_corrected"),
                    "s": record.get("seconds"),
                }
            ),
            flush=True,
        )
    return len(items)


async def clarify_oracle_item(item, base_record, values, cache, lock) -> dict[str, Any]:
    """E7: when the original wording abstained, ask the helper, then answer with an
    oracle reply (the corrected wording). Labelled oracle-assisted, never mixed in."""
    if base_record is None or base_record["status"] != "abstained":
        return {
            "question_id": item["question_id"],
            "condition": "clarify_oracle",
            "status": "not_asked",
            "base_status": None if base_record is None else base_record["status"],
            "ambiguity_candidate": item["ambiguity_candidate"],
            "input_changed": item["input_changed"],
        }
    asked = await run_item(item, "clarify_oracle", values, cache, lock, clarify=True)
    options = (asked.get("clarification") or {}).get("options") or []
    record = {
        "question_id": item["question_id"],
        "db_id": item["db_id"],
        "condition": "clarify_oracle",
        "status": "asked",
        "ambiguity_candidate": item["ambiguity_candidate"],
        "input_changed": item["input_changed"],
        "helper_valid": bool(options),
        "helper_options": len(options),
        "helper_calls": [call for call in asked["calls"] if call["role"] == "clarify"],
        "ask_seconds": asked["seconds"],
    }
    if not item["input_changed"]:
        return record | {"oracle": "no_intended_meaning_recorded"}
    question = f"{item['original_text']}\nClarification: {item['corrected_text']}"
    resumed = await run_item(item, "clarify_oracle", values, cache, lock, question=question)
    return record | {
        "oracle": "corrected_wording",
        "final_status": resumed["status"],
        "final_ex_corrected": resumed["final_ex_corrected"],
        "resume_seconds": resumed["seconds"],
        "resume_usage": resumed["usage"],
    }


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--split", choices=["dev", "held_out"], required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    count = asyncio.run(
        run_condition(args.condition, args.split, limit=args.limit, resume=args.resume)
    )
    print(json.dumps({"status": "complete", "condition": args.condition, "items": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
