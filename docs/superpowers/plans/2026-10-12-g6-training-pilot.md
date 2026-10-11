# G6 Training Pilot Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement sequentially. No parallel implementation.

**Goal:** Prove a reproducible local QLoRA training run before preparing the full E9 experiment.

**Architecture:** A separate training project under `training/` uses Python 3.12
and uv. The existing runtime environment stays unchanged. Train only adapters;
reuse the existing guard, executor, comparator and evaluation reporting later.

**Tech Stack:** Proposed torch, transformers, peft, accelerate, bitsandbytes,
huggingface-hub; standard-library JSON instead of a dataset library.

**Spec:** `docs/BUILD_SPEC.md`, section 10, and this pilot's exact constraints below.

## Status and purpose

Kunal approved pursuing fine-tuning for resume value on 2026-10-12. The specific
libraries, model and resource limits below await the required C8 answer. No
training dependency, model download or training run has happened in this task.
Success means logged GPU training and a reloadable adapter, not higher accuracy.
Resume wording will use measured results; a feasibility run alone is not an
accuracy result or completion of G6.

## Global constraints

- Native Windows first, Python 3.12, separate `training/.venv` and lockfile.
- Model: `Qwen/Qwen2.5-Coder-1.5B-Instruct`, revision
  `2e1fd397ee46e1388853d2af2c993145b0f1098a` (official metadata checked today).
- Official safetensors only, `trust_remote_code=False`; inference and training local.
- Pilot data: eight invented PostgreSQL question/schema/SQL examples, not BIRD.
- Seed 42, NF4 4-bit load, LoRA rank 8/alpha 16, attention q/v projections,
  batch size 1, gradient accumulation 4, gradient checkpointing, 512-token limit,
  20 optimizer steps, learning rate 0.0002, dropout 0, AdamW.
- Labels cover response SQL only; prompt and padding tokens have label -100.
- Use bf16 only if the installed CUDA backend supports it; otherwise fp16.
- Cap the training subprocess at 45 minutes, additional disk at 12 GiB including
  caches/downloads/checkpoints, preserve 20 GiB free on D:, and require 4 GiB
  available system RAM before loading. Abort on non-finite loss or GPU OOM.
- Do not terminate unrelated applications or unload models without identifying
  the project's own models. Ask the user to free RAM if the RAM floor fails.
- Install binary wheels from PyPI and the official PyTorch CUDA index after
  approval; choose compatible stable versions, lock them and record versions.
  No system CUDA/compiler install or Ubuntu fallback in this pilot approval.
- Weights, optimizer state, training examples and raw logs remain ignored under
  `models/`, `data/`, `results/G6_pilot/raw/` and `.tools/`.
- No money, accounts, upload, push, weight publication or runtime model replacement.

## Preflight evidence (2026-10-12)

- RTX 4060 Laptop GPU: 8188 MiB total, 7956 MiB free; NVIDIA driver 610.74.
- D: free 37,842,935,808 bytes (~35.2 GiB).
- System RAM: 1,097,364 KiB free (~1.05 GiB) at inspection; below pilot floor.
- WSL has only `docker-desktop`, so Ubuntu is not an available training environment.
- Official bitsandbytes docs list Windows x86-64 CUDA wheels. This establishes a
  candidate environment, not proof that our exact resolved packages work together.

## Review focus

Tests must cover response-only labels, all examples exceeding the token limit,
non-finite loss, interrupted runs without completed summaries, and disk/RAM
refusal. A saved adapter must change a trainable weight and reload successfully.

## Task 1 — isolated environment and bounded runner (G6.1/G6.2)

Files: `training/pyproject.toml`, `training/uv.lock`,
`scripts/run_training_pilot.py`, `tests/test_training_pilot.py`, `.gitignore`.

- [ ] Obtain C8 approval for the proposed pilot choices and packages.
- [ ] Test first: resource checks refuse insufficient memory/disk; subprocess
  timeout never writes a completed result; importing the runner needs no torch.
- [ ] Implement the stdlib supervisor and separate dependency project. Install
  and lock approved packages without adding them to runtime `pyproject.toml`.
- [ ] Check CUDA tensor operations and a bitsandbytes 4-bit forward/backward pass.
  Record package versions and GPU identity. Stop on failure rather than use CPU.
- [ ] Run focused tests, lint and format checks; update memory files and commit.

## Task 2 — actual synthetic training and adapter reload (G6.2)

Files: `training/pilot.py`, `tests/test_training_pilot.py`,
`results/G6_pilot/summary.json` (compact metadata only).

- [ ] Test first: prompt/padding labels are masked; no completion fits means
  explicit failure; a NaN/inf loss rejects completion; summary contains no SQL.
- [ ] Write eight invented examples and the response-only collator. Download
  only pinned model/tokenizer files after checking size and remaining budget.
- [ ] Train under the fixed limits; log trainable parameter count, per-step
  finite loss, elapsed time, peak GPU memory, seed, code commit and dirty state.
- [ ] Save adapter under ignored `models/`; prove a trainable weight changed,
  reload it and generate one bounded synthetic SQL response. A loss decrease
  or syntactically valid SQL is not an execution-accuracy claim.
- [ ] Unload the training process, export compact evidence, run checks, update
  progress/decisions/notebook and commit. Mark G6.2 only if actual GPU run passes.

## Task 3 — concrete full-training proposal after measurement

- [ ] Estimate throughput at a realistic schema length using the successful
  backend, then propose the full dataset and training time/disk cap.
- [ ] Prefer execution-verified PostgreSQL labels. Transpile-only labels need an
  explicit recorded choice, sample audit and unverified-label disclosure.
- [ ] Freeze training/validation by database and check IDs/schema/content
  overlaps against all existing evaluation databases before training.
- [ ] Propose base-versus-tuned E9 with identical prompt, quantization, context
  and generation budgets; compare Arctic only under a comparable contract.
  Existing held-out scores have already been viewed: reruns are historical
  regression comparisons, not a newly untouched test set.
- [ ] Specify adapter merge/GGUF conversion requirements and dependencies before
  installing conversion tools. Only measured improvements become resume claims.

## Sources checked 2026-10-12

- https://huggingface.co/docs/bitsandbytes/main/en/installation
- https://huggingface.co/docs/peft/developer_guides/quantization
- https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct

Full training, BIRD training-data acquisition and GGUF conversion are follow-on
work, not included in the 20-step feasibility pilot.
