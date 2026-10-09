"""Deterministic G0 evaluation protocol helpers."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_DEV_COUNT = 100
DEFAULT_SEED = 20261008
DEFAULT_BOOTSTRAP_SAMPLES = 10_000


class ProtocolError(ValueError):
    """Stable refusal for unsafe or inconsistent evaluation protocol inputs."""


def hash_ids(ids: list[int]) -> str:
    payload = json.dumps(list(ids), separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_gold_manifest(path: str | Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ProtocolError("manifest unavailable") from None
    _usable_items(document)
    return document


def build_protocol(
    manifest: dict[str, Any],
    *,
    dev_count: int = DEFAULT_DEV_COUNT,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    items = _usable_items(manifest)
    if dev_count <= 0 or dev_count >= len(items):
        raise ProtocolError("development count refused")
    families = _families(items)
    selected = _select_development_families(families, dev_count=dev_count, seed=seed)
    dev_ids = sorted(identifier for family in selected for identifier in family["ids"])
    all_ids = sorted(item["question_id"] for item in items)
    held_out_ids = sorted(set(all_ids) - set(dev_ids))
    if len(dev_ids) != dev_count or len(dev_ids) + len(held_out_ids) != len(all_ids):
        raise ProtocolError("split coverage failed")
    return {
        "format_version": 1,
        "protocol": "e0-dev-heldout-v1",
        "source": {
            "manifest": "docs/gold-validity-manifest.json",
            "primary_labels": manifest["primary_labels"],
            "primary_descriptions": manifest["primary_descriptions"],
            "alternate_descriptions": manifest["alternate_descriptions"],
            "usable_count": len(items),
            "usable_id_sha256": hash_ids(all_ids),
        },
        "split": {
            "seed": seed,
            "dev_count": len(dev_ids),
            "held_out_count": len(held_out_ids),
            "dev_ids": dev_ids,
            "held_out_ids": held_out_ids,
            "usable_id_sha256": hash_ids(all_ids),
            "dev_id_sha256": hash_ids(dev_ids),
            "held_out_id_sha256": hash_ids(held_out_ids),
            "dev_strata": dict(
                sorted(
                    Counter(
                        _stratum(item) for item in items if item["question_id"] in set(dev_ids)
                    ).items()
                )
            ),
            "held_out_strata": dict(
                sorted(
                    Counter(
                        _stratum(item) for item in items if item["question_id"] in set(held_out_ids)
                    ).items()
                )
            ),
            "family_policy": "family_id_when_present_else_item_id",
        },
        "metrics": {
            "bootstrap": {
                "statistic": "accuracy",
                "samples": DEFAULT_BOOTSTRAP_SAMPLES,
                "seed": seed,
                "interval": "percentile_95",
                "empty_policy": "null_interval",
            }
        },
        "contains": "item IDs, database IDs, difficulty labels and hashes only",
        "excludes": [
            "natural-language prompt text",
            "query text",
            "answer payloads",
            "secret values",
        ],
    }


def bootstrap_accuracy_interval(
    outcomes: list[bool], *, samples: int = 1000, seed: int = DEFAULT_SEED
) -> dict[str, float | int | None]:
    if samples <= 0:
        raise ProtocolError("bootstrap samples refused")
    if not outcomes:
        return {"n": 0, "mean": None, "low": None, "high": None}
    values = [1.0 if item else 0.0 for item in outcomes]
    observed = sum(values) / len(values)
    if observed in {0.0, 1.0}:
        return {"n": len(values), "mean": observed, "low": observed, "high": observed}
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        estimates.append(sum(rng.choice(values) for _ in values) / len(values))
    estimates.sort()
    low_index = int(0.025 * (samples - 1))
    high_index = int(0.975 * (samples - 1))
    return {
        "n": len(values),
        "mean": round(observed, 6),
        "low": round(estimates[low_index], 6),
        "high": round(estimates[high_index], 6),
    }


def _usable_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("primary_labels") != "arcwise_full_verified_corrected_pool":
        raise ProtocolError("primary labels refused")
    items = manifest.get("usable_items")
    if not isinstance(items, list):
        raise ProtocolError("usable items missing")
    expected_count = manifest.get("validity", {}).get("usable_count")
    if expected_count != len(items):
        raise ProtocolError("usable count mismatch")
    seen: set[int] = set()
    for item in items:
        identifier = item.get("question_id")
        if not isinstance(identifier, int) or identifier in seen:
            raise ProtocolError("duplicate or invalid question id")
        seen.add(identifier)
        if not isinstance(item.get("db_id"), str) or not isinstance(item.get("difficulty"), str):
            raise ProtocolError("usable item metadata missing")
    return items


def _families(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[str(item.get("family_id", item["question_id"]))].append(item)
    families = []
    for family_id, members in grouped.items():
        strata = {_stratum(item) for item in members}
        if len(strata) != 1:
            raise ProtocolError("family crosses strata")
        families.append(
            {
                "family_id": family_id,
                "stratum": next(iter(strata)),
                "ids": sorted(item["question_id"] for item in members),
            }
        )
    return families


def _select_development_families(
    families: list[dict[str, Any]], *, dev_count: int, seed: int
) -> list[dict[str, Any]]:
    stratum_sizes = Counter()
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in families:
        stratum_sizes[family["stratum"]] += len(family["ids"])
        by_stratum[family["stratum"]].append(family)
    targets = _stratum_targets(stratum_sizes, dev_count)
    selected: list[dict[str, Any]] = []
    selected_ids = 0
    deferred: list[dict[str, Any]] = []
    for stratum, choices in sorted(by_stratum.items()):
        target = targets[stratum]
        current = 0
        for family in sorted(choices, key=lambda family: _stable_rank(seed, family["family_id"])):
            size = len(family["ids"])
            if current + size <= target and selected_ids + size <= dev_count:
                selected.append(family)
                current += size
                selected_ids += size
            else:
                deferred.append(family)
    for family in sorted(deferred, key=lambda family: _stable_rank(seed, family["family_id"])):
        size = len(family["ids"])
        if selected_ids + size <= dev_count:
            selected.append(family)
            selected_ids += size
        if selected_ids == dev_count:
            break
    if selected_ids != dev_count:
        raise ProtocolError("exact split unavailable with family grouping")
    return selected


def _stratum_targets(stratum_sizes: Counter[str], dev_count: int) -> dict[str, int]:
    total = sum(stratum_sizes.values())
    targets = {stratum: (dev_count * size) // total for stratum, size in stratum_sizes.items()}
    remaining = dev_count - sum(targets.values())
    ranked = sorted(
        stratum_sizes,
        key=lambda stratum: (
            -((dev_count * stratum_sizes[stratum]) % total),
            stratum,
        ),
    )
    for stratum in ranked[:remaining]:
        targets[stratum] += 1
    return targets


def _stable_rank(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def _stratum(item: dict[str, Any]) -> str:
    return f"{item['db_id']}::{item['difficulty']}"
