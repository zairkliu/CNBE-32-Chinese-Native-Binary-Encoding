#!/usr/bin/env python3
"""Batch cnbe64-pilot inference over pilot chars and compare with deterministic evidence."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(EXP.parent / "2026-08-07_api_pipeline"))

from clients.evidence import aggregate, load_ids, load_radix_name_map, load_unihan_irg  # noqa: E402


def main() -> int:
    evidence = json.loads((EXP / "results" / "pilot_evidence.json").read_text(encoding="utf-8"))["entries"]
    base = REPO / "experiments" / "2026-08-05_scheme_comparison" / "build"
    unihan = load_unihan_irg(base / "Unihan_IRGSources.txt")
    ids_map = load_ids(base / "ids.txt")
    radix_name = load_radix_name_map(REPO / "evidence/8105/cnbe8105_radical_code_map.json")
    reverse = {name: code for code, name in radix_name.items()}

    sample = []
    for stratum in ("A_8105_core", "B_outside_with_semantic", "C_extension_gap"):
        sample.extend([e for e in evidence if e["stratum"] == stratum][:10])

    outputs = []
    for e in sample:
        entry = {"char": e["char"], "unicode": e["ucp"], "standard_evidence": {"issues": [], "structure": None}}
        ev = aggregate(entry, unihan, ids_map, radix_name)
        sem = e["semantic"]
        prompt = (
            "char=" + e["char"]
            + " cnbe64=" + e["cnbe64"]
            + " gb18030_pointer=" + str(e["gb18030_pointer"])
            + " definition=" + sem["definition"][:120]
            + " mandarin=" + sem["mandarin"]
            + " glyph_evidence=rendered"
        )
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "cnbe64-pilot",
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": 0.0, "num_ctx": 2048, "num_predict": 256},
            },
            timeout=300,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {}
        structure_ok = None
        radix_ok = None
        stroke_diff = None
        if data:
            structure_ok = (data.get("structure_guess") == ev["structure"])
            model_radix = data.get("radix_guess", "")
            radix_ok = (model_radix == ev["radix_name"])
            if isinstance(data.get("stroke_guess"), int) and ev["strokes"] is not None:
                stroke_diff = abs(int(data["stroke_guess"]) - int(ev["strokes"]))
        outputs.append(
            {
                "ucp": e["ucp"],
                "char": e["char"],
                "stratum": e["stratum"],
                "raw": text[:500],
                "parsed": bool(data),
                "model": data,
                "deterministic": {"structure": ev["structure"], "radix_name": ev["radix_name"], "strokes": ev["strokes"]},
                "structure_ok": structure_ok,
                "radix_ok": radix_ok,
                "stroke_diff": stroke_diff,
            }
        )

    parsed = sum(1 for o in outputs if o["parsed"])
    struct_ok = sum(1 for o in outputs if o["structure_ok"] is True)
    radix_ok = sum(1 for o in outputs if o["radix_ok"] is True)
    stroke_exact = sum(1 for o in outputs if o["stroke_diff"] == 0)
    stroke_plus1 = sum(1 for o in outputs if o["stroke_diff"] is not None and o["stroke_diff"] <= 1)
    result = {
        "schema_version": 1,
        "n": len(outputs),
        "parsed": parsed,
        "structure_agreement": struct_ok,
        "radix_agreement": radix_ok,
        "stroke_exact": stroke_exact,
        "stroke_within1": stroke_plus1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "entries": outputs,
    }
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "model_batch_30.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
