import pytest

from sqlwarden.provider import ProviderOutcome, ProviderRequest, local_ollama_config


def test_provider_request_is_typed_local_and_has_zero_hidden_retries():
    request = ProviderRequest(
        provider="ollama",
        base_url="http://127.0.0.1:11434",
        model="sqlwarden-arctic",
        revision="rev",
        digest="digest",
        template_sha256="template",
        messages=(("system", "Return SQL"), ("user", "Question")),
        params={"temperature": 0, "max_tokens": 1024},
        seed=42,
        sample_id="e0",
    )

    assert request.base_url == "http://127.0.0.1:11434"
    assert request.retries == 0
    assert request.http_retries == 0
    assert request.to_cache_material()["model"] == "sqlwarden-arctic"


@pytest.mark.parametrize(
    "base_url",
    ["https://127.0.0.1:11434", "http://localhost:11434", "http://127.0.0.1:9999"],
)
def test_provider_request_refuses_nonlocal_or_unpinned_url(base_url):
    with pytest.raises(ValueError, match="local provider"):
        ProviderRequest(
            provider="ollama",
            base_url=base_url,
            model="m",
            revision="r",
            digest="d",
            template_sha256="t",
            messages=(("user", "x"),),
            params={},
            seed=1,
            sample_id="s",
        )


def test_local_ollama_config_matches_no_retry_contract():
    config = local_ollama_config()

    assert config == {
        "base_url": "http://127.0.0.1:11434",
        "http_retries": 0,
        "sdk_retries": 0,
        "follow_redirects": False,
        "trust_env": False,
    }


def test_provider_outcome_records_usage_without_raw_text_or_zero_invention():
    outcome = ProviderOutcome(
        status="ok",
        content_sha256="a" * 64,
        prompt_tokens=10,
        completion_tokens=None,
        provider_calls=1,
        cache_hit=False,
    )

    assert outcome.to_json() == {
        "status": "ok",
        "content_sha256": "a" * 64,
        "prompt_tokens": 10,
        "completion_tokens": None,
        "provider_calls": 1,
        "cache_hit": False,
    }


@pytest.mark.parametrize("kwargs", [{"content_sha256": "short"}, {"provider_calls": -1}])
def test_provider_outcome_refuses_invalid_usage_or_content_hash(kwargs):
    fields = {
        "status": "ok",
        "content_sha256": "a" * 64,
        "prompt_tokens": None,
        "completion_tokens": None,
        "provider_calls": 1,
        "cache_hit": False,
    }
    fields.update(kwargs)

    with pytest.raises(ValueError, match="provider outcome"):
        ProviderOutcome(**fields).to_json()
