"""Freeze a bounded, database-balanced tokenized training set."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def balanced_sample(records: list[dict], *, limit: int, seed=42) -> list[dict]:
    if limit < 1:
        raise ValueError("positive sample limit required")
    buckets = defaultdict(list)
    for record in records:
        buckets[record["db_id"]].append(record)
    rng = random.Random(seed)
    for name in sorted(buckets):
        buckets[name].sort(key=lambda record: record["source_index"])
        rng.shuffle(buckets[name])
    selected = []
    while any(buckets.values()) and len(selected) < limit:
        for name in sorted(buckets):
            if buckets[name] and len(selected) < limit:
                selected.append(buckets[name].pop())
    return selected


def tokenize(records: list[dict], tokenizer, *, max_length: int) -> tuple[list[dict], int]:
    from training.pilot import response_example

    tokenized, excluded = [], 0
    for record in records:
        prompt = tokenizer.apply_chat_template(
            record["messages"], tokenize=True, add_generation_prompt=True
        )
        response = tokenizer.encode(
            record["completion"] + tokenizer.eos_token, add_special_tokens=False
        )
        try:
            encoded = response_example(
                prompt, response, max_length=max_length, pad_id=tokenizer.pad_token_id
            )
        except ValueError:
            excluded += 1
            continue
        tokenized.append(
            {"source_index": record["source_index"], "db_id": record["db_id"], **encoded}
        )
    if not tokenized:
        raise ValueError("no examples fit the token budget")
    return tokenized, excluded


def main() -> None:
    sys.path.insert(0, str(ROOT))

    from transformers import AutoTokenizer

    from training.pilot import MODEL, REVISION

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL,
        revision=REVISION,
        cache_dir=ROOT / "models/g6/cache",
        trust_remote_code=False,
        local_files_only=True,
    )
    tokenizer.pad_token = tokenizer.eos_token
    directory = ROOT / "data/training"
    manifest = json.loads((ROOT / "docs/training-data-manifest.json").read_text(encoding="utf-8"))
    output = directory / "tokenized"
    output.mkdir()
    report = {
        "seed": 42,
        "model": MODEL,
        "revision": REVISION,
        "max_length": 2048,
        "label_validity": "execution-unverified PostgreSQL conversions",
        "sampling": "seeded round-robin by database after overlength exclusion",
    }
    for split, limit in [("train", 2000), ("validation", 128)]:
        source = directory / f"prepared/{split}.jsonl"
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if source_hash != manifest[f"{split}_sha256"]:
            raise ValueError("prepared data hash mismatch")
        records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        eligible, excluded = tokenize(records, tokenizer, max_length=2048)
        selected = balanced_sample(eligible, limit=limit)
        target = output / f"{split}.jsonl"
        with target.open("x", encoding="utf-8") as handle:
            for record in selected:
                handle.write(json.dumps(record) + "\n")
        report[split] = {
            "source_sha256": source_hash,
            "eligible_count": len(eligible),
            "overlength_excluded": excluded,
            "selected_count": len(selected),
            "per_database": dict(Counter(record["db_id"] for record in selected)),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    with (ROOT / "docs/training-tokenized-manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(
        json.dumps(
            {
                split: {key: value for key, value in report[split].items() if key != "per_database"}
                for split in ["train", "validation"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
