"""Complete-result voting for generated SQL candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlwarden.executor import QueryResult


@dataclass(frozen=True, slots=True)
class CandidateResult:
    index: int
    status: Literal["ok", "blocked", "failed"]
    reason: str
    sql: str | None = None
    result: QueryResult | None = None
    repairs: int = 0


@dataclass(frozen=True, slots=True)
class VoteResult:
    status: Literal["answered", "abstained"]
    reason: str
    agreement: float
    high_confidence: bool
    selected: CandidateResult | None


def vote(candidates: list[CandidateResult], *, requested: int) -> VoteResult:
    if type(requested) is not int or requested <= 0 or len(candidates) > requested:
        raise ValueError("vote input refused")
    groups: dict[tuple, list[CandidateResult]] = {}
    for candidate in candidates:
        if (
            candidate.status == "ok"
            and candidate.result is not None
            and candidate.result.status == "ok"
        ):
            groups.setdefault(
                (candidate.result.columns, candidate.result.rows),
                [],
            ).append(candidate)
    if not groups:
        return VoteResult("abstained", "no_valid_candidate", 0.0, False, None)
    ranked = sorted(groups.values(), key=lambda group: (-len(group), group[0].index))
    if len(ranked) > 1 and len(ranked[0]) == len(ranked[1]):
        return VoteResult("abstained", "vote_tie", len(ranked[0]) / requested, False, None)
    selected = ranked[0][0]
    agreement = len(ranked[0]) / requested
    return VoteResult(
        "answered",
        "single_candidate" if requested == 1 else "consensus",
        agreement,
        requested > 1 and agreement > 0.5,
        selected,
    )
