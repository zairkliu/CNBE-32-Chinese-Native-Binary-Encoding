#!/usr/bin/env python3
"""Build a read-only 8105 Hanzi baseline and compare it with current CNBE rows."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
DEFAULT_BASELINE_OUTPUT = Path("evidence/8105/cnbe8105_standard_baseline.json")
DEFAULT_SNAPSHOT_OUTPUT = Path("evidence/8105/cnbe8105_current_cnbe_snapshot.json")
DEFAULT_COMPARISON_OUTPUT = Path("evidence/8105/cnbe8105_encoding_comparison.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md")

BASE_CHARACTER_DATA = Path("knowledge/structured/base_character_data.json")
YUANLIU_CHARS = Path("knowledge/yuanliu_chars.json")
CNBE_UPDATED = Path("knowledge/cnbe32_updated.json")
COMPONENT_DB = Path("knowledge/component_db.json")
DECOMP_DICTIONARY = Path("decomp-data/dictionary.jsonl")
CJK_DECOMP = Path("cjk-decomp/cjk-decomp.txt")
GF_STROKE_ORDER_MD = Path("source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md")

EXPECTED_8105_ROWS = 8105
SAMPLE_LIMIT = 20

ALLOWED_STRUCTURES = {
    "上下",
    "上中下",
    "左右",
    "左中右",
    "左上包",
    "右上包",
    "左三包",
    "左下包",
    "上三包",
    "下三包",
    "全包围",
    "镶嵌",
}
SPECIAL_STRUCTURE = "独体字"
ALLOWED_STRUCTURE_SET = ALLOWED_STRUCTURES | {SPECIAL_STRUCTURE}

REVIEW_REQUIRED_REASON_LABELS = {
    "missing_from_current_cnbe": "8105 字在当前 CNBE 表中缺失",
    "ambiguous_decomposition": "拆分含 ? 或证据不完整",
    "missing_standard_structure": "标准结构证据缺失",
    "missing_standard_radical": "标准部首证据缺失",
    "invalid_standard_structure": "标准侧结构名不在允许集合",
    "invalid_current_structure": "当前 CNBE 结构名不在允许集合",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            character = row.get("character")
            if isinstance(character, str) and len(character) == 1:
                rows[character] = row
    return rows


def read_cjk_decomp(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or ":" not in line:
                continue
            char, value = line.split(":", 1)
            if len(char) == 1:
                rows[char] = value
    return rows


def format_codepoint(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def codepoint_from_char(char: str) -> int:
    return ord(char)


def canonical_unicode(char: str, raw_value: Any = None) -> str:
    if isinstance(raw_value, str) and raw_value.startswith("U+"):
        try:
            return format_codepoint(int(raw_value[2:], 16))
        except ValueError:
            pass
    return format_codepoint(codepoint_from_char(char))


def char_from_unicode(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str) or not raw_value.startswith("U+"):
        return None
    try:
        return chr(int(raw_value[2:], 16))
    except (ValueError, OverflowError):
        return None


def parse_stroke_values(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"[1-5]", text)]


def level_from_standard_rank(rank: int) -> str:
    if rank <= 3500:
        return "一级"
    if rank <= 6500:
        return "二级"
    return "三级"


def read_gf_stroke_order_markdown(path: Path) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    if not path.is_file():
        return rows
    pattern = re.compile(r"^\|(?P<char_cell>.*?)\|(?P<order_cell>.*?)\|(?P<rank>\d{4})\|(?P<ucs>[0-9A-Fa-f]+)\|$")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = pattern.match(line.strip())
        if not match:
            continue
        rank = int(match.group("rank"))
        ucs = match.group("ucs").upper()
        codepoint = int(ucs, 16)
        char = chr(codepoint)
        order_values = parse_stroke_values(match.group("order_cell"))
        if not order_values:
            order_values = parse_stroke_values(match.group("char_cell"))
        rows[rank] = {
            "char": char,
            "stroke_count": len(order_values),
            "stroke_order": order_values,
            "stroke_order_str": " ".join(str(value) for value in order_values),
            "standard_rank": rank,
            "unicode": format_codepoint(codepoint),
            "level": level_from_standard_rank(rank),
            "source_line": line_number,
        }
    return rows


def normalize_structure(raw_structure: Any, decomposition: str | None = None) -> tuple[str | None, str | None]:
    if not isinstance(raw_structure, str) or not raw_structure:
        return None, "missing_standard_structure"
    if raw_structure == "右下包":
        if decomposition and decomposition.startswith("⿺"):
            return "左下包", "normalized_right_bottom_to_left_bottom"
        return None, "invalid_standard_structure"
    if raw_structure in ALLOWED_STRUCTURE_SET:
        return raw_structure, None
    return None, "invalid_standard_structure"


def evidence_status_for(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    if not row.get("radical"):
        reasons.append("missing_standard_radical")
    if not row.get("structure"):
        reasons.append("missing_standard_structure")
    if row.get("decomposition_has_unknown"):
        reasons.append("ambiguous_decomposition")
    if row.get("structure_issue") == "invalid_standard_structure":
        reasons.append("invalid_standard_structure")
    if reasons:
        return "REVIEW_REQUIRED", sorted(set(reasons))
    return "COMPLETE", []


def load_research_sources(research_root: Path) -> dict[str, Any]:
    paths = {
        "base_character_data": research_root / BASE_CHARACTER_DATA,
        "yuanliu_chars": research_root / YUANLIU_CHARS,
        "cnbe32_updated": research_root / CNBE_UPDATED,
        "component_db": research_root / COMPONENT_DB,
        "decomp_dictionary": research_root / DECOMP_DICTIONARY,
        "cjk_decomp": research_root / CJK_DECOMP,
        "gf_stroke_order_md": research_root / GF_STROKE_ORDER_MD,
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        details = ", ".join(f"{name}={paths[name]}" for name in missing)
        raise ValueError(f"required cnbe-research sources are missing: {details}")
    return {
        "paths": paths,
        "base_character_data": load_json(paths["base_character_data"]),
        "yuanliu_chars": load_json(paths["yuanliu_chars"]),
        "cnbe32_updated": load_json(paths["cnbe32_updated"]),
        "component_db": load_json(paths["component_db"]),
        "decomp_dictionary": read_jsonl(paths["decomp_dictionary"]),
        "cjk_decomp": read_cjk_decomp(paths["cjk_decomp"]),
        "gf_stroke_order": read_gf_stroke_order_markdown(paths["gf_stroke_order_md"]),
    }


def build_standard_baseline(sources: dict[str, Any]) -> dict[str, Any]:
    base_data: dict[str, dict[str, Any]] = sources["base_character_data"]
    yuanliu: dict[str, dict[str, Any]] = sources["yuanliu_chars"]
    component_db: dict[str, Any] = sources["component_db"]
    decomp_dictionary: dict[str, dict[str, Any]] = sources["decomp_dictionary"]
    cjk_decomp: dict[str, str] = sources["cjk_decomp"]
    gf_stroke_order: dict[int, dict[str, Any]] = sources["gf_stroke_order"]
    char_mappings = component_db.get("char_mappings", {})
    normalized_base_data: dict[str, dict[str, Any]] = {}
    source_char_normalizations: list[dict[str, Any]] = []

    for raw_char, raw_row in base_data.items():
        row = dict(raw_row)
        canonical_char = char_from_unicode(row.get("unicode")) or raw_char
        if canonical_char != raw_char:
            source_char_normalizations.append(
                {
                    "raw_char": raw_char,
                    "canonical_char": canonical_char,
                    "unicode": canonical_unicode(canonical_char, row.get("unicode")),
                    "standard_rank": row.get("standard_rank"),
                }
            )
        row["char"] = canonical_char
        normalized_base_data[canonical_char] = row

    existing_ranks = {row.get("standard_rank") for row in normalized_base_data.values()}
    source_rows_added = []
    for rank, gf_row in sorted(gf_stroke_order.items()):
        if 1 <= rank <= EXPECTED_8105_ROWS and rank not in existing_ranks:
            normalized_base_data[gf_row["char"]] = dict(gf_row)
            source_rows_added.append(
                {
                    "char": gf_row["char"],
                    "unicode": gf_row["unicode"],
                    "standard_rank": rank,
                    "source": "GF 0031—2026 通用规范汉字笔顺规范.md",
                    "source_line": gf_row["source_line"],
                }
            )

    characters: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()

    for char, base_row in sorted(normalized_base_data.items(), key=lambda item: item[1].get("standard_rank", 0)):
        yuan_row = yuanliu.get(char, {})
        dict_row = decomp_dictionary.get(char, {})
        decomposition = yuan_row.get("decomposition") or dict_row.get("decomposition")
        structure, structure_issue = normalize_structure(yuan_row.get("struct_name"), decomposition)
        components = char_mappings.get(char)
        if not components and decomposition:
            components = []

        row = {
            "char": char,
            "codepoint": codepoint_from_char(char),
            "unicode": canonical_unicode(char, base_row.get("unicode")),
            "standard_rank": base_row.get("standard_rank"),
            "level": base_row.get("level"),
            "stroke_count": base_row.get("stroke_count"),
            "stroke_order": base_row.get("stroke_order"),
            "stroke_order_str": base_row.get("stroke_order_str"),
            "radical": yuan_row.get("radical") or dict_row.get("radical"),
            "radix": yuan_row.get("radix"),
            "structure": structure,
            "raw_structure": yuan_row.get("struct_name"),
            "structure_issue": structure_issue,
            "decomposition": decomposition,
            "decomposition_has_unknown": bool(isinstance(decomposition, str) and "?" in decomposition),
            "components": components,
            "cjk_decomp": cjk_decomp.get(char),
            "pinyin": yuan_row.get("pinyin") or (dict_row.get("pinyin") or [None])[0],
            "definition": yuan_row.get("definition") or dict_row.get("definition"),
            "etymology_type": yuan_row.get("etym_type") or dict_row.get("etymology_type"),
            "etymology_hint": yuan_row.get("etym_hint") or dict_row.get("etymology_hint"),
            "evidence_sources": {
                "base_character_data": True,
                "gf_stroke_order_md": bool(gf_stroke_order.get(base_row.get("standard_rank"))),
                "yuanliu_chars": bool(yuan_row),
                "decomp_dictionary": bool(dict_row),
                "component_db": bool(char_mappings.get(char)),
                "cjk_decomp": char in cjk_decomp,
            },
        }
        status, reasons = evidence_status_for(row)
        row["evidence_status"] = status
        row["evidence_issues"] = reasons
        status_counts[status] += 1
        issue_counts.update(reasons)
        if structure_issue:
            issue_counts[structure_issue] += 1
        characters[char] = row
    if source_char_normalizations:
        issue_counts["source_char_normalized_from_unicode"] = len(source_char_normalizations)
    if source_rows_added:
        issue_counts["source_rows_added_from_gf_stroke_order"] = len(source_rows_added)

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "8105 通用规范汉字首次标准基准表",
            "row_count": len(characters),
            "expected_row_count": EXPECTED_8105_ROWS,
            "allowed_structures": sorted(ALLOWED_STRUCTURES),
            "special_structure": SPECIAL_STRUCTURE,
            "source_char_normalizations": source_char_normalizations,
            "source_rows_added_from_gf_stroke_order": source_rows_added,
        },
        "summary": {
            "row_count": len(characters),
            "expected_row_count": EXPECTED_8105_ROWS,
            "row_count_matches_expected": len(characters) == EXPECTED_8105_ROWS,
            "evidence_status_counts": dict(sorted(status_counts.items())),
            "evidence_issue_counts": dict(sorted(issue_counts.items())),
        },
        "characters": characters,
    }


def current_cnbe_characters(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows = raw.get("characters")
    if not isinstance(rows, list):
        raise ValueError("cnbe32_updated.json must contain a characters list")
    return rows


def build_current_snapshot(sources: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_chars = set(baseline["characters"])
    all_current_rows = current_cnbe_characters(sources["cnbe32_updated"])
    snapshot_rows: dict[str, dict[str, Any]] = {}
    duplicate_chars: list[str] = []
    out_of_scope_rows = []

    for row in all_current_rows:
        char = row.get("char")
        if not isinstance(char, str) or len(char) != 1:
            continue
        normalized = {
            "char": char,
            "codepoint": row.get("unicode"),
            "unicode": format_codepoint(int(row["unicode"])) if isinstance(row.get("unicode"), int) else None,
            "cnbe": row.get("cnbe"),
            "cnbe_hex": f"0x{int(row['cnbe']):08X}" if isinstance(row.get("cnbe"), int) else None,
            "radix": row.get("radix"),
            "radix_name": row.get("radix_name"),
            "strokes": row.get("strokes"),
            "struct_type": row.get("struct_type"),
            "struct_name": row.get("struct_name"),
            "index": row.get("index"),
        }
        if char in baseline_chars:
            if char in snapshot_rows:
                duplicate_chars.append(char)
            snapshot_rows[char] = normalized
        else:
            out_of_scope_rows.append(normalized)

    missing = sorted(baseline_chars - set(snapshot_rows), key=lambda ch: baseline["characters"][ch]["standard_rank"])
    invalid_structure_rows = sorted(
        [char for char, row in snapshot_rows.items() if row.get("struct_name") not in ALLOWED_STRUCTURE_SET]
    )

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "当前 CNBE 表中落入 8105 范围的快照",
            "source_total_rows": len(all_current_rows),
        },
        "summary": {
            "baseline_rows": len(baseline_chars),
            "current_rows_in_8105": len(snapshot_rows),
            "missing_from_current_rows": len(missing),
            "out_of_scope_current_rows": len(out_of_scope_rows),
            "duplicate_current_chars": len(duplicate_chars),
            "invalid_current_structure_rows": len(invalid_structure_rows),
        },
        "missing_from_current": missing,
        "duplicate_current_chars": sorted(set(duplicate_chars)),
        "invalid_current_structure_chars": invalid_structure_rows[:SAMPLE_LIMIT],
        "out_of_scope_samples": out_of_scope_rows[:SAMPLE_LIMIT],
        "characters": dict(sorted(snapshot_rows.items(), key=lambda item: baseline["characters"][item[0]]["standard_rank"])),
    }


def comparison_status(issues: list[str], evidence_status: str) -> str:
    if evidence_status != "COMPLETE":
        return "EVIDENCE_GAP" if "missing_standard_structure" in issues else "FAIL_REVIEW_REQUIRED"
    if not issues:
        return "PASS"
    if any(issue in issues for issue in ("missing_from_current_cnbe", "invalid_current_structure")):
        return "FAIL_REVIEW_REQUIRED"
    return "FAIL_FIXABLE"


def compare_one(standard: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
    issues: list[str] = []
    field_results: dict[str, dict[str, Any]] = {}

    def add_field(field: str, standard_value: Any, current_value: Any, issue: str) -> None:
        passed = standard_value == current_value
        field_results[field] = {
            "standard": standard_value,
            "current": current_value,
            "pass": passed,
        }
        if not passed:
            issues.append(issue)

    if current is None:
        issues.append("missing_from_current_cnbe")
        return {
            "char": standard["char"],
            "unicode": standard["unicode"],
            "standard_rank": standard["standard_rank"],
            "status": comparison_status(issues + standard.get("evidence_issues", []), standard["evidence_status"]),
            "issues": sorted(set(issues + standard.get("evidence_issues", []))),
            "field_results": {},
            "standard": standard,
            "current": None,
        }

    add_field("unicode", standard["codepoint"], current.get("codepoint"), "unicode_mismatch")
    add_field("stroke_count", standard.get("stroke_count"), current.get("strokes"), "stroke_count_mismatch")
    add_field("radical", standard.get("radical"), current.get("radix_name"), "radical_mismatch")
    add_field("structure", standard.get("structure"), current.get("struct_name"), "structure_mismatch")
    if current.get("struct_name") not in ALLOWED_STRUCTURE_SET:
        issues.append("invalid_current_structure")
    if standard.get("evidence_issues"):
        issues.extend(standard["evidence_issues"])
    if standard.get("decomposition") is None:
        issues.append("missing_decomposition")

    return {
        "char": standard["char"],
        "unicode": standard["unicode"],
        "standard_rank": standard["standard_rank"],
        "status": comparison_status(sorted(set(issues)), standard["evidence_status"]),
        "issues": sorted(set(issues)),
        "field_results": field_results,
        "standard": {
            "stroke_count": standard.get("stroke_count"),
            "radical": standard.get("radical"),
            "structure": standard.get("structure"),
            "raw_structure": standard.get("raw_structure"),
            "decomposition": standard.get("decomposition"),
            "components": standard.get("components"),
            "evidence_status": standard.get("evidence_status"),
        },
        "current": current,
    }


def build_comparison(baseline: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    baseline_chars = baseline["characters"]
    current_chars = snapshot["characters"]
    rows: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    field_mismatch_counts: Counter[str] = Counter()

    for char, standard in baseline_chars.items():
        row = compare_one(standard, current_chars.get(char))
        rows[char] = row
        status_counts[row["status"]] += 1
        issue_counts.update(row["issues"])
        for field, result in row["field_results"].items():
            if not result["pass"]:
                field_mismatch_counts[field] += 1

    sample_chars = ["家", "遛", "涡", "亾", "与", "焱", "衍", "鼻"]
    samples = {char: rows[char] for char in sample_chars if char in rows}
    top_issue_samples = {}
    for status in ("FAIL_FIXABLE", "FAIL_REVIEW_REQUIRED", "EVIDENCE_GAP", "PASS"):
        top_issue_samples[status] = [row for row in rows.values() if row["status"] == status][:SAMPLE_LIMIT]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "8105 通用规范汉字标准证据与当前 CNBE 首次比对",
            "allowed_structures": sorted(ALLOWED_STRUCTURES),
            "special_structure": SPECIAL_STRUCTURE,
        },
        "summary": {
            "total_standard_rows": len(baseline_chars),
            "current_rows_in_scope": len(current_chars),
            "missing_from_current_rows": snapshot["summary"]["missing_from_current_rows"],
            "status_counts": dict(sorted(status_counts.items())),
            "issue_counts": dict(sorted(issue_counts.items())),
            "field_mismatch_counts": dict(sorted(field_mismatch_counts.items())),
        },
        "samples": samples,
        "top_issue_samples": top_issue_samples,
        "characters": rows,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def render_markdown_report(baseline: dict[str, Any], snapshot: dict[str, Any], comparison: dict[str, Any]) -> str:
    summary = comparison["summary"]
    baseline_summary = baseline["summary"]
    snapshot_summary = snapshot["summary"]
    sample_rows = []
    for char, row in comparison["samples"].items():
        sample_rows.append(
            [
                char,
                row["status"],
                ", ".join(row["issues"]) or "none",
                row["standard"].get("radical"),
                row["current"].get("radix_name") if row["current"] else "MISSING",
                row["standard"].get("stroke_count"),
                row["current"].get("strokes") if row["current"] else "MISSING",
                row["standard"].get("structure"),
                row["current"].get("struct_name") if row["current"] else "MISSING",
            ]
        )

    status_rows = [[key, value] for key, value in summary["status_counts"].items()]
    issue_rows = [[key, value] for key, value in summary["issue_counts"].items()]
    field_rows = [[key, value] for key, value in summary["field_mismatch_counts"].items()]

    return "\n".join(
        [
            "# CNBE-32 8105 Encoding Comparison Report",
            "",
            "## Scope",
            "",
            "This is a read-only first-pass comparison between the 8105 standard Hanzi baseline and the current CNBE table.",
            "It does not rewrite `cnbe32_updated.json`, does not generate new CNBE codes, and does not cover non-8105 characters.",
            "",
            "## Gate",
            "",
            "- Baseline expected rows: 8105",
            f"- Baseline actual rows: {baseline_summary['row_count']}",
            f"- Baseline row count matches expected: {baseline_summary['row_count_matches_expected']}",
            f"- Current rows in 8105 scope: {snapshot_summary['current_rows_in_8105']}",
            f"- Missing current rows: {snapshot_summary['missing_from_current_rows']}",
            f"- Invalid current structure rows: {snapshot_summary['invalid_current_structure_rows']}",
            "",
            "## Status Counts",
            "",
            markdown_table(["Status", "Rows"], status_rows),
            "",
            "## Issue Counts",
            "",
            markdown_table(["Issue", "Rows"], issue_rows),
            "",
            "## Field Mismatch Counts",
            "",
            markdown_table(["Field", "Rows"], field_rows),
            "",
            "## Required Review Samples",
            "",
            markdown_table(
                [
                    "Char",
                    "Status",
                    "Issues",
                    "Std Radical",
                    "CNBE Radical",
                    "Std Strokes",
                    "CNBE Strokes",
                    "Std Structure",
                    "CNBE Structure",
                ],
                sample_rows,
            ),
            "",
            "## Policy Notes",
            "",
            "- Allowed structures are: "
            + ", ".join(sorted(ALLOWED_STRUCTURES))
            + f"; plus special `{SPECIAL_STRUCTURE}`.",
            "- Source labels such as `右下包` are not accepted as final normalized structure values.",
            "- Decompositions containing `?` are review-required and must not be auto-fixed.",
            "- Characters outside the 8105 baseline are out of scope for this first pass.",
            "",
            "## Next Gate",
            "",
            "The next phase may design an auto-fix candidate list only from `FAIL_FIXABLE` rows.",
            "`FAIL_REVIEW_REQUIRED` and `EVIDENCE_GAP` rows must stay in manual review pools.",
            "",
        ]
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_outputs(research_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    sources = load_research_sources(research_root)
    baseline = build_standard_baseline(sources)
    snapshot = build_current_snapshot(sources, baseline)
    comparison = build_comparison(baseline, snapshot)
    markdown = render_markdown_report(baseline, snapshot, comparison)
    return baseline, snapshot, comparison, markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, default=RESEARCH_ROOT)
    parser.add_argument("--baseline-output", type=Path, default=DEFAULT_BASELINE_OUTPUT)
    parser.add_argument("--snapshot-output", type=Path, default=DEFAULT_SNAPSHOT_OUTPUT)
    parser.add_argument("--comparison-output", type=Path, default=DEFAULT_COMPARISON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        baseline, snapshot, comparison, markdown = build_outputs(args.research_root)
    except Exception as exc:  # pragma: no cover - command-line guard
        print(f"CNBE8105 COMPARISON FAIL: {exc}", file=sys.stderr)
        return 1

    write_json(args.baseline_output, baseline)
    write_json(args.snapshot_output, snapshot)
    write_json(args.comparison_output, comparison)
    write_text(args.markdown_output, markdown)

    summary = comparison["summary"]
    print("CNBE8105 ENCODING COMPARISON PASS")
    print(f"Standard rows: {summary['total_standard_rows']}")
    print(f"Current rows in scope: {summary['current_rows_in_scope']}")
    print(f"Status counts: {json.dumps(summary['status_counts'], ensure_ascii=False, sort_keys=True)}")
    print(f"Field mismatch counts: {json.dumps(summary['field_mismatch_counts'], ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
