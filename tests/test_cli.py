import asyncio
import json
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal

import pytest

from scripts.prepare_cli_runtime import prepare
from sqlwarden import cli
from sqlwarden.executor import ExecutorLifecycleError, QueryResult
from sqlwarden.llm import Generation


class Provider:
    def __init__(self, result):
        self.result, self.questions = result, []

    async def generate(self, question):
        self.questions.append(question)
        return self.result


@pytest.mark.parametrize("question", ["", " ", "x" * 501, "line\nbreak", "\x1b[31m", "\ud800"])
async def test_invalid_question_has_no_model_or_database_io(question, monkeypatch):
    provider = Provider(Generation("SELECT 1", "ok", calls=1))
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once(question, "a" * 48, provider)
    assert answer["reason"] == "input_invalid" and provider.questions == []


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "short"},
        {"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "a" * 48, "WARDEN_BOOTSTRAP_PASSWORD": "CANARY"},
        {"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "a" * 48, "WARDEN_TEST_TARGET": "sqlwarden-local"},
        {"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "a" * 48, "ADMIN_DATABASE_URL": "CANARY"},
        {"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "a" * 48, "OPENAI_LOG": "debug"},
    ],
)
def test_runtime_environment_refuses_test_admin_or_bad_credentials(values):
    with pytest.raises(ValueError, match="runtime_configuration"):
        cli.runtime_password(values)


def test_runtime_password_accepts_only_the_separate_restricted_key():
    assert cli.runtime_password({"WARDEN_RUNTIME_CALIFORNIA_PASSWORD": "a" * 48}) == "a" * 48


@pytest.mark.parametrize(
    "generation",
    [
        Generation(None, "prompt_limit"),
        Generation(None, "model_output_invalid", calls=1),
        Generation(None, "model_output_incomplete", calls=1),
    ],
)
async def test_failed_generation_never_opens_executor(generation, monkeypatch):
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once("One.", "a" * 48, Provider(generation))
    assert answer["status"] == "failed" and "sql" not in answer


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM california_schools.schools",
        "SELECT * FROM pg_catalog.pg_class",
        "SELECT * FROM demo_other.canary",
        "SELECT pg_read_file('/x')",
    ],
)
async def test_guard_denial_never_opens_executor(sql, monkeypatch):
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once("One.", "a" * 48, Provider(Generation(sql, "ok", calls=1)))
    assert answer["status"] == "blocked" and "sql" not in answer


@pytest.mark.parametrize(
    "result",
    [
        QueryResult("ok", "ok", ("x",), ()),
        QueryResult("ok", "ok", ("x",), ((None,),)),
        QueryResult("overflow", "row_limit"),
        QueryResult("failed", "database_error"),
    ],
)
async def test_empty_null_and_nonok_results_keep_truthful_states(result, monkeypatch):
    class Executor:
        async def execute(self, sql):
            assert sql == "SELECT 1"
            return result

    @asynccontextmanager
    async def opened(password):
        assert password == "a" * 48
        yield Executor()

    monkeypatch.setattr(cli, "open_california_executor", opened)
    provider = Provider(Generation("SELECT 1", "ok", calls=1))
    answer = await cli.ask_once("One.", "a" * 48, provider)
    assert answer["status"] == ("answered" if result.status == "ok" else "failed")
    assert provider.questions == ["One."]
    assert "confidence" not in answer and "ex_score" not in answer
    if result.status != "ok":
        assert "rows" not in answer and "sql" not in answer


def test_preview_escapes_controls_and_labels_only_display_truncation():
    answer = {
        "status": "answered",
        "columns": ("x",),
        "rows": tuple(("\x1b\n" + str(i),) for i in range(21)),
        "row_count": 21,
    }
    text = cli.render(answer)
    data = json.loads(text)
    assert len(data["rows"]) == 20 and data["preview_truncated"] is True
    assert data["row_count"] == 21 and "\x1b" not in text
    assert json.loads(cli.render({"rows": ((Decimal("1.1"), date(2026, 1, 2), float("nan")),)}))[
        "rows"
    ] == [["1.1", "2026-01-02", "nan"]]


async def test_cancellation_propagates_and_does_not_continue_to_database(monkeypatch):
    entered = asyncio.Event()

    class Waiting:
        async def generate(self, question):
            entered.set()
            await asyncio.Event().wait()

    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    task = asyncio.create_task(cli.ask_once("One.", "a" * 48, Waiting()))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_loop_mode_uses_bounded_settings_and_trace(monkeypatch):
    class Provider:
        async def complete(self, messages, *, model_config):
            assert "Database Engine:" in messages[-1]["content"]
            return {"content": '{"sql":"SELECT school FROM schools"}'}

    class Executor:
        async def execute(self, sql):
            assert sql == "SELECT school FROM schools"
            return QueryResult("ok", "ok", ("school",), (("A",),))

    @asynccontextmanager
    async def opened(password):
        assert password == "a" * 48
        yield Executor()

    monkeypatch.setattr(cli, "open_california_executor", opened)
    answer = await cli.ask_loop(
        "List schools.",
        "a" * 48,
        Provider(),
        cli.AgentConfig(candidates=1, max_repairs=0, explain=False),
    )

    assert answer["status"] == "answered"
    assert answer["loop_settings"]["candidates"] == 1
    assert answer["agreement"] == 1
    assert answer["high_confidence"] is False
    assert "trace_summary" in answer


def test_setup_copy_is_exclusive_and_contains_only_restricted_runtime_value(tmp_path):
    (tmp_path / ".env.california").write_text("WARDEN_CALIFORNIA_PASSWORD=" + "a" * 48 + "\n")
    prepare(tmp_path)
    assert (
        tmp_path / ".env.runtime"
    ).read_text() == "WARDEN_RUNTIME_CALIFORNIA_PASSWORD=" + "a" * 48 + "\n"
    with pytest.raises(FileExistsError):
        prepare(tmp_path)


@pytest.mark.parametrize(
    "source", ["", "WARDEN_CALIFORNIA_PASSWORD=bad\n", "WARDEN_BOOTSTRAP_PASSWORD=" + "a" * 48]
)
def test_setup_does_not_copy_admin_or_malformed_source(tmp_path, source):
    (tmp_path / ".env.california").write_text(source)
    with pytest.raises(ValueError):
        prepare(tmp_path)
    assert not (tmp_path / ".env.runtime").exists()


def test_unknown_db_raw_sql_and_invalid_args_have_no_echo_or_io(monkeypatch, capsys):
    monkeypatch.setattr(cli, "LocalQwen", lambda: pytest.fail("Model constructed"))
    for argv in (
        ["sqlwarden", "ask", "--db", "CANARY", "One."],
        ["sqlwarden", "ask", "--raw-sql", "CANARY"],
        ["sqlwarden", "CANARY"],
    ):
        monkeypatch.setattr("sys.argv", argv)
        with pytest.raises(SystemExit) as stopped:
            cli.main()
        assert stopped.value.code == 2
        output = capsys.readouterr()
        assert "CANARY" not in output.out + output.err


async def test_library_error_is_fixed_without_canary_or_credential_echo(monkeypatch, caplog):
    class Broken:
        async def generate(self, question):
            raise RuntimeError("PRIVATE_CANARY")

    answer = await cli.ask_once("One.", "a" * 48, Broken())
    assert answer["status"] == "failed" and answer["reason"] == "internal_error"
    assert "PRIVATE_CANARY" not in cli.render(answer) + caplog.text
    assert answer["model_calls"] is None and answer["warmup_calls"] is None
    assert answer["trace"] == ["validate", "generate", "failed"]


async def test_enclosing_deadline_reports_unknown_attempts_without_database_io(monkeypatch):
    entered = asyncio.Event()
    original_timeout = asyncio.timeout

    class Waiting:
        async def generate(self, question):
            entered.set()
            await asyncio.Event().wait()

    monkeypatch.setattr(
        cli.asyncio, "timeout", lambda delay: original_timeout(0.05 if delay == 180 else delay)
    )
    monkeypatch.setattr(cli, "open_california_executor", lambda *a: pytest.fail("DB touched"))
    answer = await cli.ask_once("One.", "a" * 48, Waiting())
    assert entered.is_set() and answer["reason"] == "run_timeout"
    assert answer["model_calls"] is None and answer["warmup_calls"] is None
    assert answer["trace"] == ["validate", "generate", "failed"]


async def test_executor_lifecycle_failure_keeps_known_usage_but_not_sql_or_rows(
    monkeypatch, caplog
):
    @asynccontextmanager
    async def broken(password):
        raise ExecutorLifecycleError("PRIVATE_CANARY")
        yield

    monkeypatch.setattr(cli, "open_california_executor", broken)
    provider = Provider(Generation("SELECT 1", "ok", 80, 10, 1, 0))
    provider.cleanup_confirmed = False
    answer = await cli.ask_once("One.", "a" * 48, provider)
    assert answer["reason"] == "connection_error" and answer["status"] == "failed"
    assert answer["model_calls"] == 1 and answer["usage"]["prompt_tokens"] == 80
    assert answer["http_cleanup"] is False
    assert "sql" not in answer and "rows" not in answer
    assert "PRIVATE_CANARY" not in cli.render(answer) + caplog.text
    assert answer["trace"] == ["validate", "generate", "guard", "cost_execute", "failed"]


def test_main_refuses_setup_environment_before_constructing_provider(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sqlwarden", "ask", "--db", "california_schools", "One."])
    monkeypatch.setenv(cli.RUNTIME_KEY, "a" * 48)
    monkeypatch.setenv("WARDEN_BOOTSTRAP_PASSWORD", "PRIVATE_CANARY")
    monkeypatch.setattr(cli, "LocalQwen", lambda: pytest.fail("Model constructed"))
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    output = capsys.readouterr()
    assert stopped.value.code == 1
    assert json.loads(output.out)["reason"] == "runtime_or_input_configuration"
    assert "PRIVATE_CANARY" not in output.out + output.err


def test_main_refuses_bad_loop_settings_before_provider(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "sqlwarden",
            "ask",
            "--db",
            "california_schools",
            "--loop",
            "--candidates",
            "0",
            "One.",
        ],
    )
    monkeypatch.setattr(cli, "LocalQwen", lambda: pytest.fail("Model constructed"))
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    output = capsys.readouterr()
    assert stopped.value.code == 1
    assert json.loads(output.out)["reason"] == "runtime_or_input_configuration"


def test_main_success_uses_only_runtime_credential_and_escaped_output(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sqlwarden", "ask", "--db", "california_schools", "One."])
    for key in list(cli.os.environ):
        if (
            key.startswith("WARDEN_")
            or key in cli.PRIVATE_SDK_KEYS
            or key
            in {
                "ADMIN_DATABASE_URL",
                "APP_DATABASE_URL",
                "SANDBOX_DATABASE_URL",
                "PGPASSWORD",
                "OPENAI_LOG",
            }
        ):
            monkeypatch.delenv(key)
    monkeypatch.setenv(cli.RUNTIME_KEY, "a" * 48)

    async def answered(question, password, provider):
        assert question == "One." and password == "a" * 48
        return {"status": "answered", "rows": ((1,),), "row_count": 1}

    monkeypatch.setattr(cli, "ask_once", answered)
    cli.main()
    text = capsys.readouterr().out
    assert json.loads(text)["status"] == "answered" and "a" * 48 not in text


@pytest.mark.parametrize("key", sorted(cli.PRIVATE_SDK_KEYS))
def test_main_refuses_inherited_private_sdk_settings_before_provider(key, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sqlwarden", "ask", "--db", "california_schools", "One."])
    monkeypatch.setenv(cli.RUNTIME_KEY, "a" * 48)
    monkeypatch.setenv(key, "PRIVATE_CANARY")
    monkeypatch.setattr(cli, "LocalQwen", lambda: pytest.fail("Model constructed"))
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    output = capsys.readouterr()
    assert stopped.value.code == 1
    assert json.loads(output.out)["reason"] == "runtime_or_input_configuration"
    assert "PRIVATE_CANARY" not in output.out + output.err
