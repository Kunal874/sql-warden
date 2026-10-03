import hashlib
import json
import stat
import zipfile

import pytest

from scripts.fetch_data import MEMBERS, extract_selected


def make_archive(path, *, missing=None, duplicate=False, symlink=False):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for output_name, source_name in MEMBERS.items():
            if output_name == missing:
                continue
            info = zipfile.ZipInfo(source_name)
            if symlink and output_name == "california_schools.sqlite":
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, f"fixture: {output_name}".encode())
        archive.writestr("../../outside.txt", b"must never be extracted")
        if duplicate:
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(MEMBERS["schools.csv"], b"duplicate")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_extracts_only_exact_selected_files_and_records_content_hashes(tmp_path):
    source = tmp_path / "source.zip"
    checksum = make_archive(source)
    destination = tmp_path / "selected"
    manifest = extract_selected(source, destination, checksum)
    assert set(p.name for p in destination.iterdir()) == set(MEMBERS) | {"manifest.json"}
    assert not (tmp_path / "outside.txt").exists()
    assert manifest["archive"]["sha256"] == checksum
    assert json.loads((destination / "manifest.json").read_text()) == manifest
    for item in manifest["files"]:
        data = (destination / item["name"]).read_bytes()
        assert item["bytes"] == len(data)
        assert item["sha256"] == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("problem", ["missing", "duplicate", "symlink", "checksum", "oversize"])
def test_rejects_invalid_archives_without_publishing_partial_output(tmp_path, monkeypatch, problem):
    source = tmp_path / "source.zip"
    checksum = make_archive(
        source,
        missing="schools.csv" if problem == "missing" else None,
        duplicate=problem == "duplicate",
        symlink=problem == "symlink",
    )
    if problem == "checksum":
        checksum = "0" * 64
    if problem == "oversize":
        monkeypatch.setattr("scripts.fetch_data.MAX_MEMBER_BYTES", 8)
    destination = tmp_path / "selected"
    with pytest.raises(ValueError):
        extract_selected(source, destination, checksum)
    assert not destination.exists()
    assert not list(tmp_path.glob(".bird-extract-*"))


def test_refuses_to_overwrite_existing_selected_data(tmp_path):
    source = tmp_path / "source.zip"
    checksum = make_archive(source)
    destination = tmp_path / "selected"
    destination.mkdir()
    original = destination / "schools.csv"
    original.write_bytes(b"preserve this source")
    with pytest.raises(FileExistsError):
        extract_selected(source, destination, checksum)
    assert original.read_bytes() == b"preserve this source"
