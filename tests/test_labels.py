import hashlib
import json

import pytest

from scripts.inspect_labels import LabelError, build_report, decode_labels, read_pinned


def record(identifier=1, **changes):
    row = {
        "question_id": identifier,
        "db_id": "california_schools",
        "question": "How many schools?",
        "evidence": "",
        "SQL": "SELECT COUNT(*) FROM schools",
        "difficulty": "simple",
    }
    row.update(changes)
    return row


def parsed(rows, *, corrected=False):
    if corrected:
        rows = [dict(r, question_id=str(r["question_id"])) for r in rows]
    return decode_labels(json.dumps(rows).encode(), corrected=corrected)


def sources():
    rows = [record(1), record(2)]
    return {
        "bird_sqlite": parsed(rows),
        "bird_pg": parsed(list(reversed(rows))),
        "arcwise_sql": parsed(list(reversed(rows)), corrected=True),
        "arcwise_full": parsed(rows, corrected=True),
    }


def test_ids_join_across_types_and_order():
    report = build_report(sources())
    assert report["original_count"] == 2
    assert report["by_source"]["arcwise_sql"]["identity_aligned_count"] == 2
    assert report["by_source"]["bird_pg"]["missing_ids"] == []


@pytest.mark.parametrize("identifier", [True, -1, 0, 1.0, "1", None])
def test_original_id_types_are_strict(identifier):
    with pytest.raises(LabelError):
        decode_labels(json.dumps([record(identifier)]).encode(), corrected=False)


@pytest.mark.parametrize("identifier", [1, True, "01", "+1", "1.0", " 1", "", "1000000"])
def test_corrected_id_types_are_strict(identifier):
    with pytest.raises(LabelError):
        decode_labels(json.dumps([record(identifier)]).encode(), corrected=True)


def test_duplicate_ids_and_object_keys_are_rejected():
    with pytest.raises(LabelError):
        parsed([record(), record()])
    with pytest.raises(LabelError):
        decode_labels(b'[{"question_id":1,"question_id":2}]', corrected=False)


@pytest.mark.parametrize(
    "change",
    [
        {"db_id": "unknown"},
        {"question": ""},
        {"question": "   "},
        {"SQL": ""},
        {"SQL": "   "},
        {"SQL": False},
        {"evidence": None},
        {"original_SQL": 5},
        {"difficulty": "unknown"},
        {"difficulty": []},
        {"unreviewed_field": "value"},
    ],
)
def test_fields_reject_unreviewed_shapes(change):
    with pytest.raises(LabelError):
        parsed([record(**change)])


@pytest.mark.parametrize(
    "raw",
    [b"null", b"{}", b"[]", b"[NaN]", b"[", b"\xff", b" " * 600001],
    ids=["null", "object", "empty", "constant", "broken", "invalid_utf8", "oversize"],
)
def test_invalid_documents_are_rejected(raw):
    with pytest.raises(LabelError):
        decode_labels(raw, corrected=False)


def test_text_changes_do_not_select_labels_or_classify_ambiguity():
    data = sources()
    data["arcwise_sql"][1]["question"] = "A different question"
    data["arcwise_full"][1]["evidence"] = "A different hint"
    report = build_report(data)
    assert report["by_source"]["arcwise_sql"]["question_difference_ids"] == [1]
    assert report["by_source"]["arcwise_full"]["evidence_difference_ids"] == [1]
    assert report["corrected_pair_text_difference_ids"] == [1]
    assert report["execution_validity"] == "not_run"
    assert report["primary_labels"] == "not_selected"
    assert report["ambiguity_labels"] == "not_classified"
    assert report["splits"] == "not_frozen"
    assert "SELECT COUNT" not in json.dumps(report)
    assert "A different" not in json.dumps(report)


def test_missing_extra_database_and_difficulty_mismatches_are_visible():
    data = sources()
    data["arcwise_sql"].pop(2)
    data["arcwise_sql"][3] = record(3)
    data["arcwise_sql"][1]["db_id"] = "financial"
    data["arcwise_sql"][1]["difficulty"] = "moderate"
    track = build_report(data)["by_source"]["arcwise_sql"]
    assert track["missing_ids"] == [2]
    assert track["unexpected_ids"] == [3]
    assert track["database_mismatch_ids"] == [1]
    assert track["difficulty_mismatch_ids"] == [1]
    assert track["identity_aligned_count"] == 0


def test_original_fields_are_observations_not_trusted_overrides():
    data = sources()
    data["arcwise_full"][1]["original_question"] = "Not our pinned question"
    assert build_report(data)["by_source"]["arcwise_full"]["question_anchor_mismatch_ids"] == [1]


def test_pinned_reader_rejects_bad_size_or_digest(tmp_path):
    path = tmp_path / "labels.json"
    path.write_bytes(b"[]")
    digest = hashlib.sha256(b"[]").hexdigest()
    assert read_pinned(path, 2, digest) == b"[]"
    with pytest.raises(LabelError):
        read_pinned(path, 1, digest)
    with pytest.raises(LabelError):
        read_pinned(path, 2, "0" * 64)


def test_local_inspection_checks_every_pin(tmp_path, monkeypatch):
    import scripts.inspect_labels as module

    pins = {}
    for name in sorted(module.SOURCE_NAMES):
        row = record()
        if name.startswith("arcwise_"):
            row["question_id"] = "1"
        raw = json.dumps([row]).encode()
        filename = name + ".json"
        (tmp_path / filename).write_bytes(raw)
        pins[name] = (filename, len(raw), hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(module, "PINS", pins)
    assert module.inspect_local(tmp_path)["original_count"] == 1
    (tmp_path / pins["bird_pg"][0]).write_bytes(b"corrupt")
    with pytest.raises(LabelError):
        module.inspect_local(tmp_path)
