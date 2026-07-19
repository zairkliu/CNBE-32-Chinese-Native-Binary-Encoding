#!/usr/bin/env python3
"""Build priority reference candidates for full 8105 gap rows.

Priority order:

1. Existing 8105 standard-side fields.
2. Hanzi Yuanliu local character records.
3. Cihai local search snippets.
4. Offline Chinese Wikipedia cross-reference index.
5. ZDIC is intentionally excluded from this default workflow.

Only deterministic, self-consistent source-derived fields become review
candidates. Cihai and Wiki are context fields only and never assign structure.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

STANDARDIZER_CSV = Path("review_packets/8105_full/8105_full_no_legacy_standardizer.csv")
YUANLIU_JSON = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/yuanliu_chars.json")
CIHAI_INDEX_JSON = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cihai_search_index.json")
WIKI_INDEX_JSON = Path("reports/wikipedia_structure_cross_reference_index.json")

OUTPUT_DIR = Path("review_packets/8105_full")
CSV_OUTPUT = OUTPUT_DIR / "8105_gap_priority_reference_candidates.csv"
REMAINING_OUTPUT = OUTPUT_DIR / "8105_gap_priority_remaining_queue.csv"
JSON_OUTPUT = Path("reports/8105_gap_priority_reference_candidates.json")
MD_OUTPUT = Path("reports/8105_GAP_PRIORITY_REFERENCE_CANDIDATES.md")

EXPECTED_GAP_ROWS = 1537
ALLOWED_STRUCTURES = {
    "独体字",
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
IDS_TO_STRUCTURE = {
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def infer_structure(decomposition: str) -> str:
    if not decomposition or "?" in decomposition:
        return ""
    return IDS_TO_STRUCTURE.get(decomposition[0], "")


def first_snippets(index: dict[str, Any], char: str, limit: int = 2) -> str:
    values = index.get(char) or []
    if not isinstance(values, list):
        return ""
    return "\n".join(str(item)[:240] for item in values[:limit])


def wiki_index_by_char(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["char"]: row for row in data.get("row_records", []) if row.get("char")}


def make_row(
    gap: dict[str, str],
    yuanliu: dict[str, Any],
    cihai: dict[str, Any],
    wiki: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    char = gap["character"]
    yl = yuanliu.get(char, {})
    yl_structure = yl.get("struct_name", "")
    yl_decomposition = yl.get("decomposition", "")
    yl_ids_structure = infer_structure(yl_decomposition)
    standard_structure = gap["candidate_structure_label"]
    standard_decomposition = gap["candidate_decomposition"]
    proposed_structure = ""
    proposed_decomposition = ""
    candidate_rule = "context_only_no_safe_structure_candidate"
    source_priority = "cihai_wiki_context_only"
    confidence = "NONE"
    blocker = "SOURCE_EVIDENCE_REQUIRED"

    if standard_structure == "独体字" and standard_decomposition == "?" and char in gap["direct_component_candidates"].split(" "):
        proposed_structure = "独体字"
        proposed_decomposition = char
        candidate_rule = "standard_side_single_component_identity"
        source_priority = "existing_8105_standard_side"
        confidence = "HIGH_REVIEW_REQUIRED"
        blocker = "REVIEW_REQUIRED_BEFORE_MERGE"
    elif not standard_structure and infer_structure(standard_decomposition):
        proposed_structure = infer_structure(standard_decomposition)
        proposed_decomposition = standard_decomposition
        candidate_rule = "standard_side_ids_operator_structure"
        source_priority = "existing_8105_standard_side"
        confidence = "HIGH_REVIEW_REQUIRED"
        blocker = "REVIEW_REQUIRED_BEFORE_MERGE"
    elif (
        yl_structure in ALLOWED_STRUCTURES
        and yl_decomposition
        and "?" not in yl_decomposition
        and yl_ids_structure == yl_structure
    ):
        proposed_structure = yl_structure
        proposed_decomposition = yl_decomposition
        candidate_rule = "yuanliu_ids_consistent_structure_candidate"
        source_priority = "yuanliu_core_reference"
        confidence = "MEDIUM_REVIEW_REQUIRED"
        blocker = "REVIEW_REQUIRED_BEFORE_MERGE"

    wiki_record = wiki.get(char, {})
    wiki_hits = wiki_record.get("wiki_hits") or []
    return {
        "row_id": gap["row_id"],
        "character": char,
        "unicode_codepoint": gap["unicode_codepoint"],
        "standard_rank": gap["standard_rank"],
        "original_structure": standard_structure,
        "original_decomposition": standard_decomposition,
        "original_components": gap["direct_component_candidates"],
        "yuanliu_structure": yl_structure,
        "yuanliu_decomposition": yl_decomposition,
        "yuanliu_ids_structure": yl_ids_structure,
        "cihai_hit_count": len(cihai.get(char) or []),
        "cihai_snippets": first_snippets(cihai, char),
        "wiki_hit_count": len(wiki_hits),
        "wiki_titles": "; ".join(str(hit.get("title", "")) for hit in wiki_hits[:3]),
        "wiki_snippets": "\n".join(str(hit.get("snippet", ""))[:240] for hit in wiki_hits[:2]),
        "proposed_structure": proposed_structure,
        "proposed_decomposition": proposed_decomposition,
        "candidate_rule": candidate_rule,
        "source_priority": source_priority,
        "authority_boundary": "REVIEW_CANDIDATE_NOT_NATIONAL_STANDARD",
        "confidence": confidence,
        "blocker": blocker,
        "review_status": "HUMAN_REVIEW_REQUIRED",
        "cnbe_write_status": "NO_CNBE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
        "zdic_status": "NOT_USED_IN_PRIORITY_DEFAULT_WORKFLOW",
    }


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    standardizer_rows = read_csv(STANDARDIZER_CSV)
    gaps = [
        row
        for row in standardizer_rows
        if row["standardizer_status"] != "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"
    ]
    yuanliu = load_json(YUANLIU_JSON)
    cihai = load_json(CIHAI_INDEX_JSON)
    wiki = wiki_index_by_char(load_json(WIKI_INDEX_JSON))
    rows = [make_row(gap, yuanliu, cihai, wiki) for gap in gaps]
    candidate_rows = [row for row in rows if row["candidate_rule"] != "context_only_no_safe_structure_candidate"]
    remaining_rows = [row for row in rows if row["candidate_rule"] == "context_only_no_safe_structure_candidate"]
    proposed_structures = {row["proposed_structure"] for row in candidate_rows if row["proposed_structure"]}
    checks = {
        "gap_row_count_expected": len(gaps) == EXPECTED_GAP_ROWS,
        "all_gap_rows_accounted_for": len(candidate_rows) + len(remaining_rows) == len(gaps),
        "proposed_structures_allowed": proposed_structures <= ALLOWED_STRUCTURES,
        "zdic_not_used_by_default": all(row["zdic_status"] == "NOT_USED_IN_PRIORITY_DEFAULT_WORKFLOW" for row in rows),
        "cihai_wiki_do_not_assign_structure": all(
            row["source_priority"] not in {"cihai", "wiki"} for row in candidate_rows
        ),
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows),
    }
    report = {
        "report_schema_version": "1.0",
        "mode": "full_8105_gap_priority_reference_candidates",
        "overall_status": "PASS_8105_GAP_PRIORITY_REFERENCE_CANDIDATES_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "gap_rows": len(gaps),
            "candidate_rows": len(candidate_rows),
            "remaining_rows": len(remaining_rows),
            "yuanliu_hits": sum(1 for row in rows if row["yuanliu_structure"] or row["yuanliu_decomposition"]),
            "cihai_hits": sum(1 for row in rows if row["cihai_hit_count"]),
            "wiki_hits": sum(1 for row in rows if row["wiki_hit_count"]),
            "candidate_rule_counts": dict(Counter(row["candidate_rule"] for row in rows)),
            "source_priority_counts": dict(Counter(row["source_priority"] for row in rows)),
            "proposed_structure_counts": dict(Counter(row["proposed_structure"] or "UNRESOLVED" for row in candidate_rows)),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "candidate_csv": str(CSV_OUTPUT),
            "remaining_queue_csv": str(REMAINING_OUTPUT),
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MD_OUTPUT),
        },
        "decision": {
            "may_human_review_candidates": all(checks.values()),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The workflow uses Yuanliu only when IDS and structure are "
                "self-consistent. Cihai and offline Wiki are attached as review "
                "context only. ZDIC is excluded from the default priority path."
            ),
        },
    }
    return candidate_rows, remaining_rows, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Gap Priority Reference Candidates",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Gap rows: {report['summary']['gap_rows']}",
        f"- Candidate rows: {report['summary']['candidate_rows']}",
        f"- Remaining rows: {report['summary']['remaining_rows']}",
        f"- Yuanliu hits: {report['summary']['yuanliu_hits']}",
        f"- Cihai hits: {report['summary']['cihai_hits']}",
        f"- Wiki hits: {report['summary']['wiki_hits']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        "",
        "## Candidate Rule Counts",
        "",
        "| Rule | Rows |",
        "|---|---:|",
    ]
    for rule, count in sorted(report["summary"]["candidate_rule_counts"].items()):
        lines.append(f"| `{rule}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    candidate_rows, remaining_rows, report = build()
    write_csv(CSV_OUTPUT, candidate_rows)
    write_csv(REMAINING_OUTPUT, remaining_rows)
    write_json(JSON_OUTPUT, report)
    MD_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print(report["overall_status"])
    print(f"gap_rows={report['summary']['gap_rows']}")
    print(f"candidate_rows={report['summary']['candidate_rows']}")
    print(f"remaining_rows={report['summary']['remaining_rows']}")
    print(f"yuanliu_hits={report['summary']['yuanliu_hits']}")
    print(f"cihai_hits={report['summary']['cihai_hits']}")
    print(f"wiki_hits={report['summary']['wiki_hits']}")


if __name__ == "__main__":
    main()
