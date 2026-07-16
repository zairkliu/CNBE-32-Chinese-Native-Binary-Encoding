#!/usr/bin/env python3
"""Reconstruct and audit the full catalog's radical-based structure rule."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from build_full_catalog_db import workbook_records
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.build_full_catalog_db import workbook_records

EXPECTED_ROWS = 97_686
DEFAULT_OUTPUT = Path("reports/full_catalog_structure_audit.json")

STRUCTURE_NAMES = {
    0: "独体结构",
    1: "左右结构",
    3: "上下结构",
    5: "左上包围",
    6: "右上包围",
    7: "左下包围",
    8: "上三包围",
    9: "下三包围",
    10: "全包围",
}

# These sets are preserved in the earlier 8,105-character generator. The full
# catalog applies SPECIAL_RADICAL_STRUCTURES first, then these two sets, then
# defaults to left-right structure.
LEFT_RADICALS = {
    9, 38, 60, 61, 62, 63, 64, 66, 69, 72, 73, 74, 75, 76, 77, 78, 79,
    80, 81, 83, 84, 85, 86, 87, 88, 91, 93, 94, 96, 100, 102, 104, 106,
    107, 109, 110, 112, 113, 114, 115, 117, 118, 120, 121, 124, 126, 130,
    134, 136, 137, 139, 140, 141, 142, 144, 145, 146, 147, 148, 149, 150,
    151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164,
    165, 166, 167, 168, 169, 170, 171, 173, 174, 175, 176, 177, 178, 180,
    181, 182, 183, 184, 185, 187, 188, 189, 190, 191, 192, 193, 194, 195,
    196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209,
    210, 211, 212, 213, 214,
}

TOP_RADICALS = {
    1, 3, 7, 8, 14, 19, 20, 24, 25, 26, 27, 30, 31, 32, 34, 35, 36,
    37, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56,
    57, 58, 59, 65, 67, 68, 70, 71, 82, 89, 90, 92, 95, 97, 98, 99, 101,
    103, 105, 108, 111, 116, 119, 122, 123, 125, 127, 128, 129, 131, 132,
    133, 135, 138, 143, 172, 179, 186,
}

# Historical design documentation describes exactly 19 radical overrides.
# Their membership also follows the radical examples named in that document.
SPECIAL_RADICAL_STRUCTURES = {
    1: 0,   # 一
    2: 0,   # 丨
    3: 0,   # 丶
    4: 0,   # 丿
    5: 0,   # 乙
    6: 0,   # 亅
    13: 8,  # 冂
    20: 5,  # 勹
    22: 9,  # 匚
    27: 5,  # 厂
    31: 10, # 囗
    44: 5,  # 尸
    53: 5,  # 广
    54: 7,  # 廴
    56: 5,  # 弋
    62: 6,  # 戈
    84: 5,  # 气
    162: 7, # 辶
    169: 8, # 门
}


def classify_structure(radical: int) -> int:
    """Return the historical full-catalog structure class for a radical."""
    if radical not in range(1, 215):
        raise ValueError(f"radical must be in 1..214, got {radical}")
    if radical in SPECIAL_RADICAL_STRUCTURES:
        return SPECIAL_RADICAL_STRUCTURES[radical]
    if radical in LEFT_RADICALS:
        return 1
    if radical in TOP_RADICALS:
        return 3
    return 1


def audit_records(records: Iterable[tuple[Any, ...]]) -> dict[str, Any]:
    """Compare reconstructed structures with normalized workbook records."""
    rows = list(records)
    mismatch_samples: list[dict[str, Any]] = []
    structure_mismatches = 0
    name_mismatches = 0
    observed_by_radical: dict[int, set[int]] = defaultdict(set)
    expected_distribution: Counter[int] = Counter()
    actual_distribution: Counter[int] = Counter()

    for row in rows:
        codepoint, char = int(row[0]), str(row[1])
        radical, actual_structure = int(row[3]), int(row[5])
        actual_name = str(row[6])
        expected_structure = classify_structure(radical)
        expected_name = STRUCTURE_NAMES[expected_structure]
        observed_by_radical[radical].add(actual_structure)
        expected_distribution[expected_structure] += 1
        actual_distribution[actual_structure] += 1
        structure_differs = actual_structure != expected_structure
        name_differs = actual_name != expected_name
        structure_mismatches += structure_differs
        name_mismatches += name_differs
        if (structure_differs or name_differs) and len(mismatch_samples) < 20:
            mismatch_samples.append(
                {
                    "unicode": f"U+{codepoint:04X}",
                    "char": char,
                    "radical": radical,
                    "actual_structure": actual_structure,
                    "expected_structure": expected_structure,
                    "actual_name": actual_name,
                    "expected_name": expected_name,
                }
            )

    conflicting_radicals = {
        str(radical): sorted(values)
        for radical, values in observed_by_radical.items()
        if len(values) != 1
    }
    return {
        "row_count": len(rows),
        "radicals_observed": len(observed_by_radical),
        "special_override_count": len(SPECIAL_RADICAL_STRUCTURES),
        "structure_code_mismatches": structure_mismatches,
        "structure_name_mismatches": name_mismatches,
        "radicals_with_multiple_observed_structures": conflicting_radicals,
        "expected_distribution": {
            str(key): expected_distribution[key] for key in sorted(expected_distribution)
        },
        "actual_distribution": {
            str(key): actual_distribution[key] for key in sorted(actual_distribution)
        },
        "mismatch_samples": mismatch_samples,
    }


def build_report(source: Path) -> dict[str, Any]:
    audit = audit_records(workbook_records(source))
    passed = (
        audit["row_count"] == EXPECTED_ROWS
        and audit["radicals_observed"] == 214
        and audit["special_override_count"] == 19
        and audit["structure_code_mismatches"] == 0
        and audit["structure_name_mismatches"] == 0
        and not audit["radicals_with_multiple_observed_structures"]
    )
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": source.name,
        "status": "PASS" if passed else "FAIL",
        "rule_order": [
            "19 explicit radical overrides",
            "LEFT_RADICALS maps to left-right",
            "TOP_RADICALS maps to top-bottom",
            "default maps to left-right",
        ],
        "evidence_boundary": (
            "A zero-difference result establishes historical algorithm reproducibility. "
            "It does not establish that radical-only structure labels are linguistically authoritative."
        ),
        "audit": audit,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the 97,686-row catalog workbook")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    try:
        report = build_report(source)
    except (OSError, ValueError) as exc:
        print(f"FULL CATALOG STRUCTURE AUDIT ERROR: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"FULL CATALOG STRUCTURE AUDIT {report['status']}: {output}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
