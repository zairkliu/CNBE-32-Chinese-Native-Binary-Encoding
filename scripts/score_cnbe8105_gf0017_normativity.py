#!/usr/bin/env python3
"""Score current CNBE 8105 rows against the GF0017 50-point normativity model.

The script is read-only with respect to CNBE source data. It reads the existing
8105 comparison report and the GF0017 scoring model, then writes report files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_cnbe8105_encoding_comparison import RESEARCH_ROOT, build_outputs
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_cnbe8105_encoding_comparison import RESEARCH_ROOT, build_outputs

DEFAULT_MODEL_INPUT = Path("evidence/gf0017/gf0017_cnbe50_scoring_model.json")
DEFAULT_COMPARISON_INPUT = Path("evidence/8105/cnbe8105_encoding_comparison.json")
DEFAULT_SCORE_OUTPUT = Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md")

SAMPLE_CHARS = ["一", "家", "遛", "涡", "亾", "焱", "与", "衍", "鼻"]
SAMPLE_LIMIT = 25

SOURCE_GAP_ITEM_IDS = {
    "character_set_coverage",
    "stroke_shape",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_or_build_comparison(path: Path, research_root: Path) -> dict[str, Any]:
    if path.is_file():
        return load_json(path)
    _, _, comparison, _ = build_outputs(research_root)
    return comparison


def issue_count(row: dict[str, Any], issues: list[str]) -> int:
    row_issues = set(row.get("issues", []))
    return sum(1 for issue in issues if issue in row_issues)


def is_missing_current(row: dict[str, Any]) -> bool:
    return row.get("current") is None or "missing_from_current_cnbe" in row.get("issues", [])


def has_complete_standard(row: dict[str, Any]) -> bool:
    standard = row.get("standard") or {}
    return standard.get("evidence_status") == "COMPLETE"


def normalized_standard(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("standard") or {}


def normalized_current(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("current") or {}


def item_score(max_points: int, deduction_units: int) -> int:
    return max(0, max_points - min(max_points, deduction_units))


def item_status(
    *,
    score: int,
    max_points: int,
    source_gap: bool = False,
    evidence_gap: bool = False,
    review_required: bool = False,
) -> str:
    if evidence_gap:
        return "EVIDENCE_GAP"
    if source_gap:
        return "SOURCE_GAP"
    if review_required:
        return "REVIEW_REQUIRED"
    if score == max_points:
        return "PASS"
    if score == 0:
        return "FAIL"
    return "PARTIAL"


def score_character(row: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    standard = normalized_standard(row)
    current = normalized_current(row)
    issues = set(row.get("issues", []))
    field_results = row.get("field_results") or {}
    missing_current = is_missing_current(row)

    components = standard.get("components")
    decomposition = standard.get("decomposition")
    structure = standard.get("structure")
    current_structure = current.get("struct_name")
    evidence_status = standard.get("evidence_status")
    decomposition_ambiguous = "ambiguous_decomposition" in issues
    missing_decomposition = "missing_decomposition" in issues or decomposition is None

    item_rows: dict[str, dict[str, Any]] = {}

    def add(
        item_id: str,
        max_points: int,
        deductions: list[str],
        deduction_units: int | None = None,
        source_gap: bool = False,
        evidence_gap: bool = False,
        review_required: bool = False,
        notes: list[str] | None = None,
    ) -> None:
        units = issue_count(row, deductions) if deduction_units is None else deduction_units
        score = item_score(max_points, units)
        item_rows[item_id] = {
            "max_points": max_points,
            "score": score,
            "deducted": max_points - score,
            "status": item_status(
                score=score,
                max_points=max_points,
                source_gap=source_gap,
                evidence_gap=evidence_gap,
                review_required=review_required,
            ),
            "deduction_units": units,
            "deduction_reasons": sorted(issue for issue in deductions if issue in issues),
            "notes": notes or [],
        }

    add(
        "character_set_coverage",
        3,
        ["missing_from_current_cnbe", "unicode_mismatch", "out_of_scope"],
        source_gap=True,
        review_required=missing_current,
        notes=["GF0017 names GB2312 and 现代汉语通用字表; standalone local source files remain unresolved."],
    )

    add(
        "stroke_shape",
        3,
        ["stroke_count_mismatch"],
        source_gap=True,
        notes=["CNBE32 exposes stroke count; full stroke-shape classification is retained as an extended-evidence requirement."],
    )

    add(
        "stroke_order",
        3,
        ["stroke_count_mismatch", "missing_standard_stroke_count"],
        evidence_gap=standard.get("stroke_count") is None,
        notes=["Current CNBE comparison can verify stroke count; full stroke order is preserved outside CNBE32."],
    )

    component_evidence_gap = components is None and not decomposition
    add(
        "component_validity",
        3,
        ["ambiguous_decomposition", "missing_decomposition", "missing_standard_components", "invalid_component"],
        evidence_gap=component_evidence_gap,
        review_required=decomposition_ambiguous,
        notes=["Component repair is blocked unless GF0014/GF3001-derived evidence is complete."],
    )

    component_name_evidence_gap = components is None
    component_name_units = 0
    component_name_reasons: list[str] = []
    if component_name_evidence_gap:
        component_name_units = 8
        component_name_reasons.append("missing_component_name_evidence")
    elif decomposition_ambiguous:
        component_name_units = 1
        component_name_reasons.append("ambiguous_decomposition")
    component_name_score = item_score(8, component_name_units)
    item_rows["component_name_validity"] = {
        "max_points": 8,
        "score": component_name_score,
        "deducted": 8 - component_name_score,
        "status": item_status(
            score=component_name_score,
            max_points=8,
            evidence_gap=component_name_evidence_gap,
            review_required=decomposition_ambiguous,
        ),
        "deduction_units": component_name_units,
        "deduction_reasons": component_name_reasons,
        "notes": ["GF0014 component names must be retained in reports even if CNBE32 stores compact codes."],
    }

    add(
        "radical_validity",
        3,
        ["radical_mismatch", "missing_standard_radical"],
        evidence_gap=standard.get("radical") is None,
    )

    independent_violation = (
        structure == "独体字"
        and bool(decomposition)
        and isinstance(components, list)
        and len(components) > 1
    )
    independent_structure_mismatch = (
        (structure == "独体字" or current_structure == "独体字")
        and field_results.get("structure", {}).get("pass") is False
    )
    independent_units = 0
    independent_reasons: list[str] = []
    if independent_violation:
        independent_units += 1
        independent_reasons.append("independent_character_non_stroke_split")
    if independent_structure_mismatch:
        independent_units += 1
        independent_reasons.append("structure_mismatch_involving_independent_character")
    item_rows["independent_character_rule"] = {
        "max_points": 7,
        "score": item_score(7, independent_units),
        "deducted": 7 - item_score(7, independent_units),
        "status": item_status(
            score=item_score(7, independent_units),
            max_points=7,
            evidence_gap=structure is None,
            review_required=independent_violation,
        ),
        "deduction_units": independent_units,
        "deduction_reasons": independent_reasons,
        "notes": ["If a character is standard-confirmed as 独体字, it may only be split into strokes."],
    }

    add(
        "structure_first_decomposition",
        20,
        [
            "structure_mismatch",
            "invalid_standard_structure",
            "invalid_current_structure",
            "missing_standard_structure",
            "ambiguous_decomposition",
            "missing_decomposition",
        ],
        evidence_gap=structure is None,
        review_required=decomposition_ambiguous or missing_decomposition,
        notes=["This 20-point item is the main repair target and must start from standard structure."],
    )

    total_score = sum(item["score"] for item in item_rows.values())
    item_status_counts = Counter(item["status"] for item in item_rows.values())
    has_source_gap = bool(item_status_counts.get("SOURCE_GAP"))
    has_evidence_gap = bool(item_status_counts.get("EVIDENCE_GAP"))
    has_review_required = bool(item_status_counts.get("REVIEW_REQUIRED"))
    has_fail = bool(item_status_counts.get("FAIL"))
    if has_evidence_gap:
        overall_status = "EVIDENCE_GAP"
    elif has_review_required:
        overall_status = "REVIEW_REQUIRED"
    elif has_fail:
        overall_status = "FAIL"
    elif total_score == model["total_points"] and not has_source_gap:
        overall_status = "PASS"
    elif total_score == model["total_points"] and has_source_gap:
        overall_status = "PROVISIONAL_PASS_SOURCE_GAP"
    else:
        overall_status = "PARTIAL"

    return {
        "char": row["char"],
        "unicode": row["unicode"],
        "standard_rank": row["standard_rank"],
        "comparison_status": row.get("status"),
        "overall_status": overall_status,
        "score": total_score,
        "max_score": model["total_points"],
        "score_percent": round(total_score / model["total_points"] * 100, 2),
        "issues": sorted(issues),
        "item_status_counts": dict(sorted(item_status_counts.items())),
        "items": item_rows,
        "repair_class": classify_repair(row, item_rows),
        "standard_snapshot": {
            "radical": standard.get("radical"),
            "stroke_count": standard.get("stroke_count"),
            "structure": standard.get("structure"),
            "decomposition": standard.get("decomposition"),
            "components": standard.get("components"),
            "evidence_status": evidence_status,
        },
        "current_snapshot": {
            "radix_name": current.get("radix_name"),
            "strokes": current.get("strokes"),
            "struct_name": current.get("struct_name"),
            "cnbe_hex": current.get("cnbe_hex"),
        },
    }


def classify_repair(row: dict[str, Any], items: dict[str, dict[str, Any]]) -> str:
    issues = set(row.get("issues", []))
    if "missing_from_current_cnbe" in issues:
        return "ADD_OR_EXCLUDE_CHARACTER"
    if any(item["status"] == "EVIDENCE_GAP" for item in items.values()):
        return "COMPLETE_STANDARD_EVIDENCE_FIRST"
    if any(item["status"] == "REVIEW_REQUIRED" for item in items.values()):
        return "HUMAN_REVIEW_REQUIRED"
    fixable = {"radical_mismatch", "stroke_count_mismatch", "structure_mismatch"}
    if issues and issues <= fixable:
        return "CNBE32_FIELD_REPAIR_CANDIDATE"
    if issues:
        return "MIXED_REPAIR_REVIEW"
    return "NO_REPAIR_REQUIRED"


def build_scores(model: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    characters = comparison.get("characters", {})
    scored = {
        char: score_character(row, model)
        for char, row in sorted(characters.items(), key=lambda item: item[1]["standard_rank"])
    }
    score_distribution: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    repair_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    item_status_counts: dict[str, Counter[str]] = {
        item["id"]: Counter()
        for item in model["score_items"]
    }
    item_average_scores: dict[str, float] = {}

    for row in scored.values():
        bucket = f"{(row['score'] // 5) * 5:02d}-{min(50, (row['score'] // 5) * 5 + 4):02d}"
        if row["score"] == 50:
            bucket = "50"
        score_distribution[bucket] += 1
        status_counts[row["overall_status"]] += 1
        repair_counts[row["repair_class"]] += 1
        issue_counts.update(row["issues"])
        for item_id, item in row["items"].items():
            item_status_counts[item_id][item["status"]] += 1

    for item in model["score_items"]:
        item_id = item["id"]
        total = sum(row["items"][item_id]["score"] for row in scored.values())
        item_average_scores[item_id] = round(total / max(1, len(scored)), 4)

    samples = {char: scored[char] for char in SAMPLE_CHARS if char in scored}
    lowest = sorted(scored.values(), key=lambda row: (row["score"], row["standard_rank"]))[:SAMPLE_LIMIT]
    review_required = [
        row for row in scored.values()
        if row["overall_status"] in {"REVIEW_REQUIRED", "EVIDENCE_GAP"}
    ][:SAMPLE_LIMIT]
    fix_candidates = [
        row for row in scored.values()
        if row["repair_class"] == "CNBE32_FIELD_REPAIR_CANDIDATE"
    ][:SAMPLE_LIMIT]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_id": model["model_id"],
            "model_total_points": model["total_points"],
            "scope": "8105 character-by-character GF0017 normativity scoring",
            "read_only": True,
            "source_gap_item_ids": sorted(SOURCE_GAP_ITEM_IDS),
        },
        "summary": {
            "row_count": len(scored),
            "average_score": round(sum(row["score"] for row in scored.values()) / max(1, len(scored)), 4),
            "min_score": min((row["score"] for row in scored.values()), default=None),
            "max_score": max((row["score"] for row in scored.values()), default=None),
            "overall_status_counts": dict(sorted(status_counts.items())),
            "repair_class_counts": dict(sorted(repair_counts.items())),
            "score_distribution": dict(sorted(score_distribution.items())),
            "issue_counts": dict(sorted(issue_counts.items())),
            "item_average_scores": item_average_scores,
            "item_status_counts": {
                item_id: dict(sorted(counter.items()))
                for item_id, counter in item_status_counts.items()
            },
        },
        "samples": {
            "known_characters": samples,
            "lowest_score_rows": lowest,
            "review_required_rows": review_required,
            "cnbe32_field_repair_candidates": fix_candidates,
        },
        "characters": scored,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(scores: dict[str, Any]) -> str:
    summary = scores["summary"]
    status_rows = [[key, value] for key, value in summary["overall_status_counts"].items()]
    repair_rows = [[key, value] for key, value in summary["repair_class_counts"].items()]
    item_rows = [
        [
            item_id,
            summary["item_average_scores"][item_id],
            ", ".join(f"{k}:{v}" for k, v in summary["item_status_counts"][item_id].items()),
        ]
        for item_id in summary["item_average_scores"]
    ]
    sample_rows = []
    for char, row in scores["samples"]["known_characters"].items():
        sample_rows.append(
            [
                char,
                row["unicode"],
                row["score"],
                row["overall_status"],
                row["repair_class"],
                ", ".join(row["issues"]) or "none",
                row["standard_snapshot"]["radical"],
                row["current_snapshot"]["radix_name"],
                row["standard_snapshot"]["stroke_count"],
                row["current_snapshot"]["strokes"],
                row["standard_snapshot"]["structure"],
                row["current_snapshot"]["struct_name"],
            ]
        )
    lowest_rows = [
        [
            row["char"],
            row["unicode"],
            row["standard_rank"],
            row["score"],
            row["overall_status"],
            row["repair_class"],
            ", ".join(row["issues"][:6]),
        ]
        for row in scores["samples"]["lowest_score_rows"][:15]
    ]

    return "\n".join(
        [
            "# CNBE8105 GF0017 Normativity Score Report",
            "",
            "## Scope",
            "",
            "This report scores each 8105 character against the GF0017 50-point normativity model.",
            "It is read-only and does not modify CNBE source data, databases, or generated code.",
            "",
            "Important: `character_set_coverage` and `stroke_shape` retain `SOURCE_GAP` labels because standalone local sources for GB2312, 现代汉语通用字表, and 印刷通用汉字字形表 have not yet been confirmed.",
            "",
            "## Summary",
            "",
            f"- Rows scored: {summary['row_count']}",
            f"- Average score: {summary['average_score']} / 50",
            f"- Minimum score: {summary['min_score']} / 50",
            f"- Maximum score: {summary['max_score']} / 50",
            "",
            "## Overall Status Counts",
            "",
            markdown_table(["Status", "Rows"], status_rows),
            "",
            "## Repair Class Counts",
            "",
            markdown_table(["Repair class", "Rows"], repair_rows),
            "",
            "## Score Item Averages",
            "",
            markdown_table(["Item", "Average score", "Item statuses"], item_rows),
            "",
            "## Known Character Samples",
            "",
            markdown_table(
                [
                    "Char",
                    "Unicode",
                    "Score",
                    "Status",
                    "Repair class",
                    "Issues",
                    "Std radical",
                    "CNBE radical",
                    "Std strokes",
                    "CNBE strokes",
                    "Std structure",
                    "CNBE structure",
                ],
                sample_rows,
            ),
            "",
            "## Lowest Score Samples",
            "",
            markdown_table(["Char", "Unicode", "Rank", "Score", "Status", "Repair class", "Issues"], lowest_rows),
            "",
            "## Next Gate",
            "",
            "Use `CNBE32_FIELD_REPAIR_CANDIDATE` rows for a dry-run repair plan only after the radical-code map is validated.",
            "`EVIDENCE_GAP`, `SOURCE_GAP`, and `HUMAN_REVIEW_REQUIRED` rows must not be auto-rewritten.",
            "",
        ]
    )


def build_outputs(model_path: Path, comparison_path: Path, research_root: Path) -> tuple[dict[str, Any], str]:
    model = load_json(model_path)
    comparison = load_or_build_comparison(comparison_path, research_root)
    scores = build_scores(model, comparison)
    markdown = render_markdown(scores)
    return scores, markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_INPUT)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON_INPUT)
    parser.add_argument("--research-root", type=Path, default=RESEARCH_ROOT)
    parser.add_argument("--score-output", type=Path, default=DEFAULT_SCORE_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scores, markdown = build_outputs(args.model, args.comparison, args.research_root)
    write_json(args.score_output, scores)
    write_text(args.markdown_output, markdown)
    print(f"wrote {args.score_output}")
    print(f"wrote {args.markdown_output}")
    print(f"rows={scores['summary']['row_count']}")
    print(f"average_score={scores['summary']['average_score']}/50")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
