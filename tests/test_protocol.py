import json

import pytest

from sqlwarden import protocol


def _item(question_id, db_id, difficulty, *, family_id=None):
    item = {
        "question_id": question_id,
        "db_id": db_id,
        "difficulty": difficulty,
        "ambiguity_candidate": question_id % 2 == 0,
    }
    if family_id is not None:
        item["family_id"] = family_id
    return item


def _manifest(items):
    return {
        "format_version": 1,
        "primary_labels": "arcwise_full_verified_corrected_pool",
        "primary_descriptions": "corrected",
        "alternate_descriptions": "original",
        "validity": {"usable_count": len(items)},
        "usable_items": items,
    }


def test_split_is_seeded_stratified_and_keeps_families_together():
    manifest = _manifest(
        [
            _item(1, "a", "simple", family_id="family-a"),
            _item(2, "a", "simple", family_id="family-a"),
            _item(3, "a", "simple"),
            _item(4, "a", "moderate"),
            _item(5, "a", "moderate"),
            _item(6, "b", "simple"),
            _item(7, "b", "simple"),
            _item(8, "b", "moderate"),
            _item(9, "b", "moderate"),
            _item(10, "b", "moderate"),
        ]
    )

    first = protocol.build_protocol(manifest, dev_count=4, seed=1234)
    second = protocol.build_protocol(manifest, dev_count=4, seed=1234)
    changed_seed = protocol.build_protocol(manifest, dev_count=4, seed=5678)

    assert first == second
    assert first["split"]["dev_ids"] != changed_seed["split"]["dev_ids"]
    assert len(first["split"]["dev_ids"]) == 4
    assert set(first["split"]["dev_ids"]).isdisjoint(first["split"]["held_out_ids"])
    assert sorted(first["split"]["dev_ids"] + first["split"]["held_out_ids"]) == list(range(1, 11))
    family_members = {1, 2}
    assert family_members <= set(first["split"]["dev_ids"]) or family_members <= set(
        first["split"]["held_out_ids"]
    )
    assert set(first["split"]["dev_strata"]) <= {
        "a::simple",
        "a::moderate",
        "b::simple",
        "b::moderate",
    }
    assert first["split"]["dev_id_sha256"] == protocol.hash_ids(first["split"]["dev_ids"])


def test_real_gold_manifest_freezes_exactly_100_development_ids():
    manifest = protocol.load_gold_manifest("docs/gold-validity-manifest.json")

    document = protocol.build_protocol(manifest)

    assert document["source"]["usable_count"] == 424
    assert len(document["split"]["dev_ids"]) == 100
    assert len(document["split"]["held_out_ids"]) == 324
    assert set(document["split"]["dev_ids"]).isdisjoint(document["split"]["held_out_ids"])
    assert len(set(document["split"]["dev_ids"])) == 100
    assert document["split"]["usable_id_sha256"] == protocol.hash_ids(
        sorted(document["split"]["dev_ids"] + document["split"]["held_out_ids"])
    )
    assert document["metrics"]["bootstrap"]["samples"] == 10_000
    rendered = json.dumps(document)
    assert "SELECT" not in rendered
    assert "question" not in rendered.lower()
    assert "result cells" not in rendered
    assert "credentials" not in rendered


def test_invalid_manifest_is_refused():
    with pytest.raises(protocol.ProtocolError, match="primary labels"):
        protocol.build_protocol(_manifest([_item(1, "a", "simple")]) | {"primary_labels": "old"})
    with pytest.raises(protocol.ProtocolError, match="usable count"):
        protocol.build_protocol(_manifest([_item(1, "a", "simple")]) | {"validity": {}})
    with pytest.raises(protocol.ProtocolError, match="duplicate"):
        protocol.build_protocol(_manifest([_item(1, "a", "simple"), _item(1, "a", "simple")]))


def test_bootstrap_accuracy_interval_edge_cases_are_seeded_and_bounded():
    assert protocol.bootstrap_accuracy_interval([], samples=10, seed=1) == {
        "n": 0,
        "mean": None,
        "low": None,
        "high": None,
    }
    assert protocol.bootstrap_accuracy_interval([True, True], samples=10, seed=1) == {
        "n": 2,
        "mean": 1.0,
        "low": 1.0,
        "high": 1.0,
    }
    assert protocol.bootstrap_accuracy_interval([False, False], samples=10, seed=1) == {
        "n": 2,
        "mean": 0.0,
        "low": 0.0,
        "high": 0.0,
    }

    first = protocol.bootstrap_accuracy_interval([True, False, True, False], samples=200, seed=7)
    second = protocol.bootstrap_accuracy_interval([True, False, True, False], samples=200, seed=7)

    assert first == second
    assert first["n"] == 4
    assert first["mean"] == 0.5
    assert 0.0 <= first["low"] <= first["mean"] <= first["high"] <= 1.0


def test_clopper_pearson_interval_is_exact_and_handles_boundaries():
    from sqlwarden.protocol import clopper_pearson

    zero = clopper_pearson(0, 43)
    assert zero["low"] == 0.0
    assert abs(zero["high"] - 0.0822) < 0.0005
    full = clopper_pearson(10, 10)
    assert full["high"] == 1.0 and abs(full["low"] - 0.6915) < 0.0005
    middle = clopper_pearson(22, 100)
    assert abs(middle["low"] - 0.1433) < 0.0005 and abs(middle["high"] - 0.3139) < 0.0005
    assert clopper_pearson(0, 0) == {"n": 0, "k": 0, "low": None, "high": None}
