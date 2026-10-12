"""Merge selected LoRA into original FP16 weights on one GPU, then check reload."""

from __future__ import annotations

import gc
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from scripts.prepare_g6_serving import check_serving_budget, file_hash, merge_inputs
    from scripts.run_g6_merge import serving_storage
    from scripts.run_training_pilot import available_ram

    used, added = serving_storage()
    preload_ram = available_ram()
    check_serving_budget(
        preload_ram, shutil.disk_usage(root).free, used, added, planned_d=3 * 2**30
    )
    base_path, adapter_path = merge_inputs(root)
    output = root / "models/g6/merged"
    evidence = root / "results/G6_training/merge.evidence.json"
    if output.exists() or evidence.exists():
        raise FileExistsError("merge destination already exists")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root):
        raise RuntimeError("merge requires clean Git")
    import torch
    from peft import PeftModel
    from safetensors import safe_open
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available() or torch.cuda.mem_get_info()[0] < 4 * 2**30:
        raise RuntimeError("merge requires at least 4 GiB free GPU memory")
    torch.manual_seed(42)
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        base_path, local_files_only=True, trust_remote_code=False
    )
    base = AutoModelForCausalLM.from_pretrained(
        base_path,
        local_files_only=True,
        trust_remote_code=False,
        use_safetensors=True,
        dtype=torch.float16,
        device_map={"": 0},
        attn_implementation="sdpa",
    ).eval()
    original = {
        name: value.detach().clone()
        for name, value in base.named_parameters()
        if name.endswith(("q_proj.weight", "v_proj.weight"))
    }
    adapted = PeftModel.from_pretrained(base, adapter_path, is_trainable=False).eval()
    with torch.no_grad():
        merged = adapted.merge_and_unload(safe_merge=True).eval()
        state = merged.state_dict()
        assert not any("lora_" in name for name in state)
        assert any(not torch.equal(value, state[name]) for name, value in original.items())
        assert all(torch.isfinite(value).all() for value in state.values())
        del original
        messages = [
            {
                "role": "user",
                "content": "Write one read-only SQL statement selecting the number one.",
            }
        ]
        inputs = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
        ).to("cuda")
        expected_logits = merged(inputs, use_cache=False).logits.detach().cpu()
        merged.save_pretrained(output, safe_serialization=True, max_shard_size="500MB")
        tokenizer.save_pretrained(output)
        saved_keys = set()
        for shard in sorted(output.glob("*.safetensors")):
            with safe_open(shard, framework="pt", device="cpu") as saved:
                for name in list(saved.keys()):
                    assert torch.equal(saved.get_tensor(name), state[name].cpu())
                    saved_keys.add(name)
        missing = set(state) - saved_keys
        assert not missing or (
            missing == {"lm_head.weight"}
            and torch.equal(state["lm_head.weight"], state["model.embed_tokens.weight"])
        )
    del state, merged, adapted, base
    gc.collect()
    torch.cuda.empty_cache()
    loaded = AutoModelForCausalLM.from_pretrained(
        output,
        local_files_only=True,
        trust_remote_code=False,
        use_safetensors=True,
        dtype=torch.float16,
        device_map={"": 0},
        attn_implementation="sdpa",
    ).eval()
    loaded.requires_grad_(False)
    with torch.inference_mode():
        actual_logits = loaded(inputs, use_cache=False).logits.cpu()
        assert torch.equal(expected_logits, actual_logits), (
            "saved model logits changed after reload"
        )
        generated = loaded.generate(
            inputs, max_new_tokens=16, do_sample=False, pad_token_id=tokenizer.eos_token_id
        )
        response = tokenizer.decode(generated[0, inputs.shape[1] :], skip_special_tokens=True)
        assert response.strip(), "reloaded model returned no output"
    pin = json.loads((root / "docs/g6-serving-inputs.json").read_text(encoding="utf-8"))
    report = {
        "status": "completed",
        "model": pin["model"],
        "revision": pin["revision"],
        "selected_checkpoint": pin["selected_adapter"]["step"],
        "adapter_sha256": pin["selected_adapter"]["sha256"],
        "device": "cuda",
        "dtype": "float16",
        "preload_ram_bytes": preload_ram,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "changed_weights": True,
        "saved_tensors_equal": True,
        "reload_logits_equal": True,
        "generation_nonempty": True,
        "generation_sha256": hashlib.sha256(response.encode()).hexdigest(),
        "artifact_files": {
            path.name: {"bytes": path.stat().st_size, "sha256": file_hash(path)}
            for path in sorted(output.iterdir())
            if path.is_file()
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root)),
    }
    with evidence.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print("selected full model merged, saved and reloaded", flush=True)


if __name__ == "__main__":
    main()
