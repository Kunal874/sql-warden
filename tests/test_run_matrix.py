import asyncio
import json
from contextlib import asynccontextmanager

import httpx
import pytest

from scripts.run_matrix import derived_outcomes, ex, text_of
from sqlwarden.executor import QueryResult
from sqlwarden.voting import CandidateResult

A = QueryResult("ok", "ok", ("n",), ((1,),))
B = QueryResult("ok", "ok", ("n",), ((2,),))
BAD = QueryResult("failed", "syntax_error")


def _candidate(index, *attempts):
    final = attempts[-1]
    return CandidateResult(
        index,
        "ok" if final.status == "ok" else "failed",
        final.reason,
        result=final if final.status == "ok" else None,
        attempts=tuple((f"SELECT {index}", r) for r in attempts),
    )


def test_text_puts_evidence_before_the_question():
    assert text_of(" How many? ", " rate = a/b ") == "rate = a/b\nHow many?"
    assert text_of("How many?", None) == "How many?"


def test_empty_gold_is_valid_and_missing_gold_is_not_scored():
    empty = QueryResult("ok", "ok", ("n",), ())
    assert ex(empty, []) == 1
    assert ex(A, []) == 0
    assert ex(A, None) is None
    assert ex(None, []) == 0


def test_derived_outcomes_rescore_the_same_generations_as_smaller_loops():
    candidates = [_candidate(0, BAD, A), _candidate(1, B), _candidate(2, BAD, A)]

    derived = derived_outcomes(candidates, gold_c=[(1,)], gold_o=None)

    assert derived["n1_k0"]["status"] == "abstained"
    assert derived["n1_k0"]["ex_corrected"] == 0
    assert derived["n1_k1"] | {} == derived["n1_k1"]
    assert (derived["n1_k1"]["status"], derived["n1_k1"]["ex_corrected"]) == ("answered", 1)
    assert (derived["n3_k0"]["status"], derived["n3_k0"]["ex_corrected"]) == ("answered", 0)
    assert derived["n3_k0"]["agreement"] == 1 / 3
    assert (derived["n3_k1"]["status"], derived["n3_k1"]["agreement"]) == ("answered", 2 / 3)
    assert derived["n3_k1"]["ex_corrected"] == 1
    assert derived["n3_k1"]["ex_original"] is None


@pytest.mark.parametrize("use_tuned,correct", [(False, 0), (True, 1)])
async def test_run_item_scores_the_selected_generator_without_changing_default(
    monkeypatch, use_tuned, correct
):
    from scripts import run_matrix
    from sqlwarden.executor import dataset_password_key
    from sqlwarden.ollama import ARCTIC, LocalModel, OllamaAgentProvider
    from sqlwarden.schema import SchemaCatalog

    tuned = LocalModel("test_tuned", "test-tuned:e9-v1", "a" * 64, 8192, 3072)
    selected = tuned if use_tuned else ARCTIC

    def network(request):
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": selected.alias, "digest": selected.digest}]}
            )
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": []})
        payload = json.loads(request.content)
        assert payload["model"] == selected.alias
        assert "fake-reader-value" not in request.content.decode()
        number = 2 if use_tuned else 1
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": f"```sql\nSELECT {number}\n```"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    monkeypatch.setattr(
        run_matrix,
        "OllamaAgentProvider",
        lambda **kwargs: OllamaAgentProvider(**kwargs, transport=httpx.MockTransport(network)),
    )
    catalog = SchemaCatalog.from_mapping(
        "california_schools",
        {
            "tables": {
                "schools": {
                    "columns": [{"name": "id", "type": "INTEGER"}],
                }
            }
        },
    )
    monkeypatch.setattr(run_matrix, "load_catalog", lambda db_id: catalog)

    class Executor:
        async def execute(self, sql):
            return QueryResult("ok", "ok", ("n",), ((2 if use_tuned else 1,),))

    @asynccontextmanager
    async def reader(db_id, value):
        assert db_id == "california_schools" and value == "fake-reader-value"
        yield Executor()

    async def reference(db_id, sql, values):
        return [(2,)]

    monkeypatch.setattr(run_matrix, "open_dataset_executor", reader)
    monkeypatch.setattr(run_matrix, "gold_rows", reference)
    item = {
        "question_id": 1,
        "db_id": "california_schools",
        "difficulty": "simple",
        "ambiguity_candidate": False,
        "input_changed": False,
        "corrected_text": "Return a count.",
        "gold_corrected": "SELECT 2",
        "gold_original": "SELECT 2",
        "original_label_status": "matched",
    }
    kwargs = {"generator": tuned} if use_tuned else {}
    result = await run_matrix.run_item(
        item,
        "full_n1",
        {dataset_password_key("california_schools"): "fake-reader-value"},
        None,
        asyncio.Lock(),
        **kwargs,
    )
    assert result["status"] == "answered"
    assert result["final_ex_corrected"] == correct
    assert result["calls"][0]["model"] == selected.name
