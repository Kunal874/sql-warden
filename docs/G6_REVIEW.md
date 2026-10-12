# G6 final local review

Single fresh read-only review of2b106797..574689383 (18G6 commits), followed by
one test-first fix pass. This is not a separate comprehensive security scan.

## Findings and disposition

- No Critical or Minor findings reported.
- Important/P2: a complete JSON record without its terminating newline could
  corrupt a resume when the next record was appended. Reproduced before the fix;
  reject nonempty unterminated tails before inference and preserve their bytes.
- Important/P2: standalone E9 CLI did not enforce artifact/RAM/disk caps, although
  the actual848 completed runs were manually monitored and stayed within them.
  Reproduced before the fix; now check resources before startup, before each
  inference and with projected UTF-8/ASCII JSON bytes before metadata/record writes.
  Keep1GiB live RAM,20GiB free D reserve and24GiB combined G6 cap. No rerun,
  score change or evidence repair was required.

Four regression cases cover unterminated valid JSON, startup exhaustion, and
mid-run exhaustion before inference or append. The prior malformed-tail test
still passes.25focused E9/report tests pass; fresh whole suites recorded in PROGRESS.
The resource checks are at startup/inference/write boundaries, not a background
OS monitor during a single bounded inference. They assume the authorized sequential
workflow; they do not reserve disk against other processes.

## Rulings I made, with costs

Recorded in decision order from the plan ledger; D-083–D-103 provide context.

1. Exclude Codebase variants/group related movie names conservatively. Cost:
   fewer training examples; no content-level identity guarantee.
2. Use structurally converted, execution-unverified labels, as explicitly chosen
   by Kunal. Cost: converted SQL can have wrong meanings.
3. Retain historical Arctic reference. Cost: its environment/latency are not a
   fresh same-session comparison.
4. Distinguish selected400/1600 from complete500/2000. Cost if misstated:
   overstated training scope on the resume.
5. Refuse partial tails rather than silently repair. Cost: damaged evidence needs
   a separate scoped recovery decision.
6. Publish final E9 only after all100dev/324held-out pairs exist. Cost: no final
   accuracy claim while the experiment is partial; loss cannot substitute for EX.
7. Publish checked training-only notes while serving waited for approval, then
   preserve their addenda on G3 regeneration. Cost: loss could be mistaken for
   answer accuracy without the explicit pending-status caveat.
8. After actual native Q4_K_M refusal, use newly approved pinned llama.cpp/four
   conversion-only packages. Cost: demonstrated compatibility is Qwen2-specific.
9. Temporarily stop Docker with approval, restore the same services, and merge
   on GPU with500MB shards. Cost: services paused and a resource failure could
   leave partial artifacts; all five services were restored.
10. Keep large converter intermediates on C:,4threads/15min tools, cold4GiB and
    live1GiB RAM floors. Cost: incomplete outputs need investigation, not overwrite.
11. Match the one observed untrained base bias's exact FP16 rounding in derived
    files, save old bytes and preserve the old alias. Cost: an uncorrected precision
    difference could confound attribution; final56target-only audit passes.
12. Use actual APIshow's pinned HF Jinja template, not the assumed Go template.
    Cost: the checks cover explicit system/user text, not tools/suffix workflows.
13. Report the actual gain with regressions/coverage and leave Arctic default.
    Cost: one-seed known-set results could still be overgeneralized; caveats remain.

## Reviewer-declined items and explicit rulings

- Label semantics: keep accepted execution-unverified status, not equivalence
  claims. Cost: undetected conversion mistakes remain possible.
- Content/pretraining contamination: keep disclosed unknowns; family/schema/text
  checks alone are not proof. Cost: contamination can inflate measured performance.
- Generalization: limit claims to this repeated local subset/seed and question-
  level intervals. Cost: future datasets can differ substantially.
- Fresh Arctic results: do not add another7B experiment; retain historical label.
  Cost: no new same-session bigger-model speed comparison.
- Concurrent evaluators: retain sequential-only workflow, no simultaneous writers.
  Cost: concurrent invocation can corrupt records or interfere with model swaps.
- Hostile local artifacts/tooling: trust the controlled workstation and pinned
  source preparation; no adversarial-admin defense claimed. Cost: local tampering
  can invalidate provenance/execution assumptions.
- GPU/Docker/PostgreSQL checks: rely on actual parent-run checks/evidence; reviewer
  did not duplicate hardware/database runs. Cost: no independent second measurement.
- Publication/install/attribution/secrets: retain local-only work; parent verified
  clean root install/tests, attribution and declared secret-pattern scope separately.
  Cost: no weight/publication clearance or comprehensive secret audit implied.

No deferred Minor findings. Existing httpx and frontend bundle-size warnings were
not new review findings and were not silenced or addressed by dependency changes.
