"""Run the local E0 development-slice evaluation.

Raw records are written under ignored `results/E0_smoke/raw/`. Tracked summaries
must not contain prompts, generated SQL, gold SQL, credentials or result rows.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

from scripts.prepare_import_bundle import load_specs
from scripts.validate_gold import (
    ValidationError,
    execute_postgres,
    load_tracks,
    postgres_options,
    transpile_corrected,
)
from sqlwarden.evaluation import (
    EvaluationError,
    generate_item,
    score_execution,
    serialize_schema,
    summarize_model,
    write_atomic_record,
)
from sqlwarden.executor import ExecutorLifecycleError, dataset_password_key, open_dataset_executor
from sqlwarden.guard import DATASET_POLICIES, guard_sql

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/E0_smoke"
RAW = RESULTS / "raw"
SUMMARY = RESULTS / "summary.json"
PROTOCOL = ROOT / "docs/e0-protocol.json"
GOLD = ROOT / "docs/gold-validity-manifest.json"
DATA = ROOT / "data"
DESCRIPTIONS = DATA / "description-corrections/arcwise-fe766045"
OLLAMA = "http://127.0.0.1:11434"

MODELS = {
    "qwen": {
        "name": "qwen",
        "alias": "sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1",
        "digest": "b00066f4a0af314f23919f5644e49e37f8ec7210ecd9cc2ae4236f43ef1d9c2b",
        "context_tokens": 2048,
        "max_output_tokens": 1024,
    },
    "arctic": {
        "name": "arctic",
        "alias": "sqlwarden-arctic-text2sql-r1-7b-q4km-ctx8192:smoke-v1",
        "digest": "d4e34b35065d29da2566b3b201d9e6bd54d005c565e1e182a9e318086168b19d",
        "context_tokens": 8192,
        "max_output_tokens": 1024,
    },
}


class OllamaProvider:
    async def complete(self, messages, *, model_config):
        async with httpx.AsyncClient(
            base_url=OLLAMA,
            timeout=httpx.Timeout(150, connect=3, pool=3),
            trust_env=False,
            follow_redirects=False,
            headers={"Accept-Encoding": "identity"},
        ) as client:
            await _verify_model(client, model_config)
            started = time.perf_counter()
            response = await client.post(
                "/v1/chat/completions",
                json={
                    "model": model_config["alias"],
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": model_config["max_output_tokens"],
                    "stream": False,
                    "seed": 42,
                    "response_format": {"type": "json_object"},
                },
            )
            seconds = round(time.perf_counter() - started, 3)
            if response.status_code != 200:
                raise EvaluationError("model unavailable")
            payload = response.json()
            choice = payload["choices"][0]
            usage = payload.get("usage") or {}
            memory = await _loaded_memory(client, model_config)
            return {
                "content": choice["message"]["content"],
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                },
                "memory": memory,
                "seconds": seconds,
                "model": payload.get("model"),
            }


async def _verify_model(client, model_config):
    tags = (await client.get("/api/tags", timeout=5)).json()
    matches = [
        model for model in tags.get("models", []) if model.get("name") == model_config["alias"]
    ]
    if len(matches) != 1 or matches[0].get("digest") != model_config["digest"]:
        raise EvaluationError("model configuration")
    loaded = (await client.get("/api/ps", timeout=5)).json().get("models", [])
    others = [model for model in loaded if model.get("name") != model_config["alias"]]
    if others:
        raise EvaluationError("another model loaded")


async def _loaded_memory(client, model_config):
    loaded = (await client.get("/api/ps", timeout=5)).json().get("models", [])
    matches = [model for model in loaded if model.get("name") == model_config["alias"]]
    if not matches:
        return {"vram_bytes": None, "size_bytes": None}
    model = matches[0]
    return {
        "vram_bytes": model.get("size_vram"),
        "size_bytes": model.get("size"),
    }


async def unload_model(model_config):
    async with httpx.AsyncClient(base_url=OLLAMA, timeout=30, trust_env=False) as client:
        await client.post(
            "/api/generate",
            json={"model": model_config["alias"], "prompt": "", "stream": False, "keep_alive": 0},
        )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(db_id: str, audit: dict) -> dict:
    descriptions = _load_descriptions(db_id)
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


def _load_descriptions(db_id: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    folder = DESCRIPTIONS / db_id
    for path in folder.glob("*.csv"):
        result[path.stem] = read_description_csv(path)
    return result


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
    raise EvaluationError("description encoding refused")


def build_items(limit: int | None = None) -> list[dict[str, Any]]:
    protocol = load_json(PROTOCOL)
    gold_manifest = load_json(GOLD)
    tracks = load_tracks(DATA)
    _, audit = load_specs()
    by_id = {item["question_id"]: item for item in gold_manifest["usable_items"]}
    selected_ids = protocol["split"]["dev_ids"][:limit]
    schema_cache = {}
    items = []
    for identifier in selected_ids:
        gold_item = by_id[identifier]
        db_id = gold_item["db_id"]
        if db_id not in schema_cache:
            schema_cache[db_id] = serialize_schema(load_schema(db_id, audit), max_bytes=200_000)
        source = tracks["bird_sqlite"][identifier]
        corrected = tracks["arcwise_full"][identifier]
        items.append(
            {
                "question_id": identifier,
                "db_id": db_id,
                "question": corrected.get("question") or source["question"],
                "schema_text": schema_cache[db_id],
                "gold_sql": transpile_corrected(
                    corrected["SQL"], tables=audit["databases"][db_id]["tables"]
                ),
            }
        )
    return items


async def run_item(model_name: str, provider, item: dict[str, Any], values: dict[str, str]) -> dict:
    config = MODELS[model_name]
    record = await generate_item(provider, item, model_config=config)
    if record["status"] != "generated":
        return record
    decision = guard_sql(record["sql"], DATASET_POLICIES[item["db_id"]])
    if not decision.accepted:
        return score_execution(
            record,
            {"status": "blocked", "reason": decision.reason},
            gold_rows=[],
        )
    try:
        password = values[dataset_password_key(item["db_id"])]
        async with open_dataset_executor(item["db_id"], password) as executor:
            execution = await executor.execute(decision.sql)
        gold_rows = await _gold_rows(item, values)
    except (KeyError, ExecutorLifecycleError, ValidationError):
        return score_execution(
            record,
            {"status": "failed", "reason": "execution_failed"},
            gold_rows=[],
        )
    return score_execution(
        record,
        {
            "status": execution.status,
            "reason": execution.reason,
            "rows": list(execution.rows),
        },
        gold_rows=gold_rows,
    )


async def _gold_rows(item: dict[str, Any], values: dict[str, str]):
    import asyncpg

    connection = await asyncpg.connect(**postgres_options(item["db_id"], values))
    try:
        return await execute_postgres(connection, item["gold_sql"])
    finally:
        await connection.close()


async def run_models(model_names: list[str], *, limit: int | None, resume: bool) -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    protocol = load_json(PROTOCOL)
    values = dict(os.environ)
    items = build_items(limit)
    summaries = {}
    for model_name in model_names:
        provider = OllamaProvider()
        records = []
        for item in items:
            raw_path = RAW / model_name / f"{item['question_id']}.json"
            if resume and raw_path.exists():
                records.append(load_json(raw_path))
                continue
            record = await run_item(model_name, provider, item, values)
            write_atomic_record(raw_path, record)
            records.append(record)
        await unload_model(MODELS[model_name])
        summaries[model_name] = summarize_model(
            model_name,
            records,
            protocol
            | {"split": protocol["split"] | {"dev_ids": [item["question_id"] for item in items]}},
            seed=20261008,
            samples=10_000,
        )
    summary = {
        "format_version": 1,
        "protocol": {
            "path": "docs/e0-protocol.json",
            "dev_count": len(items),
            "full_dev_count": len(protocol["split"]["dev_ids"]),
            "dev_id_sha256": protocol["split"]["dev_id_sha256"],
        },
        "models": summaries,
        "raw_records": "results/E0_smoke/raw/<model>/<question_id>.json ignored",
        "excludes": ["prompts", "generated query text", "gold query text", "rows", "credentials"],
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    models = args.model or ["qwen", "arctic"]
    summary = asyncio.run(run_models(models, limit=args.limit, resume=args.resume))
    print(
        json.dumps(
            {
                "status": "complete",
                "models": sorted(summary["models"]),
                "dev_count": summary["protocol"]["dev_count"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
