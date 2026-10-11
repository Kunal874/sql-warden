from scripts.render_eval_docs import readme_block, render_eval, render_resume, replace_block

CONDITION = {
    "n": 324,
    "pending": 0,
    "ex": {"count": 81, "rate": 0.25, "exact": {"low": 0.2, "high": 0.3}, "bootstrap": {}},
    "answered": {"count": 200, "rate": 0.617284},
    "answered_only_ex": {"count": 81, "rate": 0.405},
    "abstained": 124,
}
SPLIT = {
    "ids": 324,
    "conditions": {"full_n1": CONDITION, "ret_n3_k1": CONDITION},
    "comparisons": {
        "full_loop_vs_full_schema": {
            "left": "ret_n3_k1",
            "right": "full_n1",
            "n": 324,
            "left_only": 10,
            "right_only": 5,
            "difference": 0.015432,
            "ci": {"low": -0.01, "high": 0.04},
        }
    },
    "accuracy_coverage": {
        "curve": [{"threshold": "2/3", "coverage": 0.5, "selective_ex": 0.6, "end_to_end_ex": 0.3}],
        "frozen_threshold": "2/3",
    },
    "failure_taxonomy": {"wrong_result": 3},
    "latency": {"ret_n3_k1": {"median_item_seconds": 40.0, "peak_vram_bytes": 5133943438}},
}
SUMMARY = {"splits": {"held_out": SPLIT, "dev": SPLIT | {"ids": 100}}}


def test_readme_block_reports_tracked_numbers_with_the_qualifier():
    block = readme_block(SUMMARY)

    assert "Held-out (324 questions" in block
    assert "25.0%" in block and "20.0%–30.0%" in block
    assert "not an official BIRD score" in block
    assert "+1.5 pp" in block
    assert "2/3" in block and "60.0%" in block


def test_block_replacement_keeps_the_rest_of_the_readme():
    text = "intro\n<!-- results:start -->\nold\n<!-- results:end -->\noutro\n"
    assert replace_block(text, "new") == (
        "intro\n<!-- results:start -->\nnew\n<!-- results:end -->\noutro\n"
    )


def test_eval_and_resume_are_generated_from_the_summary_only():
    evaluation = render_eval(SUMMARY, e0={"arctic": {"ex": 0.22}, "qwen": {"ex": 0.03}})
    resume = render_resume(SUMMARY)

    assert evaluation.startswith("# Evaluation evidence")
    assert "E8" in evaluation and "E5" in evaluation and "E9" in evaluation
    assert "25.0%" in resume and "held-out" in resume.lower()
    for text in (evaluation, resume):
        assert "SELECT" not in text
