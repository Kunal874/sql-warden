import { useEffect, useMemo, useState } from "react";
import { Payload, dataPath, request } from "./api";

type Attack = {
  id: string;
  threat_id: string;
  observed_layer: string;
  outcome: string;
  predicate: string;
  config: string;
};

const THREATS: Record<string, string> = {
  A1: "Destructive writes",
  A2: "Privilege, file or network escape",
  A3: "Cross-database or cross-tenant reads",
  A4: "Catalog and secret leakage",
  A5: "Resource exhaustion",
  A6: "Indirect injection via data",
  A7: "Direct jailbreak",
};

export function AttackLab() {
  const [data, setData] = useState<Payload | null>(null);
  const [threat, setThreat] = useState("all");

  useEffect(() => {
    request(dataPath("attacks")).then((reply) => setData(reply.ok ? reply.body : null));
  }, []);

  const attacks = (data?.attacks as Attack[] | undefined) ?? [];
  const shown = useMemo(
    () => attacks.filter((item) => threat === "all" || item.threat_id === threat),
    [attacks, threat],
  );
  const layers = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of attacks) counts.set(item.observed_layer, (counts.get(item.observed_layer) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [attacks]);
  const falseBlocks = (data?.false_blocks as Record<string, number> | undefined) ?? {};

  if (!data) return <section><h2>Attack Lab</h2><p className="banner">loading attack evidence…</p></section>;
  return (
    <section aria-labelledby="attack-title">
      <h2 id="attack-title">Attack Lab</h2>
      <p className="muted">
        Recorded outcomes with all layers on. Each row names the layer that was observed to
        stop the attack in its evidence test. A blocked attack is not proof that no other attack
        works.
      </p>
      <div className="stats">
        <Stat label="Recorded attacks" value={String(attacks.length)} />
        <Stat
          label="Blocked"
          value={String(attacks.filter((item) => item.outcome === "blocked").length)}
        />
        <Stat
          label="Safe gold queries falsely blocked"
          value={`${falseBlocks.safe_gold_guard_blocked ?? "?"} / ${falseBlocks.safe_gold_items ?? "?"}`}
        />
      </div>
      <p className="muted">
        Observed blocker:{" "}
        {layers.map(([layer, count]) => `${layer.replaceAll("_", " ")} (${count})`).join(", ")}.
        Layer-off variants: {String(data.layer_off).replaceAll("_", " ")}.
      </p>
      <label>
        Threat
        <select value={threat} onChange={(e) => setThreat(e.target.value)}>
          <option value="all">All threats</option>
          {Object.entries(THREATS).map(([id, name]) => (
            <option key={id} value={id}>
              {id} — {name}
            </option>
          ))}
        </select>
      </label>
      <div className="table-wrap" tabIndex={0} aria-label="Attack outcomes">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Observed layer</th>
              <th>Outcome</th>
              <th>Success predicate</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((item) => (
              <tr key={item.id}>
                <td>
                  <code>{item.id}</code>
                </td>
                <td>{item.observed_layer.replaceAll("_", " ")}</td>
                <td className={item.outcome}>{item.outcome}</td>
                <td>{item.predicate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="muted">{label}</span>
    </div>
  );
}
