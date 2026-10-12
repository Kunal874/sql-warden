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

## G6 training evidence — accuracy comparison pending

This addendum comes from [the completed training record](../results/G6_training/summary.json),
not the G3 matrix above. A resume-ready training bullet:

- Ran a 500-update QLoRA experiment on Qwen2.5-Coder-1.5B-Instruct using an 8 GB
  RTX 4060 laptop GPU and 2,000 PostgreSQL-converted BIRD examples; selected the
  checkpoint using 128 validation examples from separate databases and verified
  that its saved adapter reloaded exactly.

The selected checkpoint was update 400 and had seen 1,600 examples; the complete
experiment processed 2,000. Training/checkpoint/repeated-validation time was
57.70 minutes (excluding initial model loading/validation), with 6.426 GiB peak
PyTorch reserved memory measured during that loop. These are training measurements,
not inference speed or answer-accuracy results. Converted training labels are
structurally checked but execution-unverified. Do not claim an EX improvement,
that the selected checkpoint saw all 2,000 examples, or that the 1.5B model matched
Arctic until the matched E9 comparison finishes.
