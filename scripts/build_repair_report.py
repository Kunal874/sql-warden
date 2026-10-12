"""Development-only tuned-model repair comparison; old E9 evidence stays untouched."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from scripts.build_e9_report import summarize_pair
from scripts.run_e9 import RAW, ROOT, check_e9_resources, load_generators
from scripts.run_matrix import build_items
from sqlwarden.evaluation import write_atomic_record


def summarize(baseline: list[dict], repaired: list[dict], ids: list[int]) -> dict:
    for repairs, records in enumerate([baseline, repaired]):
        for record in records:
            if (
                record.get("generator") != "tuned"
                or record.get("experiment") != "E10-dev-repair"
                or record.get("condition") != ("full_n1_k1" if repairs else "full_n1")
                or len(record.get("calls", [])) > 1 + repairs
                or any(c["repairs"] > repairs for c in record.get("candidates", []))
            ):
                raise ValueError("repair record contract refused")
    # Reuse paired metrics with temporary arm labels, not a second model comparison.
    report = summarize_pair(
        [r | {"generator": "base"} for r in baseline],
        [r | {"generator": "tuned"} for r in repaired],
        ids,
    )
    return {
        "k0": report["base"],
        "k1": report["tuned"],
        "k1_vs_k0": report["tuned_vs_base"],
        "repair_attempts": sum(c["repairs"] for r in repaired for c in r.get("candidates", [])),
    }


def main() -> None:
    serving = ROOT / "docs/g6-serving-manifest.json"
    generator = asdict(load_generators(serving)["tuned"])
    serving_sha = hashlib.sha256(serving.read_bytes()).hexdigest()
    records, contracts, provenance = [], [], {}
    for repairs in (0, 1):
        path = RAW / "repair/dev" / f"k{repairs}.jsonl"
        manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        fingerprint = manifest.pop("fingerprint")
        if (
            hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest() != fingerprint
            or manifest["git"]["dirty"]
            or manifest["generator"] != generator
            or manifest["serving_sha256"] != serving_sha
            or manifest["experiment"] != "E10-dev-repair"
            or manifest["split"] != "dev"
            or manifest["condition"] != ("full_n1_k1" if repairs else "full_n1")
            or manifest["config"]["max_repairs"] != repairs
        ):
            raise ValueError("repair provenance refused")
        payload = path.read_bytes()
        if not payload.endswith(b"\n"):
            raise ValueError("repair unterminated evidence refused")
        records.append([json.loads(line) for line in payload.decode("utf-8").splitlines()])
        provenance[f"k{repairs}"] = {
            "manifest_fingerprint": fingerprint,
            "git_commit": manifest["git"]["commit"],
            "records_sha256": hashlib.sha256(payload).hexdigest(),
        }
        manifest.pop("condition")
        manifest["config"] = manifest["config"] | {"max_repairs": 0}
        contracts.append(manifest)
    if contracts[0] != contracts[1]:
        raise ValueError("repair paired contracts differ")
    summary = summarize(*records, [item["question_id"] for item in build_items("dev")]) | {
        "experiment": "E10-dev-repair",
        "claim": "development comparison only; no new held-out or official BIRD score",
        "generator": generator,
        "serving_sha256": serving_sha,
        "provenance": provenance,
        "limits": "fresh response-cache-free runs; Ollama prefix reuse not disabled; one seed",
    }
    check_e9_resources(planned_bytes=len(json.dumps(summary, indent=2, sort_keys=True)) + 1)
    write_atomic_record(ROOT / "results/G6_e9/repair/summary.json", summary)


if __name__ == "__main__":
    main()
