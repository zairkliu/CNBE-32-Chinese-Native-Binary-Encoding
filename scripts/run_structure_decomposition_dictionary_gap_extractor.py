#!/usr/bin/env python3
"""Extract read-only dictionary review packets for structure source gaps."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
SOURCE_GAP_PLAN = Path("reports/structure_decomposition_source_gap_resolution_plan.json")
PARSER_OUTPUT = Path("reports/structure_decomposition_evidence_parser.json")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_dictionary_gap_extractor.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_DICTIONARY_GAP_EXTRACTOR.md")

EXPECTED_SOURCE_GAP_ROWS = 85_001
CONTEXT_LIMIT = 5
SAMPLE_LIMIT = 80


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def research_root() -> Path:
    config = load_json(SOURCE_CONFIG)
    root = Path(config["source_root"])
    if not root.exists():
        raise FileNotFoundError(f"research source root not found: {root}")
    return root


def source_gap_records() -> list[dict[str, Any]]:
    parser = load_json(PARSER_OUTPUT)
    return [
        record
        for record in parser["row_records"]
        if record["evidence_status"] == "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP"
    ]


def compact_yuanliu_record(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "radical": record.get("radical"),
        "radix": record.get("radix"),
        "decomposition": record.get("decomposition"),
        "struct_type": record.get("struct_type"),
        "struct_name": record.get("struct_name"),
        "etym_type": record.get("etym_type"),
        "etym_hint": record.get("etym_hint"),
        "etym_phonetic": record.get("etym_phonetic"),
        "etym_semantic": record.get("etym_semantic"),
        "pinyin": record.get("pinyin"),
        "definition": record.get("definition"),
    }


def build_review_record(
    source_gap: dict[str, Any],
    yuanliu: dict[str, Any],
    cihai: dict[str, list[str]],
    definitions: dict[str, Any],
) -> dict[str, Any]:
    char = source_gap["char"]
    yuanliu_record = compact_yuanliu_record(yuanliu.get(char))
    cihai_contexts = cihai.get(char, [])[:CONTEXT_LIMIT]
    definition_record = definitions.get(char)
    source_hits = {
        "yuanliu": yuanliu_record is not None,
        "cihai": bool(cihai_contexts),
        "definitions_index": definition_record is not None,
    }
    if yuanliu_record and cihai_contexts:
        review_status = "DICTIONARY_AND_YUANLIU_REVIEW_READY"
    elif yuanliu_record:
        review_status = "YUANLIU_REVIEW_READY"
    elif cihai_contexts or definition_record:
        review_status = "DICTIONARY_CONTEXT_REVIEW_READY"
    else:
        review_status = "NO_DICTIONARY_REVIEW_HIT"

    return {
        "offset": source_gap["offset"],
        "worksheet_row": source_gap["worksheet_row"],
        "char": char,
        "unicode": source_gap["unicode"],
        "unicode_block": source_gap["unicode_block"],
        "source_gap_failure_codes": source_gap["failure_codes"],
        "review_status": review_status,
        "source_hits": source_hits,
        "yuanliu": yuanliu_record,
        "cihai_contexts": cihai_contexts,
        "definition_context": definition_record,
        "source_grade": "cross_reference",
        "can_assign_points": False,
        "score": None,
        "score_status": "NOT_SCORED_DICTIONARY_REVIEW_ONLY",
    }


def build_dictionary_gap_report() -> dict[str, Any]:
    root = research_root()
    plan = load_json(SOURCE_GAP_PLAN)
    records = source_gap_records()
    yuanliu = load_json(root / "knowledge/yuanliu_chars.json")
    cihai = load_json(root / "knowledge/structured/cihai_search_index.json")
    definitions = load_json(root / "knowledge/structured/definitions_index.json")

    review_records = [
        build_review_record(record, yuanliu, cihai, definitions)
        for record in records
    ]
    status_counts = Counter(record["review_status"] for record in review_records)
    source_hit_counts = Counter()
    for record in review_records:
        for source, hit in record["source_hits"].items():
            if hit:
                source_hit_counts[source] += 1

    overall_status = (
        "PASS_DICTIONARY_GAP_REVIEW_PACKET_READY"
        if plan["overall_status"] == "PASS_STRUCTURE_SOURCE_GAP_RESOLUTION_PLAN_READY"
        and len(review_records) == EXPECTED_SOURCE_GAP_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_structure_decomposition_dictionary_gap_extractor",
        "overall_status": overall_status,
        "next_workflow_status": "DICTIONARY_REVIEW_PACKET_READY_WIKI_INDEX_PLAN_OPTIONAL_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "source_gap_rows": len(review_records),
            "review_status_counts": dict(sorted(status_counts.items())),
            "source_hit_counts": dict(sorted(source_hit_counts.items())),
            "context_limit_per_char": CONTEXT_LIMIT,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "samples": {
            "review_hits": [
                record
                for record in review_records
                if record["review_status"] != "NO_DICTIONARY_REVIEW_HIT"
            ][:SAMPLE_LIMIT],
            "no_review_hit": [
                {
                    "offset": record["offset"],
                    "worksheet_row": record["worksheet_row"],
                    "char": record["char"],
                    "unicode": record["unicode"],
                    "unicode_block": record["unicode_block"],
                    "source_gap_failure_codes": record["source_gap_failure_codes"],
                }
                for record in review_records
                if record["review_status"] == "NO_DICTIONARY_REVIEW_HIT"
            ][:SAMPLE_LIMIT],
        },
        "row_records": review_records,
        "decision": {
            "may_start_human_review_packet": overall_status.startswith("PASS"),
            "may_plan_wikipedia_streaming_index": overall_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Dictionary and character-origin review packets are available for the small subset of source-gap rows "
                "with hits. Remaining rows still need source expansion or an optional offline-Wiki streaming index plan."
            ),
        },
        "next_artifacts": [
            "scripts/plan_wikipedia_structure_cross_reference_index.py",
            "reports/wikipedia_structure_cross_reference_index_plan.json",
            "reports/WIKIPEDIA_STRUCTURE_CROSS_REFERENCE_INDEX_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Dictionary Gap Extractor",
        "",
        "## Purpose",
        "",
        "This report extracts read-only review context from 汉字源流 and 辞海",
        "indexes for Phase 1 structure/decomposition source gaps.",
        "",
        "It does not assign GF0017 scores, modify source assets, write CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Source-gap rows: `{report['summary']['source_gap_rows']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        "",
        "## Review Status Counts",
        "",
    ]
    for status, count in report["summary"]["review_status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Source Hit Counts", ""])
    for source, count in report["summary"]["source_hit_counts"].items():
        lines.append(f"- `{source}`: {count}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_dictionary_gap_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
