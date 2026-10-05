import io
import json
import zipfile
from types import SimpleNamespace

import pytest
from test_source_audit import native_fixture, pin

from scripts import audit_sources as audit
from scripts import prepare_import_bundle as bundle


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    dump, tables = native_fixture()
    tables["thing"]["db_id"] = "card_games"
    archive = tmp_path / "source.zip"
    member = "native.sql"
    with zipfile.ZipFile(archive, "w") as target:
        target.writestr(member, dump)
    pins = {
        "archive": pin(archive.read_bytes()),
        "native_dump": pin(dump, member=member),
        "tables": tables,
    }
    columns = [
        {
            "name": c["name"],
            "native_type": c["type"],
            "declared_not_null": False,
            "primary_key_position": 0,
        }
        for c in tables["thing"]["columns"]
    ]
    metadata = {"tables": {"thing": {"columns": columns, "primary_key": []}}}
    audit_doc = {
        "databases": {i: metadata if i == "card_games" else {"tables": {}} for i in bundle.DB_IDS}
    }
    monkeypatch.setattr(bundle, "load_specs", lambda: (pins, audit_doc))
    return archive, pins


def test_native_copy_sink_is_optional_and_exact():
    dump, tables = native_fixture()
    sink = io.BytesIO()
    blocks = audit.inspect_native(
        io.BytesIO(dump), tables, pin(dump), deadline=float("inf"), copy_outputs={"thing": sink}
    )
    assert blocks["thing"] == tables["thing"]["copy"]
    assert sink.getvalue() == b"1\t2020-01-01\n2\t\\N\n"


def test_bundle_is_pinned_and_never_executes_source_sql(fixture, tmp_path):
    archive, pins = fixture
    destination = tmp_path / "native"
    bundle.prepare_bundle(archive, destination)
    assert (destination / "card_games/thing.tsv").read_bytes() == b"1\t2020-01-01\n2\t\\N\n"
    assert json.loads((destination / "manifest.json").read_text()) == bundle.bundle_metadata(pins)
    assert set(bundle.validate_bundle(destination, "card_games")) == {"thing"}
    assert not list(tmp_path.glob(".release-copy-*"))


@pytest.mark.parametrize(
    "mode", ["existing", "disk", "archive", "block", "metadata", "payload", "deadline"]
)
def test_bundle_refuses_or_keeps_failed_outputs_private(fixture, tmp_path, monkeypatch, mode):
    archive, pins = fixture
    destination = tmp_path / "native"
    if mode == "existing":
        destination.mkdir()
        (destination / "keep").write_bytes(b"unchanged")
    elif mode == "disk":
        monkeypatch.setattr(bundle.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    elif mode == "archive":
        pins["archive"]["sha256"] = "0" * 64
    elif mode == "block":
        pins["tables"]["thing"]["copy"]["sha256"] = "0" * 64
    elif mode == "deadline":
        monkeypatch.setattr(audit, "monotonic", lambda: float("inf"))
    if mode in {"metadata", "payload"}:
        bundle.prepare_bundle(archive, destination)
        if mode == "metadata":
            (destination / "manifest.json").write_text("{}")
        else:
            (destination / "card_games/thing.tsv").write_bytes(b"changed")
        with pytest.raises(ValueError):
            bundle.validate_bundle(destination, "card_games")
    else:
        with pytest.raises((ValueError, FileExistsError)):
            bundle.prepare_bundle(archive, destination)
        if mode == "existing":
            assert (destination / "keep").read_bytes() == b"unchanged"
        else:
            assert not destination.exists()
        assert not list(tmp_path.glob(".release-copy-*"))


def test_california_and_unrecognized_import_targets_refused(tmp_path):
    for db_id in ("california_schools", "app", "../other", "hosted"):
        with pytest.raises(ValueError):
            bundle.validate_bundle(tmp_path, db_id)


def test_reviewed_metadata_hash_checked_before_use(tmp_path, monkeypatch):
    metadata = tmp_path / "pins.json"
    metadata.write_text("{}")
    monkeypatch.setattr(bundle, "PINS_PATH", metadata)
    with pytest.raises(ValueError, match="metadata fingerprint"):
        bundle.load_specs()
