# One bounded local question-to-SQL demonstration

## Actual outcome (2026-10-04)

The single approved self-authored question, **How many rows are in the schools
table?**, completed with `answered / ok`, exit 0, on `california_schools`.
The complete one-cell result matched the previously verified offline count
17686. This is one demonstration, not BIRD EX, benchmark accuracy, agreement,
confidence, a full-schema baseline or a completed agent.

Started 2026-10-04T22:29:44.4410470+05:30. End-to-end wall time **11.387s**
includes uv/process startup, readiness/preload, generation, guard, database work
and HTTP close; individual phase/inference latencies were not measured.
One preload and one generation were admitted, no retry/repair/tuning or alternate
model. Reported usage: **89 prompt / 18 completion tokens**. The trace was
validate -> generate -> guard -> cost_execute -> answered. HTTP close confirmed.
No raw model response, SQL text, rows, cache or credentials are saved here.
Accepted SQL SHA-256: bd8a63bf6289f8ce717defc770c2304a929fc374b85c3877915725eb0ba47146.

## Exact configuration / provenance

- Runtime Git HEAD f8b8150b86f1c91ffd893b62b3d6a1c0d779af6b, feat/foundation;
  tracked tree clean, only new tests/test_cli_postgres.py untracked at invocation.
  Runtime sources and lock were already committed. No remote/push.
- Python 3.12.15; openai 2.54.0; httpx 0.28.1; native Ollama 0.35.1.
- Endpoint http://127.0.0.1:11434; alias
  sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1;
  digest b00066f4a0af314f23919f5644e49e37f8ec7210ecd9cc2ae4236f43ef1d9c2b.
  Existing Qwen2.5-Coder 7B Q4_K_M; no pull/create or model-setting change.
  Readiness verified sole loaded alias/digest/context 2048; actual /api/ps
  afterward reports context 2048 and size_vram 4628519320 bytes.
- Request: temperature 0, max_tokens 128, JSON object, non-streaming;
  SDK/transport retries 0, proxy/redirect disabled, 64KiB identity-response cap.
  Bounds: 1024 UTF-8 content bytes, 90s readiness, 60s generation, 180s enclosing
  flow, separate 5s HTTP cleanup. Cooperative, not hard process/heap isolation.
- Prompt version generate_smoke_v1, fixed four-column capsule
  california_schools.schools(cdscode text, county text, school text, city text).
  No full schema/retrieval, imported rows, gold SQL, evidence/labels, password or
  expected count was passed to the model. Offline count matching occurred only
  outside inference after the CLI completed.
- SYSTEM SHA-256: 2fbbf7bbdaf6e9dbbfec67ee62d1755631b59bd73d3d2b1e326c95aba8e1a637.
  Question SHA-256: d4d4beadc8d66fdca5c64ec15c65f8011020ff7c909207aa80036eae0787996c.
  Capsule SHA-256: 37e6fded4f559e776a4be6760d1a108fef5e11596b7e2783096883dc90bb24ac.
- Runtime llm.py SHA-256: f0b3fd40afac373f42a910218d07fe488c57c3427613f87606e471072ac0af07.
  cli.py SHA-256: 14c955ada58022549747433552d7458f476b6e1085176f6fb83a9fcef4f6c77b.
  uv.lock SHA-256: 11ae6fbfbf24564560d37e129f3e9b7e5e3e8e3714bc32cb456c2a3c3eb4fa51.
- Database: PostgreSQL 16.15, fixed restricted warden_sandbox_california_schools
  login, sqlwarden at 127.0.0.1:55432. Healthy container and named volume
  sqlwarden_pg16_data retained; PostgreSQL 17 on 5432 unchanged. Immutable guard
  and existing bounded executor (which re-guards) were used, not a direct query.
  Limits: 1000 rows/2097152 result bytes/65536 cell bytes, statement 5000ms,
  lock 500ms, pool 5000ms, total 15000ms, estimated cost/rows each 100000.
- Setup helper created only ignored .env.runtime exclusively, copying only the
  existing restricted password. Runtime validation passes without setup/test
  environments; no password/grant changed, no credential displayed or committed.

## Deterministic controls and remaining limits

Before the live call: 7 actual fixed-provider CLI controls passed (3.89s), then
689/689 configured tests (18.51s), zero skips including 165 actual PostgreSQL
checks. Count, empty and NULL answers remain complete; destructive/catalog/
foreign-table candidates are blocked; database error and overflow are not answers;
a next independent call recovers. Same-pool/backend cancellation belongs to the
unchanged executor tests, not this new per-call CLI test.

The initial Task 1 configured run had one existing cancellation observation
timeout (642 passed/1 failed). Isolated, executor-group and full runs subsequently
passed unchanged; the cause was not proved. No deadline was weakened.

Local metadata trusts Ollama and does not lock out privileged/concurrent changes.
Byte/chunk caps are logical bounds, not guaranteed peak allocation limits; the
question cap is not an exact tokenizer or universal truncation proof. Valid SQL
and a successful database answer do not generally prove semantic correctness.

## Model cleanup

HTTP close succeeded, but is not GPU/server cancellation evidence. The bounded
Start-Process unload helper was rejected by tool policy before execution; no
alternate launcher or server/model-wide stop was attempted. Read-only /api/ps
showed only the project alias with finite expiry 2026-10-04T22:34:55.5704569+05:30.
At 2026-10-04T22:35:16.9458759+05:30, /api/ps returned models=[]: automatic
unload is confirmed. No explicit stop timing is claimed, and the longer
keep-alive period is not hidden.

## Final review / corrected checkpoint

The single fresh read-only review of d991bfc..3e1f72e independently passed
76 deterministic client/CLI checks, without another live/actual database run.
Two Important parsing findings were reproduced and fixed in one TDD pass:
independent enforcement of known token overflow despite an unavailable other
counter, and explicit assistant-role/tool/refusal-envelope checks. Thirty new
mocked controls include executor-never-open assertions; final client/CLI 106/106,
full 719/719 zero skips (165 actual PG checks), lint/format/whitespace pass.
No Critical or deferred Minor finding; all ten review exclusions/costs in D-031.

This live record remains at the original f8b8150 runtime above; it was not
silently repeated after the parsing fix. Corrected llm.py SHA-256:
622349fd7603f010ff85e00a0a9bef337bc3912e1693de254cbc6bc77655e6b4.
cli.py/lock/prompt/model configuration remain unchanged. G0.7a is complete
after review/fix verification; G0 itself and accuracy/evaluation remain open.
