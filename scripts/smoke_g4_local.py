"""Scripted G4 flow over HTTP: health, static app, ask -> (clarify) -> result, cancel.

Live: `uv run python scripts/smoke_g4_local.py --base http://127.0.0.1:8000`
(start the runtime first; this script needs no credentials and prints no tokens).
"""

from __future__ import annotations

import argparse
import json
import time

import httpx

DEFAULT_QUESTION = "How many schools are in Alameda county?"


def _events(client: httpx.Client, run_id: str, token: str, last_id: int) -> tuple[list, int]:
    steps = []
    headers = {"authorization": "Bearer " + token, "last-event-id": str(last_id)}
    with client.stream("GET", f"/api/runs/{run_id}/events", headers=headers) as response:
        for line in response.iter_lines():
            if line.startswith("id: "):
                last_id = int(line[4:])
            elif line.startswith("data: "):
                steps.append(json.loads(line[6:]).get("step"))
    return steps, last_id


def run_smoke(client: httpx.Client, *, db_id: str, question: str, origin: str) -> dict:
    report: dict = {
        "health": client.get("/api/health").json().get("status"),
        "ready": client.get("/api/ready").json(),
        "index_served": 'id="root"' in client.get("/").text,
        "source_hidden": client.get("/package.json").status_code == 404,
    }
    body = {"db_id": db_id, "question": question}
    started = time.perf_counter()
    created = client.post("/api/ask", json=body, headers={"origin": origin})
    report["ask_status_code"] = created.status_code
    run = created.json()
    token = {"authorization": "Bearer " + run["capability"]}
    steps, last_id = _events(client, run["run_id"], run["capability"], 0)
    status = client.get(f"/api/runs/{run['run_id']}", headers=token).json()
    if status["status"] == "needs_clarification":
        options = status["clarification"].get("options") or []
        reply = {"option_id": options[0]["id"]} if options else {"text": "the total number"}
        report["clarification"] = {"options": len(options), "reply": sorted(reply)}
        sent = client.post(f"/api/runs/{run['run_id']}/clarification", json=reply, headers=token)
        report["clarification"]["status_code"] = sent.status_code
        more, last_id = _events(client, run["run_id"], run["capability"], last_id)
        steps += more
        status = client.get(f"/api/runs/{run['run_id']}", headers=token).json()
    result = status.get("result", {})
    report["run"] = {
        "status": status["status"],
        "reason": result.get("reason"),
        "row_count": result.get("row_count"),
        "agreement": result.get("agreement"),
        "steps": steps,
        "seconds": round(time.perf_counter() - started, 2),
    }
    second = client.post("/api/ask", json=body, headers={"origin": origin}).json()
    cancel_token = {"authorization": "Bearer " + second["capability"]}
    client.post(f"/api/runs/{second['run_id']}/cancel", headers=cancel_token)
    report["cancel_status"] = client.get(
        f"/api/runs/{second['run_id']}", headers=cancel_token
    ).json()["status"]
    return report


def run_abuse_checks(client: httpx.Client, *, db_id: str, origin: str, burst: int = 21) -> dict:
    """Bounded refusals. The burst admits at most max_active runs and cancels them."""
    body = {"db_id": db_id, "question": "How many rows?"}
    report = {
        "bad_origin": client.post(
            "/api/ask", json=body, headers={"origin": "https://evil.example"}
        ).status_code,
        "oversize_body": client.post(
            "/api/ask",
            content=b'{"db_id":"x","question":"' + b"a" * 8192 + b'"}',
            headers={"content-type": "application/json"},
        ).status_code,
        "unknown_db": client.post("/api/ask", json=body | {"db_id": "app"}).status_code,
        "not_json": client.post("/api/ask", content=b"{", headers={"origin": origin}).status_code,
        "missing_token": client.get("/api/runs/unknown").status_code,
        "wrong_token": client.get(
            "/api/runs/unknown", headers={"authorization": "Bearer wrong"}
        ).status_code,
    }
    codes: dict[str, int] = {}
    admitted = []
    for _ in range(burst):
        response = client.post("/api/ask", json=body, headers={"origin": origin})
        codes[str(response.status_code)] = codes.get(str(response.status_code), 0) + 1
        if response.status_code == 202:
            admitted.append(response.json())
    cancelled = [
        client.post(
            f"/api/runs/{run['run_id']}/cancel",
            headers={"authorization": "Bearer " + run["capability"]},
        ).json()["status"]
        for run in admitted
    ]
    return report | {
        "burst_codes": codes,
        "admitted_cancelled": all(status == "cancelled" for status in cancelled),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--db", default="california_schools")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--abuse", action="store_true", help="also run bounded refusal checks")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base, timeout=330, trust_env=False) as client:
        report = run_smoke(client, db_id=args.db, question=args.question, origin=args.base)
        if args.abuse:
            report["abuse"] = run_abuse_checks(client, db_id=args.db, origin=args.base)
    print(json.dumps(report, indent=2))
    return 0 if report["run"]["status"] in {"answered", "abstained", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
