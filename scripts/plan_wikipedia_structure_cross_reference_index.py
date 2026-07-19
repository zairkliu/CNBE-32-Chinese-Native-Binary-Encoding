#!/usr/bin/env python3
"""Plan a read-only offline-Wikipedia cross-reference index for source gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
DICTIONARY_EXTRACTOR = Path("reports/structure_decomposition_dictionary_gap_extractor.json")

DEFAULT_JSON_OUTPUT = Path("reports/wikipedia_structure_cross_reference_index_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/WIKIPEDIA_STRUCTURE_CROSS_REFERENCE_INDEX_PLAN.md")


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


def inspect_first_json_line(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                item = json.loads(line)
                return {
                    "keys": sorted(item.keys()),
                    "sample_id": item.get("id"),
                    "sample_title": item.get("title"),
                    "sample_tags_present": bool(item.get("tags")),
                    "sample_text_length": len(item.get("text", "")),
                }
    return {}


def build_wikipedia_index_plan() -> dict[str, Any]:
    root = research_root()
    dictionary = load_json(DICTIONARY_EXTRACTOR)
    wiki_path = root / "knowledge/wikipedia-zh-cn-20260501.json"
    no_dictionary_hits = dictionary["summary"]["review_status_counts"]["NO_DICTIONARY_REVIEW_HIT"]
    source_gap_rows = dictionary["summary"]["source_gap_rows"]
    first_line_schema = inspect_first_json_line(wiki_path)
    overall_status = (
        "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_PLAN_READY"
        if dictionary["overall_status"] == "PASS_DICTIONARY_GAP_REVIEW_PACKET_READY"
        and wiki_path.exists()
        and first_line_schema
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_wikipedia_structure_cross_reference_index_plan",
        "overall_status": overall_status,
        "next_workflow_status": "OPTIONAL_WIKI_STREAMING_INDEX_REQUIRES_REVIEW_FORMAL_SCORING_BLOCKED",
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
            "wiki_file_exists": wiki_path.exists(),
            "wiki_file_size_bytes": wiki_path.stat().st_size if wiki_path.exists() else 0,
            "wiki_schema": first_line_schema,
            "source_gap_rows": source_gap_rows,
            "rows_without_dictionary_review_hit": no_dictionary_hits,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "index_design": {
            "index_mode": "streaming_read_only_target_char_index",
            "target_chars_source": "reports/structure_decomposition_dictionary_gap_extractor.json rows with NO_DICTIONARY_REVIEW_HIT",
            "join_key": "char and unicode after Unicode identity verification",
            "search_fields": ["title", "tags", "text"],
            "stored_fields": ["id", "title", "tags", "snippet", "text_len"],
            "max_hits_per_char": 3,
            "evidence_grade": "lowest_tier_cross_reference",
            "forbidden_uses": [
                "do_not_assign_gf0017_points_from_wiki",
                "do_not_claim_national_standard_evidence_from_wiki",
                "do_not_write_cnbe_rows_from_wiki",
                "do_not_modify_source_assets",
            ],
        },
        "decision": {
            "may_implement_read_only_wiki_streaming_index": overall_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Offline Wikipedia can be indexed only as a lowest-tier cross-reference for rows without dictionary hits. "
                "The index should support human review and source discovery, not scoring or encoding."
            ),
        },
        "next_artifacts": [
            "scripts/run_wikipedia_structure_cross_reference_index.py",
            "reports/wikipedia_structure_cross_reference_index.json",
            "reports/WIKIPEDIA_STRUCTURE_CROSS_REFERENCE_INDEX.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Wikipedia Structure Cross-Reference Index Plan",
        "",
        "## Purpose",
        "",
        "This report plans a read-only streaming index over the offline Chinese",
        "Wikipedia corpus for structure/decomposition source gaps that still lack",
        "dictionary or character-origin hits.",
        "",
        "Wiki evidence is lowest-tier cross-reference only. It must not assign",
        "GF0017 scores, modify source assets, write CNBE rows, rebuild databases,",
        "or claim national-standard authority.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Wiki file exists: `{report['summary']['wiki_file_exists']}`",
        f"- Wiki file size bytes: `{report['summary']['wiki_file_size_bytes']}`",
        f"- Rows without dictionary review hit: `{report['summary']['rows_without_dictionary_review_hit']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        "",
        "## Index Design",
        "",
    ]
    for key, value in report["index_design"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_wikipedia_index_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
