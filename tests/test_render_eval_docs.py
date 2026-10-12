import json

import pytest

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


def test_layer_off_section_names_attacks_that_one_layer_off_lets_through():
    row = {"attacks": 2, "prevented": 1, "succeeded": 1, "stopped_by": {"L5_database_role": 1}}
    layer_off = {
        "project": "sqlwarden_e5_disposable",
        "configurations": {
            "all_layers_on": row | {"prevented": 2, "succeeded": 0},
            "guard_off": row,
        },
        "succeeded_with_one_layer_off": {"L-A4-05": ["guard_off"]},
        "prevented_with_any_one_layer_off": ["L-A1-01"],
    }

    evaluation = render_eval(SUMMARY | {"layer_off": layer_off}, e0={})

    assert "| guard off | 2 | 1 | 1 | L5 database role 1 |" in evaluation
    assert "1 of 2 attacks stayed prevented with any single layer off" in evaluation
    assert "L-A4-05 (guard_off)" in evaluation


def test_resume_reports_attack_bound_and_names_single_layer_dependencies():
    summary = SUMMARY | {
        "security": {
            "attacks": 43,
            "succeeded": 0,
            "success_rate_exact_95": {"low": 0.0, "high": 0.082211},
            "gold_accepted": 421,
            "gold_items": 424,
        },
        "layer_off": {
            "configurations": {"all_layers_on": {"attacks": 29}},
            "prevented_with_any_one_layer_off": ["X"] * 27,
            "succeeded_with_one_layer_off": {"L-A4-05": ["guard_off"], "L-A5-03": ["timeout_off"]},
        },
    }

    resume = render_resume(summary)

    assert "0 of 43 succeeded (exact 95% upper bound 8.2%; recorded suite only)" in resume
    assert "27 of 29 attacks stayed prevented with any single layer off" in resume
    assert "L-A4-05 depended on the SQL guard alone" in resume
    assert "L-A5-03 depended on the statement timeout alone" in resume
    assert "overlapping defenses rather than one point of failure" not in resume


@pytest.mark.parametrize(
    "resume_heading",
    ["## G6 training evidence — accuracy comparison pending", "## G6 fine-tuning evidence"],
)
def test_document_regeneration_refreshes_g3_but_preserves_g6_addenda(
    tmp_path, monkeypatch, resume_heading
):
    from scripts import build_matrix_report

    (tmp_path / "results/E0_smoke").mkdir(parents=True)
    (tmp_path / "results/E0_smoke/dashboard.json").write_text(
        json.dumps({"models": {}}), encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "intro\n<!-- results:start -->\nold G3\n<!-- results:end -->\nG6 unchanged\n",
        encoding="utf-8",
    )
    evaluation_tail = "## E9 — fine-tuning\n\nTraining complete; accuracy comparison pending.\n"
    resume_tail = f"{resume_heading}\n\nFull run 2000; selected checkpoint 1600.\n"
    (tmp_path / "docs/EVAL.md").write_text("old G3\n\n" + evaluation_tail, encoding="utf-8")
    (tmp_path / "docs/RESUME.md").write_text("old G3\n\n" + resume_tail, encoding="utf-8")
    monkeypatch.setattr(build_matrix_report, "ROOT", tmp_path)

    for _ in range(2):
        build_matrix_report.write_docs(SUMMARY)
        evaluation = (tmp_path / "docs/EVAL.md").read_text(encoding="utf-8")
        resume = (tmp_path / "docs/RESUME.md").read_text(encoding="utf-8")
        assert evaluation.endswith(evaluation_tail)
        assert resume.endswith(resume_tail)
        assert evaluation.count("## E9") == resume.count("## G6") == 1
        for document in [evaluation, resume]:
            assert "old G3" not in document and "25.0%" in document
        readme = (tmp_path / "README.md").read_text(encoding="utf-8")
        assert "old G3" not in readme and readme.endswith("G6 unchanged\n")


def test_top_failure_reasons_are_ranked_after_sorted_json_reload():
    phase = {
        "candidates": 10,
        "sql_extracted": 1.0,
        "guard_accepted": 0.5,
        "executed": 0.0,
        "first_attempt_failure_reasons": {
            "alpha": 1,
            "bravo": 1,
            "charlie": 1,
            "delta": 1,
            "zebra": 6,
        },
    }
    persisted = json.loads(
        json.dumps(
            SUMMARY | {"splits": {"dev": SPLIT | {"phase_rates": {"full_n1": phase}}}},
            sort_keys=True,
        )
    )
    evaluation = render_eval(persisted, e0={})
    row = next(line for line in evaluation.splitlines() if line.startswith("| full_n1 | 10 |"))
    assert row.endswith("| zebra 6, alpha 1, bravo 1, charlie 1 |")
