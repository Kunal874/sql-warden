from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_three_static_pages_exist_with_required_states_and_no_inline_model_html():
    pages = {
        "ask.html": ["loading", "overload", "model-unavailable", "interrupted", "blocked"],
        "attack-lab.html": ["observed blocker", "false block", "all layers on"],
        "benchmark.html": ["Arctic", "Qwen", "answered-only", "not an official benchmark"],
    }

    for filename, required in pages.items():
        text = (ROOT / "web" / filename).read_text(encoding="utf-8")
        assert "<script>" not in text
        assert "innerHTML" not in text
        for phrase in required:
            assert phrase in text


def test_local_full_stack_smoke_script_reports_static_pages_and_api_flow(capsys):
    from scripts import smoke_g4_local

    assert smoke_g4_local.main() == 0
    output = capsys.readouterr().out
    assert "ask.html" in output
    assert "api_run_status=answered" in output
