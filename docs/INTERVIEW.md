# Interview questions (G7.5)

Twelve questions an interviewer is likely to ask, with short answers and the file that
backs each claim. Numbers come from `results/G3_matrix/summary.json` (commit c412438)
and the manifests named; re-read those files if anything is rebuilt.

1. **What does SQLWarden do, in one sentence?**
   It turns a question into read-only PostgreSQL, runs it under a one-dataset login
   with hard limits, and answers only when independent candidates agree on the result.
   Evidence: [agent.py](../src/sqlwarden/agent.py), [README](../README.md).

2. **Why not trust the model to write only SELECT queries?**
   A prompt is a request, not a boundary. The guard parses SQL and refuses anything
   outside an allowlist; the database login can read only its own schema in a read-only
   transaction. In the disposable layer-off run, 27 of 29 attacks stayed prevented with
   any single layer switched off. Evidence: [SECURITY](../SECURITY.md),
   `results/G3_matrix/e5-layer-off.json`.

3. **Did any attack get through, and what does "0 succeeded" mean?**
   0 of 43 recorded attacks succeeded with all layers on (exact 95% upper bound 8.2%).
   That bounds this recorded suite, not future attacks. With one layer off, `version()`
   relied on the guard alone and a huge cross join on the timeout alone.
   Evidence: [EVAL](EVAL.md) E5, `docs/attack-suite-manifest.json`.

4. **How accurate is it?**
   On 324 held-out questions the simplest setting (full schema, one candidate) reached
   54.3%; the full loop 42.9% end to end. With the agreement threshold chosen on
   development data, the loop answered 61.7% of questions and was right on 66.5% of
   those. Local PostgreSQL-adapted subset, not an official BIRD score. Evidence: EVAL.

5. **So the agent features made it worse?**
   End to end, yes: retrieval cost 8.6 points and voting about 3 more. Their measured
   value is selective accuracy, not coverage. I reported this instead of tuning on
   held-out data. Evidence: EVAL E2 paired comparisons, D-078.

6. **Why did repair not help?**
   56 of 58 repairs on development repeated the same failure class. The repair prompt
   receives only a sanitized category such as `function_not_allowed`, not which function
   or column was wrong. Safe, specific feedback is the next experiment.
   Evidence: EVAL repair outcomes, D-081.

7. **What was the single biggest accuracy lever you found?**
   The prompt format. The model was trained to reason before a final SQL block; matching
   that format (and adding BIRD's evidence) moved a 20-question development probe from
   3 to 10 correct before the evaluation was frozen. Evidence: D-075,
   `results/G3_matrix/prompt-probe.jsonl`.

8. **How did you avoid fooling yourself in evaluation?**
   Frozen 100/324 split, development-only tuning, a threshold rule fixed and frozen before
   any held-out run, every question kept in the denominator, exact and paired bootstrap
   intervals, and commit plus dirty-flag provenance on every run. Evidence:
   `docs/e0-protocol.json`, `docs/e8-threshold.json`, D-078, D-081.

9. **How did you handle wrong benchmark labels?**
   I used the verified corrected label pool (424 of 498 questions) and scored the same
   predictions against original labels where those were valid. Separate runs with the
   original wording showed it cost 20 points on the 40 changed development questions.
   Evidence: D-053, EVAL E1/E3, `docs/ambiguity-audit.json`.

10. **Does it ask clarifying questions well?**
    Partly. It asked on 44% of genuinely ambiguous development questions versus 15% of
    clear ones, and the helper's options were always well formed, but answers after
    clarification were often still wrong. On the self-authored set it asked on 5 of 15
    ambiguous evaluation questions and wrongly on 3 of 15 clear ones. Evidence: EVAL E7.

11. **How is a running query kept safe and bounded in the web app?**
    Each run has an unguessable capability stored only as a hash; bodies are size-capped
    before parsing; overload is refused immediately; events stream with replay and
    heartbeats; runs time out; shutdown marks them interrupted. Evidence:
    [api.py](../src/sqlwarden/api.py), [webapp.py](../src/sqlwarden/webapp.py), D-073.

12. **Why is the public demo static?**
    Free hosting tiers were too small, or would send every question to a third-party
    model, and managed Postgres would not allow some permission hardening. A static
    evidence site plus a local demo costs nothing and leaks nothing. Evidence:
    [DEPLOY](DEPLOY.md), D-077.

## G6 training and measured E9 addendum

13. **What did you actually fine-tune?**
    Qwen2.5-Coder-1.5B-Instruct, using NF4 QLoRA on the laptop's 8 GB RTX 4060.
    The original weights stayed frozen; 1,089,536 adapter parameters on query/value
    projections learned the task. The full trial ran 500 updates on 2,000 examples.
    Evidence: [training summary](../results/G6_training/summary.json),
    [full worker](../training/full.py).

14. **Why choose update 400 instead of the final model?**
    I froze the selection rule before training: lowest loss on 128 validation
    examples from separate databases, with earlier updates winning a tie. Update
    400 scored 0.093843 versus 0.093926 at 500. The selected version saw 1,600
    examples, although the full experiment processed 2,000. I did not use benchmark
    execution accuracy to select it. Evidence: training summary, D-088/D-091.

15. **Does lower loss prove better SQL answers?**
    No. Token loss measures how well the model predicts the saved answer tokens;
    execution accuracy checks whether a query returns the correct database answer.
    The matched E9 test measured11.4→23.5% on324existing known held-out questions,
    with a paired interval +7.1 to +17.0points. That is separate evidence from
    loss, not proof of broad generalization. The small model still does not match
    Arctic54.3%. Evidence: EVAL E9 and the compact E9 summary.

16. **What are the main data-quality limits?**
    BIRD training labels started as SQLite. I converted them to PostgreSQL and
    checked names, syntax and the guard, but did not execute them on the training
    databases. Conversion can change meaning. Database families were separated;
    evaluation families/shared schemas/exact text were screened out, but full
    row-content separation and unknown pretraining contamination are unproven.
    Evidence: [data manifest](training-data-manifest.json), D-087/D-088.

17. **Is the trained model already running in SQLWarden?**
    It now serves locally as a separate experimental Ollama alias and completed
    the fresh guarded comparison. It is not the app's default: Arctic remains
    more accurate in the historical reference. Full merge/tensor/reload, matched
    quantization/template and actual PostgreSQL checks passed. G3 results are
    unchanged. No new weights or commits were pushed.
    Evidence: [serving inputs](g6-serving-inputs.json), PROGRESS Handoff.

### Three-question G6 practice drill

18. **What did the tuning improve, and what did it make worse?**
    End-to-end EX increased37→76correct on324 questions (+12.0points);55
    questions improved and16 regressed. More queries became executable, and
    coverage rose25.3→53.1%, but correctness among answered queries changed
    45.1→44.2%. Unknown-object failures remained common. Do not claim universal
    reliability or promote the smaller model over Arctic based on this result.

19. **How did you make base and tuned comparable?**
    Same source revision, selected validation checkpoint, converter/quantizer,
    Q4_K_M/layout/tokenizer, actual chat template, prompt/schema/seed/budgets,
    safeguards and question order; response cache off. A strict weight audit
    caught one untrained bias rounding difference, corrected only in the derived
    base file with recoverable original bytes. Final files differ only in56
    adapter-target matrices. All848 attempts used clean faa41c9 provenance.

20. **Why did the tuned model answer faster?**
    It produced shorter answers: held-out median completion length417→106tokens,
    while median item latency2.94→0.82s. The experiment measures local task
    latency, not faster GPU hardware or a universal speedup. Loaded-model VRAM
    was reported similarly for both. Prefix reuse inside Ollama was not disabled.

This is a supplied practice sheet, not a claim that a human interview was assessed.

21. **Did adding repair improve the tuned model enough to use it by default?**
    In a separate development-only comparison, no repair scored20/100 and one
    repair22/100. There were two wins and no regressions, but the paired95%
    interval0–5points includes zero. It needed54extra calls and median time rose
    0.766→1.204s. Invalid repair output remained common. I retained the existing
    default rather than treating a small practice-set gain as proven test accuracy.
