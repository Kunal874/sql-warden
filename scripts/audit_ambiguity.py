"""E7 audit: one reviewed reason per C1 text-difference candidate (IDs only).

Method (2026-10-11): word-level diffs of original versus corrected question and
evidence for all 189 candidates were read and given one primary category. The first
four categories mean the original wording admitted several reasonable readings.
Writes docs/ambiguity-audit.json; no question text is stored.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "docs/gold-validity-manifest.json"
OUTPUT = ROOT / "docs/ambiguity-audit.json"

AMBIGUOUS = {
    "aggregation_scope_clarified": "which rows or records count (e.g. 'at least one record')",
    "output_specified": "what to return or in what form (columns, ids, yes/no, order)",
    "entity_reference_clarified": "which column or entity a term refers to",
    "calculation_clarified": "how a metric is computed (ratio direction, exact age, sums)",
}
NOT_AMBIGUOUS = {
    "factual_error_fixed": "the question named a wrong value, entity or date",
    "hint_formula_fixed": "the evidence hint was wrong or incomplete",
    "dialect_quoting_only": "identifier quoting changed for PostgreSQL",
    "typo_or_grammar": "spelling or equivalent wording",
    "whitespace_only": "no word-level difference",
}
REVIEWED = {
    "aggregation_scope_clarified": [
        145,
        198,
        200,
        201,
        215,
        240,
        242,
        255,
        260,
        263,
        549,
        584,
        637,
        672,
        726,
        862,
        877,
        940,
        959,
        962,
        1014,
        1029,
        1035,
        1037,
        1080,
        1084,
        1088,
        1124,
        1134,
        1135,
        1141,
        1144,
        1146,
        1148,
        1232,
        1235,
        1247,
        1254,
        1255,
        1270,
        1490,
        1505,
        1525,
    ],
    "output_specified": [
        17,
        27,
        37,
        83,
        87,
        94,
        95,
        128,
        129,
        159,
        189,
        231,
        244,
        248,
        340,
        341,
        344,
        349,
        465,
        469,
        473,
        530,
        587,
        634,
        728,
        766,
        772,
        865,
        866,
        894,
        928,
        967,
        989,
        1002,
        1011,
        1058,
        1092,
        1187,
        1205,
        1338,
        1399,
        1405,
        1486,
    ],
    "entity_reference_clarified": [
        23,
        25,
        41,
        92,
        93,
        168,
        169,
        412,
        557,
        571,
        861,
        896,
        902,
        906,
        950,
        1147,
        1166,
        1168,
        1175,
        1198,
        1201,
        1387,
        1426,
    ],
    "calculation_clarified": [
        48,
        194,
        898,
        1031,
        1149,
        1152,
        1156,
        1189,
        1227,
        1239,
        1241,
        1331,
        1376,
        1392,
        1403,
    ],
    "factual_error_fixed": [
        26,
        46,
        62,
        208,
        247,
        347,
        529,
        595,
        685,
        751,
        944,
        1133,
        1389,
        1500,
        1501,
    ],
    "hint_formula_fixed": [
        118,
        226,
        227,
        228,
        236,
        273,
        282,
        356,
        366,
        371,
        397,
        402,
        405,
        408,
        424,
        474,
        486,
        487,
        581,
        716,
        724,
        743,
        747,
        788,
        801,
        846,
        904,
        930,
        971,
        1155,
        1162,
        1185,
        1209,
        1275,
        1350,
    ],
    "dialect_quoting_only": [11, 28, 77, 85, 1091],
    "typo_or_grammar": [377, 937],
    "whitespace_only": [230, 249, 1003, 1032, 1036, 1116, 1507, 1528],
}


def build() -> dict:
    manifest = json.loads(GOLD.read_text(encoding="utf-8"))
    candidates = {i["question_id"]: i for i in manifest["usable_items"] if i["ambiguity_candidate"]}
    assigned = [qid for ids in REVIEWED.values() for qid in ids]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(candidates):
        raise SystemExit("every candidate needs exactly one reviewed category")
    category = {qid: name for name, ids in REVIEWED.items() for qid in ids}
    negatives = sorted(
        i["question_id"] for i in manifest["usable_items"] if not i["ambiguity_candidate"]
    )
    items = [
        {
            "question_id": qid,
            "db_id": candidates[qid]["db_id"],
            "category": category[qid],
            "ambiguous_original": category[qid] in AMBIGUOUS,
        }
        for qid in sorted(candidates)
    ]
    return {
        "format_version": 1,
        "reviewed_on": "2026-10-11",
        "method": "word-level diff of original vs corrected question and evidence; one category",
        "categories": {"ambiguous": AMBIGUOUS, "not_ambiguous": NOT_AMBIGUOUS},
        "counts": dict(Counter(item["category"] for item in items).most_common()),
        "ambiguous_original": sum(item["ambiguous_original"] for item in items),
        "changed_not_ambiguous": sum(not item["ambiguous_original"] for item in items),
        "clear_negatives": len(negatives),
        "items": items,
        "clear_negative_ids": negatives,
        "excludes": ["question text", "evidence text", "sql"],
    }


if __name__ == "__main__":
    report = build()
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "counts",
                    "ambiguous_original",
                    "changed_not_ambiguous",
                    "clear_negatives",
                )
            }
        )
    )
