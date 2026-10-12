"""Matched fresh base/tuned E9 through the existing guarded agent path.

Launch with restricted evaluation credentials only, never .env.setup:
uv run --env-file .env.california --env-file .env.datasets \
    python -m scripts.run_e9 --model base --split dev --resume
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from scripts.run_matrix import build_items, manifest_for, run_item
from sqlwarden.evaluation import append_jsonl_record, load_jsonl_records, write_atomic_record
from sqlwarden.ollama import LocalModel

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/G6_e9/raw"


def load_generators(path: Path) -> dict[str, LocalModel]:
    data = json.loads(path.read_text(encoding="utf-8"))
    generators = {}
    for name in ["base", "tuned"]:
        source = data[name]
        if (
            source["context_tokens"] != 8192
            or source["max_output_tokens"] != 3072
            or source["quantization"] != "Q4_K_M"
            or not source["alias"].startswith("sqlwarden-")
            or len(source["digest"]) != 64
            or any(letter not in "0123456789abcdef" for letter in source["digest"])
        ):
            raise ValueError("E9 inference contract refused")
        generators[name] = LocalModel(
            **{
                key: source[key]
                for key in ["name", "alias", "digest", "context_tokens", "max_output_tokens"]
            }
        )
    if (
        generators["base"].alias == generators["tuned"].alias
        or generators["base"].digest == generators["tuned"].digest
    ):
        raise ValueError("E9 distinct-model contract refused")
    return generators


def validate_done(records: list[dict], ids: list[int]) -> set[int]:
    done = [record["question_id"] for record in records]
    if len(set(done)) != len(done) or not set(done) <= set(ids):
        raise ValueError("E9 run records refused")
    return set(done)


def check_evaluation_env(values: dict[str, str]) -> None:
    forbidden = {
        "WARDEN_BOOTSTRAP_PASSWORD",
        "WARDEN_TEST_TARGET",
        "PGPASSWORD",
        "ADMIN_DATABASE_URL",
        "APP_DATABASE_URL",
        "SANDBOX_DATABASE_URL",
    }
    if forbidden.intersection(values) or any(key.startswith("WARDEN_SETUP_") for key in values):
        raise ValueError("setup credentials refused by E9")


async def run(model_name: str, split: str, *, resume: bool) -> None:
    values = dict(os.environ)
    check_evaluation_env(values)
    serving = ROOT / "docs/g6-serving-manifest.json"
    generator = load_generators(serving)[model_name]
    items = build_items(split)
    manifest = manifest_for("full_n1", split, items)
    manifest.pop("fingerprint")
    manifest |= {
        "experiment": "E9",
        "generator": asdict(generator),
        "models": {generator.name: generator.digest},
        "quantization": "Q4_K_M",
        "cache": "disabled; every recorded item is fresh inference",
        "serving_sha256": hashlib.sha256(serving.read_bytes()).hexdigest(),
        "runtime_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
    }
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest["fingerprint"] = fingerprint
    if manifest["git"]["dirty"]:
        raise ValueError("E9 requires clean Git provenance")
    path = RAW / split / f"{model_name}.jsonl"
    metadata = path.with_suffix(".manifest.json")
    if resume and metadata.exists():
        if json.loads(metadata.read_text(encoding="utf-8"))["fingerprint"] != fingerprint:
            raise ValueError("E9 resume configuration mismatch")
    elif metadata.exists() or path.exists():
        raise FileExistsError("E9 run output exists; use verified resume")
    else:
        write_atomic_record(metadata, manifest)
    if path.exists():
        # Refuse a partial tail rather than append across an interrupted JSON record.
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                json.loads(line)
    records = load_jsonl_records(path)
    done = validate_done(records, [item["question_id"] for item in items])
    if any(record.get("generator") != generator.name for record in records):
        raise ValueError("E9 recorded generator mismatch")
    lock = asyncio.Lock()
    for item in items:
        if item["question_id"] in done:
            continue
        record = await run_item(item, "full_n1", values, None, lock, generator=generator)
        record |= {"generator": generator.name, "experiment": "E9"}
        if not record["gold_corrected_valid"]:
            raise ValueError("frozen evaluation gold unavailable; run stopped")
        append_jsonl_record(path, record)
        done.add(item["question_id"])
        print(
            f"{model_name}/{split}: {len(done)}/{len(items)} "
            f"status={record['status']} EX={record['final_ex_corrected']}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["base", "tuned"], required=True)
    parser.add_argument("--split", choices=["dev", "held_out"], required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.model, args.split, resume=args.resume))


if __name__ == "__main__":
    main()
