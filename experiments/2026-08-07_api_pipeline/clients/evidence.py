#!/usr/bin/env python3
"""Local evidence aggregation for CNBE candidate prefill.

Only cross-reference evidence is produced here. Nothing in this module claims
national-standard authority; GF0011/GF0012/GF0013 adjudication stays gated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

STRUCT_ORDER = [
    "独体字", "上下", "上中下", "左右", "左中右", "左上包", "右上包",
    "左三包", "左下包", "上三包", "下三包", "全包围", "镶嵌",
]
STRUCT_CODE = {name: i for i, name in enumerate(STRUCT_ORDER)}
IDS_STRUCT = {
    "\u2ff0": "左右",
    "\u2ff1": "上下",
    "\u2ff2": "左中右",
    "\u2ff3": "上中下",
    "\u2ff4": "全包围",
    "\u2ff5": "上三包",
    "\u2ff6": "下三包",
    "\u2ff7": "左三包",
    "\u2ff8": "左上包",
    "\u2ff9": "右上包",
    "\u2ffa": "左下包",
    "\u2ffb": "镶嵌",
}


def load_unihan_irg(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        result.setdefault(parts[0], {})[parts[1]] = parts[2].strip()
    return result


def load_ids(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        ucp, _, rest = line.partition("\t")
        if re.fullmatch(r"U\+[0-9A-Fa-f]{4,6}", ucp):
            result[ucp] = rest
    return result


def load_radix_name_map(path: Path) -> dict[int, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[int, str] = {}
    for rec in data.get("records", []):
        code = rec.get("code")
        if code is not None and rec.get("status") in ("DIRECT", "ALIAS"):
            result.setdefault(code, rec.get("canonical_radical") or rec["radical"])
    return result


def infer_structure(ids_text: str | None) -> str | None:
    if not ids_text:
        return None
    first_op = next((ch for ch in ids_text if ch in IDS_STRUCT), None)
    if first_op:
        return IDS_STRUCT[first_op]
    return "独体字" if len(ids_text.strip()) <= 2 else None


def aggregate(
    entry: dict,
    unihan: dict[str, dict[str, str]],
    ids_map: dict[str, str],
    radix_name: dict[int, str],
) -> dict:
    ucp = entry["unicode"]
    row = unihan.get(ucp, {})
    krs = row.get("kRSUnicode", "")
    m = re.match(r"\d+", krs)
    radix_code = int(m.group(0)) if m else None
    strokes = int(row["kTotalStrokes"]) if row.get("kTotalStrokes", "").isdigit() else None
    ids_text = ids_map.get(ucp)
    structure = infer_structure(ids_text)
    return {
        "kRSUnicode": krs,
        "radix_code": radix_code,
        "radix_name": radix_name.get(radix_code) if radix_code is not None else None,
        "strokes": strokes,
        "ids": ids_text,
        "structure": structure,
    }


def deterministic_proposal(entry: dict, ev: dict, index: int) -> dict:
    issues = set(entry.get("standard_evidence", {}).get("issues", []))
    reasons = []
    confidence = 0.5
    if ev["radix_code"] is not None and ev["radix_name"]:
        confidence += 0.2
        reasons.append("radix: cross-reference kRSUnicode mapped")
    else:
        reasons.append("radix: missing usable cross-reference")
    if ev["strokes"] is not None:
        confidence += 0.1
        reasons.append("strokes: Unihan kTotalStrokes available")
    else:
        reasons.append("strokes: missing")
    structure = ev["structure"]
    if structure:
        confidence += 0.1
        reasons.append("structure: CHISE IDS inferred")
    else:
        std_structure = entry.get("standard_evidence", {}).get("structure")
        if std_structure in STRUCT_CODE:
            structure = std_structure
            confidence += 0.05
            reasons.append("structure: standard-evidence fallback (candidate only)")
        else:
            reasons.append("structure: missing")
    if "ambiguous_decomposition" in issues:
        confidence -= 0.15
        reasons.append("penalty: ambiguous decomposition")
    confidence = round(min(confidence, 0.95), 3)

    proposal = {
        "radix": ev["radix_code"],
        "radix_name": ev["radix_name"],
        "strokes": ev["strokes"],
        "struct_name": structure,
        "struct_type": STRUCT_CODE.get(structure) if structure else None,
        "index": index,
        "ext": 0,
        "track": "provisional",
        "confidence": confidence,
        "reasons": reasons,
        "evidence_grade": "cross_reference_unihan_ids",
    }
    if proposal["strokes"] is not None and proposal["strokes"] > 31:
        confidence -= 0.05
        reasons.append("boundary: stroke count exceeds CNBE32 5-bit field, needs CNBE64/extended")
        proposal["confidence"] = round(min(confidence, 0.95), 3)
    return proposal
