from scripts.run_e7_self_authored import matched_reading, summarize


def _row(partition, kind, *, asked, first, final, first_reading=None, final_reading=None):
    return {
        "partition": partition,
        "kind": kind,
        "asked": asked,
        "first_status": "needs_clarification" if asked else "answered",
        "first_correct": first,
        "final_correct": final,
        "first_reading": first_reading,
        "final_reading": final_reading,
        "helper_options": 2 if asked else 0,
        "helper_calls": [{"seconds": 4.0}] if asked else [],
    }


def test_reading_match_distinguishes_intended_other_and_neither():
    assert matched_reading("a", {"A": "a", "B": "b"}) == "A"
    assert matched_reading("c", {"A": "a", "B": "b"}) == "neither"
    assert matched_reading(None, {"A": "a"}) is None


def test_summary_separates_false_asks_and_clarification_outcomes():
    rows = [
        _row("evaluation", "ambiguous", asked=True, first=False, final=True, final_reading="B"),
        _row(
            "evaluation",
            "ambiguous",
            asked=False,
            first=False,
            final=False,
            first_reading="A",
            final_reading="A",
        ),
        _row("evaluation", "clear", asked=True, first=False, final=False),
        _row("evaluation", "clear", asked=False, first=True, final=True),
    ]

    summary = summarize(rows)

    ambiguous, clear = summary["evaluation_ambiguous"], summary["evaluation_clear"]
    assert (ambiguous["asked"], ambiguous["asked_then_correct"]) == (1, 1)
    assert ambiguous["first_reading"] == {"A": 1, "None": 1}
    assert (clear["asked"], clear["asked_then_wrong"], clear["correct_final"]) == (1, 1, 1)
    assert clear["helper_median_seconds"] == 4.0


def test_simulated_reply_uses_the_frozen_meaning_or_restates_a_clear_question():
    from scripts.run_e7_self_authored import simulated_reply

    assert simulated_reply({"kind": "ambiguous", "question": "Q?", "reply": "I mean A."}) == (
        "I mean A."
    )
    assert simulated_reply({"kind": "clear", "question": "How many rows?"}) == (
        "I mean exactly what I asked: How many rows?"
    )
