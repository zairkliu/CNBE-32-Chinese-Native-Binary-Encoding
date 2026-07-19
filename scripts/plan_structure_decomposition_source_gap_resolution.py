#!/usr/bin/env python3
"""Plan source-gap resolution for Phase 1 structure/decomposition evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
REVIEW_PLAN = Path("reports/structure_decomposition_evidence_review.json")
PARSER_OUTPUT = Path("reports/structure_decomposition_evidence_parser.json")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_source_gap_resolution_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_SOURCE_GAP_RESOLUTION_PLAN.md")

EXPECTED_SOURCE_GAP_ROWS = 85_001
SAMPLE_LIMIT = 120


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


def load_optional_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = load_json(path)
    return data if isinstance(data, dict) else {}


def source_gap_records() -> list[dict[str, Any]]:
    parser = load_json(PARSER_OUTPUT)
    return [
        record
        for record in parser["row_records"]
        if record["evidence_status"] == "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP"
    ]


def sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "unicode_block": record["unicode_block"],
            "failure_codes": record["failure_codes"],
        }
        for record in records[:SAMPLE_LIMIT]
    ]


def build_resolution_plan() -> dict[str, Any]:
    root = research_root()
    review = load_json(REVIEW_PLAN)
    records = source_gap_records()

    yuanliu = load_optional_dict(root / "knowledge/yuanliu_chars.json")
    cihai = load_optional_dict(root / "knowledge/structured/cihai_search_index.json")
    definitions = load_optional_dict(root / "knowledge/structured/definitions_index.json")

    wiki_path = root / "knowledge/wikipedia-zh-cn-20260501.json"
    yuanliu_hits = [record for record in records if record["char"] in yuanliu]
    cihai_hits = [record for record in records if record["char"] in cihai]
    definitions_hits = [record for record in records if record["char"] in definitions]

    source_hit_counts = {
        "hanzi_yuanliu_chars": len(yuanliu_hits),
        "cihai_search_index": len(cihai_hits),
        "definitions_index": len(definitions_hits),
        "wikipedia_offline_file_available": int(wiki_path.exists()),
    }
    block_counts = Counter(record["unicode_block"] for record in records)

    resolution_phases = [
        {
            "phase": 1,
            "phase_name": "authoritative_standard_recheck",
            "source_tier": "national_standard_or_standard_derived",
            "input_sources": [
                "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
            ],
            "purpose": "confirm the source gap is real before adding dictionary context",
            "eligible_rows": len(records),
            "can_assign_points": False,
            "writes_source_assets": False,
        },
        {
            "phase": 2,
            "phase_name": "hanzi_yuanliu_structure_clue_extraction",
            "source_tier": "dictionary_or_character_origin_cross_reference",
            "input_sources": [
                "knowledge/yuanliu_chars.json",
                "source/13-汉字源流大典/汉字源流大典 钱中立主编 9典可搜索检字 中国语言文学学科建设文库.md",
            ],
            "purpose": "extract etymology, definition, decomposition, and structure clues for human review",
            "eligible_rows": len(yuanliu_hits),
            "can_assign_points": False,
            "writes_source_assets": False,
        },
        {
            "phase": 3,
            "phase_name": "cihai_definition_review_packet",
            "source_tier": "dictionary_cross_reference",
            "input_sources": [
                "knowledge/structured/cihai_search_index.json",
                "knowledge/structured/definitions_index.json",
                "source/10-辞海/",
            ],
            "purpose": "provide dictionary contexts for meaning and usage; do not derive final structure labels from definitions alone",
            "eligible_rows": len(set(record["char"] for record in cihai_hits + definitions_hits)),
            "can_assign_points": False,
            "writes_source_assets": False,
        },
        {
            "phase": 4,
            "phase_name": "offline_wikipedia_lowest_tier_cross_reference",
            "source_tier": "encyclopedia_lowest_tier_cross_reference",
            "input_sources": ["knowledge/wikipedia-zh-cn-20260501.json"],
            "purpose": "use only after dictionary and standard evidence is insufficient; requires a streaming Unicode-keyed index before row-level use",
            "eligible_rows": len(records) if wiki_path.exists() else 0,
            "can_assign_points": False,
            "writes_source_assets": False,
            "requires_new_read_only_indexer": True,
        },
        {
            "phase": 5,
            "phase_name": "human_review_and_rule_learning_packet",
            "source_tier": "agent_standard_review",
            "input_sources": [
                "reports/structure_decomposition_evidence_parser.json",
                "reports/structure_decomposition_evidence_review.json",
                "reports/structure_decomposition_source_gap_resolution_plan.json",
            ],
            "purpose": "prepare review packets and identify 8105-aligned rule-learning candidates without writing CNBE rows",
            "eligible_rows": len(records),
            "can_assign_points": False,
            "writes_source_assets": False,
        },
    ]

    overall_status = (
        "PASS_STRUCTURE_SOURCE_GAP_RESOLUTION_PLAN_READY"
        if review["overall_status"] == "PASS_PHASE_1_EVIDENCE_REVIEW_PLAN_READY"
        and len(records) == EXPECTED_SOURCE_GAP_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_structure_decomposition_source_gap_resolution_plan",
        "overall_status": overall_status,
        "next_workflow_status": "READ_ONLY_SOURCE_GAP_EXTRACTORS_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "source_policy": {
            "national_standards": "direct evidence for standard fields when present",
            "hanzi_yuanliu": "character-origin and decomposition clue source for review, not direct national-standard authority",
            "cihai": "dictionary meaning and usage context for review, not direct structure authority",
            "wikipedia_offline": "lowest-tier cross-reference only after standards and dictionaries; never direct scoring authority",
            "llm_memory": "not an evidence source",
        },
        "summary": {
            "source_gap_rows": len(records),
            "source_gap_unicode_block_counts": dict(sorted(block_counts.items())),
            "source_hit_counts": source_hit_counts,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "resolution_phases": resolution_phases,
        "samples": {
            "source_gap_rows": sample(records),
            "yuanliu_hits": sample(yuanliu_hits),
            "cihai_hits": sample(cihai_hits),
            "definitions_hits": sample(definitions_hits),
        },
        "decision": {
            "may_start_read_only_yuanliu_extractor": overall_status.startswith("PASS"),
            "may_start_read_only_cihai_review_packet": overall_status.startswith("PASS"),
            "may_start_read_only_wikipedia_index_plan": overall_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Source-gap resolution can proceed through read-only extractors and review packets. "
                "Dictionaries and Wikipedia may enrich evidence review, but they do not authorize formal scoring or CNBE row writes."
            ),
        },
        "next_artifacts": [
            "scripts/run_structure_decomposition_yuanliu_gap_extractor.py",
            "reports/structure_decomposition_yuanliu_gap_extractor.json",
            "reports/STRUCTURE_DECOMPOSITION_YUANLIU_GAP_EXTRACTOR.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Source-Gap Resolution Plan",
        "",
        "## Purpose",
        "",
        "This report plans how the Agent should resolve Phase 1 structure and",
        "decomposition source gaps using standards first, then dictionary and",
        "character-origin evidence, and only then offline Wiki as the lowest-tier",
        "cross-reference.",
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
        "## Source Hit Counts",
        "",
    ]
    for source, count in report["summary"]["source_hit_counts"].items():
        lines.append(f"- `{source}`: {count}")
    lines.extend(["", "## Source Policy", ""])
    for key, value in report["source_policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Resolution Phases", ""])
    for phase in report["resolution_phases"]:
        lines.append(
            f"- Phase {phase['phase']} `{phase['phase_name']}`: {phase['eligible_rows']} eligible rows; "
            f"tier `{phase['source_tier']}`"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_resolution_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
