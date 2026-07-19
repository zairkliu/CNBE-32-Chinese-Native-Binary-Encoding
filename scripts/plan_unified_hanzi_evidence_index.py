#!/usr/bin/env python3
"""Plan a unified Hanzi evidence index without scoring or encoding rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

IDENTITY_REPORT = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")
SOURCE_AUDIT = Path("reports/cnbe_research_source_audit.json")
MERGE_AUDIT = Path("reports/dictionary_context_knowledge_merge_audit.json")
AGENT_EVIDENCE_JOIN = Path("reports/full_catalog_agent_mapping_evidence_join.json")

BASE_CHARACTER_DATA = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/base_character_data.json")
CNBE_CHARACTER_KNOWLEDGE = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cnbe_character_knowledge.json")
DICTIONARY_CONTEXT_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json")
YUANLIU_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/yuanliu_chars.json")
CIHAI_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cihai_search_index.json")
WIKIPEDIA_CORPUS = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/wikipedia-zh-cn-20260501.json")
UNIHAN2_ARCHIVE = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/Unihan2.zip")
LEGACY_UNIHAN_ARCHIVE = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/Unihan.zip")

DEFAULT_JSON_OUTPUT = Path("reports/unified_hanzi_evidence_index_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/UNIFIED_HANZI_EVIDENCE_INDEX_PLAN.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def json_top_count(path: Path) -> tuple[str, int]:
    data = load_json(path)
    return type(data).__name__, len(data)


def wikipedia_line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def build_plan() -> dict[str, Any]:
    identity = load_json(IDENTITY_REPORT)
    inventory = load_json(KNOWLEDGE_INVENTORY)
    source_audit = load_json(SOURCE_AUDIT)
    merge_audit = load_json(MERGE_AUDIT)
    agent_join = load_json(AGENT_EVIDENCE_JOIN)

    base_type, base_count = json_top_count(BASE_CHARACTER_DATA)
    cnbe_type, cnbe_count = json_top_count(CNBE_CHARACTER_KNOWLEDGE)
    dictionary_type, dictionary_count = json_top_count(DICTIONARY_CONTEXT_INDEX)
    yuanliu_type, yuanliu_count = json_top_count(YUANLIU_INDEX)
    cihai_type, cihai_count = json_top_count(CIHAI_INDEX)
    wiki_count = wikipedia_line_count(WIKIPEDIA_CORPUS)

    checks = {
        "unicode_identity_passed": identity["summary"]["status"] == "PASS",
        "full_catalog_rows_match": identity["summary"]["data_rows"] == 97_686,
        "knowledge_inventory_review_required": inventory["gates"]["encoding_generation_gate"] == "REVIEW_REQUIRED",
        "knowledge_inventory_no_blockers": inventory["gates"]["blocker_count"] == 0,
        "source_audit_passed": source_audit["summary"]["status"] == "PASS",
        "source_audit_review_required": source_audit["summary"]["encoding_generation_gate"] == "REVIEW_REQUIRED",
        "dictionary_merge_audited": merge_audit["overall_status"] == "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED",
        "base_8105_count": base_count == 8_105,
        "cnbe_8105_count": cnbe_count == 8_105,
        "dictionary_context_count": dictionary_count == 49_085,
        "agent_join_ready": agent_join["overall_status"] == "PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED",
        "formal_scoring_blocked": agent_join["summary"]["formal_gf0017_scoring_allowed"] is False,
    }
    status = "PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_unified_hanzi_evidence_index_plan",
        "overall_status": status,
        "next_workflow_status": "UNIFIED_EVIDENCE_INDEX_BUILD_READY_FORMAL_SCORING_BLOCKED",
        "purpose": (
            "Plan a Unicode-keyed evidence graph before any CNBE row repair, "
            "formal GF0017 scoring, or database reconstruction."
        ),
        "authority_boundary": {
            "unicode_first": True,
            "national_standard_core_separate": True,
            "dictionary_context_cross_reference_only": True,
            "wikipedia_lowest_tier_cross_reference_only": True,
            "agent_standard_not_national_standard": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "input_summaries": {
            "full_catalog_rows": identity["summary"]["data_rows"],
            "unique_unicode": identity["summary"]["unique_unicode"],
            "base_character_data": {
                "path": str(BASE_CHARACTER_DATA),
                "top_type": base_type,
                "count": base_count,
                "layer": "national_standard_core",
            },
            "cnbe_character_knowledge": {
                "path": str(CNBE_CHARACTER_KNOWLEDGE),
                "top_type": cnbe_type,
                "count": cnbe_count,
                "layer": "national_standard_core_enriched",
            },
            "dictionary_context_index": {
                "path": str(DICTIONARY_CONTEXT_INDEX),
                "top_type": dictionary_type,
                "count": dictionary_count,
                "layer": "dictionary_cross_reference_context",
            },
            "yuanliu_index": {
                "path": str(YUANLIU_INDEX),
                "top_type": yuanliu_type,
                "count": yuanliu_count,
                "layer": "character_origin_cross_reference",
            },
            "cihai_index": {
                "path": str(CIHAI_INDEX),
                "top_type": cihai_type,
                "count": cihai_count,
                "layer": "dictionary_cross_reference_context",
            },
            "wikipedia_corpus": {
                "path": str(WIKIPEDIA_CORPUS),
                "top_type": "jsonl",
                "count": wiki_count,
                "layer": "lowest_tier_semantic_cross_reference",
            },
            "unihan2_archive": {
                "path": str(UNIHAN2_ARCHIVE),
                "layer": "unicode_identity_cross_reference",
                "status": "canonical_archive_integrity_passed",
            },
            "legacy_unihan_archive": {
                "path": str(LEGACY_UNIHAN_ARCHIVE),
                "layer": "excluded_legacy_artifact",
                "status": "warning_only_when_unihan2_passes",
            },
        },
        "planned_index_schema": {
            "top_level": "object keyed by Unicode label",
            "entry_key": "unicode",
            "entry_fields": [
                "unicode",
                "char",
                "codepoint",
                "catalog_scope",
                "national_standard_core",
                "dictionary_context",
                "origin_context",
                "wiki_context",
                "legacy_cnbe_context",
                "agent_standard_context",
                "gf0017_item_statuses",
                "evidence_gaps",
                "review_status",
                "allowed_next_action",
            ],
            "forbidden_fields_before_later_gates": [
                "gf0017_score",
                "final_structure_label",
                "cnbe32_repair_value",
                "database_write_record",
            ],
        },
        "layer_contract": {
            "national_standard_core": {
                "source_grade": "direct_standard_or_standard_derived",
                "allowed_use": "GF0017 evidence candidate after item-level validation",
                "must_not_mix_with": "dictionary_context_as_direct_standard",
            },
            "dictionary_cross_reference_context": {
                "source_grade": "cross_reference_dictionary_context",
                "allowed_use": "human review, source-gap triage, semantic/context support",
                "must_not_use_as": "national-standard structure authority",
            },
            "wikipedia_lowest_tier_cross_reference": {
                "source_grade": "lowest_tier_cross_reference",
                "allowed_use": "semantic disambiguation and review navigation only",
                "must_not_use_as": "GF0017 scoring evidence",
            },
            "agent_standard_context": {
                "source_grade": "agent_standard_candidate_not_national_standard",
                "allowed_use": "project-level candidate routing after gates",
                "must_not_use_as": "national_standard claim",
            },
        },
        "build_plan": {
            "recommended_script": "scripts/build_unified_hanzi_evidence_index.py",
            "recommended_json_output": "reports/unified_hanzi_evidence_index.json",
            "recommended_markdown_output": "reports/UNIFIED_HANZI_EVIDENCE_INDEX.md",
            "build_mode": "read_only_index_materialization",
            "batching": {
                "primary_key": "unicode",
                "resume_key": "catalog_offset",
                "checkpoint": "reports/unified_hanzi_evidence_index_checkpoint.json",
                "stop_on_unicode_mismatch": True,
            },
        },
        "checks": checks,
        "decision": {
            "may_build_unified_evidence_index": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Source gates are now REVIEW_REQUIRED rather than NO_GO, so a "
                "read-only evidence index may be materialized. Scoring and "
                "database work remain blocked until the index is audited."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unified Hanzi Evidence Index Plan",
        "",
        "## Purpose",
        "",
        report["purpose"],
        "",
        "The planned index is evidence infrastructure only. It does not assign",
        "GF0017 scores, emit final structure labels, repair CNBE rows, or rebuild",
        "databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- May build unified evidence index: `{report['decision']['may_build_unified_evidence_index']}`",
        f"- May start formal GF0017 scoring: `{report['decision']['may_start_formal_gf0017_scoring']}`",
        f"- May write CNBE rows: `{report['decision']['may_write_cnbe_rows']}`",
        f"- May rebuild database: `{report['decision']['may_rebuild_database']}`",
        "",
        "## Input Layers",
        "",
        "| Layer | Count | Role |",
        "|---|---:|---|",
    ]
    for key, value in report["input_summaries"].items():
        if isinstance(value, dict) and "layer" in value:
            lines.append(f"| `{key}` | {value.get('count', 'n/a')} | {value['layer']} |")
    lines.extend(["", "## Planned Entry Fields", ""])
    for field in report["planned_index_schema"]["entry_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "## Forbidden Before Later Gates", ""])
    for field in report["planned_index_schema"]["forbidden_fields_before_later_gates"]:
        lines.append(f"- `{field}`")
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    if report["overall_status"] != "PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
