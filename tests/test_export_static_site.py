import json

from scripts.export_static_site import export


def _keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _keys(item)


def test_static_export_writes_only_sanitized_evidence(tmp_path):
    paths = export(tmp_path)

    assert sorted(path.name for path in paths) == ["attacks.json", "benchmark.json"]
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert not {"sql", "question", "rows", "password", "capability"} & set(_keys(payload))
