"""Setup-only extraction of pinned native COPY payloads for ten new datasets."""

import json
import shutil
import zipfile
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from scripts.audit_sources import inspect_native
from scripts.prepare_sources import (
    ARCHIVE,
    PINS_PATH,
    checked_file,
    load_pins,
    new_destination,
    relative_path,
    selected_member,
)
from sqlwarden.data import file_sha256

AUDIT_PATH = Path("docs/source-audit-manifest.json")
PINS_SHA = "f8c61dbc426deab580174c965fbd1883192e98ec30253e8d2b6aa85eb7114f7c"
AUDIT_SHA = "f52ecfd71c53fb470bb85e899e4b97178df304e0b30f66cba32518fa7f286c31"
BUNDLE = Path("data/import-release/minidev-0703/native")
DB_IDS = (
    "toxicology",
    "thrombosis_prediction",
    "superhero",
    "student_club",
    "debit_card_specializing",
    "formula_1",
    "financial",
    "card_games",
    "codebase_community",
    "european_football_2",
)


def load_specs():
    for path, expected in ((PINS_PATH, PINS_SHA), (AUDIT_PATH, AUDIT_SHA)):
        if path.stat().st_size > 256 * 1024 or file_sha256(path) != expected:
            raise ValueError("Reviewed metadata fingerprint differs")
    pins = load_pins()
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    return pins, audit


def bundle_metadata(pins):
    return {
        "format_version": 1,
        "source_pins_sha256": PINS_SHA,
        "source_audit_sha256": AUDIT_SHA,
        "tables": {
            name: {"db_id": t["db_id"], "columns": t["columns"], **t["copy"]}
            for name, t in pins["tables"].items()
            if t["db_id"] in DB_IDS
        },
    }


def validate_bundle(source, db_id):
    if db_id not in DB_IDS:
        raise ValueError("Unsupported dataset")
    pins, audit = load_specs()
    manifest = source / "manifest.json"
    if manifest.stat().st_size > 256 * 1024:
        raise ValueError("COPY manifest exceeds budget")
    if json.loads(manifest.read_text(encoding="utf-8")) != bundle_metadata(pins):
        raise ValueError("COPY metadata differs")
    tables = audit["databases"][db_id]["tables"]
    wanted = {n: t for n, t in pins["tables"].items() if t["db_id"] == db_id}
    if set(tables) != set(wanted):
        raise ValueError("Dataset table metadata differs")
    for name, table in wanted.items():
        checked_file(source / relative_path(db_id + "/" + name + ".tsv"), table["copy"])
        if [
            {"name": c["name"], "type": c["native_type"]} for c in tables[name]["columns"]
        ] != table["columns"]:
            raise ValueError("Dataset columns differ")
    return tables


def prepare_bundle(archive_path, destination):
    pins, _audit = load_specs()
    new_destination(destination)
    checked_file(archive_path, pins["archive"])
    selected = bundle_metadata(pins)["tables"]
    deadline = monotonic() + 1200
    destination.parent.mkdir(parents=True, exist_ok=True)
    if (
        shutil.disk_usage(destination.parent).free
        < sum(t["bytes"] for t in selected.values()) + 2**30
    ):
        raise ValueError("Insufficient COPY disk reserve")
    with TemporaryDirectory(prefix=".release-copy-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "native"
        staging.mkdir()
        with ExitStack() as outputs, zipfile.ZipFile(archive_path) as archive:
            sinks = {}
            for name, table in selected.items():
                path = staging / relative_path(table["db_id"] + "/" + name + ".tsv")
                path.parent.mkdir(parents=True, exist_ok=True)
                sinks[name] = outputs.enter_context(path.open("xb"))
            with archive.open(selected_member(archive, pins["native_dump"])) as stream:
                inspect_native(
                    stream,
                    pins["tables"],
                    pins["native_dump"],
                    deadline=deadline,
                    copy_outputs=sinks,
                )
        (staging / "manifest.json").write_text(
            json.dumps(bundle_metadata(pins), indent=2) + "\n", encoding="utf-8"
        )
        for db_id in DB_IDS:
            validate_bundle(staging, db_id)
        if monotonic() >= deadline:
            raise ValueError("COPY preparation deadline exceeded")
        new_destination(destination)
        staging.rename(destination)


def main():
    try:
        prepare_bundle(ARCHIVE, BUNDLE)
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": "COPY preparation",
                    "error_type": type(error).__name__,
                }
            )
        )
        return 1
    print(json.dumps({"status": "prepared", "datasets": 10, "tables": 72}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
