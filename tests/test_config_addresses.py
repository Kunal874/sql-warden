import pytest

from sqlwarden.config import database_address, model_url


def test_defaults_are_the_local_laptop_services():
    assert database_address({}) == ("127.0.0.1", 55432)
    assert model_url({}) == "http://127.0.0.1:11434"


def test_container_addresses_are_accepted():
    env = {
        "WARDEN_DB_HOST": "postgres",
        "WARDEN_DB_PORT": "5432",
        "WARDEN_OLLAMA_URL": "http://host.docker.internal:11434",
    }
    assert database_address(env) == ("postgres", 5432)
    assert model_url(env) == "http://host.docker.internal:11434"


@pytest.mark.parametrize(
    "env",
    [
        {"WARDEN_DB_HOST": "a b"},
        {"WARDEN_DB_HOST": "x;y"},
        {"WARDEN_DB_HOST": ""},
        {"WARDEN_DB_PORT": "0"},
        {"WARDEN_DB_PORT": "70000"},
        {"WARDEN_DB_PORT": "5432x"},
    ],
)
def test_bad_database_addresses_are_refused(env):
    with pytest.raises(ValueError, match="database address refused"):
        database_address(env)


@pytest.mark.parametrize(
    "url",
    ["https://api.groq.com/openai/v1", "http://10.0.0.5:11434", "http://127.0.0.1:11434/"],
)
def test_inference_stays_local_until_a_hosted_model_is_approved(url):
    with pytest.raises(ValueError, match="model url refused"):
        model_url({"WARDEN_OLLAMA_URL": url})
