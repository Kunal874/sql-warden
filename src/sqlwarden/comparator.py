"""Offline row-set EX for complete results, not the future voting comparator.

Rule independently reproduced from bird-bench/mini_dev evaluation_ex.py,
revision abd11b6db92a1c9f809b32f7564c7c71b34d67f0, lines 18-22.
See docs/EX_COMPARATOR.md for the primary-source link and fingerprints.
"""

from dataclasses import dataclass
from typing import Literal

from sqlwarden.executor import QueryResult, Row


@dataclass(frozen=True, slots=True)
class EXComparison:
    score: Literal[0, 1] | None
    reason: Literal["match", "mismatch", "prediction_failed", "gold_invalid", "comparison_error"]


def _row_set(result: QueryResult) -> set[Row]:
    if type(result.rows) is not tuple or any(type(row) is not tuple for row in result.rows):
        raise TypeError("Invalid result row container")
    return set(result.rows)


def compare_ex(predicted: QueryResult, reference: QueryResult) -> EXComparison:
    """Score a terminal prediction; invalid gold does not select a denominator."""
    if type(reference) is not QueryResult or reference.status != "ok":
        return EXComparison(None, "gold_invalid")
    try:
        reference_rows = _row_set(reference)
    except (TypeError, ValueError, ArithmeticError):
        return EXComparison(None, "gold_invalid")
    if type(predicted) is not QueryResult or predicted.status != "ok":
        return EXComparison(0, "prediction_failed")
    try:
        matches = _row_set(predicted) == reference_rows
    except (TypeError, ValueError, ArithmeticError):
        return EXComparison(0, "comparison_error")
    return EXComparison(1, "match") if matches else EXComparison(0, "mismatch")
