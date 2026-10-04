"""A local single-candidate demonstration, not the full agent or EX evaluator."""

import argparse
import asyncio
import json
import math
import os
import re
from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from sqlwarden.executor import ExecutorLifecycleError, open_california_executor
from sqlwarden.guard import CALIFORNIA_POLICY, guard_sql
from sqlwarden.llm import ALIAS, DIGEST, PRIVATE_SDK_KEYS, PROMPT_VERSION, LocalQwen

RUNTIME_KEY = "WARDEN_RUNTIME_CALIFORNIA_PASSWORD"


def validate_question(question: str) -> str | None:
    try:
        if (
            type(question) is not str
            or not question.strip()
            or len(question) > 500
            or any(ord(c) < 32 or 127 <= ord(c) < 160 for c in question)
        ):
            return "input_invalid"
        question.encode("utf-8")
    except UnicodeError:
        return "input_invalid"
    return None


def runtime_password(values: Mapping[str, str]) -> str:
    forbidden = {
        "ADMIN_DATABASE_URL",
        "APP_DATABASE_URL",
        "SANDBOX_DATABASE_URL",
        "PGPASSWORD",
        "OPENAI_LOG",
    } | PRIVATE_SDK_KEYS
    if (
        any(k.startswith("WARDEN_") and k != RUNTIME_KEY for k in values)
        or forbidden.intersection(values)
        or re.fullmatch(r"[a-f0-9]{48}", values.get(RUNTIME_KEY, "")) is None
    ):
        raise ValueError("runtime_configuration") from None
    return values[RUNTIME_KEY]


async def ask_once(question: str, password: str, provider) -> dict:
    answer = {
        "status": "failed",
        "reason": "input_invalid",
        "model_calls": 0,
        "warmup_calls": 0,
        "trace": ["validate"],
        "prompt_version": PROMPT_VERSION,
        "model": ALIAS,
        "model_digest": DIGEST,
    }
    if validate_question(question):
        answer["trace"].append("failed")
        return answer
    generation = None
    try:
        async with asyncio.timeout(180):
            answer["trace"].append("generate")
            generation = await provider.generate(question)
            answer.update(
                reason=generation.reason,
                model_calls=generation.calls,
                warmup_calls=generation.warmups,
                http_cleanup=getattr(provider, "cleanup_confirmed", None),
                usage={
                    "prompt_tokens": generation.prompt_tokens,
                    "completion_tokens": generation.completion_tokens,
                },
            )
            if generation.sql is None or generation.reason != "ok":
                answer["trace"].append("failed")
                return answer
            answer["trace"].append("guard")
            decision = guard_sql(generation.sql, CALIFORNIA_POLICY)
            if not decision.accepted:
                answer.update(status="blocked", reason=decision.reason)
                answer["trace"].append("blocked")
                return answer
            answer["trace"].append("cost_execute")
            async with open_california_executor(password) as executor:
                result = await executor.execute(decision.sql)
            answer.update(
                status="answered"
                if result.status == "ok"
                else "blocked"
                if result.status == "blocked"
                else "failed",
                reason=result.reason,
            )
            if result.status == "ok":
                answer.update(
                    sql=decision.sql,
                    columns=result.columns,
                    rows=result.rows,
                    row_count=len(result.rows),
                )
            answer["trace"].append(answer["status"])
            return answer
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        answer.update(status="failed", reason="run_timeout")
        if generation is None:
            answer.update(model_calls=None, warmup_calls=None)
    except ExecutorLifecycleError:
        answer.update(status="failed", reason="connection_error")
    except Exception:
        answer.update(status="failed", reason="internal_error")
        if generation is None:
            answer.update(model_calls=None, warmup_calls=None)
    answer["trace"].append(answer["status"])
    return answer


def _display_cell(value):
    if type(value) in (Decimal, date) or type(value) is float and not math.isfinite(value):
        return str(value)
    return value


def render(answer: dict) -> str:
    output = dict(answer)
    if "rows" in output:
        rows = output["rows"]
        output["preview_truncated"] = len(rows) > 20
        output["rows"] = [[_display_cell(cell) for cell in row] for row in rows[:20]]
    return json.dumps(output, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        print('{"status":"failed","reason":"invalid_arguments"}')
        raise SystemExit(2)


def main() -> None:
    parser = _Parser(
        description="Local single-candidate SQL demonstration; no accuracy/confidence score"
    )
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    ask = sub.add_parser("ask")
    ask.add_argument("--db", required=True, choices=["california_schools"])
    ask.add_argument("question")
    args = parser.parse_args()
    try:
        if validate_question(args.question):
            raise ValueError("input_invalid")
        password = runtime_password(os.environ)
        answer = asyncio.run(ask_once(args.question, password, LocalQwen()))
    except ValueError:
        answer = {"status": "failed", "reason": "runtime_or_input_configuration"}
    except KeyboardInterrupt:
        answer = {"status": "cancelled", "reason": "cancelled", "model_calls": None}
    print(render(answer))
    if answer["status"] != "answered":
        raise SystemExit(130 if answer["status"] == "cancelled" else 1)
