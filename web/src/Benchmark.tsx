import { useEffect, useState } from "react";
import { Payload, request } from "./api";

type ModelSummary = Record<string, number>;

const PHASES: [string, string][] = [
  ["parse_rate", "Parsed"],
  ["guard_rate", "Guard accepted"],
  ["execution_rate", "Executed"],
  ["ex", "Correct (EX)"],
];

export function Benchmark() {
  const [data, setData] = useState<Payload | null>(null);
  useEffect(() => {
    request("/api/benchmark").then((reply) => setData(reply.ok ? reply.body : null));
  }, []);
  if (!data) return <section><h2>Benchmark</h2><p className="banner">loading results…</p></section>;
  const models = (data.models as Record<string, ModelSummary>) ?? {};
  return (
    <section aria-labelledby="bench-title">
      <h2 id="bench-title">Benchmark</h2>
      <p className="muted">
        Local PostgreSQL-adapted BIRD Mini-Dev development slice (n=100).{" "}
        <strong>Not an official BIRD score</strong>; numbers come from tracked result files.
      </p>
      <div className="table-wrap" tabIndex={0} aria-label="E0 phase rates">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              {PHASES.map(([, label]) => (
                <th key={label}>{label}</th>
              ))}
              <th>Median latency</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(models).map(([name, summary]) => (
              <tr key={name}>
                <td>{name}</td>
                {PHASES.map(([key]) => (
                  <td key={key}>{percent(summary[key])}</td>
                ))}
                <td>{summary.median_seconds?.toFixed(2)} s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function percent(value: number | undefined | null) {
  return value === undefined || value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}
