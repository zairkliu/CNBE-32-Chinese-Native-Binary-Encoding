#!/usr/bin/env python3
"""Advance the remaining 8105 legacy-track rows to a reviewable completion packet.

Read-only by design: this script never writes `data/cnbe32.db`. It joins the 8105
standard baseline, the current runtime database, and the first-pass encoding
comparison evidence, then emits a candidate packet with per-row next actions.

Usage:
    PYTHONPATH=repo/src python3 scripts/advance_8105_remaining.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import sqlite3  # noqa: E402

from cnbe32 import decode_cnbe, encode_cnbe  # noqa: E402

STRUCT_ORDER = [
    "\u72ec\u4f53\u5b57",  # 独体字
    "\u4e0a\u4e0b",        # 上下
    "\u4e0a\u4e2d\u4e0b",  # 上中下
    "\u5de6\u53f3",        # 左右
    "\u5de6\u4e2d\u53f3",  # 左中右
    "\u5de6\u4e0a\u5305",  # 左上包
    "\u53f3\u4e0a\u5305",  # 右上包
    "\u5de6\u4e09\u5305",  # 左三包
    "\u5de6\u4e0b\u5305",  # 左下包
    "\u4e0a\u4e09\u5305",  # 上三包
    "\u4e0b\u4e09\u5305",  # 下三包
    "\u5168\u5305\u56f4",  # 全包围
    "\u9576\u5d4c",        # 镶嵌
]
STRUCT_CODE = {name: i for i, name in enumerate(STRUCT_ORDER)}


def load_radix_map(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for rec in data.get("records", []):
        result[rec["radical"]] = {
            "code": rec.get("code"),
            "canonical_radical": rec.get("canonical_radical"),
            "status": rec.get("status"),
            "reason": rec.get("reason"),
        }
    return result


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unihan-irg", type=Path, default=None)
    args = parser.parse_args()

    scope_path = REPO / "evidence" / "8105" / "cnbe8105_standard_baseline.json"
    comparison_path = REPO / "evidence" / "8105" / "cnbe8105_encoding_comparison.json"
    radix_map_path = REPO / "evidence" / "8105" / "cnbe8105_radical_code_map.json"
    out_packet = REPO / "evidence" / "8105" / "8105_REMAINING_503_COMPLETION_PACKET.json"
    out_report = REPO / "reports" / "8105_REMAINING_503_PROGRESS.md"

    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    radix_map = load_radix_map(radix_map_path)
    unihan = load_unihan_irg(args.unihan_irg) if args.unihan_irg else {}
    chars = scope["characters"]

    code_to_name: dict[int, str] = {}
    for name, rec in radix_map.items():
        if rec.get("code") is not None and rec.get("status") in ("DIRECT", "ALIAS"):
            code_to_name.setdefault(rec["code"], rec.get("canonical_radical") or name)

    con = sqlite3.connect(str(REPO / "data" / "cnbe32.db"))
    con.row_factory = sqlite3.Row
    rows = {r["char"]: r for r in con.execute("SELECT * FROM cnbe32")}
    con.close()

    allowed = set(scope["metadata"]["allowed_structures"])
    allowed.add("\u72ec\u4f53\u5b57")

    legacy = []
    missing = []
    for c in chars:
        r = rows.get(c)
        if r is None:
            missing.append(c)
            continue
        if r["track"] != "legacy":
            continue
        legacy.append((c, r))

    comparison_chars = comparison["characters"]
    packet_entries = []
    status_counter = Counter()
    unresolved_radix = Counter()

    for c, current in legacy:
        std = comparison_chars.get(c, {}).get("standard", {})
        issues = comparison_chars.get(c, {}).get("issues", [])
        ucp = f"U+{ord(c):04X}"
        radical_name = std.get("radical")
        strokes = std.get("stroke_count")
        structure = std.get("structure")
        decomposition = std.get("decomposition")
        evidence_status = std.get("evidence_status", "REVIEW_REQUIRED")
        baseline_entry = chars.get(c, {})

        cross = {}
        if unihan:
            unihan_row = unihan.get(ucp, {})
            krs = unihan_row.get("kRSUnicode")
            kst = unihan_row.get("kTotalStrokes")
            if krs:
                match = re.match(r"\d+", krs)
                cross["kRSUnicode"] = krs
                if match:
                    code = int(match.group(0))
                    cross["krs_radical_code"] = code
                    cross["krs_radical_name"] = code_to_name.get(code)
            if kst:
                cross["kTotalStrokes"] = kst
            if baseline_entry.get("cjk_decomp"):
                cross["cjk_decomp"] = baseline_entry["cjk_decomp"]
                cross["cjk_decomp_operator"] = baseline_entry["cjk_decomp"][0] if baseline_entry["cjk_decomp"] else None

        radix_rec = radix_map.get(radical_name) if radical_name else None
        radix_code = radix_rec.get("code") if radix_rec else None
        struct_code = STRUCT_CODE.get(structure) if structure else None

        has_unknown = decomposition is not None and "\u003f" in decomposition
        auto_ok = (
            radical_name is not None
            and radix_code is not None
            and strokes is not None
            and structure is not None
            and struct_code is not None
            and not has_unknown
            and "ambiguous_decomposition" not in issues
        )

        proposed = None
        roundtrip = None
        if auto_ok:
            code = encode_cnbe(radix_code, int(strokes), struct_code, int(current["idx"]), 0)
            decoded = decode_cnbe(code)
            roundtrip = {
                "pass": decoded["radix"] == radix_code
                and decoded["stroke"] == int(strokes)
                and decoded["struct"] == struct_code
                and decoded["index"] == int(current["idx"]),
                "decoded": decoded,
            }
            proposed = {
                "radix": radix_code,
                "radix_name": radical_name,
                "canonical_radical": radix_rec.get("canonical_radical"),
                "strokes": int(strokes),
                "struct_name": structure,
                "struct_type": struct_code,
                "index": int(current["idx"]),
                "ext": 0,
                "cnbe": code.code,
                "cnbe_hex": hex(code.code),
                "roundtrip": roundtrip,
            }
            action = "AUTO_CANDIDATE"
        else:
            action = "REVIEW_REQUIRED"
            if radical_name and radix_code is None:
                unresolved_radix[radical_name] += 1

        status_counter[action] += 1
        packet_entries.append(
            {
                "char": c,
                "unicode": ucp,
                "codepoint": ord(c),
                "standard_rank": std.get("standard_rank") or comparison_chars.get(c, {}).get("standard_rank"),
                "current": {
                    "cnbe": current["cnbe"],
                    "radix": current["radix"],
                    "radix_name": current["radix_name"],
                    "strokes": current["strokes"],
                    "struct_name": current["struct_name"],
                    "struct_type": current["struct_type"],
                    "track": current["track"],
                },
                "standard_evidence": {
                    "radical": radical_name,
                    "stroke_count": strokes,
                    "structure": structure,
                    "decomposition": decomposition,
                    "evidence_status": evidence_status,
                    "issues": issues,
                },
                "cross_reference": cross,
                "action": action,
                "proposed": proposed,
            }
        )

    summary = {
        "scope_8105_total": len(chars),
        "runtime_rows_8105": len(chars) - len(missing),
        "missing_from_runtime": len(missing),
        "legacy_rows_remaining": len(legacy),
        "action_counts": dict(status_counter),
        "unresolved_radix_names": len(unresolved_radix),
        "cross_reference_available": sum(1 for e in packet_entries if e["cross_reference"]),
        "cross_reference_radix_available": sum(1 for e in packet_entries if e["cross_reference"].get("krs_radical_code") is not None),
        "cross_reference_strokes_available": sum(1 for e in packet_entries if e["cross_reference"].get("kTotalStrokes") is not None),
        "cross_reference_decomp_available": sum(1 for e in packet_entries if e["cross_reference"].get("cjk_decomp")),
        "write_gate": "NO_WRITE_TO_RELEASE_DB",
    }
    packet = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "summary": summary,
        "entries": packet_entries,
    }
    out_packet.parent.mkdir(parents=True, exist_ok=True)
    out_packet.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 8105 Remaining Rows Progress Report",
        "",
        f"Date: 2026-08-05",
        "",
        "## Current state",
        "",
        f"- 8105 scope: {len(chars)} chars; runtime rows: {len(chars) - len(missing)}; missing: {len(missing)}",
        f"- Standard-track rows: {len(chars) - len(legacy) - len(missing)}",
        f"- Remaining legacy-track rows: {len(legacy)}",
        "",
        "## Completion packet",
        "",
        f"- Path: `evidence/8105/8105_REMAINING_503_COMPLETION_PACKET.json`",
        f"- Actions: {dict(status_counter)}",
        f"- Unresolved radical names (no code in current radical map): {len(unresolved_radix)}",
        f"- Rows with cross-reference evidence (Unihan radical/strokes or cjk_decomp): "
        f"{summary['cross_reference_available']}",
        f"- Rows with cross-reference radical code: {summary['cross_reference_radix_available']}",
        f"- Rows with cross-reference total strokes: {summary['cross_reference_strokes_available']}",
        f"- Rows with cjk_decomp: {summary['cross_reference_decomp_available']}",
        "",
        "## Policy",
        "",
        "- This run is read-only. No release database row is written.",
        "- `AUTO_CANDIDATE` rows carry a verified roundtrip (encode/decode) and still require governance approval before apply.",
        "- `REVIEW_REQUIRED` rows need expert adjudication (decomposition ambiguity or missing standard evidence).",
        "",
        "## Reproduce",
        "",
        "```bash",
        "PYTHONPATH=repo/src python3 scripts/advance_8105_remaining.py \\",
        "    --unihan-irg experiments/2026-08-05_scheme_comparison/build/Unihan_IRGSources.txt",
        "```",
    ]
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
