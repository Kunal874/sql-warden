import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Payload, dataPath, request } from "./api";
import { Stat } from "./AttackLab";

type Interval = { low: number | null; high: number | null };
type Condition = {
  n: number;
  pending: number;
  ex: { count: number; rate: number; exact: Interval; bootstrap: Interval };
  answered: { count: number; rate: number };
  answered_only_ex: { rate: number | null };
};
type Comparison = {
  left: string;
  right: string;
  n: number;
  left_only: number;
  right_only: number;
  difference: number;
  ci: Interval;
};
type CurvePoint = {
  threshold: string;
  coverage: number;
  selective_ex: number | null;
  end_to_end_ex: number;
  covered: number;
};
type Split = {
  ids: number;
  conditions: Record<string, Condition>;
  comparisons: Record<string, Comparison>;
  accuracy_coverage?: { curve: CurvePoint[]; frozen_threshold: string | null };
  failure_taxonomy: Record<string, number>;
  latency: Record<string, Record<string, unknown>>;
};

const SETTINGS: [string, string][] = [
  ["full_n1", "Full schema, 1 candidate"],
  ["ret_n1_k0", "Retrieval, 1 candidate"],
  ["ret_n1_k1", "Retrieval + repair"],
  ["ret_n3_k0", "Retrieval, 3-vote"],
  ["ret_n3_k1", "Retrieval + repair, 3-vote"],
  ["messy_n1", "Messy names, 1 candidate"],
  ["orig_n1_k0", "Original wording, 1 candidate"],
];
const LABEL = Object.fromEntries(SETTINGS);

export function Benchmark() {
  const [data, setData] = useState<Payload | null>(null);
  const [split, setSplit] = useState<"held_out" | "dev">("held_out");
  useEffect(() => {
    request(dataPath("benchmark")).then((reply) => setData(reply.ok ? reply.body : null));
  }, []);
  if (!data)
    return (
      <section>
        <h2>Benchmark</h2>
        <p className="banner">loading results…</p>
      </section>
    );
  const splits = ((data.matrix as Payload | null)?.splits ?? {}) as Record<string, Split>;
  const current = splits[split] ?? splits.dev;
  return (
    <section aria-labelledby="bench-title" className="viz-root">
      <h2 id="bench-title">Benchmark</h2>
      <p className="muted">
        Arctic-Text2SQL-R1-7B (Q4_K_M, local) on the PostgreSQL-adapted BIRD Mini-Dev subset
        with corrected labels. <strong>Not an official BIRD score</strong>; every number comes
        from tracked result files. Accuracy is execution match (EX) with abstentions counted
        as wrong.
      </p>
      <fieldset className="row wrap" aria-label="Question split">
        {(["held_out", "dev"] as const)
          .filter((name) => splits[name])
          .map((name) => (
            <label key={name} className="radio">
              <input
                type="radio"
                name="split"
                checked={split === name || (!splits[split] && name === "dev")}
                onChange={() => setSplit(name)}
              />
              {name === "held_out" ? `Held-out (${splits[name].ids}, primary)` : `Development (${splits[name].ids})`}
            </label>
          ))}
      </fieldset>
      {current ? <SplitView split={current} /> : <p className="banner">No matrix results yet.</p>}
      <E0 data={data} />
    </section>
  );
}

function SplitView({ split }: { split: Split }) {
  const rows = SETTINGS.filter(([key]) => split.conditions[key]).map(([key, label]) => ({
    key,
    label,
    ...split.conditions[key],
    rate: split.conditions[key].ex.rate,
  }));
  const loop = split.conditions.ret_n3_k1;
  const single = split.conditions.ret_n1_k0;
  const full = split.conditions.full_n1;
  return (
    <>
      <div className="stats">
        {loop && <Stat label="Full loop EX (3-vote + repair)" value={pct(loop.ex.rate)} />}
        {single && <Stat label="Retrieval, single candidate" value={pct(single.ex.rate)} />}
        {full && <Stat label="Full-schema baseline" value={pct(full.ex.rate)} />}
        {loop && <Stat label="Full loop answered (coverage)" value={pct(loop.answered.rate)} />}
      </div>
      <h3>Execution accuracy by loop setting</h3>
      <div className="chart" role="img" aria-label="Execution accuracy by loop setting; table below">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24 }}>
            <CartesianGrid horizontal={false} stroke="var(--grid)" />
            <XAxis type="number" domain={[0, 1]} tickFormatter={pct} stroke="var(--muted)" />
            <YAxis type="category" dataKey="label" width={190} stroke="var(--muted)" />
            <Tooltip
              cursor={{ fill: "var(--hover)" }}
              formatter={(_value, _name, item) => {
                const row = item.payload as (typeof rows)[number];
                return [`${row.ex.count}/${row.n} (${ci(row.ex.exact)})`, "EX"];
              }}
            />
            <Bar dataKey="rate" fill="var(--series-1)" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <Table
        caption="Accuracy by setting (exact 95% binomial interval)"
        head={["Setting", "Correct", "EX", "95% CI", "Answered", "Answered-only EX"]}
        rows={rows.map((row) => [
          row.label,
          `${row.ex.count}/${row.n}${row.pending ? ` (${row.pending} pending)` : ""}`,
          pct(row.ex.rate),
          ci(row.ex.exact),
          pct(row.answered.rate),
          pct(row.answered_only_ex.rate),
        ])}
      />
      <Table
        caption="Paired comparisons on the same questions (bootstrap 95% CI, 10,000 resamples)"
        head={["Comparison", "Difference", "95% CI", "Only left correct", "Only right correct"]}
        rows={Object.values(split.comparisons).map((c) => [
          `${LABEL[c.left] ?? c.left} vs ${LABEL[c.right] ?? c.right}`,
          signed(c.difference),
          ci(c.ci),
          String(c.left_only),
          String(c.right_only),
        ])}
      />
      {split.accuracy_coverage && <Coverage curve={split.accuracy_coverage} />}
      <Table
        caption="Why the full loop missed (one category per question)"
        head={["Category", "Questions"]}
        rows={Object.entries(split.failure_taxonomy).map(([name, count]) => [
          name.replaceAll("_", " "),
          String(count),
        ])}
      />
      <Latency latency={split.latency} />
    </>
  );
}

function Coverage({ curve }: { curve: { curve: CurvePoint[]; frozen_threshold: string | null } }) {
  const points = curve.curve.filter((p) => p.selective_ex !== null);
  return (
    <>
      <h3>Agreement threshold: accuracy versus coverage</h3>
      <p className="muted">
        Answer only when at least this share of the 3 candidates agree. The agreement score is
        a vote count, not a probability. Threshold chosen on the development slice before the
        held-out run: <strong>{curve.frozen_threshold ?? "not frozen yet"}</strong>.
      </p>
      <div className="chart small" role="img" aria-label="Accuracy versus coverage; table below">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ left: 8, right: 24, top: 8 }}>
            <CartesianGrid stroke="var(--grid)" />
            <XAxis
              dataKey="coverage"
              type="number"
              domain={[0, 1]}
              tickFormatter={pct}
              stroke="var(--muted)"
            />
            <YAxis domain={[0, 1]} tickFormatter={pct} stroke="var(--muted)" />
            <Tooltip
              formatter={(value) => [pct(value as number), "Accuracy when answering"]}
              labelFormatter={(value) => `Coverage ${pct(value as number)}`}
            />
            <Line
              dataKey="selective_ex"
              stroke="var(--series-1)"
              strokeWidth={2}
              dot={{ r: 5, fill: "var(--series-1)", stroke: "var(--surface)", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <Table
        caption="Accuracy-coverage points"
        head={["Agreement at least", "Coverage", "Accuracy when answering", "End-to-end EX"]}
        rows={curve.curve.map((p) => [
          p.threshold,
          pct(p.coverage),
          pct(p.selective_ex),
          pct(p.end_to_end_ex),
        ])}
      />
    </>
  );
}

function Latency({ latency }: { latency: Record<string, Record<string, unknown>> }) {
  const rows = Object.entries(latency)
    .filter(([name]) => name !== "clarify_oracle")
    .map(([name, value]) => {
      const generate = (value.per_role as Record<string, Record<string, number>> | undefined)
        ?.generate;
      return [
        LABEL[name] ?? name.replaceAll("_", " "),
        String(value.items),
        `${value.median_item_seconds ?? "—"} s`,
        `${generate?.median_seconds ?? "—"} s`,
        String(generate?.median_completion_tokens ?? "—"),
        String(value.cache_hits),
      ];
    });
  return (
    <Table
      caption="Cost and latency (fresh local calls; cache hits are replays, not live latency)"
      head={["Run", "Questions", "Median per question", "Median per call", "Output tokens", "Cache hits"]}
      rows={rows}
    />
  );
}

function E0({ data }: { data: Payload }) {
  const models = (data.models as Record<string, Record<string, number>>) ?? {};
  return (
    <details>
      <summary>Earlier E0 smoke (contract v1, question only, JSON output; historical)</summary>
      <Table
        caption="E0 development slice, n=100"
        head={["Model", "Parsed", "Guard accepted", "Executed", "EX"]}
        rows={Object.entries(models).map(([name, m]) => [
          name,
          pct(m.parse_rate),
          pct(m.guard_rate),
          pct(m.execution_rate),
          pct(m.ex),
        ])}
      />
    </details>
  );
}

function Table({ caption, head, rows }: { caption: string; head: string[]; rows: string[][] }) {
  return (
    <div className="table-wrap" tabIndex={0} aria-label={caption}>
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {head.map((name) => (
              <th key={name} scope="col">
                {name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, column) => (
                <td key={column}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function pct(value: number | undefined | null) {
  return value === undefined || value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function signed(value: number | null) {
  return value === null ? "—" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)} pp`;
}

function ci(interval: Interval | undefined) {
  return interval && interval.low !== null && interval.high !== null
    ? `${pct(interval.low)}–${pct(interval.high)}`
    : "—";
}
