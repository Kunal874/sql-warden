"""Build compact, tracked E1-E8 evidence from the ignored matrix run records.

Offline only: reads results/G3_matrix/raw/**.jsonl and writes summary/failure files,
docs/EVAL.md and docs/RESUME.md. Tracked outputs hold IDs, counts and rates only,
never SQL, question text, rows or credentials.

`--freeze-threshold` writes docs/e8-threshold.json from the dev slice once, before
any held-out run, and refuses to overwrite it.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.run_matrix import RAW, RESULTS
from sqlwarden.evaluation import _bootstrap_difference_interval, load_jsonl_records
from sqlwarden.protocol import bootstrap_accuracy_interval, clopper_pearson

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/e0-protocol.json"
THRESHOLD = ROOT / "docs/e8-threshold.json"
SUMMARY = RESULTS / "summary.json"
FAILURES = RESULTS / "failure-labels.json"
SEED, SAMPLES = 20261008, 10_000
THRESHOLDS = (("1/3", 1 / 3), ("2/3", 2 / 3), ("1", 1.0))
VIEWS = {
    "full_n1": ("full_n1", "n1_k0"),
    "ret_n1_k0": ("ret_n3_k1", "n1_k0"),
    "ret_n1_k1": ("ret_n3_k1", "n1_k1"),
    "ret_n3_k0": ("ret_n3_k1", "n3_k0"),
    "ret_n3_k1": ("ret_n3_k1", "n3_k1"),
    "orig_n1_k0": ("orig_n3_k1", "n1_k0"),
    "orig_n3_k1": ("orig_n3_k1", "n3_k1"),
    "messy_n1": ("messy_n1", "n1_k0"),
}
COMPARISONS = {
    "retrieval_vs_full_schema": ("ret_n1_k0", "full_n1"),
    "repair_effect": ("ret_n1_k1", "ret_n1_k0"),
    "voting_effect_with_repair": ("ret_n3_k1", "ret_n1_k1"),
    "voting_effect_without_repair": ("ret_n3_k0", "ret_n1_k0"),
    "full_loop_vs_full_schema": ("ret_n3_k1", "full_n1"),
    "messy_vs_clean_names": ("messy_n1", "ret_n1_k0"),
}


def load(split: str, condition: str) -> dict[int, dict[str, Any]]:
    return {
        record["question_id"]: record
        for record in load_jsonl_records(RAW / split / f"{condition}.jsonl")
    }


def view_of(records: dict[int, dict[str, Any]], key: str) -> dict[int, dict[str, Any]]:
    return {qid: r["derived"][key] for qid, r in records.items() if key in r.get("derived", {})}


def condition_metrics(view: dict[int, dict[str, Any]], *, ids: list[int]) -> dict[str, Any]:
    outcomes = [view.get(qid, {}).get("ex_corrected") == 1 for qid in ids]
    answered = [qid for qid in ids if view.get(qid, {}).get("status") == "answered"]
    correct_answered = sum(1 for qid in answered if view[qid].get("ex_corrected") == 1)
    n, correct = len(ids), sum(outcomes)
    return {
        "n": n,
        "pending": sum(1 for qid in ids if qid not in view),
        "ex": {
            "count": correct,
            "rate": _rate(correct, n),
            "bootstrap": bootstrap_accuracy_interval(outcomes, samples=SAMPLES, seed=SEED),
            "exact": clopper_pearson(correct, n),
        },
        "answered": {"count": len(answered), "rate": _rate(len(answered), n)},
        "answered_only_ex": {
            "count": correct_answered,
            "rate": _rate(correct_answered, len(answered)),
        },
        "abstained": sum(1 for qid in ids if view.get(qid, {}).get("status") == "abstained"),
    }


def paired(left: dict, right: dict, *, ids: list[int]) -> dict[str, Any]:
    rows = [
        (left.get(qid, {}).get("ex_corrected") == 1, right.get(qid, {}).get("ex_corrected") == 1)
        for qid in ids
    ]
    left_only = sum(1 for a, b in rows if a and not b)
    right_only = sum(1 for a, b in rows if b and not a)
    return {
        "n": len(rows),
        "left_only": left_only,
        "right_only": right_only,
        "both": sum(1 for a, b in rows if a and b),
        "neither": sum(1 for a, b in rows if not a and not b),
        "difference": round((left_only - right_only) / len(rows), 6) if rows else None,
        "ci": _bootstrap_difference_interval(rows, samples=SAMPLES, seed=SEED),
    }


def accuracy_coverage_curve(view: dict, *, ids: list[int]) -> list[dict[str, Any]]:
    curve = []
    for label, value in THRESHOLDS:
        covered = [
            qid
            for qid in ids
            if view.get(qid, {}).get("status") == "answered"
            and view[qid].get("agreement", 0) >= value - 1e-9
        ]
        correct = sum(1 for qid in covered if view[qid].get("ex_corrected") == 1)
        curve.append(
            {
                "threshold": label,
                "covered": len(covered),
                "coverage": _rate(len(covered), len(ids)),
                "selective_ex": _rate(correct, len(covered)),
                "end_to_end_ex": _rate(correct, len(ids)),
            }
        )
    return curve


def select_threshold(curve: list[dict[str, Any]]) -> str:
    """Predefined (D-078): best selective EX with dev coverage >= 50%; ties -> lower."""
    eligible = [p for p in curve if (p["coverage"] or 0) >= 0.5 and p["selective_ex"] is not None]
    if not eligible:
        return "1/3"
    best = max(p["selective_ex"] for p in eligible)
    return next(p["threshold"] for p in eligible if p["selective_ex"] == best)


def phase_rates(records: dict[int, dict[str, Any]], *, first_only: bool) -> dict[str, Any]:
    candidates = [
        c
        for r in records.values()
        for c in (r["candidates"][:1] if first_only else r["candidates"])
    ]
    generated = [c for c in candidates if c["attempts"]]
    accepted = [c for c in generated if c["attempts"][0]["status"] != "blocked"]
    executed = [c for c in generated if c["attempts"][0]["status"] == "ok"]
    return {
        "candidates": len(candidates),
        "sql_extracted": _rate(len(generated), len(candidates)),
        "guard_accepted": _rate(len(accepted), len(candidates)),
        "executed": _rate(len(executed), len(candidates)),
        "first_attempt_failure_reasons": dict(
            Counter(
                c["attempts"][0]["reason"] if c["attempts"] else c["reason"]
                for c in candidates
                if not c["attempts"] or c["attempts"][0]["status"] != "ok"
            ).most_common()
        ),
    }


def label_rescoring(view: dict, records: dict[int, dict[str, Any]], *, ids: list[int]) -> dict:
    """E1/E3: the same predictions scored against original and corrected labels."""
    scored = [qid for qid in ids if view.get(qid, {}).get("ex_original") is not None]
    corrected = sum(1 for qid in scored if view[qid].get("ex_corrected") == 1)
    original = sum(1 for qid in scored if view[qid].get("ex_original") == 1)
    return {
        "scored_both": len(scored),
        "excluded_original_label": dict(
            Counter(
                records[qid].get("original_label_status")
                for qid in ids
                if qid in records and qid not in scored
            )
        ),
        "correct_under_corrected": corrected,
        "correct_under_original": original,
        "correct_only_under_corrected": sum(
            1
            for qid in scored
            if view[qid].get("ex_corrected") == 1 and view[qid].get("ex_original") != 1
        ),
        "correct_only_under_original": sum(
            1
            for qid in scored
            if view[qid].get("ex_original") == 1 and view[qid].get("ex_corrected") != 1
        ),
    }


def failure_category(record: dict[str, Any], key: str = "n3_k1") -> str | None:
    outcome = record.get("derived", {}).get(key)
    if not outcome or outcome.get("ex_corrected") == 1:
        return None
    if outcome["status"] == "answered":
        return "wrong_result"
    if outcome["reason"] == "vote_tie":
        return "abstained_disagreement"
    reasons = Counter(
        (c["attempts"][-1]["reason"] if c["attempts"] else c["reason"])
        for c in record["candidates"]
    )
    top = reasons.most_common(1)[0][0] if reasons else "unknown"
    return {
        "function_not_allowed": "dialect_or_unreviewed_function",
        "undefined_object": "unknown_identifier",
        "syntax_error": "sql_syntax_error",
        "model output invalid": "no_sql_in_model_output",
        "row_limit": "result_too_large",
        "result_limit": "result_too_large",
        "timeout": "query_timeout",
        "prompt_budget": "prompt_over_context",
    }.get(top, f"other:{top}")


def latency(records: list[dict[str, Any]]) -> dict[str, Any]:
    calls = [c for r in records for c in r.get("calls", []) if c.get("status") == "ok"]
    live = [c for c in calls if not c["cache_hit"]]
    per_role = {}
    for role in sorted({c["role"] for c in live}):
        seconds = [c["seconds"] for c in live if c["role"] == role]
        tokens = [
            c["completion_tokens"] for c in live if c["role"] == role and c["completion_tokens"]
        ]
        per_role[role] = {
            "live_calls": len(seconds),
            "median_seconds": _median(seconds),
            "p95_seconds": _p95(seconds),
            "median_completion_tokens": _median(tokens),
        }
    item_seconds = [r["seconds"] for r in records if "seconds" in r]
    return {
        "items": len(records),
        "calls": len(calls),
        "cache_hits": len(calls) - len(live),
        "per_role": per_role,
        "median_item_seconds": _median(item_seconds),
        "p95_item_seconds": _p95(item_seconds),
        "questions_per_hour": round(3600 / _median(item_seconds), 1) if item_seconds else None,
        "peak_vram_bytes": max((c.get("vram_bytes") or 0 for c in live), default=None),
        "swap_seconds_total": round(sum(c.get("swap_seconds") or 0 for c in live), 3),
    }


def clarification_summary(records: dict[int, dict[str, Any]]) -> dict[str, Any]:
    asked = [r for r in records.values() if r["status"] == "asked"]
    candidates = [r for r in records.values() if r["ambiguity_candidate"]]
    negatives = [r for r in records.values() if not r["ambiguity_candidate"]]
    oracle = [r for r in asked if r.get("oracle") == "corrected_wording"]
    helper = [c for r in asked for c in r.get("helper_calls", []) if c.get("status") == "ok"]
    return {
        "label": "oracle-assisted: the reply is the corrected wording, reported separately",
        "items": len(records),
        "asked": len(asked),
        "ask_rate_on_ambiguity_candidates": _rate(
            sum(1 for r in candidates if r["status"] == "asked"), len(candidates)
        ),
        "ask_rate_on_clear_negatives": _rate(
            sum(1 for r in negatives if r["status"] == "asked"), len(negatives)
        ),
        "helper_valid_options": _rate(sum(1 for r in asked if r["helper_valid"]), len(asked)),
        "helper_median_seconds": _median([c["seconds"] for c in helper if c.get("seconds")]),
        "helper_median_swap_seconds": _median([c.get("swap_seconds") or 0 for c in helper]),
        "oracle_replies": len(oracle),
        "answered_after_oracle": sum(1 for r in oracle if r.get("final_status") == "answered"),
        "correct_after_oracle": sum(1 for r in oracle if r.get("final_ex_corrected") == 1),
    }


def build() -> dict[str, Any]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))["split"]
    splits = {"dev": protocol["dev_ids"], "held_out": protocol["held_out_ids"]}
    threshold = json.loads(THRESHOLD.read_text(encoding="utf-8")) if THRESHOLD.exists() else None
    summary: dict[str, Any] = {
        "format_version": 1,
        "contract": "v2 (D-075)",
        "model": "Arctic-Text2SQL-R1-7B Q4_K_M via local Ollama",
        "claim": "local PostgreSQL-adapted BIRD Mini-Dev subset; not an official BIRD score",
        "excludes": ["sql", "question text", "rows", "credentials"],
        "splits": {},
    }
    labels = []
    for split, ids in splits.items():
        raw = {c: load(split, c) for c in {c for c, _ in VIEWS.values()} | {"clarify_oracle"}}
        views = {name: view_of(raw[c], key) for name, (c, key) in VIEWS.items() if raw[c]}
        if not views:
            continue
        result: dict[str, Any] = {
            "ids": len(ids),
            "conditions": {name: condition_metrics(v, ids=ids) for name, v in views.items()},
            "comparisons": {
                name: {"left": a, "right": b} | paired(views[a], views[b], ids=ids)
                for name, (a, b) in COMPARISONS.items()
                if a in views and b in views
            },
            "phase_rates": {
                c: phase_rates(raw[c], first_only=c not in {"ret_n3_k1", "orig_n3_k1"})
                for c in raw
                if raw[c] and c != "clarify_oracle"
            },
            "latency": {c: latency(list(raw[c].values())) for c in raw if raw[c]},
        }
        for name in ("ret_n1_k0", "ret_n3_k1", "full_n1"):
            if name in views:
                result.setdefault("label_rescoring", {})[name] = label_rescoring(
                    views[name], raw[VIEWS[name][0]], ids=ids
                )
        if "ret_n3_k1" in views:
            curve = accuracy_coverage_curve(views["ret_n3_k1"], ids=ids)
            result["accuracy_coverage"] = {
                "curve": curve,
                "dev_rule_choice": select_threshold(curve) if split == "dev" else None,
                "frozen_threshold": threshold["threshold"] if threshold else None,
            }
        changed = [qid for qid in ids if raw["ret_n3_k1"].get(qid, {}).get("input_changed")]
        if "orig_n3_k1" in views and changed:
            result["input_change"] = {
                "changed_items": len(changed),
                "single_candidate": paired(views["orig_n1_k0"], views["ret_n1_k0"], ids=changed),
                "full_loop": paired(views["orig_n3_k1"], views["ret_n3_k1"], ids=changed),
            }
        if raw["clarify_oracle"]:
            result["clarification"] = clarification_summary(raw["clarify_oracle"])
        if raw["messy_n1"]:
            result["messy_schema"] = {
                "leaked_names": sum(
                    r.get("messy_leaked_names", 0) for r in raw["messy_n1"].values()
                ),
                "translated": sum(r.get("translated", 0) for r in raw["messy_n1"].values()),
                "untranslated": sum(r.get("untranslated", 0) for r in raw["messy_n1"].values()),
            }
        categories = Counter()
        for qid in ids:
            record = raw["ret_n3_k1"].get(qid)
            category = failure_category(record) if record else None
            if category:
                categories[category] += 1
                labels.append(
                    {
                        "question_id": qid,
                        "db_id": record["db_id"],
                        "split": split,
                        "difficulty": record["difficulty"],
                        "category": category,
                    }
                )
        result["failure_taxonomy"] = dict(categories.most_common())
        summary["splits"][split] = result
    return summary | {"failure_labels": labels}


def freeze_threshold() -> dict[str, Any]:
    if THRESHOLD.exists():
        raise SystemExit("threshold already frozen; refusing to overwrite")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))["split"]
    if load("held_out", "ret_n3_k1"):
        raise SystemExit("held-out records exist; the threshold must be frozen before them")
    dev = view_of(load("dev", "ret_n3_k1"), "n3_k1")
    if len(dev) != len(protocol["dev_ids"]):
        raise SystemExit("dev voting run incomplete")
    curve = accuracy_coverage_curve(dev, ids=protocol["dev_ids"])
    frozen = {
        "format_version": 1,
        "rule": "best dev selective EX with coverage >= 0.5; ties to lower threshold (D-078)",
        "threshold": select_threshold(curve),
        "dev_curve": curve,
    }
    THRESHOLD.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    return frozen


def _rate(count: int, total: int) -> float | None:
    return round(count / total, 6) if total else None


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 3) if values else None


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, int(0.95 * (len(ordered) - 1) + 0.5))], 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-threshold", action="store_true")
    args = parser.parse_args()
    if args.freeze_threshold:
        print(json.dumps(freeze_threshold(), indent=2))
        return 0
    summary = build()
    labels = summary.pop("failure_labels")
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    FAILURES.write_text(
        json.dumps({"format_version": 1, "labels": labels[:50], "total": len(labels)}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"splits": sorted(summary["splits"]), "failure_labels": len(labels)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
