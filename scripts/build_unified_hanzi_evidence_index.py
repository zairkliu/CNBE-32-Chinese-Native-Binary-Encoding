#!/usr/bin/env python3
"""Build a read-only Unicode-keyed Hanzi evidence index.

This index is evidence infrastructure only. It deliberately does not assign
GF0017 points, emit final structure labels, repair CNBE rows, or rebuild any
database.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

IDENTITY_REPORT = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
SOURCE_JOIN_BATCH = Path("reports/full_catalog_gf0017_source_join_batch.json")
AGENT_EVIDENCE_JOIN = Path("reports/full_catalog_agent_mapping_evidence_join.json")
AGENT_FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")
WIKI_CROSS_REFERENCE = Path("reports/wikipedia_structure_cross_reference_index.json")
DICTIONARY_GAP_EXTRACTOR = Path("reports/structure_decomposition_dictionary_gap_extractor.json")
PHASE1_PARSER = Path("reports/structure_decomposition_evidence_parser.json")
PLAN_REPORT = Path("reports/unified_hanzi_evidence_index_plan.json")

BASE_CHARACTER_DATA = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/base_character_data.json")
CNBE_CHARACTER_KNOWLEDGE = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cnbe_character_knowledge.json")
DICTIONARY_CONTEXT_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json")
YUANLIU_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/yuanliu_chars.json")
CIHAI_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cihai_search_index.json")

DEFAULT_JSON_OUTPUT = Path("reports/unified_hanzi_evidence_index.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/UNIFIED_HANZI_EVIDENCE_INDEX.md")

EXPECTED_FULL_CATALOG_ROWS = 97_686
EXPECTED_8105_ROWS = 8_105
PREVIEW_LIMIT = 2
TEXT_PREVIEW_CHARS = 180
SAMPLE_UNICODES = ["U+4E00", "U+5BB6", "U+946B", "U+3400", "U+3401", "U+323AF"]

FORBIDDEN_OUTPUTS = [
    "gf0017_score",
    "final_structure_label",
    "cnbe32_repair_value",
    "database_write_record",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def row_map(report: dict[str, Any], field: str = "row_records") -> dict[str, dict[str, Any]]:
    return {row["unicode"]: row for row in report.get(field, [])}


def text_preview(value: Any, limit: int = TEXT_PREVIEW_CHARS) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return text[:limit]


def compact_source_ids(entries: list[dict[str, Any]]) -> list[str]:
    source_ids = []
    for entry in entries:
        source_id = entry.get("source_id")
        if source_id and source_id not in source_ids:
            source_ids.append(source_id)
    return source_ids


def dictionary_context(char: str, dictionary_index: dict[str, Any]) -> dict[str, Any]:
    record = dictionary_index.get(char)
    entries = record.get("dictionary_context_entries", []) if isinstance(record, dict) else []
    previews = [
        {
            "source_id": entry.get("source_id"),
            "source_grade": entry.get("source_grade", "cross_reference_dictionary_context"),
            "content_preview": text_preview(entry.get("content_preview") or entry.get("content")),
        }
        for entry in entries[:PREVIEW_LIMIT]
    ]
    return {
        "source_grade": "cross_reference_dictionary_context",
        "has_context": bool(entries),
        "source_count": len(compact_source_ids(entries)),
        "source_ids": compact_source_ids(entries),
        "preview_count": len(previews),
        "content_previews": previews,
        "can_assign_points": False,
    }


def origin_context(char: str, yuanliu_index: dict[str, Any]) -> dict[str, Any]:
    record = yuanliu_index.get(char)
    if not isinstance(record, dict):
        return {
            "source_grade": "cross_reference_character_origin",
            "has_context": False,
            "can_assign_points": False,
        }
    return {
        "source_grade": "cross_reference_character_origin",
        "has_context": True,
        "radical": record.get("radical"),
        "radix": record.get("radix"),
        "decomposition": record.get("decomposition"),
        "raw_structure_name": record.get("struct_name"),
        "raw_structure_type": record.get("struct_type"),
        "pinyin": record.get("pinyin"),
        "definition_preview": text_preview(record.get("definition")),
        "can_assign_points": False,
    }


def cihai_context(char: str, cihai_index: dict[str, Any]) -> dict[str, Any]:
    snippets = cihai_index.get(char, [])
    if not isinstance(snippets, list):
        snippets = []
    return {
        "source_grade": "cross_reference_dictionary_context",
        "has_context": bool(snippets),
        "hit_count": len(snippets),
        "snippet_previews": [text_preview(snippet) for snippet in snippets[:PREVIEW_LIMIT]],
        "can_assign_points": False,
    }


def wiki_context(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "source_grade": "lowest_tier_cross_reference",
            "wiki_review_status": "NO_WIKI_CROSS_REFERENCE_ROW",
            "hit_count": 0,
            "hit_previews": [],
            "can_assign_points": False,
        }
    hits = row.get("wiki_hits", [])
    previews = [
        {
            "title": hit.get("title"),
            "field": hit.get("field"),
            "source_grade": hit.get("source_grade", "lowest_tier_cross_reference"),
            "snippet": text_preview(hit.get("snippet")),
        }
        for hit in hits[:PREVIEW_LIMIT]
    ]
    return {
        "source_grade": "lowest_tier_cross_reference",
        "wiki_review_status": row.get("wiki_review_status"),
        "hit_count": len(hits),
        "hit_previews": previews,
        "can_assign_points": False,
    }


def national_standard_core(
    char: str,
    base_index: dict[str, Any],
    cnbe_knowledge_by_char: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    base = base_index.get(char)
    enriched = cnbe_knowledge_by_char.get(char)
    if not isinstance(base, dict):
        return {
            "status": "OUTSIDE_8105_NO_DIRECT_NATIONAL_STANDARD_CORE_ROW",
            "source_grade": "unresolved_for_national_standard_core",
            "can_assign_points": False,
        }
    return {
        "status": "JOINED_8105_NATIONAL_STANDARD_CORE",
        "source_grade": "standard_derived",
        "level": base.get("level") or (enriched or {}).get("level"),
        "standard_rank": base.get("standard_rank") or (enriched or {}).get("standard_rank"),
        "stroke_count": base.get("stroke_count") or (enriched or {}).get("stroke_count"),
        "stroke_order": base.get("stroke_order") or (enriched or {}).get("stroke_order"),
        "stroke_order_str": base.get("stroke_order_str") or (enriched or {}).get("stroke_order_str"),
        "has_dictionary_entry": bool((enriched or {}).get("has_dictionary_entry")),
        "has_wiki_entry": bool((enriched or {}).get("has_wiki_entry")),
        "can_assign_points": False,
    }


def legacy_cnbe_context(source_join_row: dict[str, Any] | None, source_join_profile_id: str | None) -> dict[str, Any]:
    if not source_join_row:
        return {
            "join_status": "NO_LEGACY_SOURCE_JOIN_ROW",
            "score": None,
            "score_status": "NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY",
        }
    return {
        "join_status": source_join_row.get("join_status"),
        "standard_level": source_join_row.get("standard_level"),
        "gf0017_source_item_statuses_profile_id": source_join_profile_id,
        "issues": source_join_row.get("issues", []),
        "score": None,
        "score_status": "NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY",
    }


def compact_agent_item_statuses(agent_row: dict[str, Any] | None) -> dict[str, str]:
    if not agent_row:
        return {}
    statuses = agent_row.get("gf0017_item_evidence_statuses", {})
    return {
        item: status.get("evidence_status", "UNKNOWN")
        for item, status in statuses.items()
        if isinstance(status, dict)
    }


def agent_standard_context(
    agent_row: dict[str, Any] | None,
    feature_row: dict[str, Any] | None,
    phase1_row: dict[str, Any] | None,
    dictionary_gap_row: dict[str, Any] | None,
    feature_profile_id: str | None,
    agent_evidence_profile_id: str | None,
    evidence_gap_profile_id: str,
) -> dict[str, Any]:
    return {
        "standard_level": (
            (agent_row or {}).get("standard_level")
            or (feature_row or {}).get("standard_level")
            or (phase1_row or {}).get("standard_level")
        ),
        "row_evidence_status": (agent_row or {}).get("row_evidence_status"),
        "review_queue": (feature_row or {}).get("review_queue"),
        "review_prior": (feature_row or {}).get("review_prior"),
        "feature_flags_profile_id": feature_profile_id,
        "phase1_evidence_status": (phase1_row or {}).get("evidence_status"),
        "phase1_source_grade": (phase1_row or {}).get("source_grade"),
        "phase1_structure_rule": (phase1_row or {}).get("structure_rule"),
        "phase1_raw_structure_label_not_final": (phase1_row or {}).get("structure_label"),
        "dictionary_gap_review_status": (dictionary_gap_row or {}).get("review_status"),
        "source_gap_profile_id": evidence_gap_profile_id,
        "item_evidence_profile_id": agent_evidence_profile_id,
        "can_assign_points": False,
        "can_emit_final_structure_label": False,
    }


def evidence_gaps(
    source_join_row: dict[str, Any] | None,
    agent_row: dict[str, Any] | None,
    feature_row: dict[str, Any] | None,
    phase1_row: dict[str, Any] | None,
    dictionary_gap_row: dict[str, Any] | None,
    wiki_row: dict[str, Any] | None,
) -> list[str]:
    gaps: set[str] = set()
    for item, status in (source_join_row or {}).get("gf0017_source_item_statuses", {}).items():
        if status in {"SOURCE_GAP", "SOURCE_EVIDENCE_REQUIRED", "EVIDENCE_GAP"}:
            gaps.add(f"{item}:{status}")
    for item, status in compact_agent_item_statuses(agent_row).items():
        if status in {"SOURCE_GAP_NOT_SCORABLE", "ROW_LEVEL_EVIDENCE_JOIN_PENDING"}:
            gaps.add(f"{item}:{status}")
    gaps.update((feature_row or {}).get("source_gap_failure_codes", []))
    gaps.update((phase1_row or {}).get("failure_codes", []))
    gaps.update((dictionary_gap_row or {}).get("source_gap_failure_codes", []))
    if dictionary_gap_row and dictionary_gap_row.get("review_status") == "NO_DICTIONARY_REVIEW_HIT":
        gaps.add("NO_DICTIONARY_REVIEW_HIT")
    if wiki_row and wiki_row.get("wiki_review_status") == "NO_WIKI_CROSS_REFERENCE_HIT":
        gaps.add("NO_WIKI_CROSS_REFERENCE_HIT")
    return sorted(gaps)


def review_status_for(scope: str, gaps: list[str], dictionary: dict[str, Any], wiki: dict[str, Any]) -> str:
    if scope == "8105_core":
        return "READY_FOR_8105_CORE_ITEM_LEVEL_REVIEW"
    if dictionary["has_context"] or wiki["hit_count"] > 0:
        return "OUTSIDE_8105_REVIEW_CONTEXT_AVAILABLE"
    if gaps:
        return "OUTSIDE_8105_SOURCE_GAP_REVIEW_REQUIRED"
    return "OUTSIDE_8105_AGENT_STANDARD_REVIEW_REQUIRED"


def compact_context_ref(kind: str, unicode_label: str, detail: dict[str, Any], hit_key: str = "has_context") -> dict[str, Any]:
    has_context = bool(detail.get(hit_key))
    compact = {
        "has_context": has_context,
        "detail_ref": f"{kind}:{unicode_label}" if has_context else None,
        "can_assign_points": False,
    }
    for key in ("source_grade", "source_count", "preview_count", "hit_count", "wiki_review_status"):
        if key in detail:
            compact[key] = detail[key]
    return compact


def profile_id_for(prefix: str, value: Any, profiles: dict[str, Any], registry: dict[str, str]) -> str:
    key = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    existing = registry.get(key)
    if existing:
        return existing
    profile_id = f"{prefix}_{len(registry) + 1:04d}"
    registry[key] = profile_id
    profiles[profile_id] = value
    return profile_id


def build_unified_index() -> dict[str, Any]:
    identity = load_json(IDENTITY_REPORT)
    source_join_by_unicode = row_map(load_json(SOURCE_JOIN_BATCH))
    agent_join_by_unicode = row_map(load_json(AGENT_EVIDENCE_JOIN))
    feature_by_unicode = row_map(load_json(AGENT_FEATURE_TABLE))
    wiki_by_unicode = row_map(load_json(WIKI_CROSS_REFERENCE))
    dictionary_gap_by_unicode = row_map(load_json(DICTIONARY_GAP_EXTRACTOR))
    phase1_by_unicode = row_map(load_json(PHASE1_PARSER))
    plan = load_json(PLAN_REPORT)

    base_index = load_json(BASE_CHARACTER_DATA)
    cnbe_knowledge_rows = load_json(CNBE_CHARACTER_KNOWLEDGE)
    cnbe_knowledge_by_char = {row["char"]: row for row in cnbe_knowledge_rows}
    dictionary_index = load_json(DICTIONARY_CONTEXT_INDEX)
    yuanliu_index = load_json(YUANLIU_INDEX)
    cihai_index = load_json(CIHAI_INDEX)

    index: dict[str, list[Any]] = {}
    sample_entries: dict[str, dict[str, Any]] = {}
    scope_counts: Counter[str] = Counter()
    review_status_counts: Counter[str] = Counter()
    dictionary_hit_count = 0
    origin_hit_count = 0
    cihai_hit_count = 0
    wiki_hit_count = 0
    entries_with_evidence_gaps = 0
    profiles: dict[str, dict[str, Any]] = {
        "source_join_item_statuses": {},
        "agent_evidence_item_statuses": {},
        "evidence_gaps": {},
        "feature_flags": {},
        "forbidden_outputs": {"forbidden_outputs_0001": FORBIDDEN_OUTPUTS},
    }
    profile_registries: dict[str, dict[str, str]] = {
        "source_join_item_statuses": {},
        "agent_evidence_item_statuses": {},
        "evidence_gaps": {},
        "feature_flags": {},
    }

    for identity_row in identity["row_identities"]:
        char = identity_row["char"]
        unicode_label = identity_row["unicode"]
        source_join_row = source_join_by_unicode.get(unicode_label)
        agent_row = agent_join_by_unicode.get(unicode_label)
        feature_row = feature_by_unicode.get(unicode_label)
        wiki_row = wiki_by_unicode.get(unicode_label)
        dictionary_gap_row = dictionary_gap_by_unicode.get(unicode_label)
        phase1_row = phase1_by_unicode.get(unicode_label)

        scope = "8105_core" if char in base_index else "outside_8105_agent_candidate"
        dictionary = dictionary_context(char, dictionary_index)
        origin = origin_context(char, yuanliu_index)
        cihai = cihai_context(char, cihai_index)
        wiki = wiki_context(wiki_row)
        national_core = national_standard_core(char, base_index, cnbe_knowledge_by_char)
        gaps = evidence_gaps(source_join_row, agent_row, feature_row, phase1_row, dictionary_gap_row, wiki_row)
        source_join_statuses = (source_join_row or {}).get("gf0017_source_item_statuses", {})
        agent_evidence_statuses = compact_agent_item_statuses(agent_row)
        feature_flags = (feature_row or {}).get("feature_flags", {})
        source_join_profile_id = profile_id_for(
            "source_join",
            source_join_statuses,
            profiles["source_join_item_statuses"],
            profile_registries["source_join_item_statuses"],
        )
        agent_evidence_profile_id = profile_id_for(
            "agent_evidence",
            agent_evidence_statuses,
            profiles["agent_evidence_item_statuses"],
            profile_registries["agent_evidence_item_statuses"],
        )
        evidence_gap_profile_id = profile_id_for(
            "evidence_gap",
            gaps,
            profiles["evidence_gaps"],
            profile_registries["evidence_gaps"],
        )
        feature_profile_id = profile_id_for(
            "feature_flags",
            feature_flags,
            profiles["feature_flags"],
            profile_registries["feature_flags"],
        )
        review_status = review_status_for(scope, gaps, dictionary, wiki)

        scope_counts[scope] += 1
        review_status_counts[review_status] += 1
        dictionary_hit_count += int(dictionary["has_context"])
        origin_hit_count += int(origin["has_context"])
        cihai_hit_count += int(cihai["has_context"])
        wiki_hit_count += int(wiki["hit_count"] > 0)
        entries_with_evidence_gaps += int(bool(gaps))

        detailed_entry = {
            "unicode": unicode_label,
            "char": char,
            "codepoint": identity_row["codepoint"],
            "catalog_offset": identity_row["sequence"],
            "worksheet_row": identity_row["worksheet_row"],
            "catalog_scope": scope,
            "national_standard_core": {
                "status": national_core["status"],
                "source_grade": national_core["source_grade"],
                "detail_ref": f"national_standard_core:{unicode_label}"
                if national_core["status"] == "JOINED_8105_NATIONAL_STANDARD_CORE"
                else None,
                "can_assign_points": False,
            },
            "dictionary_context": compact_context_ref("dictionary_context", unicode_label, dictionary),
            "origin_context": compact_context_ref("origin_context", unicode_label, origin),
            "cihai_context": compact_context_ref("cihai_context", unicode_label, cihai),
            "wiki_context": compact_context_ref("wiki_context", unicode_label, wiki, hit_key="hit_count"),
            "legacy_cnbe_context": legacy_cnbe_context(source_join_row, source_join_profile_id),
            "agent_standard_context": agent_standard_context(
                agent_row,
                feature_row,
                phase1_row,
                dictionary_gap_row,
                feature_profile_id,
                agent_evidence_profile_id,
                evidence_gap_profile_id,
            ),
            "gf0017_item_statuses": {
                "source_join_profile_id": source_join_profile_id,
                "agent_evidence_profile_id": agent_evidence_profile_id,
            },
            "evidence_gaps": {
                "profile_id": evidence_gap_profile_id,
                "gap_count": len(gaps),
                "codes_preview": gaps[:5],
            },
            "review_status": review_status,
            "allowed_next_action": "audit_unified_evidence_index_only",
            "forbidden_outputs_profile_id": "forbidden_outputs_0001",
            "score": None,
            "score_status": "NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY",
        }
        if unicode_label in SAMPLE_UNICODES:
            sample_entries[unicode_label] = detailed_entry
        index[unicode_label] = [
            char,
            identity_row["codepoint"],
            identity_row["sequence"],
            identity_row["worksheet_row"],
            scope,
            review_status,
            source_join_profile_id,
            agent_evidence_profile_id,
            evidence_gap_profile_id,
            feature_profile_id,
            dictionary["source_count"],
            origin["has_context"],
            cihai["hit_count"],
            wiki["hit_count"],
        ]

    status = "PASS_UNIFIED_EVIDENCE_INDEX_BUILT"
    checks = {
        "plan_ready": plan["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY",
        "total_entries_match": len(index) == EXPECTED_FULL_CATALOG_ROWS,
        "unicode_identity_unique": len(index) == identity["summary"]["unique_unicode"],
        "core_8105_count_match": scope_counts["8105_core"] == EXPECTED_8105_ROWS,
        "outside_count_match": scope_counts["outside_8105_agent_candidate"] == EXPECTED_FULL_CATALOG_ROWS - EXPECTED_8105_ROWS,
        "score_values_assigned_zero": True,
        "final_structure_labels_emitted_zero": True,
        "cnbe_row_write_records_zero": True,
    }
    if not all(checks.values()):
        status = "BLOCKED_UNIFIED_EVIDENCE_INDEX_BUILD_FAILED"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_unified_hanzi_evidence_index",
        "overall_status": status,
        "next_workflow_status": "UNIFIED_EVIDENCE_INDEX_AUDIT_REQUIRED_FORMAL_SCORING_BLOCKED",
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
        "summary": {
            "total_entries": len(index),
            "catalog_scope_counts": dict(scope_counts),
            "review_status_counts": dict(review_status_counts),
            "entries_with_dictionary_context": dictionary_hit_count,
            "entries_with_origin_context": origin_hit_count,
            "entries_with_cihai_context": cihai_hit_count,
            "entries_with_wiki_context": wiki_hit_count,
            "entries_with_evidence_gaps": entries_with_evidence_gaps,
            "profile_counts": {
                key: len(value)
                for key, value in profiles.items()
            },
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_gf0017_scoring_allowed": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
        },
        "index_schema": [
            "char",
            "codepoint",
            "catalog_offset",
            "worksheet_row",
            "catalog_scope",
            "review_status",
            "source_join_profile_id",
            "agent_evidence_profile_id",
            "evidence_gap_profile_id",
            "feature_flags_profile_id",
            "dictionary_source_count",
            "has_origin_context",
            "cihai_hit_count",
            "wiki_hit_count",
        ],
        "checks": checks,
        "profiles": profiles,
        "samples": sample_entries,
        "index": index,
        "decision": {
            "may_audit_unified_evidence_index": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The unified index links available evidence by Unicode. It is still "
                "review infrastructure, so formal scores, final labels, CNBE row "
                "writes, and database rebuilds remain blocked."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Unified Hanzi Evidence Index",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total entries: {summary['total_entries']}",
        f"- 8105 core entries: {summary['catalog_scope_counts'].get('8105_core', 0)}",
        f"- Outside-8105 Agent candidates: {summary['catalog_scope_counts'].get('outside_8105_agent_candidate', 0)}",
        f"- Entries with dictionary context: {summary['entries_with_dictionary_context']}",
        f"- Entries with origin context: {summary['entries_with_origin_context']}",
        f"- Entries with Cihai context: {summary['entries_with_cihai_context']}",
        f"- Entries with Wiki context: {summary['entries_with_wiki_context']}",
        f"- Entries with evidence gaps: {summary['entries_with_evidence_gaps']}",
        "",
        "## Boundary",
        "",
        "- This index is Unicode-keyed and read-only.",
        "- Dictionary, Cihai, Kangxi/Zhonghua, origin, and Wiki material is review context unless a later gate upgrades a specific item with evidence.",
        "- It does not assign GF0017 scores, emit final structure labels, write CNBE rows, or rebuild SQLite databases.",
        "",
        "## Decisions",
        "",
        f"- May audit unified evidence index: `{report['decision']['may_audit_unified_evidence_index']}`",
        f"- May start formal GF0017 scoring: `{report['decision']['may_start_formal_gf0017_scoring']}`",
        f"- May write CNBE rows: `{report['decision']['may_write_cnbe_rows']}`",
        f"- May rebuild database: `{report['decision']['may_rebuild_database']}`",
        "",
        "## Review Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(summary["review_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Samples", ""])
    for unicode_label, entry in report["samples"].items():
        lines.extend(
            [
                f"### {entry['char']} `{unicode_label}`",
                "",
                f"- Scope: `{entry['catalog_scope']}`",
                f"- Review status: `{entry['review_status']}`",
                f"- Dictionary context: `{entry['dictionary_context']['has_context']}`",
                f"- Origin context: `{entry['origin_context']['has_context']}`",
                f"- Wiki hits: {entry['wiki_context']['hit_count']}",
                f"- Score status: `{entry['score_status']}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_unified_index()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"entries={report['summary']['total_entries']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
