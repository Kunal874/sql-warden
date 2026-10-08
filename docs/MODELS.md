# Local model evidence

## G0.6 — Arctic Text2SQL second-model smoke (2026-10-08)

The second 7B candidate is installed and passed a bounded local synthetic SQL
capability smoke. This is not an accuracy score. The prompt contained only a tiny
invented `planets` table and question; it contained no project database data,
labels, gold SQL, result cells or credentials.

The official source is
[Snowflake/Arctic-Text2SQL-R1-7B](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B/tree/2d73facaf7e15831d0b918d219e0d565f113f592)
at revision `2d73facaf7e15831d0b918d219e0d565f113f592`, Apache-2.0. The
fixed local artifact is the community Q4_K_M conversion from
[revision 8e1a5118](https://huggingface.co/mradermacher/Arctic-Text2SQL-R1-7B-GGUF/tree/8e1a51188952afa8021bce6c8b3e5b495b3e85cd):

- `Arctic-Text2SQL-R1-7B.Q4_K_M.gguf`, 4,683,074,144 bytes.
- SHA-256 `9c005244e3ab7fada2c53a9511999f4d22fbbd4f76a4416416a6d41d82702255`.
- Download used the revision-addressed URL, identity encoding, explicit no-proxy
  client, exact byte/range checks, staging rename and a 12 GiB disk reserve.
- The ignored local weight was hashed again after download; weights are not in Git.

The fixed Ollama alias is
`sqlwarden-arctic-text2sql-r1-7b-q4km-ctx8192:smoke-v1`, digest
`d4e34b35065d29da2566b3b201d9e6bd54d005c565e1e182a9e318086168b19d`.
It sets context 8,192, default output 1,024 and temperature zero. Ollama identifies
the artifact as Qwen2-family, 7.6B, Q4_K_M. The effective 2,507-byte template hashes
to `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.

Two identical temperature-zero/seed-42 calls each reported 56 input and 18 output
tokens, produced parseable SQL for the synthetic schema, and had the same output
hash. They took 8.718 seconds cold and 0.360 seconds warm. A third request stopped at
the four-token cap in 0.109 seconds with `done_reason=length`. Usage was available.
Only Arctic was loaded; Ollama reported context 8,192 and 5,133,943,438 bytes wholly
on GPU. Sampled GPU free memory moved from 7,956 MiB to 2,956 MiB and returned to
7,956 MiB after unload. Minimum sampled available system RAM was 948,318,208 bytes.

An initial metadata-only request exceeded the probe's 128 KiB response cap before
loading the model. It made no generation call and cleanup was verified. The successful
retry requested ordinary metadata and made exactly three calls. The compact tracked
record is [arctic-smoke-manifest.json](arctic-smoke-manifest.json); raw content stays
ignored. The model is now unloaded. The official card limits intended use to
text-to-SQL, so Arctic is not selected as the general helper model.

## G0.6a — Qwen feasibility smoke (2026-10-03)

The warmed-up Qwen model responds locally on this laptop. Six tiny synthetic
requests passed through /v1/chat/completions from Python 3.12. This is not a
text-to-SQL result or an accuracy benchmark. No database rows, labels, credentials
or generated SQL were sent to or executed by the probe.

Native Ollama is 0.35.1, bound to 127.0.0.1:11434. The probe used Python's standard
library with proxies/redirects disabled, not the future runtime SDK/client.
The [compact manifest](qwen-smoke-manifest.json) records the exact observations,
including the unsuccessful cold request; raw generations and weights are not in Git.

### Model and source pinning

The selected [Ollama Qwen tag](https://ollama.com/library/qwen2.5-coder:7b-instruct-q4_K_M)
is Qwen2.5-Coder-7B-Instruct in Q4_K_M GGUF form. Native metadata reports
7,615,616,512 parameters and an advertised 32,768-token context.

- Registry package SHA-256: dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364.
- GGUF model layer: 4683074048 bytes; SHA-256 60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463.
- Effective template: 1615 bytes; SHA-256 1e65450c30670713aa47fe23e8b9662bdf4065e81cc8e3cbfaa98924fcc0d320.
- All base model/system/template/license layers were independently checked with
  local file sizes and SHA-256, matching the [registry manifest](https://registry.ollama.ai/v2/library/qwen2.5-coder/manifests/7b-instruct-q4_K_M).
- The [upstream model card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/tree/c03e6d358207e414f1eca0bb1891e29f1db0e242)
  is recorded at revision c03e6d358207e414f1eca0bb1891e29f1db0e242 as a reference,
  not as proof that this particular Ollama conversion used that revision.
  Its source declares Apache-2.0; the downloaded license layer is retained locally.

### Bounded local alias

Created only this new, previously absent alias:
sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1. It shares the base GGUF/template;
it does not duplicate the model download. Package digest:
b00066f4a0af314f23919f5644e49e37f8ec7210ecd9cc2ae4236f43ef1d9c2b.

The alias sets num_ctx=2048 and default num_predict=64. Each actual request
also specified its output cap. Using a local alias to control context follows
[Ollama's compatibility guidance](https://docs.ollama.com/api/openai-compatibility).
No system-wide Ollama settings were changed. The context size was verified in
/api/ps and ollama ps; overflow/truncation behavior was not tested.

The successful setup-only /api/create request was:

```json
{"model":"sqlwarden-qwen2.5-coder-7b-ctx2048:smoke-v1","from":"qwen2.5-coder:7b-instruct-q4_K_M","parameters":{"num_ctx":2048,"num_predict":64},"stream":false}
```

Do not blindly recreate or overwrite this existing alias. Compare recorded
digests and parameters before use. [Ollama's create endpoint](https://docs.ollama.com/api/create)
documents the configuration operation.

### Actual requests and limits

One cold request timed out at 60.031 seconds and has unavailable usage. The
server log reports 45.30 seconds to start its runner; the first-use request
had not produced a response when its client deadline expired. We did not
increase that deadline or change the product code. Once the same runner was
loaded, one warm probe passed all six checks with the original 60-second
per-call bound. Warm success does not fix or hide the cold-start failure.

| Warm check | Observed result | Seconds | Input / output tokens |
| --- | --- | ---: | ---: |
| Exact short text | LOCAL_SMOKE_OK matched | 3.781 | 41 / 6 |
| JSON object | status=ok, sum=5 parsed and matched | 0.782 | 47 / 17 |
| JSON schema | same object matched the requested shape | 0.750 | 46 / 17 |
| Seed 42, call A | successful fresh generation | 0.265 | 42 / 6 |
| Seed 42, call B | content hash matched A | 0.203 | 42 / 6 |
| max_tokens=2 | two output tokens; finish_reason=length | 0.172 | 42 / 2 |

The complete warm probe took 5.969 seconds. Seven generation requests were
actually made: one timed out, six succeeded. Reported successful usage totals
260 input and 54 output tokens; the timeout's usage is unknown, not zero.
There was no application response-cache replay. Ollama did reuse prompt/KV
processing, which appears in its cached_tokens fields. These tiny warmed timings
are not benchmark throughput or cold-start performance.

Text prompt: "Reply with exactly LOCAL_SMOKE_OK and nothing else." JSON prompts
requested only status=ok and the sum of 2+3. The seed pair requested three
comma-separated color names at temperature=0.7, seed=42, max_tokens=32.
The cap control requested counting from 1 to 50 with max_tokens=2. Other calls
used temperature=0; JSON output caps were 64. The schema required status="ok",
sum=5 as an integer, both fields and no extra properties. JSON was parsed and
the exact expected object checked; this does not prove arbitrary schema support.

The throwaway probe is ignored under .tools/probes/qwen_smoke.py. It allowed
at most 64 KiB per HTTP response and checked a 180-second total budget before
starting another call. It is not a retained runtime implementation. The future
runtime must use the approved SDK and its own tested limits/cancellation.

### Measured memory and cleanup

Ollama reported 4628519320 bytes of model memory, all on GPU, with context 2048.
Only one project model was loaded at a time. The highest sampled NVIDIA device
usage in the warm probe was 5565 MiB, including other applications and driver
usage; it is not model-only usage or a guaranteed exact peak. Minimum sampled
GPU free memory was 2392 MiB; available physical RAM was at least 1958367232
bytes in those samples. Sampling was approximately once per second.

After the checks, ollama stop unloaded the project model. /api/ps reports zero
running models; a following device sample reported 1194 MiB used and 6763 MiB
free. The downloaded weights remain installed for reuse. No other application
was closed or changed by the probe.

### What remains unproved

- Cold-start requests can exceed 60 seconds; use a separately bounded readiness/
  warmup strategy in later implementation rather than unbounded retries.
- Larger contexts, context overflow/truncation, cancellation and concurrent
  requests are not established. A 2048-token smoke is not a full-schema budget.
- One matching seed pair is not a universal repeatability guarantee. Tool calling
  is advertised by metadata, but was not exercised.
- No SQL accuracy, BIRD EX score, gold query or database execution occurred.
- Exact conversion ancestry is unavailable; the actual GGUF artifact is pinned.
- The second model, runtime provider, guarded CLI and production attack controls
  remain later tasks.

Next: G0.7a's reviewed minimum SQL guard, bounded executor, pinned result comparator
and one-database CLI. Do not execute generated SQL until those controls pass.
