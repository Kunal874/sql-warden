"""One frozen QLoRA pass with database-separated validation checkpoints."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def choose_checkpoint(checkpoints: list[dict]) -> int:
    if not checkpoints or any(not math.isfinite(item["loss"]) for item in checkpoints):
        raise ValueError("missing or nonfinite validation metric")
    return min(checkpoints, key=lambda item: (item["loss"], item["step"]))["step"]


def load_tokenized(path: Path, fingerprint: str, *, max_length: int) -> list[dict]:
    if path.is_symlink() or path.stat().st_size > 128 * 2**20:
        raise ValueError("token file size/type refused")
    with path.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != fingerprint:
            raise ValueError("token fingerprint mismatch")
    with path.open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    if not records or len(records) > 2000:
        raise ValueError("token record count refused")
    for record in records:
        inputs, labels, mask = (record[key] for key in ["input_ids", "labels", "attention_mask"])
        if not len(inputs) == len(labels) == len(mask) == max_length:
            raise ValueError("token shape refused")
        if any(type(token) is not int or not 0 <= token < 200000 for token in inputs):
            raise ValueError("token value refused")
        if any(type(value) is not int or value not in (0, 1) for value in mask):
            raise ValueError("attention mask refused")
        if not any(label != -100 for label in labels) or any(
            type(label) is not int or (label != -100 and (label != token or not attended))
            for token, label, attended in zip(inputs, labels, mask, strict=True)
        ):
            raise ValueError("answer labels refused")
    return records


def main() -> None:
    import argparse
    import importlib.metadata
    import shutil
    import subprocess
    import sys
    import time

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()

    import torch
    from peft import (
        LoraConfig,
        PeftModel,
        get_peft_model,
        get_peft_model_state_dict,
        prepare_model_for_kbit_training,
    )
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from scripts.run_training_pilot import available_ram, check_resources, disk_used
    from training.pilot import MODEL, REVISION, validate_losses

    manifest = json.loads(
        (root / "docs/training-tokenized-manifest.json").read_text(encoding="utf-8")
    )
    if (
        manifest["model"] != MODEL
        or manifest["revision"] != REVISION
        or manifest["max_length"] != 2048
    ):
        raise ValueError("frozen tokenization contract mismatch")
    train = load_tokenized(
        root / "data/training/tokenized/train.jsonl", manifest["train"]["sha256"], max_length=2048
    )
    validation = load_tokenized(
        root / "data/training/tokenized/validation.jsonl",
        manifest["validation"]["sha256"],
        max_length=2048,
    )
    if {row["db_id"] for row in train} & {row["db_id"] for row in validation}:
        raise ValueError("training/validation database overlap")
    steps = 2 if args.probe else 500
    output = root / ("models/g6/length-probe" if args.probe else "models/g6/full-adapters")
    if output.exists() or args.evidence.exists():
        raise FileExistsError("training output already exists")
    check_resources(available_ram(), shutil.disk_usage(root).free, disk_used())
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.set_num_threads(4)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL,
        revision=REVISION,
        cache_dir=root / "models/g6/cache",
        local_files_only=True,
        trust_remote_code=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        MODEL,
        revision=REVISION,
        cache_dir=root / "models/g6/cache",
        local_files_only=True,
        trust_remote_code=False,
        device_map={"": 0},
        torch_dtype=dtype,
        attn_implementation="sdpa",
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        ),
    )
    base = prepare_model_for_kbit_training(
        base,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    model = get_peft_model(
        base,
        LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0,
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model.config.use_cache = False
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    tracked = next(parameter for name, parameter in model.named_parameters() if "lora_B" in name)
    initial = tracked.detach().clone()
    parameter_counts = model.get_nb_trainable_parameters()
    optimizer = torch.optim.AdamW(trainable, lr=0.0002, weight_decay=0)
    scaler = torch.amp.GradScaler("cuda", enabled=dtype == torch.float16)

    def batch_of(record):
        return {
            key: torch.tensor([record[key]], device="cuda")
            for key in ["input_ids", "attention_mask", "labels"]
        }

    def validation_loss(model):
        model.eval()
        losses = []
        with torch.inference_mode():
            for record in validation:
                with torch.autocast("cuda", dtype=dtype):
                    loss = model(**batch_of(record)).loss.detach().float().item()
                if not math.isfinite(loss):
                    raise RuntimeError("nonfinite validation loss")
                losses.append(loss)
        model.train()
        return sum(losses) / len(losses)

    before = None if args.probe else validation_loss(model)
    losses, checkpoints = [], []
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    model.train()
    for step in range(steps):
        optimizer.zero_grad(set_to_none=True)
        step_loss = 0.0
        for micro in range(4):
            record = train[step * 4 + micro]
            with torch.autocast("cuda", dtype=dtype):
                loss = model(**batch_of(record)).loss
            if not torch.isfinite(loss):
                raise RuntimeError("nonfinite training loss")
            step_loss += loss.detach().float().item() / 4
            scaler.scale(loss / 4).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(trainable, 1, error_if_nonfinite=True)
        scaler.step(optimizer)
        scaler.update()
        losses.append(step_loss)
        print(f"optimizer_step={step + 1}/{steps} loss={step_loss:.5f}", flush=True)
        if args.probe or (step + 1) % 100 == 0:
            score = step_loss if args.probe else validation_loss(model)
            checkpoint = output / f"step-{step + 1}"
            model.save_pretrained(checkpoint, safe_serialization=True)
            checkpoints.append(
                {
                    "step": step + 1,
                    "loss": score,
                    "adapter_sha256": hashlib.sha256(
                        (checkpoint / "adapter_model.safetensors").read_bytes()
                    ).hexdigest(),
                }
            )
            print(f"checkpoint={step + 1} validation_loss={score:.5f}", flush=True)
    elapsed = time.monotonic() - started
    validate_losses(losses, expected_steps=steps)
    changed = not torch.equal(initial, tracked.detach())
    if not changed:
        raise RuntimeError("adapter weights unchanged")
    chosen = steps if args.probe else choose_checkpoint(checkpoints)
    chosen_path = output / f"step-{chosen}"
    expected = load_file(str(chosen_path / "adapter_model.safetensors"))
    peak_allocated, peak_reserved = (
        torch.cuda.max_memory_allocated(),
        torch.cuda.max_memory_reserved(),
    )
    base = model.unload()
    del model, optimizer, trainable, tracked, initial
    reloaded = PeftModel.from_pretrained(base, chosen_path, is_trainable=False)
    state = get_peft_model_state_dict(reloaded)
    if set(state) != set(expected) or any(
        not torch.equal(state[key].cpu(), expected[key]) for key in state
    ):
        raise RuntimeError("checkpoint reload weights differ")
    reloaded.eval()
    reloaded.config.use_cache = True
    record = train[0]
    prompt_length = next(index for index, label in enumerate(record["labels"]) if label != -100)
    inputs = torch.tensor([record["input_ids"][:prompt_length]], device="cuda")
    with torch.inference_mode():
        output_tokens = reloaded.generate(
            input_ids=inputs,
            attention_mask=torch.ones_like(inputs),
            max_new_tokens=64,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    response = tokenizer.decode(output_tokens[0, prompt_length:], skip_special_tokens=True)
    if not response.strip():
        raise RuntimeError("reloaded checkpoint generated no response")
    (
        root / ".tools/g6" / ("probe-generation.txt" if args.probe else "full-generation.txt")
    ).write_text(response, encoding="utf-8")
    report = {
        "status": "completed",
        "device": "cuda",
        "model": MODEL,
        "revision": REVISION,
        "seed": 42,
        "steps": steps,
        "gpu_name": torch.cuda.get_device_name(),
        "max_length": 2048,
        "train_samples": steps * 4,
        "validation_samples": 0 if args.probe else len(validation),
        "train_sha256": manifest["train"]["sha256"],
        "validation_sha256": manifest["validation"]["sha256"],
        "label_validity": "execution-unverified PostgreSQL conversions",
        "elapsed_seconds": elapsed,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "trainable_parameters": parameter_counts[0],
        "logical_total_parameters": parameter_counts[1],
        "losses": losses,
        "validation_loss_before": before,
        "checkpoints": checkpoints,
        "chosen_checkpoint": chosen,
        "adapter_changed": changed,
        "adapter_reloaded": True,
        "adapter_sha256": hashlib.sha256(
            (chosen_path / "adapter_model.safetensors").read_bytes()
        ).hexdigest(),
        "generation_nonempty": True,
        "generation_sha256": hashlib.sha256(response.encode()).hexdigest(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in [
                "torch",
                "transformers",
                "peft",
                "accelerate",
                "bitsandbytes",
                "huggingface-hub",
            ]
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
        ),
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    with args.evidence.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(f"checkpoint_reload=passed chosen={chosen}", flush=True)


if __name__ == "__main__":
    main()
