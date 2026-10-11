"""Response-only QLoRA pilot; heavy packages are imported only when running."""

from __future__ import annotations

import math

MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
REVISION = "2e1fd397ee46e1388853d2af2c993145b0f1098a"


def response_example(
    prompt: list[int], response: list[int], *, max_length: int, pad_id: int
) -> dict[str, list[int]]:
    if not response or len(prompt) + len(response) > max_length:
        raise ValueError("example exceeds token limit or has no response")
    padding = max_length - len(prompt) - len(response)
    return {
        "input_ids": prompt + response + [pad_id] * padding,
        "attention_mask": [1] * (len(prompt) + len(response)) + [0] * padding,
        "labels": [-100] * len(prompt) + response + [-100] * padding,
    }


def validate_losses(losses: list[float], *, expected_steps: int) -> None:
    if not losses or any(not math.isfinite(loss) for loss in losses):
        raise ValueError("missing or non-finite loss")
    if len(losses) != expected_steps:
        raise ValueError("incomplete optimizer steps")


def main() -> None:
    import argparse
    import hashlib
    import importlib.metadata
    import json
    import subprocess
    import sys
    import time
    from pathlib import Path

    import bitsandbytes as bnb
    import torch
    from huggingface_hub import snapshot_download
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import shutil

    from scripts.run_training_pilot import available_ram, check_resources, disk_used

    check_resources(available_ram(), shutil.disk_usage(root).free, disk_used())
    if args.evidence.exists():
        raise FileExistsError("evidence already exists")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; CPU training is refused")
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    probe = bnb.nn.Linear4bit(16, 16, quant_type="nf4", compute_dtype=dtype).to("cuda")
    probe_input = torch.randn(2, 16, device="cuda", dtype=dtype, requires_grad=True)
    probe(probe_input).float().sum().backward()
    if not torch.isfinite(probe_input.grad).all():
        raise RuntimeError("4-bit GPU backward probe failed")
    del probe, probe_input
    torch.cuda.empty_cache()
    print("cuda_4bit_backward=passed", flush=True)

    model_path = snapshot_download(
        MODEL,
        revision=REVISION,
        token=False,
        cache_dir=root / "models/g6/cache",
        allow_patterns=["*.safetensors", "*.json", "merges.txt", "vocab.json"],
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    examples = [
        ("How many planets are recorded?", "SELECT COUNT(*) FROM planets;"),
        ("List all planet names.", "SELECT name FROM planets;"),
        ("Which planets have more than 2 moons?", "SELECT name FROM planets WHERE moons > 2;"),
        ("What is the largest moon count?", "SELECT MAX(moons) FROM planets;"),
        ("What is the average moon count?", "SELECT AVG(moons) FROM planets;"),
        ("List planet names alphabetically.", "SELECT name FROM planets ORDER BY name;"),
        ("How many planets have no moons?", "SELECT COUNT(*) FROM planets WHERE moons = 0;"),
        ("What is the total number of moons?", "SELECT SUM(moons) FROM planets;"),
    ]
    records = []
    for question, sql in examples:
        messages = [
            {
                "role": "user",
                "content": "Write one read-only PostgreSQL query in a sql code block.\n"
                "Schema: planets(id INTEGER PRIMARY KEY, name TEXT, moons INTEGER).\n" + question,
            }
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        answer = tokenizer.encode(
            f"```sql\n{sql}\n```" + tokenizer.eos_token, add_special_tokens=False
        )
        records.append(
            response_example(prompt, answer, max_length=512, pad_id=tokenizer.pad_token_id)
        )
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=dtype,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map={"": 0},
        quantization_config=quantization,
        torch_dtype=dtype,
        trust_remote_code=False,
        attn_implementation="sdpa",
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(
        model,
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
    # LoRA B starts at zero, so compare a B weight to prove an update actually happened.
    tracked = next(
        parameter
        for name, parameter in model.named_parameters()
        if "lora_B" in name and parameter.requires_grad
    )
    initial_weight = tracked.detach().clone()
    optimizer = torch.optim.AdamW(trainable, lr=0.0002, weight_decay=0)
    scaler = torch.amp.GradScaler("cuda", enabled=dtype == torch.float16)
    losses = []
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    model.train()
    for step in range(20):
        optimizer.zero_grad(set_to_none=True)
        step_loss = 0.0
        for micro in range(4):
            record = records[(step * 4 + micro) % len(records)]
            batch = {key: torch.tensor([value], device="cuda") for key, value in record.items()}
            with torch.autocast("cuda", dtype=dtype):
                loss = model(**batch).loss
            if not torch.isfinite(loss):
                raise RuntimeError("non-finite loss; run aborted")
            step_loss += loss.detach().float().item() / 4
            scaler.scale(loss / 4).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(trainable, 1.0, error_if_nonfinite=True)
        scaler.step(optimizer)
        scaler.update()
        losses.append(step_loss)
        print(f"optimizer_step={step + 1} loss={step_loss:.5f}", flush=True)
    validate_losses(losses, expected_steps=20)
    changed = not torch.equal(initial_weight, tracked.detach())
    if not changed:
        raise RuntimeError("adapter did not learn; no weight changed")
    adapter_path = root / "models/g6/pilot-adapter"
    if adapter_path.exists():
        raise FileExistsError("adapter output already exists")
    model.save_pretrained(adapter_path, safe_serialization=True)
    elapsed = time.monotonic() - started
    peak_allocated = torch.cuda.max_memory_allocated()
    peak_reserved = torch.cuda.max_memory_reserved()
    trained_count = sum(parameter.numel() for parameter in trainable)
    total_count = sum(parameter.numel() for parameter in model.parameters())
    expected_weight = tracked.detach().cpu().clone()
    base_model = model.unload()
    del model, optimizer, trainable, tracked, initial_weight
    reloaded = PeftModel.from_pretrained(base_model, adapter_path, is_trainable=False)
    loaded_weight = next(
        parameter for name, parameter in reloaded.named_parameters() if "lora_B" in name
    )
    if not torch.equal(expected_weight, loaded_weight.detach().cpu()):
        raise RuntimeError("saved adapter weight differs after reload")
    reloaded.eval()
    reloaded.config.use_cache = True
    record = records[0]
    prompt_length = record["labels"].index(
        next(value for value in record["labels"] if value != -100)
    )
    inputs = torch.tensor([record["input_ids"][:prompt_length]], device="cuda")
    with torch.inference_mode():
        generated = reloaded.generate(
            input_ids=inputs,
            attention_mask=torch.ones_like(inputs),
            max_new_tokens=64,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    response = tokenizer.decode(generated[0, prompt_length:], skip_special_tokens=True)
    if not response.strip():
        raise RuntimeError("reloaded adapter generated no response")
    raw_path = root / ".tools/g6"
    raw_path.mkdir(parents=True, exist_ok=True)
    (raw_path / "pilot-generation.txt").write_text(response, encoding="utf-8")
    report = {
        "status": "completed",
        "device": "cuda",
        "model": MODEL,
        "revision": REVISION,
        "seed": 42,
        "steps": 20,
        "gpu_name": torch.cuda.get_device_name(),
        "elapsed_seconds": elapsed,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "trainable_parameters": trained_count,
        "parameter_storage_elements": total_count,
        "losses": losses,
        "adapter_changed": changed,
        "adapter_reloaded": True,
        "cuda_probe": True,
        "generation_nonempty": True,
        "generation_sha256": hashlib.sha256(response.encode()).hexdigest(),
        "adapter_sha256": hashlib.sha256(
            (adapter_path / "adapter_model.safetensors").read_bytes()
        ).hexdigest(),
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
    print("adapter_reload=passed", flush=True)


if __name__ == "__main__":
    main()
