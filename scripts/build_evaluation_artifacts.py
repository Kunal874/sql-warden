"""Build compact tracked G3 evaluation artifacts from ignored raw E0 records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlwarden.evaluation import label_failures, summarize_model, summarize_paired_models

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/E0_smoke"
RAW = RESULTS / "raw"
SUMMARY = RESULTS / "summary.json"
DASHBOARD = RESULTS / "dashboard.json"
FAILURES = RESULTS / "failure-labels.json"
PROTOCOL = ROOT / "docs/e0-protocol.json"
MATRIX = ROOT / "docs/evaluation-matrix.json"
EVAL_DOC = ROOT / "docs/EVAL.md"
RESUME_DOC = ROOT / "docs/RESUME.md"

EXCLUDES = ["prompts", "generated query text", "gold query text", "rows", "credentials"]


def load_records(raw_root: Path, model_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    records = {}
    for model_name in model_names:
        model_records = []
        for path in sorted((raw_root / model_name).glob("*.json")):
            if path.name == "manifest.json":
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("model") == model_name:
                model_records.append(record)
        records[model_name] = model_records
    return records


def build_artifacts(
    protocol: dict[str, Any], records: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    metric_config = protocol.get("metrics", {}).get("bootstrap", {})
    seed = int(metric_config.get("seed", 20261008))
    samples = int(metric_config.get("samples", 10_000))
    models = {
        model: summarize_model(model, model_records, protocol, seed=seed, samples=samples)
        for model, model_records in sorted(records.items())
    }
    paired = {}
    if {"arctic", "qwen"}.issubset(records):
        paired["arctic_vs_qwen"] = summarize_paired_models(
            "arctic",
            records["arctic"],
            "qwen",
            records["qwen"],
            protocol,
            seed=seed,
            samples=samples,
        )
    failure_labels = label_failures(
        [record for model_records in records.values() for record in model_records], limit=50
    )
    summary = {
        "format_version": 2,
        "protocol": {
            "path": "docs/e0-protocol.json",
            "dev_count": len(protocol["split"]["dev_ids"]),
            "full_dev_count": len(protocol["split"]["dev_ids"]),
            "dev_id_sha256": protocol["split"]["dev_id_sha256"],
        },
        "models": models,
        "paired": paired,
        "raw_records": "results/E0_smoke/raw/<model>/<question_id>.json ignored",
        "excludes": EXCLUDES,
    }
    return {
        "summary": summary,
        "dashboard": _dashboard(summary),
        "failures": {
            "format_version": 1,
            "label_count": len(failure_labels),
            "labels": failure_labels,
            "excludes": EXCLUDES,
        },
        "matrix": evaluation_matrix(protocol),
        "resume": _resume_markdown(summary),
    }


def evaluation_matrix(protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "format_version": 1,
        "protocol": {
            "base": "docs/e0-protocol.json",
            "dev_count": len(protocol["split"]["dev_ids"]),
            "held_out_count": protocol["split"].get("held_out_count"),
            "dev_id_sha256": protocol["split"]["dev_id_sha256"],
            "held_out_id_sha256": protocol["split"].get("held_out_id_sha256"),
        },
        "time_budget": {"weekly_hours": "15-20", "source": "Kunal approved weekly budget"},
        "experiments": [
            _experiment("E1", "corrected/original label baselines", "separate_rerun"),
            _experiment("E2", "same-input full schema/retrieval/repair/voting effects", "rescore"),
            _experiment("E3", "matched rescoring and annotation-change case studies", "rescore"),
            _experiment("E4", "seeded messy-schema transformation", "separate_rerun"),
            _experiment(
                "E6", "fresh/cached latency, tokens, helper overhead and VRAM", "separate_rerun"
            ),
            _experiment(
                "E7", "ambiguity, negatives and simulated/oracle assistance labels", "rescore"
            ),
            _experiment("E8", "held-out accuracy-coverage curve", "separate_rerun"),
        ],
        "deferred": {
            "E5": "security attack evidence already covered in G2; layer-off stays approval-gated",
            "E9": "optional fine-tuning, not part of the local portfolio minimum",
        },
        "rules": [
            "Development evidence may tune defaults; held-out IDs remain untouched until E8.",
            "Rescoring reuses unchanged model outputs; separate reruns must record "
            "new run fingerprints.",
            "Tracked artifacts exclude prompts, generated SQL, gold SQL, rows and credentials.",
        ],
    }


def write_artifacts(artifacts: dict[str, Any]) -> None:
    _write_json(SUMMARY, artifacts["summary"])
    _write_json(DASHBOARD, artifacts["dashboard"])
    _write_json(FAILURES, artifacts["failures"])
    _write_json(MATRIX, artifacts["matrix"])
    EVAL_DOC.write_text(_eval_markdown(artifacts), encoding="utf-8", newline="\n")
    RESUME_DOC.write_text(artifacts["resume"], encoding="utf-8", newline="\n")


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    records = load_records(RAW, ["arctic", "qwen"])
    write_artifacts(build_artifacts(protocol, records))
    return 0


def _dashboard(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "format_version": 1,
        "models": {
            model: {
                "denominator": metrics["denominator"],
                "ex": metrics["ex"],
                "answered_only_ex": metrics["answered_only"]["ex"],
                "coverage_rate": metrics["coverage"]["rate"],
                "parse_rate": metrics["phase_metrics"]["parse"]["rate"],
                "guard_rate": metrics["phase_metrics"]["guard"]["rate"],
                "execution_rate": metrics["phase_metrics"]["execution"]["rate"],
                "median_seconds": metrics["median_seconds"],
                "p95_seconds": metrics["p95_seconds"],
            }
            for model, metrics in summary["models"].items()
        },
        "paired": summary["paired"],
        "excludes": EXCLUDES,
    }


def _experiment(identifier: str, name: str, evidence_mode: str) -> dict[str, str]:
    return {"id": identifier, "name": name, "evidence_mode": evidence_mode, "status": "planned"}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _eval_markdown(artifacts: dict[str, Any]) -> str:
    arctic = artifacts["summary"]["models"].get("arctic", {})
    qwen = artifacts["summary"]["models"].get("qwen", {})
    return (
        "# Evaluation evidence\n\n"
        "This file summarizes local development-slice evaluation artifacts. It is not an "
        "official benchmark claim.\n\n"
        "## E0 current result\n\n"
        f"- Arctic: {arctic.get('correct')}/{arctic.get('denominator')} EX, "
        f"answered-only EX {arctic.get('answered_only', {}).get('ex')}.\n"
        f"- Qwen: {qwen.get('correct')}/{qwen.get('denominator')} EX, "
        f"answered-only EX {qwen.get('answered_only', {}).get('ex')}.\n"
        "- Raw prompts, generated SQL, gold SQL, rows and credentials are excluded from "
        "tracked artifacts.\n\n"
        "## G3 matrix\n\n"
        "The frozen matrix is tracked in `docs/evaluation-matrix.json`. E5 remains tied "
        "to G2 security evidence and E9 is optional.\n"
    )


def _resume_markdown(summary: dict[str, Any]) -> str:
    arctic = summary["models"].get("arctic", {})
    qwen = summary["models"].get("qwen", {})
    paired = summary["paired"].get("arctic_vs_qwen", {})
    arctic_parse = arctic.get("phase_metrics", {}).get("parse", {}).get("rate")
    arctic_guard = arctic.get("phase_metrics", {}).get("guard", {}).get("rate")
    arctic_execution = arctic.get("phase_metrics", {}).get("execution", {}).get("rate")
    return (
        "# Resume evidence\n\n"
        "Use these only with the local-development qualifier; this is not an official "
        "benchmark or public leaderboard score.\n\n"
        "- Built a local read-only text-to-SQL evaluation slice with guard checks, "
        "restricted PostgreSQL execution and compact tracked metrics that exclude raw "
        "prompts, SQL, rows and credentials.\n"
        f"- Arctic measured {arctic.get('correct')}/{arctic.get('denominator')} exact "
        f"matches on the frozen development slice; Qwen measured {qwen.get('correct')}/"
        f"{qwen.get('denominator')} under its smaller context window.\n"
        f"- Added phase metrics: Arctic parse {arctic_parse}, "
        f"guard {arctic_guard}, execution {arctic_execution}; "
        f"paired Arctic-Qwen delta {paired.get('accuracy_difference')} on "
        f"{paired.get('paired_count')} matched development questions.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
