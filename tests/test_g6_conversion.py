import subprocess

import pytest

from scripts import run_g6_conversion as conversion


@pytest.mark.parametrize("failure", ["resource", "timeout", "exit"])
def test_conversion_failure_stops_only_owned_child(monkeypatch, failure):
    calls = []

    class Process:
        returncode = 1 if failure == "exit" else None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def poll(self):
            return self.returncode

        def wait(self, **kwargs):
            calls.append("wait")

        def kill(self):
            calls.append("kill")

    monkeypatch.setattr(conversion.subprocess, "Popen", lambda *a, **k: Process())
    times = iter([0, 901])
    monkeypatch.setattr(conversion.time, "monotonic", lambda: next(times))

    def monitor(**kwargs):
        if failure == "resource" and not kwargs.get("loading", True):
            raise RuntimeError("resource limit")

    monkeypatch.setattr(conversion, "monitor", monitor)
    with pytest.raises((RuntimeError, subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        conversion.run_tool(["owned-tool"], planned_c=1)
    assert calls == ["kill", "wait"]


def test_conversion_checks_projected_c_artifacts_before_start(monkeypatch):
    monkeypatch.setattr(conversion, "serving_storage", lambda: (13 * 2**30, 10 * 2**30))
    monkeypatch.setattr(conversion, "available_ram", lambda: 6 * 2**30)
    monkeypatch.setattr(
        conversion.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 21 * 2**30})()
    )
    with pytest.raises(RuntimeError, match="24 GiB"):
        conversion.monitor(planned_c=2 * 2**30)
