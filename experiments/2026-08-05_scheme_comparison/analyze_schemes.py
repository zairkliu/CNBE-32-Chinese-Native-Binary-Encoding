#!/usr/bin/env python3
"""Objective comparison of CNBE-32, IDS, Four-Corner, and Cangjie on the 8105 scope.

Data inputs:
  - CNBE-32: runtime database (repo/data/cnbe32.db)
  - IDS: cjkvi/cjkvi-ids ids.txt (external, GPL, aggregate stats only)
  - Four-Corner / Cangjie / strokes / radical: Unicode Unihan tables

Wubi is documented qualitatively because no authoritative machine-readable table is
included in this repository.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

IDS_UCP = re.compile(r"U\+[0-9A-Fa-f]{4,6}")


def load_ids(path: Path) -> dict[str, str]:
    ids: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        ucp = parts[0].strip()
        if not IDS_UCP.fullmatch(ucp):
            continue
        # Last tab field is usually the IDS expression; fall back to scanning.
        candidate = parts[-1].strip()
        if candidate and any(ch in candidate for ch in "\u2ff0\u2ff1\u2ff2\u2ff3\u2ff4\u2ff5\u2ff6\u2ff7\u2ff8\u2ff9\u2ffa\u2ffb"):
            ids[ucp] = candidate
    return ids


def load_unihan_map(path: Path, field: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3 or parts[1] != field:
            continue
        result[parts[0]] = parts[2].strip()
    return result


def stats_for_codes(values: dict[str, str]) -> dict:
    distinct = set(values.values())
    collisions = sum(1 for _, count in Counter(values.values()).items() if count > 1)
    lengths = [len(v) for v in values.values()]
    avg_len = sum(lengths) / len(lengths) if lengths else 0.0
    return {
        "covered": len(values),
        "distinct_codes": len(distinct),
        "unique_ratio": round(len(distinct) / len(values), 4) if values else 0.0,
        "colliding_code_values": collisions,
        "avg_code_length": round(avg_len, 3),
        "min_code_length": min(lengths) if lengths else 0,
        "max_code_length": max(lengths) if lengths else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--unihan-irg", type=Path, required=True)
    parser.add_argument("--unihan-readings", type=Path, required=True)
    parser.add_argument("--unihan-dict-like", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    parser.add_argument("--report", type=Path, default=Path("REPORT.md"))
    args = parser.parse_args()

    scope = json.loads(args.scope.read_text(encoding="utf-8"))
    chars = list(scope["characters"].keys())
    allowed = set(scope["metadata"]["allowed_structures"])
    allowed.add("\u72ec\u4f53\u5b57")  # 独体字

    con = sqlite3.connect(str(args.db))
    con.row_factory = sqlite3.Row
    rows = {r["char"]: r for r in con.execute("SELECT * FROM cnbe32")}
    con.close()

    cnbe_codes = {c: rows[c]["cnbe"] for c in chars if c in rows}
    cnbe_stats = stats_for_codes({c: str(v) for c, v in cnbe_codes.items()})
    cnbe_stats["storage_bytes"] = len(chars) * 4
    cnbe_stats["display_length"] = "32-bit fixed (4 bytes)"
    cnbe_stats["standard_track"] = sum(1 for c in chars if c in rows and rows[c]["track"] == "standard")
    cnbe_stats["legacy_track"] = sum(1 for c in chars if c in rows and rows[c]["track"] == "legacy")
    cnbe_stats["invalid_structure"] = sum(
        1 for c in chars if c in rows and rows[c]["struct_name"] not in allowed
    )

    ids_map = load_ids(args.ids)
    ids_by_char = {}
    for c in chars:
        ucp = f"U+{ord(c):04X}"
        if ucp in ids_map:
            ids_by_char[c] = ids_map[ucp]
    ids_stats = stats_for_codes(ids_by_char)
    ids_stats["storage_bytes"] = sum(len(v.encode("utf-8")) for v in ids_by_char.values())
    ids_stats["with_unknown_component"] = sum(1 for v in ids_by_char.values() if "\u003f" in v)

    four_corner = load_unihan_map(args.unihan_dict_like, "kFourCornerCode")
    cangjie = load_unihan_map(args.unihan_dict_like, "kCangjie")
    krs = load_unihan_map(args.unihan_irg, "kRSUnicode")
    kst = load_unihan_map(args.unihan_irg, "kTotalStrokes")

    four_by_char = {}
    for c in chars:
        ucp = f"U+{ord(c):04X}"
        code = four_corner.get(ucp)
        if code:
            four_by_char[c] = code
    four_stats = stats_for_codes(four_by_char)
    four_stats["storage_bytes"] = sum(len(v.encode("ascii")) for v in four_by_char.values())

    cangjie_by_char = {}
    for c in chars:
        ucp = f"U+{ord(c):04X}"
        code = cangjie.get(ucp)
        if code:
            # kCangjie can contain multiple forms separated by spaces; use first.
            cangjie_by_char[c] = code.split()[0]
    cangjie_stats = stats_for_codes(cangjie_by_char)
    cangjie_stats["storage_bytes"] = sum(len(v.encode("ascii")) for v in cangjie_by_char.values())

    unihan_coverage = {
        "kRSUnicode": sum(1 for c in chars if f"U+{ord(c):04X}" in krs),
        "kTotalStrokes": sum(1 for c in chars if f"U+{ord(c):04X}" in kst),
    }

    wubi = {
        "covered": None,
        "note": "No authoritative machine-readable Wubi table is bundled; metrics are documented qualitatively.",
        "code_length_rule": "1-4 letters, optional fifth letter for phrases; single chars usually 1-4.",
    }

    result = {
        "schema_version": 1,
        "scope": "8105 national-standard common Chinese characters",
        "scope_size": len(chars),
        "cnbe32": cnbe_stats,
        "ids": ids_stats,
        "four_corner": four_stats,
        "cangjie": cangjie_stats,
        "unihan_coverage": unihan_coverage,
        "wubi": wubi,
        "boundary_notes": [
            "IDS data is from cjkvi/cjkvi-ids; aggregate statistics only, no source file is shipped.",
            "Four-Corner and Cangjie are read from Unicode Unihan fields kFourCornerCode and kCangjie.",
            "Wubi is not measured because no authoritative machine-readable table is available here.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# CNBE-32 vs IDS / Four-Corner / Cangjie: Objective Comparison (8105 scope)",
        "",
        f"Scope: {len(chars)} characters from the national-standard 8105 table. "
        "All measured numbers are produced by `analyze_schemes.py`; see `results.json` for raw data.",
        "",
        "## 1. Coverage and code statistics",
        "",
        "| Scheme | Covered | Distinct codes | Unique ratio | Colliding code values | Avg length | Storage bytes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, stats in [
        ("CNBE-32", cnbe_stats),
        ("IDS", ids_stats),
        ("Four-Corner", four_stats),
        ("Cangjie", cangjie_stats),
    ]:
        display_length = stats.get("display_length", f"{stats['avg_code_length']:.2f}")
        report.append(
            f"| {name} | {stats['covered']} | {stats['distinct_codes']} | "
            f"{stats['unique_ratio']:.4f} | {stats['colliding_code_values']} | "
            f"{display_length} | {stats['storage_bytes']} |"
        )

    report += [
        "",
        "| Scheme | Fixed width | Bit-level compute | Standard status | Primary use |",
        "|---|---|---|---|---|",
        "| CNBE-32 | Yes, 32-bit | Yes, direct field extraction | GF alignment in progress | Structural computing layer |",
        "| IDS | No, variable | No, text parsing | Part of Unicode standard | Describing character composition |",
        "| Four-Corner | Yes, 5 digits | No, lookup table | Unofficial | Input/retrieval |",
        "| Cangjie | No, 1-5 letters | No, lookup table | Unofficial | Input method |",
        "| Wubi | No, 1-4 letters | No, lookup table | Unofficial | Input method |",
        "",
        "## 2. CNBE-32 field statistics",
        "",
        f"- Standard track rows in scope: {cnbe_stats['standard_track']}",
        f"- Legacy track rows in scope: {cnbe_stats['legacy_track']}",
        f"- Rows whose structure label is outside the 13 GF 0017 labels: {cnbe_stats['invalid_structure']}",
        f"- Storage at 4 bytes per char: {cnbe_stats['storage_bytes']} bytes for {len(chars)} chars",
        "",
        "## 3. Boundary statements",
        "",
    ]
    for note in result["boundary_notes"]:
        report.append(f"- {note}")
    report += [
        "",
        "Wubi: code length is fixed by its rule (1-4 letters), but an authoritative machine-readable "
        "mapping for all 8105 chars is not bundled, so no measured collision or storage number is reported.",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
