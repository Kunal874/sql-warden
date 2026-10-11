import json
from pathlib import Path

from scripts import audit_attack_suite


def test_attack_suite_manifest_is_regenerated_and_complete():
    manifest = audit_attack_suite.build_manifest()
    saved = json.loads(Path("docs/attack-suite-manifest.json").read_text())

    assert saved == manifest
    assert manifest["deterministic_sql_attack_count"] >= 40
    assert manifest["model_mediated_attack_count"] >= 2
    assert {attack["threat_id"] for attack in manifest["attacks"]} == {
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
    }
    for attack in manifest["attacks"]:
        assert set(attack) == {
            "evidence",
            "id",
            "input_fixture",
            "observed_layer",
            "outcome",
            "seed_configuration",
            "success_predicate",
            "threat_id",
        }
        assert attack["outcome"] in {"blocked", "escaped_plain_text"}
        assert attack["success_predicate"]
        assert attack["evidence"]
    assert "credentials" in manifest["excludes"]
    assert "model prompts" in manifest["excludes"]
    rendered = json.dumps(manifest, sort_keys=True)
    assert "password" not in rendered.lower()


def test_e5_layer_off_policy_is_disposable_local_only():
    policy = audit_attack_suite.build_manifest()["e5_layer_off_policy"]

    assert policy == {
        "status": "not_run_in_this_slice",
        "target": "local_disposable_only",
        "hosted_targets": "rejected",
        "docker_project": "sqlwarden_e5_disposable",
        "volume": "sqlwarden_e5_disposable_pg16_data",
        "network": "disposable_internal_only",
        "host_directory_mounts": "forbidden",
        "cleanup_scope": [
            "docker project sqlwarden_e5_disposable",
            "volume sqlwarden_e5_disposable_pg16_data",
        ],
    }


def test_false_block_measurement_uses_existing_benign_guard_evidence():
    measurement = audit_attack_suite.build_manifest()["false_block_measurement"]

    assert measurement["safe_guard_cases"] >= 40
    assert measurement["safe_gold_items"] == 424
    assert measurement["safe_gold_guard_accepted"] == 421
    assert measurement["safe_gold_guard_blocked"] == 3
    assert measurement["safe_gold_blocked_reason_counts"] == {"unsupported_node": 3}
