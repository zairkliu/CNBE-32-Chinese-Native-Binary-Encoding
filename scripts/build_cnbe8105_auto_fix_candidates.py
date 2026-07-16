#!/usr/bin/env python3
"""Build a read-only auto-fix candidate list from the 8105 comparison report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_cnbe8105_encoding_comparison import (
        ALLOWED_STRUCTURES,
        SPECIAL_STRUCTURE,
        build_outputs,
    )
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_cnbe8105_encoding_comparison import (
        ALLOWED_STRUCTURES,
        SPECIAL_STRUCTURE,
        build_outputs,
    )

DEFAULT_COMPARISON_INPUT = Path("evidence/8105/cnbe8105_encoding_comparison.json")
DEFAULT_CANDIDATE_OUTPUT = Path("evidence/8105/cnbe8105_auto_fix_candidates.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/8105/CNBE8105_AUTO_FIX_CANDIDATES.md")

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
SAMPLE_LIMIT = 30

STRUCTURE_TYPE_BY_NAME = {
    SPECIAL_STRUCTURE: 0,
    "上下": 1,
    "上中下": 2,
    "左右": 3,
    "左中右": 4,
    "左上包": 5,
    "右上包": 6,
    "左三包": 7,
    "左下包": 8,
    "上三包": 9,
    "下三包": 10,
    "全包围": 11,
    "镶嵌": 12,
}

AUTO_FIX_REQUIRED_ISSUES = {
    "radical_mismatch",
    "stroke_count_mismatch",
    "structure_mismatch",
}

EXCLUDED_STATUSES = {
    "PASS",
    "FAIL_REVIEW_REQUIRED",
    "EVIDENCE_GAP",
    "OUT_OF_SCOPE",
}

BLOCKED_FIELDS = {
    "cnbe": "CNBE 32-bit values are not recalculated in this read-only candidate phase.",
    "radix": "Numeric radical codes require a separately validated radical-code mapping table.",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def load_or_build_comparison(path: Path, research_root: Path) -> dict[str, Any]:
    if path.is_file():
        return load_json(path)
    _, _, comparison, _ = build_outputs(research_root)
    return comparison


def is_candidate(row: dict[str, Any]) -> bool:
    if row.get("status") != "FAIL_FIXABLE":
        return False
    issues = set(row.get("issues", []))
    if issues - AUTO_FIX_REQUIRED_ISSUES:
        return False
    standard = row.get("standard") or {}
    current = row.get("current") or {}
    if not current:
        return False
    if standard.get("evidence_status") != "COMPLETE":
        return False
    if standard.get("structure") not in STRUCTURE_TYPE_BY_NAME:
        return False
    if not standard.get("radical"):
        return False
    if not isinstance(standard.get("stroke_count"), int):
        return False
    if not standard.get("decomposition"):
        return False
    return True


def candidate_patch_fields(row: dict[str, Any]) -> dict[str, Any]:
    standard = row["standard"]
    return {
        "radix_name": standard["radical"],
        "strokes": standard["stroke_count"],
        "struct_name": standard["structure"],
        "struct_type": STRUCTURE_TYPE_BY_NAME[standard["structure"]],
        "decomposition": standard["decomposition"],
        "components": standard.get("components") or [],
    }


def candidate_record(row: dict[str, Any]) -> dict[str, Any]:
    current = row["current"]
    proposed = candidate_patch_fields(row)
    return {
        "char": row["char"],
        "unicode": row["unicode"],
        "standard_rank": row["standard_rank"],
        "status": "AUTO_FIX_CANDIDATE",
        "source_status": row["status"],
        "issues": row["issues"],
        "current": {
            "cnbe": current.get("cnbe"),
            "cnbe_hex": current.get("cnbe_hex"),
            "radix": current.get("radix"),
            "radix_name": current.get("radix_name"),
            "strokes": current.get("strokes"),
            "struct_type": current.get("struct_type"),
            "struct_name": current.get("struct_name"),
            "index": current.get("index"),
        },
        "proposed": proposed,
        "blocked_fields": BLOCKED_FIELDS,
        "apply_gate": "NO_APPLY_IN_THIS_PHASE",
        "review_note": "Candidate is safe for planning only; do not overwrite CNBE values until radical-code mapping and encoder regeneration are separately approved.",
    }


def exclusion_reason(row: dict[str, Any]) -> str:
    status = row.get("status")
    if status in EXCLUDED_STATUSES:
        return f"status_{status}"
    if row.get("status") != "FAIL_FIXABLE":
        return "not_fail_fixable"
    issues = set(row.get("issues", []))
    extra_issues = sorted(issues - AUTO_FIX_REQUIRED_ISSUES)
    if extra_issues:
        return "non_auto_fix_issue:" + ",".join(extra_issues)
    standard = row.get("standard") or {}
    if standard.get("evidence_status") != "COMPLETE":
        return "standard_evidence_not_complete"
    if standard.get("structure") not in STRUCTURE_TYPE_BY_NAME:
        return "unsupported_standard_structure"
    if not standard.get("radical"):
        return "missing_standard_radical"
    if not isinstance(standard.get("stroke_count"), int):
        return "missing_standard_stroke_count"
    if not standard.get("decomposition"):
        return "missing_decomposition"
    if not row.get("current"):
        return "missing_current_row"
    return "unknown"


def build_candidates(comparison: dict[str, Any]) -> dict[str, Any]:
    rows = comparison.get("characters", {})
    candidates = []
    exclusion_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    structure_counts: Counter[str] = Counter()
    radical_counts: Counter[str] = Counter()

    for row in sorted(rows.values(), key=lambda item: item["standard_rank"]):
        if is_candidate(row):
            record = candidate_record(row)
            candidates.append(record)
            issue_counts.update(record["issues"])
            structure_counts[record["proposed"]["struct_name"]] += 1
            radical_counts[record["proposed"]["radix_name"]] += 1
        else:
            exclusion_counts[exclusion_reason(row)] += 1

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "8105 auto-fix candidate design; no writes to source CNBE data",
            "candidate_rule": "source status must be FAIL_FIXABLE with only radical/stroke/structure mismatches and complete standard evidence",
            "allowed_structures": sorted(ALLOWED_STRUCTURES),
            "special_structure": SPECIAL_STRUCTURE,
            "blocked_fields": BLOCKED_FIELDS,
        },
        "summary": {
            "comparison_rows": len(rows),
            "candidate_rows": len(candidates),
            "excluded_rows": len(rows) - len(candidates),
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
            "candidate_issue_counts": dict(sorted(issue_counts.items())),
            "candidate_structure_counts": dict(sorted(structure_counts.items())),
            "top_candidate_radicals": dict(radical_counts.most_common(20)),
            "apply_gate": "NO_APPLY_IN_THIS_PHASE",
        },
        "samples": {
            "first_candidates": candidates[:SAMPLE_LIMIT],
            "known_samples": {
                record["char"]: record
                for record in candidates
                if record["char"] in {"家", "遛", "涡", "焱", "衍"}
            },
        },
        "candidates": candidates,
    }


def render_markdown_report(candidate_model: dict[str, Any]) -> str:
    summary = candidate_model["summary"]
    known_samples = candidate_model["samples"]["known_samples"]
    sample_rows = []
    for char in ["家", "遛", "涡", "焱", "衍"]:
        record = known_samples.get(char)
        if not record:
            continue
        sample_rows.append(
            [
                char,
                record["unicode"],
                record["current"]["radix_name"],
                record["proposed"]["radix_name"],
                record["current"]["strokes"],
                record["proposed"]["strokes"],
                record["current"]["struct_name"],
                record["proposed"]["struct_name"],
            ]
        )

    return "\n".join(
        [
            "# CNBE-32 8105 Auto-Fix Candidates",
            "",
            "## Scope",
            "",
            "This report designs a read-only auto-fix candidate pool from the 8105 comparison output.",
            "It does not rewrite `cnbe32_updated.json`, does not recalculate 32-bit CNBE values, and does not assign numeric radical codes.",
            "",
            "## Gate",
            "",
            f"- Comparison rows: {summary['comparison_rows']}",
            f"- Candidate rows: {summary['candidate_rows']}",
            f"- Excluded rows: {summary['excluded_rows']}",
            f"- Apply gate: {summary['apply_gate']}",
            "",
            "## Candidate Issue Counts",
            "",
            markdown_table(["Issue", "Rows"], [[key, value] for key, value in summary["candidate_issue_counts"].items()]),
            "",
            "## Candidate Structure Counts",
            "",
            markdown_table(
                ["Structure", "Rows"],
                [[key, value] for key, value in summary["candidate_structure_counts"].items()],
            ),
            "",
            "## Exclusion Counts",
            "",
            markdown_table(["Reason", "Rows"], [[key, value] for key, value in summary["exclusion_counts"].items()]),
            "",
            "## Known Candidate Samples",
            "",
            markdown_table(
                [
                    "Char",
                    "Unicode",
                    "Current Radical",
                    "Proposed Radical",
                    "Current Strokes",
                    "Proposed Strokes",
                    "Current Structure",
                    "Proposed Structure",
                ],
                sample_rows,
            ),
            "",
            "## Blocked Fields",
            "",
            "- `cnbe`: not recalculated in this phase.",
            "- `radix`: numeric radical codes require a separately validated radical-code mapping table.",
            "",
            "## Next Gate",
            "",
            "Before any write patch is allowed, build and validate a radical-code mapping table, then design a dry-run patch against a copy of the CNBE dataset.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-input", type=Path, default=DEFAULT_COMPARISON_INPUT)
    parser.add_argument("--research-root", type=Path, default=RESEARCH_ROOT)
    parser.add_argument("--candidate-output", type=Path, default=DEFAULT_CANDIDATE_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        comparison = load_or_build_comparison(args.comparison_input, args.research_root)
        candidate_model = build_candidates(comparison)
    except Exception as exc:  # pragma: no cover - command-line guard
        print(f"CNBE8105 AUTO-FIX CANDIDATES FAIL: {exc}", file=sys.stderr)
        return 1

    write_json(args.candidate_output, candidate_model)
    write_text(args.markdown_output, render_markdown_report(candidate_model))

    summary = candidate_model["summary"]
    print("CNBE8105 AUTO-FIX CANDIDATES PASS")
    print(f"Comparison rows: {summary['comparison_rows']}")
    print(f"Candidate rows: {summary['candidate_rows']}")
    print(f"Excluded rows: {summary['excluded_rows']}")
    print(f"Apply gate: {summary['apply_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
