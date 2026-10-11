"""Run the local E0 development-slice evaluation.

Raw records are written under ignored `results/E0_smoke/raw/`. Tracked summaries
must not contain prompts, generated SQL, gold SQL, credentials or result rows.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
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
from sqlwarden.catalog import schema_mapping
from sqlwarden.evaluation import (
    EvaluationError,
    append_jsonl_record,
    build_prompt,
    generate_item,
    load_jsonl_records,
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
        "generation_timeout_seconds": 120,
        "total_timeout_seconds": 150,
    },
    "arctic": {
        "name": "arctic",
        "alias": "sqlwarden-arctic-text2sql-r1-7b-q4km-ctx8192:smoke-v1",
        "digest": "d4e34b35065d29da2566b3b201d9e6bd54d005c565e1e182a9e318086168b19d",
        "context_tokens": 8192,
        "max_output_tokens": 1024,
        "generation_timeout_seconds": 120,
        "total_timeout_seconds": 150,
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
    return schema_mapping(db_id, audit, descriptions_root=DESCRIPTIONS)


def build_items(limit: int | None = None) -> list[dict[str, Any]]:
    protocol = load_json(PROTOCOL)
    gold_manifest = load_json(GOLD)
    tracks = load_tracks(DATA)
    _, audit = load_specs()
    by_id = {item["question_id"]: item for item in gold_manifest["usable_items"]}
    evidence_sha256 = gold_manifest["evidence"]["sha256"]
    label_sha256 = hashlib.sha256(GOLD.read_bytes()).hexdigest()
    git_commit = _git_commit()
    git_dirty = _git_dirty()
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
                "data_sha256": evidence_sha256,
                "label_sha256": label_sha256,
                "git_commit": git_commit,
                "git_dirty": git_dirty,
            }
        )
    return items


async def run_item(model_name: str, provider, item: dict[str, Any], values: dict[str, str]) -> dict:
    config = MODELS[model_name]
    try:
        async with asyncio.timeout(config["total_timeout_seconds"]):
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
    except TimeoutError:
        return score_execution(
            expected_resume_record(model_name, item) | {"status": "generated", "reason": "ok"},
            {"status": "failed", "reason": "total_timeout"},
            gold_rows=[],
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
        manifest = build_run_manifest(model_name, items, protocol)
        manifest_path = RAW / model_name / "manifest.json"
        jsonl_path = RAW / model_name / "records.jsonl"
        raw_paths = [RAW / model_name / f"{item['question_id']}.json" for item in items]
        jsonl_by_id = {}
        if resume:
            if manifest_path.exists():
                validate_resume_manifest(load_json(manifest_path), manifest)
            jsonl_by_id = {
                record["question_id"]: record
                for record in load_jsonl_records(jsonl_path)
                if record.get("model") == model_name and type(record.get("question_id")) is int
            }
        elif (
            manifest_path.exists()
            or jsonl_path.exists()
            or any(path.exists() for path in raw_paths)
        ):
            raise EvaluationError("run records exist")
        else:
            write_atomic_record(manifest_path, manifest)
        try:
            for item in items:
                raw_path = RAW / model_name / f"{item['question_id']}.json"
                expected = expected_resume_record(model_name, item)
                if resume and item["question_id"] in jsonl_by_id:
                    record = jsonl_by_id[item["question_id"]]
                    validate_resume_record(record, expected)
                    records.append(record)
                    continue
                if resume and raw_path.exists():
                    record = load_json(raw_path)
                    validate_resume_record(record, expected)
                    records.append(record)
                    continue
                record = await run_item(model_name, provider, item, values)
                write_atomic_record(raw_path, record)
                append_jsonl_record(jsonl_path, record)
                records.append(record)
        finally:
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


PROVENANCE_KEYS = (
    "question_id",
    "db_id",
    "model",
    "model_alias",
    "model_digest",
    "prompt_sha256",
    "schema_sha256",
    "data_sha256",
    "label_sha256",
    "git_commit",
    "git_dirty",
)


def expected_resume_record(model_name: str, item: dict[str, Any]) -> dict[str, Any]:
    config = MODELS[model_name]
    messages = build_prompt(item["question"], item["schema_text"], model=config["name"])
    return {
        "question_id": item["question_id"],
        "db_id": item["db_id"],
        "model": config["name"],
        "model_alias": config["alias"],
        "model_digest": config["digest"],
        "prompt_sha256": _hash_json(messages),
        "schema_sha256": hashlib.sha256(item["schema_text"].encode("utf-8")).hexdigest(),
        "data_sha256": item["data_sha256"],
        "label_sha256": item["label_sha256"],
        "git_commit": item["git_commit"],
        "git_dirty": item["git_dirty"],
    }


def validate_resume_record(record: dict[str, Any], expected: dict[str, Any]) -> None:
    if any(record.get(key) != expected.get(key) for key in PROVENANCE_KEYS):
        raise EvaluationError("resume provenance mismatch")


def build_run_manifest(
    model_name: str, items: list[dict[str, Any]], protocol: dict
) -> dict[str, Any]:
    config = MODELS[model_name]
    manifest = {
        "format_version": 1,
        "protocol": {
            "path": "docs/e0-protocol.json",
            "dev_count": len(items),
            "full_dev_count": len(protocol["split"]["dev_ids"]),
            "dev_id_sha256": protocol["split"]["dev_id_sha256"],
            "selected_id_sha256": _hash_json([item["question_id"] for item in items]),
        },
        "model": {
            "name": config["name"],
            "alias": config["alias"],
            "digest": config["digest"],
            "context_tokens": config["context_tokens"],
            "max_output_tokens": config["max_output_tokens"],
            "generation_timeout_seconds": config["generation_timeout_seconds"],
            "total_timeout_seconds": config["total_timeout_seconds"],
        },
        "git": {
            "commit": items[0]["git_commit"] if items else _git_commit(),
            "dirty": items[0]["git_dirty"] if items else _git_dirty(),
        },
        "excludes": ["prompts", "generated query text", "gold query text", "rows", "credentials"],
    }
    return manifest | {"run_fingerprint": _hash_json(manifest)}


def validate_resume_manifest(recorded: dict[str, Any], expected: dict[str, Any]) -> None:
    if recorded != expected:
        raise EvaluationError("resume manifest mismatch")


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        raise EvaluationError("git provenance unavailable") from None
    commit = result.stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise EvaluationError("git provenance unavailable")
    return commit


def _git_dirty() -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        raise EvaluationError("git provenance unavailable") from None
    return bool(result.stdout.strip())


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
