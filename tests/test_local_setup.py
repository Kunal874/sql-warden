"""Catch accidental admin-secret exposure and credential overwrites."""

import pytest

from scripts.init_local import initialize


def read_env(path):
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def test_separates_bootstrap_credentials_from_the_runtime_environment(tmp_path):
    initialize(tmp_path)
    setup = read_env(tmp_path / ".env.setup")
    runtime = read_env(tmp_path / ".env")
    assert "WARDEN_BOOTSTRAP_PASSWORD" in setup
    assert "WARDEN_BOOTSTRAP_PASSWORD" not in runtime
    assert "WARDEN_TEST_TARGET" not in runtime
    assert setup["WARDEN_TEST_TARGET"] == "sqlwarden-local"
    assert runtime["WARDEN_PG_PORT"] == "55432"
    assert all(
        len(setup[key]) >= 48
        for key in (
            "WARDEN_BOOTSTRAP_PASSWORD",
            "WARDEN_APP_PASSWORD",
            "WARDEN_SCHOOLS_PASSWORD",
            "WARDEN_OTHER_PASSWORD",
        )
    )
    assert len({setup[key] for key in setup if key.endswith("_PASSWORD")}) == 4


@pytest.mark.parametrize("existing", [".env", ".env.setup"])
def test_existing_credentials_are_never_overwritten(tmp_path, existing):
    path = tmp_path / existing
    path.write_text("OWNER_VALUE=keep\n")
    with pytest.raises(FileExistsError):
        initialize(tmp_path)
    assert path.read_text() == "OWNER_VALUE=keep\n"
    assert not (tmp_path / ({".env", ".env.setup"} - {existing}).pop()).exists()
