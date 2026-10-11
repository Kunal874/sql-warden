"""Fill docs/evaluation-matrix.json statuses and run hours from the ignored run records.

Offline. Reads only record counts and per-item seconds; the frozen protocol, rules and
time budget are kept as they are. Hours are agent wall-clock per item (model calls
plus database time), summed once per run file:

uv run python -m scripts.update_evaluation_matrix
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.run_matrix import RAW, RESULTS
from sqlwarden.evaluation import load_jsonl_records

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/evaluation-matrix.json"
EXPECTED = {"dev": 100, "held_out": 324, "e7": 50}
DEV_LOOP, DEV_FULL = ("dev", "ret_n3_k1"), ("dev", "full_n1")
HELD_LOOP, HELD_FULL = ("held_out", "ret_n3_k1"), ("held_out", "full_n1")
DEV_ORIG = ("dev", "orig_n3_k1")
PLAN = (
    ("E1", "corrected vs original labels; original-wording rerun on dev only",
     "rescore + dev rerun", (DEV_LOOP, HELD_LOOP, HELD_FULL, DEV_ORIG)),
    ("E2", "same-input full schema, retrieval, repair and voting effects",
     "rescore", (DEV_LOOP, DEV_FULL, HELD_LOOP, HELD_FULL)),
    ("E3", "matched re-scoring and annotation-change case studies",
     "rescore", (DEV_LOOP, DEV_ORIG, HELD_LOOP)),
    ("E4", "seeded messy-schema transformation (dev only)",
     "separate_rerun", (("dev", "messy_n1"),)),
    ("E6", "fresh and cached latency, tokens, helper overhead and VRAM",
     "separate_rerun", (DEV_LOOP, ("dev", "ret_n3_k1_replay"))),
    ("E7", "oracle-assisted clarification (dev) and the self-authored set",
     "separate_rerun", (("dev", "clarify_oracle"), ("e7", "self_authored"))),
    ("E8", "held-out accuracy-coverage at the dev-frozen threshold",
     "rescore", (HELD_LOOP,)),
)  # fmt: skip


def _hours(records: list[dict[str, Any]]) -> float:
    keys = ("seconds", "ask_seconds", "resume_seconds")
    return round(sum(r.get(k) or 0 for r in records for k in keys) / 3600, 2)


def matrix(
    frozen: dict[str, Any], runs: dict[tuple[str, str], list[dict]], *, e5_done: bool
) -> dict[str, Any]:
    experiments = []
    for identifier, name, mode, needed in PLAN:
        detail = [
            {
                "run": f"{split}/{condition}",
                "items": len(runs.get((split, condition), [])),
                "expected": EXPECTED[split],
                "hours": _hours(runs.get((split, condition), [])),
            }
            for split, condition in needed
        ]
        done = all(d["items"] == d["expected"] for d in detail)
        experiments.append(
            {
                "id": identifier,
                "name": name,
                "evidence_mode": mode,
                "status": "complete" if done else "pending",
                "runs": detail,
            }
        )
    experiments += [
        {
            "id": "E5",
            "name": "layer-off attacks in the disposable Docker project",
            "evidence_mode": "disposable_layer_off",
            "status": "complete" if e5_done else "pending",
            "evidence": "results/G3_matrix/e5-layer-off.json",
        },
        {
            "id": "E9",
            "name": "optional fine-tuning (G6)",
            "evidence_mode": None,
            "status": "not_run",
        },
    ]
    hours = {
        f"{split}/{condition}": _hours(records) for (split, condition), records in runs.items()
    }
    kept = {key: value for key, value in frozen.items() if key != "deferred"}
    return kept | {
        "experiments": sorted(experiments, key=lambda e: int(e["id"][1:])),
        "measured_run_hours": dict(sorted(hours.items()))
        | {"total": round(sum(hours.values()), 2)},
    }


def main() -> int:
    runs = {}
    for _, _, _, needed in PLAN:
        for split, condition in needed:
            records = load_jsonl_records(RAW / split / f"{condition}.jsonl")
            if records:
                runs[(split, condition)] = records
    frozen = json.loads(MATRIX.read_text(encoding="utf-8"))
    updated = matrix(frozen, runs, e5_done=(RESULTS / "e5-layer-off.json").exists())
    with MATRIX.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(updated, indent=2, sort_keys=True) + "\n")
    print(json.dumps({e["id"]: e["status"] for e in updated["experiments"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
