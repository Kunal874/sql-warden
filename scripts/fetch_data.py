"""Verify a pinned source archive and extract only the first BIRD database.

Download URLs and provenance are recorded in docs/DATA.md. No archive-provided
SQL or executable is run, and archive paths are never used as output paths.
"""

import argparse
import hashlib
import json
import stat
import tempfile
import zipfile
from pathlib import Path

ARCHIVE_SHA256 = "aeb211c0e39010bbdae3838bb5e8bd27dc446ed77495b1709f85ccc9bf67f2be"
MAX_MEMBER_BYTES = 32 * 1024 * 1024
PREFIX = "minidev/MINIDEV/dev_databases/california_schools"
MEMBERS = {
    "california_schools.sqlite": f"{PREFIX}/california_schools.sqlite",
    "schools.csv": f"{PREFIX}/database_description/schools.csv",
    "satscores.csv": f"{PREFIX}/database_description/satscores.csv",
    "frpm.csv": f"{PREFIX}/database_description/frpm.csv",
    "dev_tables.json": "minidev/MINIDEV/dev_tables.json",
}


def extract_selected(archive_path: Path, destination: Path, expected_sha256: str) -> dict:
    if destination.exists():
        raise FileExistsError("Refusing to overwrite selected source data")
    with archive_path.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    if checksum != expected_sha256:
        raise ValueError("Source archive checksum differs from the pinned artifact")
    with zipfile.ZipFile(archive_path) as archive:
        selected = {}
        for output_name, source_name in MEMBERS.items():
            matches = [item for item in archive.infolist() if item.filename == source_name]
            if len(matches) != 1:
                raise ValueError("A required archive member is missing or duplicated")
            item = matches[0]
            if stat.S_ISLNK(item.external_attr >> 16) or item.is_dir() or item.flag_bits & 1:
                raise ValueError("A selected member is not a plain unencrypted file")
            if item.file_size > MAX_MEMBER_BYTES:
                raise ValueError("Selected archive member exceeds the extraction budget")
            selected[output_name] = item

        manifest = {
            "db_id": "california_schools",
            "archive": {
                "name": archive_path.name,
                "bytes": archive_path.stat().st_size,
                "sha256": checksum,
            },
            "files": [],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".bird-extract-", dir=destination.parent) as work:
            staging = Path(work)
            for output_name, item in selected.items():
                digest = hashlib.sha256()
                size = 0
                with archive.open(item) as source, (staging / output_name).open("xb") as output:
                    while chunk := source.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_MEMBER_BYTES:
                            raise ValueError("Decompressed data exceeds the extraction budget")
                        digest.update(chunk)
                        output.write(chunk)
                if size != item.file_size:
                    raise ValueError("Decompressed data size differs from the directory record")
                manifest["files"].append(
                    {
                        "name": output_name,
                        "source_member": item.filename,
                        "bytes": size,
                        "sha256": digest.hexdigest(),
                    }
                )
            (staging / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            staging.rename(destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/raw/minidev_0703.zip"))
    parser.add_argument("--output", type=Path, default=Path("data/bird_california"))
    args = parser.parse_args()
    manifest = extract_selected(args.archive, args.output, ARCHIVE_SHA256)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
