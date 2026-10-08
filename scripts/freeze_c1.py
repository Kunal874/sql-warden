"""Freeze the owner-selected C1 corrected pool from sanitized local evidence."""

import argparse
import hashlib
import json
from pathlib import Path

from scripts.inspect_labels import inspect_local
from scripts.validate_gold import ValidationError, build_c1_manifest, load_tracks, publish_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / ".tools/gold-validation/recovery-final.json"
DEFAULT_OUTPUT = ROOT / "docs/gold-validity-manifest.json"


def project_relative(path: Path, *, root: Path = ROOT) -> str:
    try:
        resolved = path.resolve()
        if not resolved.exists():
            resolved = (root / path).resolve()
        return str(resolved.relative_to(root.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        raise ValidationError("path outside project") from None


def freeze_c1_manifest(evidence: Path, output: Path) -> dict:
    try:
        raw = evidence.read_bytes()
        report = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        raise ValidationError("evidence unavailable") from None
    tracks = load_tracks(ROOT / "data")
    manifest = build_c1_manifest(
        report,
        {"alignment": inspect_local(ROOT / "data"), **_label_revisions()},
        tracks["bird_sqlite"],
        evidence_sha256=hashlib.sha256(raw).hexdigest(),
        evidence_path=project_relative(evidence),
        decision_source="Kunal chose the corrected pool on 2026-10-08",
    )
    publish_manifest(output, manifest)
    return manifest


def _label_revisions() -> dict[str, str]:
    label_manifest = ROOT / "docs/label-alignment-manifest.json"
    try:
        document = json.loads(label_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValidationError("label manifest unavailable") from None
    return {
        "original_revision": document["original_revision"],
        "correction_revision": document["correction_revision"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        manifest = freeze_c1_manifest(args.evidence, args.output)
    except ValidationError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    print(
        json.dumps(
            {
                "status": "complete",
                "output": str(args.output),
                "usable_count": manifest["validity"]["usable_count"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
