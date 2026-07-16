#!/usr/bin/env python3
"""Run a read-only 20,902-row pre-encoding test through the CNBE agent gates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CNBE_INPUT = Path("data/cnbe32.json")
DEFAULT_GF0017_SCORES = Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json")
DEFAULT_JSON_OUTPUT = Path("evidence/agent-standard/cnbe20902_agent_preencoding_test.json")
DEFAULT_MARKDOWN_OUTPUT = Path("evidence/agent-standard/CNBE20902_AGENT_PREENCODING_TEST.md")
DEFAULT_CHECKPOINT_OUTPUT = Path("evidence/agent-standard/cnbe20902_agent_preencoding_checkpoint.json")

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

ENGLISH_STRUCTURE_ALIASES = {
    "single": "独体字",
    "up-down": "上下",
    "up-mid-down": "上中下",
    "left-right": "左右",
    "left-mid-right": "左中右",
    "left-up-wrap": "左上包",
    "top-left-wrap": "左上包",
    "right-up-wrap": "右上包",
    "top-right-wrap": "右上包",
    "left-3-wrap": "左三包",
    "left-wrap": "左三包",
    "left-down-wrap": "左下包",
    "bottom-left-wrap": "左下包",
    "up-3-wrap": "上三包",
    "top-wrap": "上三包",
    "down-3-wrap": "下三包",
    "bottom-wrap": "下三包",
    "full-wrap": "全包围",
    "embedded": "镶嵌",
    "triangle": "镶嵌",
}

STRUCTURE_TYPE_BY_NAME = {
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def format_unicode(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def unicode_alignment(row: dict[str, Any]) -> tuple[str, list[str]]:
    issues: list[str] = []
    char = row.get("char")
    codepoint = row.get("unicode")
    if not isinstance(char, str) or len(char) != 1:
        issues.append("invalid_char_cell")
    if not isinstance(codepoint, int):
        issues.append("invalid_unicode_codepoint")
    if isinstance(char, str) and len(char) == 1 and isinstance(codepoint, int) and ord(char) != codepoint:
        issues.append("unicode_char_mismatch")
    return ("PASS" if not issues else "BLOCKER", issues)


def normalize_structure(raw: Any) -> tuple[str | None, str, list[str]]:
    issues: list[str] = []
    if raw in ALLOWED_STRUCTURES:
        return raw, "direct_chinese", []
    if raw in ENGLISH_STRUCTURE_ALIASES:
        normalized = ENGLISH_STRUCTURE_ALIASES[raw]
        issues.append("structure_label_requires_localization")
        return normalized, "english_alias", issues
    issues.append("unknown_structure_label")
    return None, "unresolved", issues


def bitfield_status(row: dict[str, Any], normalized_structure: str | None) -> tuple[str, list[str]]:
    issues: list[str] = []
    cnbe = row.get("cnbe")
    radix = row.get("radix")
    strokes = row.get("strokes")
    struct_type = row.get("struct_type")
    index = row.get("index")
    if not isinstance(cnbe, int) or not 0 <= cnbe <= 0xFFFFFFFF:
        issues.append("cnbe32_out_of_uint32_range")
    if not isinstance(radix, int) or not 0 <= radix <= 255:
        issues.append("radix_out_of_8bit_range")
    if not isinstance(strokes, int) or not 0 <= strokes <= 31:
        issues.append("strokes_out_of_5bit_range")
    if not isinstance(struct_type, int) or not 0 <= struct_type <= 15:
        issues.append("struct_type_out_of_4bit_range")
    if not isinstance(index, int) or not 0 <= index <= 2047:
        issues.append("index_out_of_11bit_range")
    if normalized_structure in STRUCTURE_TYPE_BY_NAME and struct_type != STRUCTURE_TYPE_BY_NAME[normalized_structure]:
        issues.append("struct_type_name_mismatch_after_normalization")
    return ("PASS" if not issues else "REVIEW_REQUIRED", issues)


def source_gate_for(char: str, gf_scores: dict[str, Any]) -> tuple[str, dict[str, Any] | None, list[str]]:
    score_row = gf_scores.get("characters", {}).get(char)
    if not score_row:
        return "EVIDENCE_GAP", None, ["outside_8105_gf0017_score_scope"]
    item_statuses = Counter(item["status"] for item in score_row.get("items", {}).values())
    issues = []
    if item_statuses.get("SOURCE_GAP"):
        issues.append("gf0017_source_gap_present")
    if item_statuses.get("EVIDENCE_GAP"):
        issues.append("gf0017_evidence_gap_present")
    if score_row.get("overall_status") == "REVIEW_REQUIRED":
        issues.append("gf0017_human_review_required")
    if score_row.get("repair_class") == "CNBE32_FIELD_REPAIR_CANDIDATE":
        issues.append("gf0017_cnbe32_field_repair_candidate")
    status = "PASS"
    if "gf0017_evidence_gap_present" in issues:
        status = "EVIDENCE_GAP"
    elif "gf0017_human_review_required" in issues:
        status = "REVIEW_REQUIRED"
    elif "gf0017_source_gap_present" in issues:
        status = "SOURCE_GAP"
    return status, score_row, issues


def classify_row(
    *,
    unicode_status: str,
    source_status: str,
    bitfield_status_value: str,
    all_issues: list[str],
) -> str:
    if unicode_status == "BLOCKER":
        return "BLOCKER"
    if "unknown_structure_label" in all_issues:
        return "BLOCKER"
    if source_status == "EVIDENCE_GAP":
        return "EVIDENCE_GAP"
    if source_status == "REVIEW_REQUIRED":
        return "HUMAN_REVIEW_REQUIRED"
    if bitfield_status_value == "REVIEW_REQUIRED":
        return "CNBE32_REVIEW_REQUIRED"
    if source_status == "SOURCE_GAP":
        return "SOURCE_GAP"
    if all_issues:
        return "PREENCODING_REVIEW_REQUIRED"
    return "PREENCODING_PASS"


def build_outputs(cnbe_input: Path, gf0017_scores_path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    cnbe = load_json(cnbe_input)
    gf_scores = load_json(gf0017_scores_path)
    rows = cnbe.get("characters", [])
    if not isinstance(rows, list):
        raise ValueError("data/cnbe32.json must contain a characters list")

    records: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    source_status_counts: Counter[str] = Counter()
    unicode_status_counts: Counter[str] = Counter()
    bitfield_status_counts: Counter[str] = Counter()
    checkpoint = {
        "batch_id": "cnbe20902-agent-preencoding-test",
        "mode": "scan_all_with_strict_stop_simulation",
        "last_verified_offset": None,
        "blocker_offset": None,
        "blocker_char": None,
        "blocker_unicode": None,
        "failed_gate": None,
        "resume_from": None,
    }
    first_blocker_seen = False
    verified_offset = -1

    seen_chars: set[str] = set()
    seen_codepoints: set[int] = set()
    duplicate_chars: list[str] = []
    duplicate_codepoints: list[str] = []
    raw_structure_counts: Counter[str] = Counter()
    structure_source_counts: Counter[str] = Counter()

    for offset, row in enumerate(rows):
        char = row.get("char")
        codepoint = row.get("unicode")
        if isinstance(char, str):
            if char in seen_chars:
                duplicate_chars.append(char)
            seen_chars.add(char)
        if isinstance(codepoint, int):
            if codepoint in seen_codepoints:
                duplicate_codepoints.append(format_unicode(codepoint))
            seen_codepoints.add(codepoint)

        u_status, u_issues = unicode_alignment(row)
        normalized_structure, structure_source, structure_issues = normalize_structure(row.get("struct_name"))
        raw_structure_counts[str(row.get("struct_name"))] += 1
        structure_source_counts[structure_source] += 1
        b_status, b_issues = bitfield_status(row, normalized_structure)
        source_status, gf_row, source_issues = source_gate_for(char, gf_scores) if isinstance(char, str) else (
            "EVIDENCE_GAP",
            None,
            ["invalid_char_for_source_gate"],
        )

        all_issues = sorted(set(u_issues + structure_issues + b_issues + source_issues))
        agent_status = classify_row(
            unicode_status=u_status,
            source_status=source_status,
            bitfield_status_value=b_status,
            all_issues=all_issues,
        )
        if agent_status not in {"BLOCKER", "EVIDENCE_GAP", "HUMAN_REVIEW_REQUIRED"}:
            verified_offset = offset

        if agent_status == "BLOCKER" and not first_blocker_seen:
            first_blocker_seen = True
            checkpoint.update(
                {
                    "last_verified_offset": verified_offset if verified_offset < offset else offset - 1,
                    "blocker_offset": offset,
                    "blocker_char": char,
                    "blocker_unicode": format_unicode(codepoint) if isinstance(codepoint, int) else None,
                    "failed_gate": "unicode_or_structure_identity",
                    "resume_from": offset,
                }
            )

        record = {
            "offset": offset,
            "char": char,
            "unicode": format_unicode(codepoint) if isinstance(codepoint, int) else None,
            "codepoint": codepoint,
            "agent_status": agent_status,
            "unicode_gate": {
                "status": u_status,
                "issues": u_issues,
            },
            "source_gate": {
                "status": source_status,
                "issues": source_issues,
                "gf0017_score": gf_row.get("score") if gf_row else None,
                "gf0017_status": gf_row.get("overall_status") if gf_row else None,
                "repair_class": gf_row.get("repair_class") if gf_row else None,
            },
            "knowledge_schema_gate": {
                "current_structure_raw": row.get("struct_name"),
                "current_structure_normalized": normalized_structure,
                "structure_source": structure_source,
                "issues": structure_issues,
            },
            "cnbe32_gate": {
                "status": b_status,
                "cnbe_hex": f"0x{row['cnbe']:08X}" if isinstance(row.get("cnbe"), int) else None,
                "radix": row.get("radix"),
                "radix_name": row.get("radix_name"),
                "strokes": row.get("strokes"),
                "struct_type": row.get("struct_type"),
                "index": row.get("index"),
                "issues": b_issues,
            },
            "issues": all_issues,
            "no_write": True,
        }
        records.append(record)
        status_counts[agent_status] += 1
        issue_counts.update(all_issues)
        source_status_counts[source_status] += 1
        unicode_status_counts[u_status] += 1
        bitfield_status_counts[b_status] += 1

    if checkpoint["blocker_offset"] is None:
        checkpoint.update(
            {
                "last_verified_offset": len(rows) - 1,
                "resume_from": len(rows),
            }
        )

    report = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent_skill": "cnbe-hanzi-structure-encoding-agent",
            "batch_audit_skill": "cnbe-gf0017-batch-audit",
            "mode": "read_only_preencoding_pressure_test",
            "source": str(cnbe_input),
            "gf0017_scores": str(gf0017_scores_path),
            "row_count": len(rows),
            "no_write": True,
        },
        "summary": {
            "row_count": len(rows),
            "unique_chars": len(seen_chars),
            "unique_codepoints": len(seen_codepoints),
            "duplicate_chars": len(duplicate_chars),
            "duplicate_codepoints": len(duplicate_codepoints),
            "agent_status_counts": dict(sorted(status_counts.items())),
            "unicode_status_counts": dict(sorted(unicode_status_counts.items())),
            "source_status_counts": dict(sorted(source_status_counts.items())),
            "bitfield_status_counts": dict(sorted(bitfield_status_counts.items())),
            "issue_counts": dict(sorted(issue_counts.items())),
            "raw_structure_counts": dict(sorted(raw_structure_counts.items())),
            "structure_source_counts": dict(sorted(structure_source_counts.items())),
            "first_blocker_offset": checkpoint["blocker_offset"],
            "first_blocker_char": checkpoint["blocker_char"],
            "first_blocker_unicode": checkpoint["blocker_unicode"],
        },
        "checkpoint": checkpoint,
        "samples": {
            "first_rows": records[:20],
            "first_blockers": [record for record in records if record["agent_status"] == "BLOCKER"][:20],
            "first_evidence_gaps": [record for record in records if record["agent_status"] == "EVIDENCE_GAP"][:20],
            "first_source_gaps": [record for record in records if record["agent_status"] == "SOURCE_GAP"][:20],
            "first_cnbe32_review_required": [
                record for record in records if record["agent_status"] == "CNBE32_REVIEW_REQUIRED"
            ][:20],
        },
        "records": records,
    }
    markdown = render_markdown(report)
    return report, checkpoint, markdown


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    checkpoint = report["checkpoint"]
    status_rows = [[key, value] for key, value in summary["agent_status_counts"].items()]
    issue_rows = [[key, value] for key, value in summary["issue_counts"].items()]
    structure_rows = [[key, value] for key, value in summary["raw_structure_counts"].items()]
    blocker_rows = [
        [
            row["offset"],
            row["char"],
            row["unicode"],
            row["agent_status"],
            ", ".join(row["issues"][:8]),
        ]
        for row in report["samples"]["first_blockers"][:10]
    ]
    first_rows = [
        [
            row["offset"],
            row["char"],
            row["unicode"],
            row["agent_status"],
            row["knowledge_schema_gate"]["current_structure_raw"],
            row["knowledge_schema_gate"]["current_structure_normalized"],
            row["source_gate"]["gf0017_score"],
            ", ".join(row["issues"][:6]),
        ]
        for row in report["samples"]["first_rows"][:12]
    ]
    return "\n".join(
        [
            "# CNBE 20,902 Agent Pre-Encoding Test",
            "",
            "## Scope",
            "",
            "This is a read-only pressure test of `cnbe-hanzi-structure-encoding-agent` on the repository's 20,902-row CNBE dataset.",
            "It does not modify CNBE source tables, databases, generated code, releases, or package artifacts.",
            "",
            "## Summary",
            "",
            f"- Rows scanned: {summary['row_count']}",
            f"- Unique chars: {summary['unique_chars']}",
            f"- Unique Unicode code points: {summary['unique_codepoints']}",
            f"- Duplicate chars: {summary['duplicate_chars']}",
            f"- Duplicate code points: {summary['duplicate_codepoints']}",
            f"- First strict blocker offset: {summary['first_blocker_offset']}",
            f"- First strict blocker char: {summary['first_blocker_char']} {summary['first_blocker_unicode']}",
            "",
            "## Agent Status Counts",
            "",
            markdown_table(["Status", "Rows"], status_rows),
            "",
            "## Issue Counts",
            "",
            markdown_table(["Issue", "Rows"], issue_rows),
            "",
            "## Raw Structure Label Counts",
            "",
            markdown_table(["Raw structure label", "Rows"], structure_rows),
            "",
            "## Checkpoint",
            "",
            "```json",
            json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## First Rows",
            "",
            markdown_table(
                ["Offset", "Char", "Unicode", "Status", "Raw structure", "Normalized structure", "GF0017", "Issues"],
                first_rows,
            ),
            "",
            "## First Blockers",
            "",
            markdown_table(["Offset", "Char", "Unicode", "Status", "Issues"], blocker_rows),
            "",
            "## Workflow Problems Found",
            "",
            "1. The 20,902-row repository table uses legacy English structure labels; the agent needs a formal localization layer before production repair.",
            "2. Many rows outside the 8105 GF0017 report have no standard-side score yet, so they must be treated as `EVIDENCE_GAP` rather than encoded automatically.",
            "3. The strict stop-on-blocker rule is useful for production batches, but a diagnostic full-scan mode is also needed to discover systemic issues in one run.",
            "4. Current CNBE32 rows can pass raw bit-range checks while still failing professional pre-encoding gates; this confirms that bit validity is not enough.",
            "",
            "## Next Recommendation",
            "",
            "Add a dedicated checkpointed batch runner with two modes: `strict` for production and `diagnostic-scan` for workflow discovery. Before any repair, create a structure-label localization layer and extend GF0017 scoring beyond the 8105 scope.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cnbe-input", type=Path, default=DEFAULT_CNBE_INPUT)
    parser.add_argument("--gf0017-scores", type=Path, default=DEFAULT_GF0017_SCORES)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--checkpoint-output", type=Path, default=DEFAULT_CHECKPOINT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, checkpoint, markdown = build_outputs(args.cnbe_input, args.gf0017_scores)
    write_json(args.json_output, report)
    write_json(args.checkpoint_output, checkpoint)
    write_text(args.markdown_output, markdown)
    print(f"wrote {args.json_output}")
    print(f"wrote {args.checkpoint_output}")
    print(f"wrote {args.markdown_output}")
    print(f"rows={report['summary']['row_count']}")
    print(f"first_blocker={report['summary']['first_blocker_offset']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
