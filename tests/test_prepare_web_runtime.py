import pytest

from scripts.prepare_web_runtime import prepare
from sqlwarden.guard import DATASET_POLICIES
from sqlwarden.runtime import runtime_passwords


def _sources(root, *, bad=False):
    (root / ".env.california").write_text("WARDEN_CALIFORNIA_PASSWORD=" + "a" * 48 + "\n")
    lines = [
        f"WARDEN_DATASET_{db_id.upper()}_PASSWORD=" + ("z" if bad else "b") * 48
        for db_id in DATASET_POLICIES
        if db_id != "california_schools"
    ]
    (root / ".env.datasets").write_text("\n".join(lines) + "\n")


def test_prepare_writes_only_restricted_runtime_keys_once(tmp_path):
    _sources(tmp_path)

    prepare(tmp_path)

    values = dict(line.split("=", 1) for line in (tmp_path / ".env.web").read_text().splitlines())
    assert set(runtime_passwords(values)) == set(DATASET_POLICIES)
    with pytest.raises(FileExistsError):
        prepare(tmp_path)


def test_prepare_refuses_malformed_sources_without_writing(tmp_path):
    _sources(tmp_path, bad=True)
    with pytest.raises(ValueError):
        prepare(tmp_path)
    assert not (tmp_path / ".env.web").exists()
