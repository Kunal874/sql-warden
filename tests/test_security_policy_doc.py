from pathlib import Path


def test_security_policy_records_g2_evidence_and_limitations():
    text = Path("SECURITY.md").read_text(encoding="utf-8")

    for heading in (
        "## System and Scope",
        "## Threat Model and Trust Boundaries",
        "## Security Invariants",
        "## Evidence",
        "## Reportable Findings and Severity Context",
        "## Known Limitations and Accepted Risk",
    ):
        assert heading in text
    for artifact in (
        "docs/attack-suite-manifest.json",
        "docs/grants-permission-manifest.json",
        "docs/executor-cost-calibration-manifest.json",
        "docs/guard-gold-audit-manifest.json",
    ):
        assert artifact in text
    for limitation in (
        "not a production SaaS",
        "does not prove universal prompt-injection resistance",
        "Layer-off E5 covers only the SQL guard, database role, read-only",
        "Some catalog metadata is normally visible",
        "No official benchmark score",
    ):
        assert limitation in text
