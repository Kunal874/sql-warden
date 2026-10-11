# Resume evidence

Generated from `results/G3_matrix/summary.json`. Local PostgreSQL-adapted BIRD Mini-Dev subset with corrected labels and a 4-bit 7B model; not an official BIRD score.

- Built SQLWarden, a local read-only text-to-SQL agent (FastAPI, PostgreSQL 16,
  sqlglot, React) with a SQL guard, per-dataset read-only logins, bounded execution,
  repair, result voting, clarification and abstention.
- Measured the full loop at 42.9% execution accuracy on 324 held-out questions (95% CI 37.4%–48.5%), answering 68.5% and correct on 62.6% of answered questions.
- With an agreement threshold chosen on development data before the held-out run, the agent answered 61.7% of held-out questions and was correct on 66.5% of the ones it answered.
- Reported honestly that a full-schema single-candidate baseline scored 54.3% end to end on the same held-out questions, higher than the full loop, using paired bootstrap intervals for every ablation.
- Recorded 43 attacks with threat-specific success predicates; 0 succeeded. The guard accepts 421 of 424 safe gold queries after a reviewed allowlist change (56 were blocked before D-076).
- Switched security layers off one at a time in a disposable database: 27 of 29 attacks stayed prevented with any single layer off, showing overlapping defenses rather than one point of failure.
- Found by a 20-question development probe that matching the model's training prompt format raised accuracy from 3/20 to 10/20 before freezing the evaluation contract.
