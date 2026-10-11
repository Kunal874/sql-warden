import { FormEvent, useEffect, useRef, useState } from "react";
import { Payload, RunEvent, request, streamEvents } from "./api";

type Option = { id: string; text: string };
type Phase = "idle" | "running" | "clarify" | "done";
type Run = { id: string; token: string; lastId: number };

const MODEL_REASONS = new Set(["model_unavailable", "model_timeout", "model_configuration"]);

export function Ask() {
  const [databases, setDatabases] = useState<string[]>([]);
  const [dbId, setDbId] = useState("california_schools");
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [trace, setTrace] = useState<RunEvent[]>([]);
  const [result, setResult] = useState<Payload | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [ready, setReady] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const run = useRef<Run | null>(null);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    request("/api/databases").then((r) => {
      const list = (r.body.databases as string[] | undefined) ?? [];
      setDatabases(list);
      if (list.length && !list.includes(dbId)) setDbId(list[0]);
    });
    request("/api/ready").then((r) => setReady(r.ok ? null : String(r.body.reason ?? "not_ready")));
  }, []);

  async function follow(current: Run) {
    abort.current = new AbortController();
    setPhase("running");
    try {
      const streamed = await streamEvents(
        current.id,
        current.token,
        current.lastId,
        (event) => setTrace((items) => [...items, event]),
        abort.current.signal,
      );
      current.lastId = streamed.lastId;
    } catch {
      if (abort.current.signal.aborted) return;
    }
    const status = await request(`/api/runs/${current.id}`, { token: current.token });
    if (status.status === 401) {
      setNotice("interrupted: the server no longer has this run (it restarted). Ask again.");
      setPhase("done");
      return;
    }
    if (status.body.status === "needs_clarification") {
      setResult(status.body.clarification as Payload);
      setPhase("clarify");
      return;
    }
    setResult((status.body.result as Payload) ?? { status: status.body.status });
    setPhase("done");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setTrace([]);
    setResult(null);
    setNotice(null);
    setPhase("running");
    const created = await request("/api/ask", { method: "POST", body: { db_id: dbId, question } });
    if (!created.ok) {
      setNotice(refusal(created.status, String(created.body.reason ?? "")));
      setPhase("idle");
      return;
    }
    run.current = {
      id: String(created.body.run_id),
      token: String(created.body.capability),
      lastId: 0,
    };
    await follow(run.current);
  }

  async function clarify(body: { option_id: string } | { text: string }) {
    if (!run.current) return;
    const sent = await request(`/api/runs/${run.current.id}/clarification`, {
      method: "POST",
      body,
      token: run.current.token,
    });
    if (!sent.ok) {
      setNotice(`Clarification refused: ${String(sent.body.reason ?? sent.status)}`);
      setResult({ status: "expired", reason: String(sent.body.reason ?? "") });
      setPhase("done");
      return;
    }
    setReply("");
    await follow(run.current);
  }

  async function cancel() {
    if (!run.current) return;
    abort.current?.abort();
    await request(`/api/runs/${run.current.id}/cancel`, {
      method: "POST",
      token: run.current.token,
    });
    const status = await request(`/api/runs/${run.current.id}`, { token: run.current.token });
    setResult((status.body.result as Payload) ?? { status: "cancelled" });
    setPhase("done");
  }

  const busy = phase === "running";
  return (
    <section aria-labelledby="ask-title">
      <h2 id="ask-title">Ask</h2>
      <p className="muted">
        One read-only question runs through retrieval, several SQL candidates, the SQL guard,
        restricted execution, repair and a vote. Generated SQL never runs with more than one
        dataset's read-only login.
      </p>
      {ready && (
        <p className="banner warn" role="status">
          {ready === "model_unavailable"
            ? "model-unavailable: the local model server is not ready."
            : "database-unavailable: the local PostgreSQL container is not reachable."}
        </p>
      )}
      <form onSubmit={submit} className="ask-form">
        <label>
          Dataset
          <select value={dbId} onChange={(e) => setDbId(e.target.value)} disabled={busy}>
            {databases.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label>
          Question
          <textarea
            value={question}
            maxLength={500}
            rows={3}
            required
            disabled={busy}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="How many schools are in Alameda county?"
          />
        </label>
        <div className="row">
          <button type="submit" disabled={busy || !question.trim()}>
            {busy ? "Running…" : "Ask"}
          </button>
          {busy && (
            <button type="button" className="secondary" onClick={cancel}>
              Cancel
            </button>
          )}
          <span className="muted">{question.length}/500</span>
        </div>
      </form>
      {notice && (
        <p className="banner warn" role="alert">
          {notice}
        </p>
      )}
      {busy && (
        <p className="banner" role="status" aria-live="polite">
          loading: the run is in progress.
        </p>
      )}
      {trace.length > 0 && <Trace events={trace} />}
      {phase === "clarify" && result && (
        <Clarification payload={result} reply={reply} setReply={setReply} send={clarify} />
      )}
      {phase === "done" && result && <Outcome payload={result} />}
    </section>
  );
}

function refusal(status: number, reason: string) {
  if (status === 503) return "overload: too many runs are active. Try again shortly.";
  if (status === 429) return "rate-limited: wait a minute before asking again.";
  if (status === 0) return "network error: the API is not reachable.";
  return `Request refused: ${reason || status}`;
}

function Trace({ events }: { events: RunEvent[] }) {
  return (
    <details className="trace" open>
      <summary>Trace ({events.length} events)</summary>
      <ol>
        {events.map((event) => (
          <li key={event.id}>
            <code>{event.payload.step}</code> {String(event.payload.detail ?? event.payload.status)}
            {event.payload.reason ? ` — ${String(event.payload.reason)}` : ""}
          </li>
        ))}
      </ol>
    </details>
  );
}

function Clarification(props: {
  payload: Payload;
  reply: string;
  setReply: (value: string) => void;
  send: (body: { option_id: string } | { text: string }) => void;
}) {
  const options = (props.payload.options as Option[] | undefined) ?? [];
  return (
    <div className="card" role="region" aria-label="Clarification">
      <h3>Needs clarification</h3>
      <p>{String(props.payload.question ?? "Please clarify the exact result you want.")}</p>
      <p className="muted">The candidates disagreed. You can reply once.</p>
      <div className="row wrap">
        {options.map((option) => (
          <button key={option.id} onClick={() => props.send({ option_id: option.id })}>
            {option.text}
          </button>
        ))}
      </div>
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          props.send({ text: props.reply });
        }}
      >
        <label className="grow">
          Or describe what you meant
          <input
            value={props.reply}
            maxLength={200}
            onChange={(e) => props.setReply(e.target.value)}
          />
        </label>
        <button type="submit" disabled={!props.reply.trim()}>
          Reply
        </button>
      </form>
    </div>
  );
}

function Outcome({ payload }: { payload: Payload }) {
  const status = String(payload.status ?? "failed");
  const reason = String(payload.reason ?? "");
  if (status !== "answered") return <p className={`banner ${status}`}>{statusText(status, reason)}</p>;
  const columns = (payload.columns as string[]) ?? [];
  const rows = (payload.rows as unknown[][]) ?? [];
  const count = Number(payload.row_count ?? rows.length);
  const agreement = Number(payload.agreement ?? 0);
  const candidates = ((payload.candidates as unknown[]) ?? []).length;
  return (
    <div className="card">
      <h3>Answer</h3>
      <p>{String(payload.explanation ?? "")}</p>
      <p className="muted">
        Agreement score {Math.round(agreement * candidates)}/{candidates} candidates — a vote
        count, not a probability of correctness.
      </p>
      <pre className="sql">{String(payload.sql ?? "")}</pre>
      {count === 0 ? (
        <p className="banner">empty: the query ran and returned no rows. That can be correct.</p>
      ) : (
        <>
          {Boolean(payload.preview_truncated) && (
            <p className="banner">
              truncated preview: showing the first {rows.length} of {count} rows.
            </p>
          )}
          <div className="table-wrap" tabIndex={0} aria-label="Result preview">
            <table>
              <thead>
                <tr>
                  {columns.map((name) => (
                    <th key={name}>{name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={index}>
                    {row.map((cell, column) => (
                      <td key={column}>{cell === null ? "NULL" : String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function statusText(status: string, reason: string) {
  if (status === "failed" && MODEL_REASONS.has(reason))
    return `model-unavailable: the local model did not answer (${reason}).`;
  const text: Record<string, string> = {
    abstained: `abstained: no answer is shown because the candidates did not agree (${reason}).`,
    blocked: `blocked: the SQL guard refused every candidate (${reason}); nothing was executed.`,
    cancelled: "cancelled: the run was stopped.",
    expired: "expired: the clarification window closed. Ask again.",
    interrupted: "interrupted: the server restarted during this run. Ask again.",
    failed: `failed: ${reason || "the run did not finish"}.`,
  };
  return text[status] ?? `${status}: ${reason}`;
}
