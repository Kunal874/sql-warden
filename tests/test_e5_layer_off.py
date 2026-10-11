import pytest

from scripts.e5_harness import ATTACKS, CONFIGS, LAYERS, succeeded
from scripts.run_e5_layer_off import require_local_docker, summarize

BASE = {"dataset_changed": False, "canary_changed": False}


def test_each_layer_off_config_differs_from_all_on_in_exactly_one_layer():
    configs = {c.name: c for c in CONFIGS}
    on = configs["all_layers_on"]
    off = [c for c in CONFIGS if c.name not in {"all_layers_on", "all_off_positive_control"}]

    assert {c.name for c in off} == {f"{layer}_off" for layer in LAYERS}
    for config in off:
        changed = [layer for layer in LAYERS if getattr(config, layer) != getattr(on, layer)]
        assert changed == [config.name.removesuffix("_off")]
    control = configs["all_off_positive_control"]
    assert all(getattr(control, layer) != getattr(on, layer) for layer in LAYERS)


def test_attack_ids_are_unique():
    assert len({attack[0] for attack in ATTACKS}) == len(ATTACKS)


def test_an_error_after_running_past_the_limit_still_counts_as_success():
    assert succeeded("ran_past_limit", {"error": True, "seconds": 6.0}, BASE, "c")
    assert not succeeded("ran_past_limit", {"error": True, "seconds": 2.1}, BASE, "c")


def test_an_error_never_counts_as_disclosure_but_a_real_change_does():
    assert not succeeded("canary_exposed", {"error": True, "rows_text": "c"}, BASE, "c")
    changed = BASE | {"dataset_changed": True}
    assert succeeded("dataset_modified", {"error": True}, changed, "c")


def test_role_switch_counts_only_when_the_session_identity_changed():
    assert succeeded("role_switched", {"login": "r", "current_user": "e5_owner"}, BASE, "c")
    assert not succeeded("role_switched", {"login": "r", "current_user": "r"}, BASE, "c")
    assert not succeeded("role_switched", {"error": True}, BASE, "c")


@pytest.mark.parametrize(
    "host", ["npipe:////./pipe/dockerDesktopLinuxEngine", "unix:///var/run/docker.sock"]
)
def test_local_docker_endpoints_are_accepted(host):
    require_local_docker(host)


@pytest.mark.parametrize("host", ["tcp://10.0.0.5:2376", "ssh://user@host", ""])
def test_remote_or_missing_docker_endpoints_are_refused(host):
    with pytest.raises(SystemExit):
        require_local_docker(host)


def test_summary_counts_per_config_and_names_single_layer_failures():
    raw = {
        "configs": [{"name": "all_layers_on"}, {"name": "guard_off"}],
        "results": [
            {"attack": "X", "config": "all_layers_on", "succeeded": False, "stopped_by": "L3"},
            {"attack": "Y", "config": "all_layers_on", "succeeded": False, "stopped_by": "L3"},
            {"attack": "X", "config": "guard_off", "succeeded": True, "stopped_by": None},
            {"attack": "Y", "config": "guard_off", "succeeded": False, "stopped_by": "L5"},
        ],
    }

    summary = summarize(raw)

    assert summary["configurations"]["all_layers_on"] == {
        "attacks": 2,
        "prevented": 2,
        "succeeded": 0,
        "stopped_by": {"L3": 2},
    }
    assert summary["configurations"]["guard_off"]["stopped_by"] == {"L5": 1}
    assert summary["succeeded_with_one_layer_off"] == {"X": ["guard_off"]}
    assert summary["prevented_with_any_one_layer_off"] == ["Y"]
