#!/usr/bin/env python3
"""Run the hanzi_decomp_v0.3 zip as a read-only 8105 candidate layer.

The supplied tool is useful for IDS-based structure lookup, but it is not
treated as national-standard evidence. This adapter reads the zip directly,
normalizes structure labels into the approved CNBE Agent set, compares them
against the current 8105 review packet, and emits review artifacts only.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_ZIP = Path("/Volumes/u盘 256g/hanzi_decomp_v0.3.zip")
INITIAL_PACKET = Path("review_packets/8105_full/8105_initial_auto_filled_review_packet.csv")

OUTPUT_DIR = Path("review_packets/8105_full")
ALL_CSV = OUTPUT_DIR / "8105_hanzi_decomp_v03_adapter_all.csv"
FILL_CSV = OUTPUT_DIR / "8105_hanzi_decomp_v03_gap_fill_candidates.csv"
CONFLICT_CSV = OUTPUT_DIR / "8105_hanzi_decomp_v03_conflicts.csv"
JSON_REPORT = Path("reports/8105_hanzi_decomp_v03_adapter.json")
MD_REPORT = Path("reports/8105_HANZI_DECOMP_V03_ADAPTER.md")

EXPECTED_8105_ROWS = 8105
APPROVED_STRUCTURES = {
    "独体字": 0,
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
IDC_TO_STRUCTURE = {
    "⿰": "左右",
    "⿱": "上下",
    "⿲": "左中右",
    "⿳": "上中下",
    "⿴": "全包围",
    "⿵": "上三包",
    "⿶": "下三包",
    "⿷": "左三包",
    "⿸": "左上包",
    "⿹": "右上包",
    "⿺": "左下包",
    "⿻": "镶嵌",
}
IDC_SET = set(IDC_TO_STRUCTURE)
FORBIDDEN_STRUCTURES = {"右下包", "品字形", "三叠结构", "会意结构", "独体结构"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_zip_json(zf: zipfile.ZipFile, name: str) -> Any:
    return json.loads(zf.read(name).decode("utf-8"))


def load_dutizi_set(zf: zipfile.ZipFile) -> set[str]:
    source = zf.read("dutizi.py").decode("utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DUTIZI_LIST":
                    return set(ast.literal_eval(node.value))
    return set()


def zip_manifest(zf: zipfile.ZipFile) -> list[dict[str, Any]]:
    return [
        {
            "name": info.filename,
            "size": info.file_size,
            "compressed_size": info.compress_size,
        }
        for info in zf.infolist()
    ]


def detect_tool_risks(zf: zipfile.ZipFile) -> dict[str, Any]:
    risks: dict[str, Any] = {
        "hardcoded_windows_base_path": False,
        "starts_local_http_server": False,
        "opens_browser": False,
        "uses_subprocess": False,
        "writes_files": False,
    }
    for name in zf.namelist():
        if not name.endswith((".py", ".js", ".html", ".bat")):
            continue
        text = zf.read(name).decode("utf-8", errors="replace")
        if "C:" in text and "Users" in text:
            risks["hardcoded_windows_base_path"] = True
        if "HTTPServer" in text or "localhost" in text:
            risks["starts_local_http_server"] = True
        if "webbrowser.open" in text:
            risks["opens_browser"] = True
        if "subprocess" in text:
            risks["uses_subprocess"] = True
        if re.search(r"\bopen\([^)]*['\"]w|write\(", text):
            risks["writes_files"] = True
    return risks


def strip_ids_annotations(ids: str) -> str:
    return re.sub(r"\[[A-Za-z0-9]+\]", "", ids)


def top_level_parts(ids: str) -> list[str]:
    clean = strip_ids_annotations(ids)
    if not clean or clean[0] not in IDC_SET:
        return []
    remaining = clean[1:]
    parts: list[str] = []
    depth = 0
    current = ""
    for char in remaining:
        current += char
        if char in IDC_SET:
            depth += 1
            continue
        if depth:
            depth -= 1
            continue
        parts.append(current)
        current = ""
    if current:
        parts.append(current)
    return parts


def infer_structure(char: str, ids: str, dutizi: set[str]) -> tuple[str, str]:
    if ids:
        clean = strip_ids_annotations(ids)
        structure = IDC_TO_STRUCTURE.get(clean[:1], "")
        return structure, clean
    if char in dutizi:
        return "独体字", char
    return "", ""


def make_row(source_row: dict[str, str], ids_data: dict[str, str], dutizi: set[str]) -> dict[str, Any]:
    char = source_row["character"]
    tool_structure, tool_decomposition = infer_structure(char, ids_data.get(char, ""), dutizi)
    current_structure = source_row["candidate_structure_label"]
    if not tool_structure:
        status = "TOOL_GAP"
    elif not current_structure:
        status = "TOOL_FILLS_CURRENT_GAP_REVIEW_REQUIRED"
    elif current_structure == tool_structure:
        status = "TOOL_CONFIRMS_CURRENT"
    else:
        status = "TOOL_CONFLICT_REVIEW_REQUIRED"
    if tool_structure not in APPROVED_STRUCTURES and tool_structure:
        status = "TOOL_STRUCTURE_OUTSIDE_APPROVED_SET"
    return {
        "row_id": source_row["row_id"],
        "character": char,
        "unicode_codepoint": source_row["unicode_codepoint"],
        "standard_rank": source_row["standard_rank"],
        "current_structure": current_structure,
        "current_decomposition": source_row["candidate_decomposition"],
        "tool_structure": tool_structure,
        "tool_struct_type": APPROVED_STRUCTURES.get(tool_structure, ""),
        "tool_decomposition": tool_decomposition,
        "tool_top_level_parts": " ".join(top_level_parts(tool_decomposition)),
        "tool_status": status,
        "authority_boundary": "USER_SUPPLIED_PROGRAM_AGENT_REFERENCE_NOT_NATIONAL_STANDARD",
        "candidate_encoding_status": (
            "AGENT_STRUCTURE_CODE_CANDIDATE_REVIEW_REQUIRED"
            if status == "TOOL_FILLS_CURRENT_GAP_REVIEW_REQUIRED"
            else "NOT_AN_ENCODING_WRITE"
        ),
        "cnbe32_write_status": "NO_CNBE32_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
        "review_status": "HUMAN_REVIEW_REQUIRED",
    }


def build(zip_path: Path = DEFAULT_ZIP) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source_rows = read_csv(INITIAL_PACKET)
    with zipfile.ZipFile(zip_path) as zf:
        ids_data = load_zip_json(zf, "ids_data_v6.json")
        chars8105 = load_zip_json(zf, "chars8105.json")
        dutizi = load_dutizi_set(zf)
        manifest = zip_manifest(zf)
        risks = detect_tool_risks(zf)
    packet_chars = [row["character"] for row in source_rows]
    rows = [make_row(row, ids_data, dutizi) for row in source_rows]
    fill_rows = [row for row in rows if row["tool_status"] == "TOOL_FILLS_CURRENT_GAP_REVIEW_REQUIRED"]
    conflict_rows = [row for row in rows if row["tool_status"] == "TOOL_CONFLICT_REVIEW_REQUIRED"]
    structures = {row["tool_structure"] for row in rows if row["tool_structure"]}
    status_counts = Counter(row["tool_status"] for row in rows)
    checks = {
        "source_packet_row_count_is_8105": len(source_rows) == EXPECTED_8105_ROWS,
        "zip_chars8105_row_count_is_8105": len(chars8105) == EXPECTED_8105_ROWS,
        "zip_chars_match_source_packet_set": set(chars8105) == set(packet_chars),
        "tool_structures_approved_or_blank": structures <= set(APPROVED_STRUCTURES),
        "forbidden_structure_labels_absent": not (structures & FORBIDDEN_STRUCTURES),
        "conflicts_are_separated": len(conflict_rows) == status_counts["TOOL_CONFLICT_REVIEW_REQUIRED"],
        "no_cnbe32_writes": all(row["cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows),
    }
    report = {
        "report_schema_version": "1.0",
        "mode": "hanzi_decomp_v03_8105_read_only_adapter",
        "overall_status": "PASS_HANZI_DECOMP_V03_ADAPTER_READY_FOR_REVIEW" if all(checks.values()) else "BLOCKED",
        "zip_path": str(zip_path),
        "summary": {
            "source_packet_rows": len(source_rows),
            "zip_chars8105_rows": len(chars8105),
            "ids_data_rows": len(ids_data),
            "tool_8105_ids_or_dutizi_coverage": sum(1 for row in rows if row["tool_structure"]),
            "tool_gap_rows": status_counts["TOOL_GAP"],
            "tool_confirms_current_rows": status_counts["TOOL_CONFIRMS_CURRENT"],
            "tool_gap_fill_candidate_rows": len(fill_rows),
            "tool_conflict_rows": len(conflict_rows),
            "tool_status_counts": dict(status_counts),
            "tool_structure_counts": dict(Counter(row["tool_structure"] or "UNRESOLVED" for row in rows)),
            "cnbe32_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "tool_risks": risks,
        "manifest": manifest,
        "outputs": {
            "all_rows_csv": str(ALL_CSV),
            "gap_fill_candidates_csv": str(FILL_CSV),
            "conflicts_csv": str(CONFLICT_CSV),
            "json_report": str(JSON_REPORT),
            "markdown_report": str(MD_REPORT),
        },
        "decision": {
            "may_use_as_agent_reference_candidates": all(checks.values()),
            "may_promote_to_national_standard": False,
            "may_write_cnbe32": False,
            "may_rebuild_database": False,
            "recommended_next_step": (
                "Review the gap-fill candidates first, and separately audit "
                "the conflicts before any source merge or encoding write."
            ),
        },
    }
    return rows, fill_rows, conflict_rows, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Hanzi Decomp v0.3 8105 Adapter",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Source packet rows: {report['summary']['source_packet_rows']}",
        f"- IDS data rows: {report['summary']['ids_data_rows']}",
        f"- 8105 coverage: {report['summary']['tool_8105_ids_or_dutizi_coverage']}",
        f"- Gap-fill candidate rows: {report['summary']['tool_gap_fill_candidate_rows']}",
        f"- Conflict rows: {report['summary']['tool_conflict_rows']}",
        f"- CNBE32 rows written: {report['summary']['cnbe32_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "The tool is treated as `USER_SUPPLIED_PROGRAM_AGENT_REFERENCE_NOT_NATIONAL_STANDARD`.",
        "Its structure codes are review candidates only.",
        "",
        "## Tool Risks",
        "",
        "| Risk | Present |",
        "|---|---:|",
    ]
    for key, value in sorted(report["tool_risks"].items()):
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Status Counts", "", "| Status | Rows |", "|---|---:|"])
    for status, count in sorted(report["summary"]["tool_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["recommended_next_step"], ""])
    return "\n".join(lines)


def run(zip_path: Path = DEFAULT_ZIP) -> dict[str, Any]:
    rows, fill_rows, conflict_rows, report = build(zip_path)
    write_csv(ALL_CSV, rows)
    write_csv(FILL_CSV, fill_rows)
    write_csv(CONFLICT_CSV, conflict_rows)
    write_json(JSON_REPORT, report)
    write_text(MD_REPORT, render_markdown(report))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run(args.zip)
    print(report["overall_status"])
    print(f"coverage={report['summary']['tool_8105_ids_or_dutizi_coverage']}")
    print(f"gap_fill_candidates={report['summary']['tool_gap_fill_candidate_rows']}")
    print(f"conflicts={report['summary']['tool_conflict_rows']}")


if __name__ == "__main__":
    main()
