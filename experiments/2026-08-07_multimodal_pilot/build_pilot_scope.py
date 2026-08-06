#!/usr/bin/env python3
"""Build a stratified 300-character multimodal pilot scope.

Strata:
  A: 100 chars inside the 8105 national-standard core
  B: 100 outside-8105 chars with existing semantic cross-reference
  C: 100 outside-8105 extension/gap chars (Extension B+ or no semantic ref)
"""

from __future__ import annotations

import gzip
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent


def load_catalog_rows(path: Path) -> list[dict]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("id,"):
                continue
            parts = line.split(",")
            ucp = parts[1]
            rows.append(
                {
                    "ucp": ucp,
                    "char": chr(int(ucp[2:], 16)),
                    "cnbe_hex": parts[2],
                    "block": parts[6],
                }
            )
    return rows


def load_8105_ucps(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {f"U+{ord(c):04X}" for c in data["characters"]}


def load_semantic_ucps(base: Path) -> set[str]:
    semantic: set[str] = set()
    readings = base / "Unihan_Readings.txt"
    for line in readings.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and parts[1] in ("kDefinition", "kMandarin", "kHanyuPinyin", "kCantonese"):
            semantic.add(parts[0])
    return semantic


def main() -> int:
    rng = random.Random(42)
    rows = load_catalog_rows(REPO / "data" / "cnbe_catalog_fixed.csv.gz")
    core = load_8105_ucps(REPO / "evidence" / "8105" / "cnbe8105_standard_baseline.json")
    semantic = load_semantic_ucps(REPO / "experiments" / "2026-08-05_scheme_comparison" / "build")

    a = [r for r in rows if r["ucp"] in core]
    b = [r for r in rows if r["ucp"] not in core and r["ucp"] in semantic]
    c = [r for r in rows if r["ucp"] not in core and (r["ucp"] not in semantic or r["block"] not in ("CJK Unified Ideographs", "CJK Unified Ideographs Extension A"))]

    rng.shuffle(a)
    rng.shuffle(b)
    rng.shuffle(c)
    scope = [
        {**r, "stratum": "A_8105_core", "semantic_ref": r["ucp"] in semantic}
        for r in a[:100]
    ] + [
        {**r, "stratum": "B_outside_with_semantic", "semantic_ref": True}
        for r in b[:100]
    ] + [
        {**r, "stratum": "C_extension_gap", "semantic_ref": r["ucp"] in semantic}
        for r in c[:100]
    ]
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "seed": 42,
        "strata": {
            "A_8105_core": 100,
            "B_outside_with_semantic": 100,
            "C_extension_gap": 100,
        },
        "entries": scope,
    }
    (out / "pilot_scope.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    from collections import Counter
    print(Counter(e["stratum"] for e in scope))
    print("total", len(scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
