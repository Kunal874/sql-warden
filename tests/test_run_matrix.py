from scripts.run_matrix import derived_outcomes, ex, text_of
from sqlwarden.executor import QueryResult
from sqlwarden.voting import CandidateResult

A = QueryResult("ok", "ok", ("n",), ((1,),))
B = QueryResult("ok", "ok", ("n",), ((2,),))
BAD = QueryResult("failed", "syntax_error")


def _candidate(index, *attempts):
    final = attempts[-1]
    return CandidateResult(
        index,
        "ok" if final.status == "ok" else "failed",
        final.reason,
        result=final if final.status == "ok" else None,
        attempts=tuple((f"SELECT {index}", r) for r in attempts),
    )


def test_text_puts_evidence_before_the_question():
    assert text_of(" How many? ", " rate = a/b ") == "rate = a/b\nHow many?"
    assert text_of("How many?", None) == "How many?"


def test_empty_gold_is_valid_and_missing_gold_is_not_scored():
    empty = QueryResult("ok", "ok", ("n",), ())
    assert ex(empty, []) == 1
    assert ex(A, []) == 0
    assert ex(A, None) is None
    assert ex(None, []) == 0


def test_derived_outcomes_rescore_the_same_generations_as_smaller_loops():
    candidates = [_candidate(0, BAD, A), _candidate(1, B), _candidate(2, BAD, A)]

    derived = derived_outcomes(candidates, gold_c=[(1,)], gold_o=None)

    assert derived["n1_k0"]["status"] == "abstained"
    assert derived["n1_k0"]["ex_corrected"] == 0
    assert derived["n1_k1"] | {} == derived["n1_k1"]
    assert (derived["n1_k1"]["status"], derived["n1_k1"]["ex_corrected"]) == ("answered", 1)
    assert (derived["n3_k0"]["status"], derived["n3_k0"]["ex_corrected"]) == ("answered", 0)
    assert derived["n3_k0"]["agreement"] == 1 / 3
    assert (derived["n3_k1"]["status"], derived["n3_k1"]["agreement"]) == ("answered", 2 / 3)
    assert derived["n3_k1"]["ex_corrected"] == 1
    assert derived["n3_k1"]["ex_original"] is None
