"""Static GitHub Pages variant: Benchmark and Attack Lab read exported JSON, no live API.

Build: `cd web && npm run build:static`, then
`uv run python -m scripts.export_static_site` (writes web/dist-static/data/*.json).
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlwarden.webapp import ROOT, attacks_payload, benchmark_payload

OUT = ROOT / "web/dist-static"


def export(out: Path = OUT) -> list[Path]:
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    written = []
    for name, payload in (("benchmark", benchmark_payload()), ("attacks", attacks_payload())):
        path = data / f"{name}.json"
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in export():
        print(path.relative_to(ROOT))
