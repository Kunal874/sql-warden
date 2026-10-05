import hashlib
import stat
import zipfile

import pytest

from scripts import prepare_sources as prep


def pin(raw, **fields):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), **fields}


def fixture_archive(tmp_path, *, duplicate=False, symlink=False):
    archive_path = tmp_path / "source.zip"
    blobs = {"schema.json": b"{}", "source.sqlite": b"fixture bytes", "source.csv": b"csv"}
    with zipfile.ZipFile(archive_path, "w") as archive:
        for member, raw in blobs.items():
            info = zipfile.ZipInfo(member)
            if symlink and member == "source.csv":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, raw)
        archive.writestr("__MACOSX/source.csv", b"not selected")
        if duplicate:
            with pytest.warns(UserWarning):
                archive.writestr("source.csv", b"csv")
    pins = {
        "archive": pin(archive_path.read_bytes()),
        "metadata": pin(blobs["schema.json"], member="schema.json", output="dev_tables.json"),
        "sqlite_sources": [
            pin(blobs["source.sqlite"], member="source.sqlite", output="sqlite/db.sqlite")
        ],
        "original_description_sources": [
            pin(blobs["source.csv"], member="source.csv", output="original/db/table.csv")
        ],
    }
    return archive_path, pins


def test_extracts_only_fixed_members_without_overwrite(tmp_path):
    archive_path, pins = fixture_archive(tmp_path)
    destination = tmp_path / "release"
    prep.extract_sources(archive_path, destination, pins=pins)
    assert sorted(
        p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()
    ) == ["dev_tables.json", "original/db/table.csv", "sqlite/db.sqlite"]
    with pytest.raises(ValueError, match="already exists"):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert (destination / "original/db/table.csv").read_bytes() == b"csv"


@pytest.mark.parametrize("mode", ["duplicate", "symlink", "missing", "bytes", "hash", "archive"])
def test_bad_source_never_publishes_partial_tree(tmp_path, mode):
    archive_path, pins = fixture_archive(
        tmp_path, duplicate=mode == "duplicate", symlink=mode == "symlink"
    )
    if mode == "missing":
        pins["original_description_sources"][0]["member"] = "absent.csv"
    if mode == "bytes":
        pins["original_description_sources"][0]["bytes"] += 1
    if mode == "hash":
        pins["original_description_sources"][0]["sha256"] = "0" * 64
    if mode == "archive":
        pins["archive"]["sha256"] = "0" * 64
    destination = tmp_path / "release"
    with pytest.raises(ValueError):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert not destination.exists()
    assert not list(tmp_path.glob(".source-prep-*"))
    assert archive_path.exists()


@pytest.mark.parametrize("value", ["../x", "/x", "C:/x", "a\\b", "a//b", "a/./b", ""])
def test_unsafe_output_paths_rejected(value):
    with pytest.raises(ValueError, match="output path"):
        prep.relative_path(value)


def test_case_collision_disk_limit_and_deadline(tmp_path, monkeypatch):
    archive_path, pins = fixture_archive(tmp_path)
    pins["original_description_sources"][0]["output"] = "SQLITE/DB.SQLITE"
    with pytest.raises(ValueError, match="collision"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    pins["original_description_sources"][0]["output"] = "original/db/table.csv"
    monkeypatch.setattr(prep.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 0})())
    with pytest.raises(ValueError, match="disk reserve"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    monkeypatch.setattr(prep.shutil, "disk_usage", lambda _: type("Usage", (), {"free": 10**12})())
    ticks = iter([0, 901])
    monkeypatch.setattr(prep, "monotonic", lambda: next(ticks))
    with pytest.raises(ValueError, match="deadline"):
        prep.extract_sources(archive_path, tmp_path / "release", pins=pins)
    assert not (tmp_path / "release").exists()


def test_refuses_existing_file_and_malformed_pin(tmp_path):
    archive_path, pins = fixture_archive(tmp_path)
    destination = tmp_path / "release"
    destination.write_bytes(b"keep")
    with pytest.raises(ValueError, match="already exists"):
        prep.extract_sources(archive_path, destination, pins=pins)
    assert destination.read_bytes() == b"keep"
    pins["archive"]["bytes"] = True
    with pytest.raises(ValueError, match="invalid source pin"):
        prep.checked_file(archive_path, pins["archive"])
