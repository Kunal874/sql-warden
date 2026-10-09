import json

import httpx
import pytest

from scripts import run_e0
from sqlwarden import evaluation


def test_schema_serialization_is_complete_and_bounded():
    schema = {
        "tables": {
            "school": {
                "description": "school table",
                "primary_key": ["id"],
                "foreign_keys": [{"columns": ["district_id"], "references": "district.id"}],
                "columns": [
                    {"name": "id", "type": "BIGINT", "description": "identifier"},
                    {"name": "district_id", "type": "BIGINT", "description": ""},
                ],
            },
            "district": {
                "description": "",
                "primary_key": ["id"],
                "foreign_keys": [],
                "columns": [{"name": "id", "type": "BIGINT", "description": "identifier"}],
            },
        }
    }

    rendered = evaluation.serialize_schema(schema, max_bytes=2048)

    assert "table school -- school table" in rendered
    assert "column school.id BIGINT -- identifier" in rendered
    assert "primary key school(id)" in rendered
    assert "foreign key school(district_id) -> district.id" in rendered
    with pytest.raises(evaluation.EvaluationError, match="schema budget"):
        evaluation.serialize_schema(schema, max_bytes=20)


def test_schema_serialization_preserves_long_descriptions_until_budget_refuses():
    long_description = "important " * 40
    schema = {
        "tables": {
            "school": {
                "description": "",
                "primary_key": [],
                "foreign_keys": [],
                "columns": [{"name": "note", "type": "TEXT", "description": long_description}],
            }
        }
    }

    rendered = evaluation.serialize_schema(schema, max_bytes=4096)

    assert long_description.strip() in rendered


def test_prompt_separates_schema_question_and_reference_data():
    messages = evaluation.build_prompt(
        question="How many schools are there?",
        schema_text="table school\ncolumn school.id BIGINT",
        model="qwen",
    )
    rendered = json.dumps(messages)

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "How many schools" in rendered
    assert "table school" in rendered
    assert "gold" not in rendered.lower()
    assert "expected answer" not in rendered.lower()
    assert "password" not in rendered.lower()


@pytest.mark.parametrize(
    ("content", "sql"),
    [
        ('{"sql":"SELECT count(*) FROM school"}', "SELECT count(*) FROM school"),
        ("```sql\nSELECT 1\n```", "SELECT 1"),
    ],
)
def test_strict_sql_extraction_accepts_one_readonly_statement(content, sql):
    assert evaluation.extract_sql(content) == sql


@pytest.mark.parametrize("content", ['{"sql":"SELECT 1","extra":true}', "SELECT 1; SELECT 2", ""])
def test_strict_sql_extraction_refuses_ambiguous_output(content):
    with pytest.raises(evaluation.EvaluationError):
        evaluation.extract_sql(content)


class FakeProvider:
    def __init__(self, content='{"sql":"SELECT 1"}'):
        self.content = content
        self.calls = 0

    async def complete(self, messages, *, model_config):
        self.calls += 1
        return {
            "content": self.content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            "memory": {"vram_bytes": 123},
            "seconds": 0.25,
            "model": model_config["alias"],
        }


@pytest.mark.asyncio
async def test_single_item_generation_is_one_call_no_retry_and_no_gold():
    provider = FakeProvider()

    record = await evaluation.generate_item(
        provider,
        {
            "question_id": 7,
            "db_id": "financial",
            "question": "Count accounts",
            "schema_text": "table account\ncolumn account.account_id BIGINT",
        },
        model_config={"name": "qwen", "alias": "local-qwen", "digest": "digest"},
    )

    assert provider.calls == 1
    assert record["status"] == "generated"
    assert record["sql"] == "SELECT 1"
    assert record["live_call"] is True
    assert record["usage"] == {"prompt_tokens": 10, "completion_tokens": 4}
    assert record["model_alias"] == "local-qwen"
    assert record["model_digest"] == "digest"
    assert "gold" not in json.dumps(record["messages"]).lower()


@pytest.mark.asyncio
async def test_generation_failure_preserves_provider_measurements_without_sql():
    provider = FakeProvider(content="not JSON")

    record = await evaluation.generate_item(
        provider,
        {
            "question_id": 9,
            "db_id": "financial",
            "question": "Count accounts",
            "schema_text": "table account\ncolumn account.account_id BIGINT",
        },
        model_config={"name": "qwen", "alias": "local-qwen", "digest": "digest"},
    )

    assert record["status"] == "generation_failed"
    assert record["reason"] == "model output invalid"
    assert record["usage"] == {"prompt_tokens": 10, "completion_tokens": 4}
    assert record["seconds"] == 0.25
    assert record["memory"] == {"vram_bytes": 123}
    assert record["model_alias"] == "local-qwen"
    assert "sql" not in record


@pytest.mark.asyncio
async def test_provider_transport_timeout_is_sanitized_generation_failure():
    class TimeoutProvider:
        async def complete(self, messages, *, model_config):
            raise httpx.ReadTimeout("PRIVATE_CANARY")

    record = await evaluation.generate_item(
        TimeoutProvider(),
        {
            "question_id": 10,
            "db_id": "financial",
            "question": "Count accounts",
            "schema_text": "table account\ncolumn account.account_id BIGINT",
        },
        model_config={"name": "qwen", "alias": "local-qwen", "digest": "digest"},
    )

    assert record["status"] == "generation_failed"
    assert record["reason"] == "model_timeout"
    assert "PRIVATE_CANARY" not in json.dumps(record)


@pytest.mark.asyncio
async def test_generation_refuses_prompt_when_context_output_budget_cannot_fit():
    provider = FakeProvider()

    record = await evaluation.generate_item(
        provider,
        {
            "question_id": 8,
            "db_id": "financial",
            "question": "Count accounts",
            "schema_text": "x" * 200,
        },
        model_config={
            "name": "qwen",
            "alias": "local-qwen",
            "digest": "digest",
            "context_tokens": 64,
            "max_output_tokens": 32,
        },
    )

    assert provider.calls == 0
    assert record["status"] == "generation_failed"
    assert record["reason"] == "prompt_budget"


def test_atomic_records_refuse_overwrite_and_mark_interrupted_pending(tmp_path):
    path = tmp_path / "raw" / "qwen" / "7.json"
    evaluation.write_atomic_record(path, {"question_id": 7, "status": "generated"})

    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "generated"
    with pytest.raises(evaluation.EvaluationError, match="exists"):
        evaluation.write_atomic_record(path, {"question_id": 7, "status": "again"})

    assert evaluation.pending_record(8, "qwen") == {
        "question_id": 8,
        "model": "qwen",
        "status": "pending",
        "reason": "interrupted",
    }


def test_jsonl_records_resume_after_interrupted_final_line(tmp_path):
    path = tmp_path / "raw" / "qwen" / "records.jsonl"
    first = {"question_id": 7, "model": "qwen", "status": "correct"}
    second = {"question_id": 8, "model": "qwen", "status": "incorrect"}

    evaluation.append_jsonl_record(path, first)
    evaluation.append_jsonl_record(path, second)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write('{"question_id": ')

    assert evaluation.load_jsonl_records(path) == [first, second]


def test_jsonl_records_reject_corrupt_middle_line(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text('{"ok": true}\nnot-json\n{"ok": false}\n', encoding="utf-8")

    with pytest.raises(evaluation.EvaluationError, match="jsonl record invalid"):
        evaluation.load_jsonl_records(path)


def test_resume_record_requires_matching_provenance():
    record = {
        "question_id": 7,
        "db_id": "financial",
        "model": "qwen",
        "model_alias": "local-qwen",
        "model_digest": "digest",
        "prompt_sha256": "a" * 64,
        "schema_sha256": "b" * 64,
        "data_sha256": "c" * 64,
        "label_sha256": "d" * 64,
        "git_commit": "e" * 40,
        "git_dirty": False,
        "status": "correct",
    }

    run_e0.validate_resume_record(record, record)

    changed = record | {"model_digest": "changed"}
    with pytest.raises(evaluation.EvaluationError, match="resume provenance"):
        run_e0.validate_resume_record(record, changed)


def test_run_manifest_fingerprints_config_without_raw_prompt_or_sql():
    item = {
        "question_id": 7,
        "git_commit": "e" * 40,
        "git_dirty": False,
    }
    protocol = {
        "split": {
            "dev_ids": [7, 8],
            "dev_id_sha256": "abc",
        }
    }

    manifest = run_e0.build_run_manifest("qwen", [item], protocol)
    rendered = json.dumps(manifest, sort_keys=True)

    assert manifest["run_fingerprint"]
    assert manifest["protocol"]["selected_id_sha256"]
    assert manifest["model"]["digest"] == run_e0.MODELS["qwen"]["digest"]
    assert "generated query text" in manifest["excludes"]
    assert "SELECT" not in rendered
    assert "messages" not in rendered
    assert "gold_sql" not in rendered
    run_e0.validate_resume_manifest(manifest, manifest)

    changed = manifest | {"model": manifest["model"] | {"digest": "changed"}}
    with pytest.raises(evaluation.EvaluationError, match="resume manifest"):
        run_e0.validate_resume_manifest(changed, manifest)


@pytest.mark.asyncio
async def test_run_models_refuses_existing_records_without_resume(tmp_path, monkeypatch):
    protocol = {"split": {"dev_ids": [7], "dev_id_sha256": "abc"}}
    item = {"question_id": 7, "git_commit": "e" * 40, "git_dirty": False}
    raw = tmp_path / "raw"
    existing = raw / "qwen" / "7.json"
    existing.parent.mkdir(parents=True)
    existing.write_text('{"question_id": 7}\n', encoding="utf-8")
    monkeypatch.setattr(run_e0, "RESULTS", tmp_path)
    monkeypatch.setattr(run_e0, "RAW", raw)
    monkeypatch.setattr(run_e0, "load_json", lambda path: protocol)
    monkeypatch.setattr(run_e0, "build_items", lambda limit: [item])

    with pytest.raises(evaluation.EvaluationError, match="run records exist"):
        await run_e0.run_models(["qwen"], limit=None, resume=False)

    assert not (raw / "qwen" / "manifest.json").exists()


def test_summary_uses_exact_denominator_and_seeded_interval():
    protocol = {"split": {"dev_ids": [1, 2, 3], "dev_id_sha256": "abc"}}
    records = [
        {
            "question_id": 1,
            "model": "qwen",
            "status": "correct",
            "seconds": 1.0,
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
            "memory": {"vram_bytes": 100},
        },
        {
            "question_id": 2,
            "model": "qwen",
            "status": "incorrect",
            "seconds": 3.0,
            "usage": {"prompt_tokens": 20, "completion_tokens": 4},
            "memory": {"vram_bytes": 300},
        },
        {
            "question_id": 3,
            "model": "qwen",
            "status": "blocked",
            "reason": "table_not_allowed",
            "seconds": 2.0,
            "usage": {"prompt_tokens": None, "completion_tokens": None},
            "memory": {"vram_bytes": 200},
        },
    ]

    summary = evaluation.summarize_model("qwen", records, protocol, seed=5, samples=200)

    assert summary["model"] == "qwen"
    assert summary["denominator"] == 3
    assert summary["correct"] == 1
    assert summary["ex"] == 1 / 3
    assert summary["median_seconds"] == 2.0
    assert summary["p95_seconds"] == 3.0
    assert summary["usage"] == {
        "known_items": 2,
        "prompt_tokens": 30,
        "completion_tokens": 6,
    }
    assert summary["reason_counts"] == {"table_not_allowed": 1}
    assert summary["peak_vram_bytes"] == 300
    assert summary["confidence_interval"]["n"] == 3
    assert 0 <= summary["confidence_interval"]["low"] <= summary["confidence_interval"]["high"] <= 1


def test_score_execution_categories_use_complete_gold_comparison():
    generated = {
        "question_id": 7,
        "db_id": "financial",
        "model": "qwen",
        "seconds": 1.2,
        "memory": {"vram_bytes": 123},
        "git_dirty": False,
    }

    correct = evaluation.score_execution(
        generated, {"status": "ok", "rows": [(1, "a")]}, gold_rows=[(1, "a")]
    )
    incorrect = evaluation.score_execution(
        generated, {"status": "ok", "rows": [(2, "a")]}, gold_rows=[(1, "a")]
    )
    set_match = evaluation.score_execution(
        generated, {"status": "ok", "rows": [(1,)]}, gold_rows=[(1,), (1,)]
    )
    blocked = evaluation.score_execution(
        generated, {"status": "blocked", "reason": "table_not_allowed"}, gold_rows=[(1, "a")]
    )
    failed = evaluation.score_execution(
        generated, {"status": "failed", "reason": "timeout"}, gold_rows=[(1, "a")]
    )

    assert correct["status"] == "correct"
    assert set_match["status"] == "correct"
    assert incorrect["status"] == "incorrect"
    assert blocked["status"] == "blocked"
    assert failed["status"] == "failed"
    assert "rows" not in correct
    assert correct["seconds"] == 1.2
    assert correct["memory"] == {"vram_bytes": 123}
    assert correct["git_dirty"] is False


def test_description_csv_reader_handles_known_windows_encoding(tmp_path):
    path = tmp_path / "budget.csv"
    path.write_bytes(
        b"original_column_name,column_name,column_description,data_format,value_description\r\n"
        b"Budget_ID,Budget_ID,approved \x95 bullet,text,\r\n"
    )

    descriptions = run_e0.read_description_csv(path)

    assert descriptions == {"Budget_ID": "approved • bullet"}
