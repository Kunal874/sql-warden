"""Tiny offline CPU/FP16 merge self-check; does not load the real Qwen weights."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path


def main() -> None:
    import torch
    from peft import LoraConfig, get_peft_model
    from safetensors.torch import load_file
    from transformers import Qwen2Config, Qwen2ForCausalLM

    root = Path(__file__).resolve().parents[1]
    report_path = root / "results/G6_training/merge-probe.json"
    if report_path.exists():
        raise FileExistsError("merge probe evidence already exists")
    torch.manual_seed(42)
    torch.set_num_threads(4)
    started = time.perf_counter()
    config = Qwen2Config(
        vocab_size=128,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=2,
        max_position_embeddings=128,
    )
    model = get_peft_model(
        Qwen2ForCausalLM(config).to(dtype=torch.float16),
        LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"),
    ).eval()
    with torch.no_grad():
        for name, value in model.named_parameters():
            if "lora_" in name:
                value.fill_(0.01)
        inputs = torch.tensor([[1, 2, 3, 4]])
        adapted = model(inputs).logits.clone()
        with model.disable_adapter():
            original = model(inputs).logits.clone()
        assert not torch.equal(adapted, original), "probe adapter has no effect"
        merged = model.merge_and_unload(safe_merge=True)
        assert not any("lora_" in name for name, _ in merged.named_parameters())
        merged_logits = merged(inputs).logits
        assert torch.allclose(adapted, merged_logits, atol=0.005, rtol=0.01)
        workspace = root / ".tools/g6"
        workspace.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="merge-probe-", dir=workspace) as directory:
            merged.save_pretrained(directory, safe_serialization=True)
            saved = load_file(str(Path(directory) / "model.safetensors"))
            loaded = Qwen2ForCausalLM.from_pretrained(
                directory, local_files_only=True, dtype=torch.float16
            ).eval()
            assert all(torch.equal(value, loaded.state_dict()[key]) for key, value in saved.items())
            assert torch.equal(merged_logits, loaded(inputs).logits)
    unsafe = get_peft_model(
        Qwen2ForCausalLM(config).to(dtype=torch.float16),
        LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"),
    )
    with torch.no_grad():
        next(value for name, value in unsafe.named_parameters() if "lora_B" in name).fill_(
            float("nan")
        )
    try:
        unsafe.merge_and_unload(safe_merge=True)
    except ValueError:
        pass
    else:
        raise AssertionError("safe_merge accepted nonfinite adapter")
    report = {
        "scope": "tiny invented Qwen2 CPU FP16 model; not full-model conversion",
        "status": "passed",
        "adapter_effect_checked": True,
        "merge_logits_close": True,
        "saved_tensors_reload_equal": True,
        "reload_logits_equal": True,
        "nonfinite_merge_refused": True,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root)),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
