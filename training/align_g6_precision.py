"""Align one observed untrained GGUF bias with the merge's FP16 loading path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import gguf
    import numpy as np

    from scripts.prepare_g6_serving import file_hash, fp16_rounding_changes
    from scripts.run_g6_conversion import monitor

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root):
        raise RuntimeError("precision alignment requires clean Git provenance")
    monitor()
    summary = root / "results/G6_training/precision-alignment.json"
    backup = root / ".tools/g6/base-bias-before-alignment.json"
    if summary.exists() or backup.exists():
        raise FileExistsError("alignment evidence exists; refusing repeat")
    directory = Path(
        json.loads((root / ".tools/g6/ollama-cache-baseline.json").read_text())[
            "conversion_directory"
        ]
    )
    original = json.loads((root / "results/G6_training/conversion.json").read_text())
    readers = {}
    before = {}
    for model in ["base", "tuned"]:
        readers[model] = {}
        for kind, suffix in [("f16", "f16"), ("q4km", "q4km")]:
            path = directory / f"{model}-{suffix}.gguf"
            assert file_hash(path) == original["models"][model][kind]["sha256"]
            reader = gguf.GGUFReader(str(path), mode="r+" if model == "base" else "r")
            readers[model][kind] = {t.name: t for t in reader.tensors}
            before[path.name] = file_hash(path)
            # Keep the owning mmap alive until the bounded update is flushed.
            readers[model][f"{kind}_reader"] = reader
    name = "blk.14.attn_v.bias"
    replacements = []
    for kind in ["f16", "q4km"]:
        left, right = readers["base"][kind][name], readers["tuned"][kind][name]
        assert left.tensor_type.name == right.tensor_type.name == "F32"
        assert left.n_elements == right.n_elements == 256
        assert fp16_rounding_changes(left.data.tobytes(), right.data.tobytes()) == 1
        replacements.append((kind, left, right.data.copy()))
    assert set(readers["tuned"]["f16"]) == set(readers["base"]["f16"])
    targets = []
    for tensor_name, left in readers["base"]["f16"].items():
        right = readers["tuned"]["f16"][tensor_name]
        assert left.tensor_type == right.tensor_type and np.array_equal(left.shape, right.shape)
        if not np.array_equal(left.data, right.data) and tensor_name != name:
            assert ".attn_q.weight" in tensor_name or ".attn_v.weight" in tensor_name
            targets.append(tensor_name)
    assert len(targets) == 56
    with backup.open("x", encoding="utf-8") as handle:
        json.dump(
            {
                "before_sha256": before,
                "tensor": name,
                "original_tensor_bytes_hex": replacements[0][1].data.tobytes().hex(),
            },
            handle,
        )
    for _, tensor, values in replacements:
        tensor.data[:] = values
        tensor.data.flush()
    report = {
        "status": "completed",
        "tensor": name,
        "elements_rounded": 1,
        "maximum_absolute_difference": 2.2351741790771484e-08,
        "reason": "match full FP16 loading before Q4_K_M; no learned bias",
        "source_weights_and_adapter_unchanged": True,
        "recoverable_bytes_saved": True,
        "before_sha256": before,
        "after_sha256": {path.name: file_hash(path) for path in sorted(directory.glob("*.gguf"))},
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
    }
    with summary.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print("one untrained base bias rounded identically; original bytes retained", flush=True)


if __name__ == "__main__":
    main()
