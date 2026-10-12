"""Build compact E9 evidence; never copy SQL, prompts or answer rows to Git."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict

from scripts.build_matrix_report import condition_metrics, latency, paired
from scripts.run_e9 import RAW, ROOT, load_generators, validate_done
from scripts.run_matrix import build_items
from sqlwarden.evaluation import write_atomic_record


def summarize_pair(base: list[dict], tuned: list[dict], ids: list[int]) -> dict:
    summary, views = {}, {}
    for name, records in [("base", base), ("tuned", tuned)]:
        if validate_done(records, ids) != set(ids) or any(
            record.get("generator") != name
            or record.get("gold_corrected_valid") is not True
            or type(record.get("final_ex_corrected")) is not int
            or record["final_ex_corrected"] not in (0, 1)
            or any(call.get("cache_hit") for call in record.get("calls", []))
            for record in records
        ):
            raise ValueError("E9 complete fresh paired records required")
        view = {
            record["question_id"]: {
                "status": record["status"],
                "ex_corrected": record["final_ex_corrected"],
            }
            for record in records
        }
        views[name] = view
        timings = latency(records)
        reported_vram = [
            call["vram_bytes"]
            for record in records
            for call in record.get("calls", [])
            if call.get("vram_bytes") is not None
        ]
        timings["peak_vram_bytes"] = max(reported_vram, default=None)
        summary[name] = {
            "accuracy": condition_metrics(view, ids=ids),
            "latency": timings,
            "failures": dict(
                Counter(record["reason"] for record in records if not record["final_ex_corrected"])
            ),
        }
    summary["tuned_vs_base"] = paired(views["tuned"], views["base"], ids=ids)
    return summary


def main() -> None:
    serving = ROOT / "docs/g6-serving-manifest.json"
    generators = load_generators(serving)
    summary = {
        "experiment": "E9",
        "claim": "repeat local PostgreSQL-adapted Mini-Dev comparison; not official BIRD",
        "labels": "training conversions structurally checked, execution-unverified",
        "serving_sha256": hashlib.sha256(serving.read_bytes()).hexdigest(),
        "splits": {},
    }
    for split in ["dev", "held_out"]:
        inputs, provenance, contracts = {}, {}, []
        ids = [item["question_id"] for item in build_items(split)]
        for name in ["base", "tuned"]:
            path = RAW / split / f"{name}.jsonl"
            manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
            fingerprint = manifest.pop("fingerprint")
            if (
                hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
                != fingerprint
            ):
                raise ValueError("E9 manifest fingerprint mismatch")
            if (
                manifest["git"]["dirty"]
                or manifest["generator"] != asdict(generators[name])
                or manifest["serving_sha256"] != summary["serving_sha256"]
                or manifest["experiment"] != "E9"
                or manifest["split"] != split
            ):
                raise ValueError("E9 provenance refused")
            contracts.append(
                {
                    key: value
                    for key, value in manifest.items()
                    if key not in {"git", "generator", "models"}
                }
            )
            inputs[name] = [
                json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            ]
            provenance[name] = {
                "manifest_fingerprint": fingerprint,
                "git_commit": manifest["git"]["commit"],
                "records_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "model_digest": generators[name].digest,
            }
        if contracts[0] != contracts[1]:
            raise ValueError("E9 paired inference contracts differ")
        summary["splits"][split] = summarize_pair(inputs["base"], inputs["tuned"], ids) | {
            "provenance": provenance
        }
    write_atomic_record(ROOT / "results/G6_e9/summary.json", summary)


if __name__ == "__main__":
    main()
