"""Offline correction inspection. Never imported by the SQL runtime."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

REVISION = "fe766045c55b6875a43b30e9ac7683df5582f8cf"
CORRECTION_DIR = "corrections/arcwise-fe766045"
DATABASES = {
    "california_schools",
    "card_games",
    "codebase_community",
    "debit_card_specializing",
    "european_football_2",
    "financial",
    "formula_1",
    "student_club",
    "superhero",
    "thrombosis_prediction",
    "toxicology",
}
SOURCE_NAMES = {"bird_sqlite", "bird_pg", "arcwise_sql", "arcwise_full"}
PINS = {
    "bird_sqlite": (
        "raw/mini_dev_sqlite.json",
        278513,
        "88ceb0710163cae46a256ecea8f0a8c98286599530b60587fda5c3cfe57d45d2",
    ),
    "bird_pg": (
        "raw/mini_dev_pg.json",
        283551,
        "7fa740ef9225389cff6c34432120e8325d0ca3008d73db1ae38731234bc10da7",
    ),
    "arcwise_sql": (
        CORRECTION_DIR + "/arcwise_plat_sql_only_with_diff.json",
        287718,
        "e7bf76408f99266506ea558d84982c69422e5db3dfecab5f08a3a8d3900e8395",
    ),
    "arcwise_full": (
        CORRECTION_DIR + "/arcwise_plat_full_with_diff.json",
        332246,
        "baefe2ca4fbab86c000df72aad9eaa563f7d422e425af2cbff071f656ea4eea8",
    ),
}
REQUIRED = {"question_id", "db_id", "question", "evidence", "SQL"}
OPTIONAL = {"difficulty", "original_SQL", "original_question", "original_evidence"}


class LabelError(ValueError):
    """Stable offline failure without record text or SQL."""


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LabelError("duplicate JSON field")
        result[key] = value
    return result


def _constant(value):
    raise LabelError("non-standard JSON constant")


def read_pinned(path: Path, size: int, digest: str) -> bytes:
    try:
        if path.is_symlink():
            raise LabelError("source is a symlink")
        with path.open("rb") as stream:
            raw = stream.read(size + 1)
    except OSError:
        raise LabelError("source unavailable") from None
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise LabelError("source pin mismatch")
    return raw


def decode_labels(raw: bytes, *, corrected: bool) -> dict[int, dict]:
    if not raw or len(raw) > 600000:
        raise LabelError("document size rejected")
    try:
        rows = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise LabelError("invalid JSON") from None
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise LabelError("record count rejected")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not row.keys() >= REQUIRED:
            raise LabelError("required fields missing")
        if row.keys() - (REQUIRED | OPTIONAL):
            raise LabelError("unreviewed field")
        value = row["question_id"]
        if corrected:
            if not isinstance(value, str) or not re.fullmatch("[1-9][0-9]{0,5}", value):
                raise LabelError("invalid corrected ID")
            identifier = int(value)
        else:
            if type(value) is not int or not 1 <= value <= 999999:
                raise LabelError("invalid original ID")
            identifier = value
        if identifier in result:
            raise LabelError("duplicate ID")
        for field in (REQUIRED | OPTIONAL) - {"question_id", "difficulty"}:
            if field in row and not isinstance(row[field], str):
                raise LabelError("invalid text field")
        if not row["question"].strip() or not row["SQL"].strip() or row["db_id"] not in DATABASES:
            raise LabelError("invalid required value")
        if "difficulty" in row and (
            not isinstance(row["difficulty"], str)
            or row["difficulty"] not in {"simple", "moderate", "challenging"}
        ):
            raise LabelError("invalid difficulty")
        if not corrected and "difficulty" not in row:
            raise LabelError("original difficulty missing")
        result[identifier] = dict(row, question_id=identifier)
    return result


def build_report(sources: dict[str, dict[int, dict]]) -> dict:
    if sources.keys() != SOURCE_NAMES:
        raise LabelError("source set mismatch")
    original = sources["bird_sqlite"]
    by_source = {}
    for name in sorted(sources):
        current = sources[name]
        common = sorted(original.keys() & current.keys())
        database_mismatch = [i for i in common if original[i]["db_id"] != current[i]["db_id"]]
        track = {
            "count": len(current),
            "identity_aligned_count": len(common) - len(database_mismatch),
            "missing_ids": sorted(original.keys() - current.keys()),
            "unexpected_ids": sorted(current.keys() - original.keys()),
            "database_mismatch_ids": database_mismatch,
            "difficulty_mismatch_ids": [
                i
                for i in common
                if "difficulty" in current[i]
                and current[i]["difficulty"] != original[i]["difficulty"]
            ],
        }
        for field, label in (("question", "question"), ("evidence", "evidence"), ("SQL", "sql")):
            track[label + "_difference_ids"] = [
                i for i in common if original[i][field] != current[i][field]
            ]
        track["question_anchor_mismatch_ids"] = [
            i
            for i in common
            if current[i].get("original_question", current[i]["question"])
            != original[i]["question"]
        ]
        track["evidence_anchor_mismatch_ids"] = [
            i
            for i in common
            if current[i].get("original_evidence", current[i]["evidence"])
            != original[i]["evidence"]
        ]
        by_source[name] = track
    sql_only, full = sources["arcwise_sql"], sources["arcwise_full"]
    pair = sorted(sql_only.keys() & full.keys())
    return {
        "format_version": 1,
        "original_count": len(original),
        "per_database": dict(sorted(Counter(r["db_id"] for r in original.values()).items())),
        "per_difficulty": dict(sorted(Counter(r["difficulty"] for r in original.values()).items())),
        "by_source": by_source,
        "corrected_pair_missing_from_sql_ids": sorted(full.keys() - sql_only.keys()),
        "corrected_pair_missing_from_full_ids": sorted(sql_only.keys() - full.keys()),
        "corrected_pair_database_mismatch_ids": [
            i for i in pair if sql_only[i]["db_id"] != full[i]["db_id"]
        ],
        "corrected_pair_text_difference_ids": [
            i
            for i in pair
            if sql_only[i]["question"] != full[i]["question"]
            or sql_only[i]["evidence"] != full[i]["evidence"]
        ],
        "execution_validity": "not_run",
        "primary_labels": "not_selected",
        "ambiguity_labels": "not_classified",
        "splits": "not_frozen",
    }


def inspect_local(data_root: Path) -> dict:
    sources = {
        name: decode_labels(
            read_pinned(data_root / filename, size, digest), corrected=name.startswith("arcwise_")
        )
        for name, (filename, size, digest) in PINS.items()
    }
    return build_report(sources)


def main() -> int:
    try:
        report = inspect_local(Path("data"))
    except LabelError as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
