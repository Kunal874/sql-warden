from scripts.build_matrix_report import (
    accuracy_coverage_curve,
    condition_metrics,
    paired,
    select_threshold,
)


def _view(*rows):
    return {
        index: {"status": status, "agreement": agreement, "ex_corrected": ex}
        for index, (status, agreement, ex) in enumerate(rows)
    }


def test_condition_metrics_keep_abstentions_and_pending_in_the_denominator():
    view = _view(("answered", 1.0, 1), ("answered", 1 / 3, 0), ("abstained", 1 / 3, 0))

    metrics = condition_metrics(view, ids=[0, 1, 2, 3])

    assert metrics["n"] == 4 and metrics["pending"] == 1
    assert metrics["ex"]["count"] == 1 and metrics["ex"]["rate"] == 0.25
    assert metrics["answered"]["count"] == 2
    assert metrics["answered_only_ex"]["rate"] == 0.5
    assert metrics["ex"]["exact"]["low"] is not None


def test_accuracy_coverage_curve_and_predefined_threshold_rule():
    view = _view(
        ("answered", 1.0, 1),
        ("answered", 1.0, 1),
        ("answered", 2 / 3, 1),
        ("answered", 2 / 3, 0),
        ("answered", 1 / 3, 0),
        ("abstained", 1 / 3, 0),
    )

    curve = accuracy_coverage_curve(view, ids=list(range(6)))

    assert [point["threshold"] for point in curve] == ["1/3", "2/3", "1"]
    assert [point["covered"] for point in curve] == [5, 4, 2]
    assert [point["selective_ex"] for point in curve] == [0.6, 0.75, 1.0]
    assert select_threshold(curve) == "2/3"
    assert select_threshold([{"threshold": "1/3", "coverage": 0.2, "selective_ex": 0.9}]) == "1/3"


def test_paired_difference_counts_discordant_items():
    left = _view(("answered", 1.0, 1), ("answered", 1.0, 0), ("answered", 1.0, 1))
    right = _view(("answered", 1.0, 0), ("answered", 1.0, 0), ("answered", 1.0, 1))

    result = paired(left, right, ids=[0, 1, 2])

    assert (result["left_only"], result["right_only"], result["both"]) == (1, 0, 1)
    assert result["difference"] == round(1 / 3, 6)
    assert result["ci"]["n"] == 3
