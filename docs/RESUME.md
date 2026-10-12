# Resume evidence

Generated from `results/G3_matrix/summary.json`. Local PostgreSQL-adapted BIRD Mini-Dev subset with corrected labels and a 4-bit 7B model; not an official BIRD score.

- Built SQLWarden, a local read-only text-to-SQL agent (FastAPI, PostgreSQL 16,
  sqlglot, React) with a SQL guard, per-dataset read-only logins, bounded execution,
  repair, result voting, clarification and abstention.
- Measured the full loop at 42.9% execution accuracy on 324 held-out questions (95% CI 37.4%–48.5%), answering 68.5% and correct on 62.6% of answered questions.
- With an agreement threshold chosen on development data before the held-out run, the agent answered 61.7% of held-out questions and was correct on 66.5% of the ones it answered.
- Reported honestly that a full-schema single-candidate baseline scored 54.3% end to end on the same held-out questions, higher than the full loop, using paired bootstrap intervals for every ablation.
- Recorded 43 attacks with threat-specific success predicates; 0 of 43 succeeded (exact 95% upper bound 8.2%; recorded suite only). The guard accepts 421 of 424 safe gold queries after a reviewed allowlist change (56 were blocked before D-076).
- Switched security layers off one at a time in a disposable database: 27 of 29 attacks stayed prevented with any single layer off; L-A4-05 depended on the SQL guard alone; L-A5-03 depended on the statement timeout alone.
- Found by a 20-question development probe that matching the model's training prompt format raised accuracy from 3/20 to 10/20 before freezing the evaluation contract.

## G6 — measured fine-tuning evidence

This addendum comes from [the training record](../results/G6_training/summary.json)
and [matched E9 evidence](../results/G6_e9/summary.json), not the G3 matrix above.
A resume-ready bullet:

- Ran a 500-update QLoRA experiment on Qwen2.5-Coder-1.5B-Instruct using an 8 GB
  RTX 4060 laptop GPU and 2,000 PostgreSQL-converted BIRD examples; selected the
  checkpoint using 128 validation examples from separate databases, and increased
  execution accuracy from 11.4% to 23.5% on a matched 324-question repeat local
  PostgreSQL benchmark (+12.0 percentage points; paired 95% interval +7.1 to +17.0),
  with median per-question latency 2.94 s→0.82 s under unchanged SQL safeguards.

The selected checkpoint was update 400 and had seen 1,600 examples; the complete
experiment processed 2,000. Training/checkpoint/repeated-validation time was
57.70 minutes (excluding initial model loading/validation), with 6.426 GiB peak
PyTorch reserved memory measured during that loop. These are training measurements,
not serving measurements. The separate E9 serving measurements above use matching
Q4_K_M models and no response cache. Converted training labels are structurally
checked but execution-unverified. The held-out set was already known, so say
"repeat local benchmark," not an untouched test or official BIRD leaderboard.
Do not claim the selected checkpoint saw all 2,000 examples or beat Arctic's 54.3%.
Tuning had 55 wins and 16 regressions; accuracy among answered questions did not
improve. The app still uses Arctic by default. No model weights were published.
