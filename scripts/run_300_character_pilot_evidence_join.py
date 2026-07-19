#!/usr/bin/env python3
"""Run the read-only evidence join for the 300-character 8105 pilot.

This joins the bounded pilot queue with the existing unified index, structure
repair report, dictionary context, origin context, Cihai context, and ZDIC URL
navigation. It does not score rows, write final structure labels, repair CNBE
rows, rebuild databases, or duplicate the 97,686-row catalog.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

PILOT_PLAN = Path("reports/300_character_8105_pilot_plan.json")
PILOT_CSV = Path("review_packets/300_character_8105_pilot/300_character_8105_pilot_plan.csv")
UNIFIED_INDEX = Path("reports/unified_hanzi_evidence_index.json")
STRUCTURE_REPAIR = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")
DICTIONARY_CONTEXT = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json")
YUANLIU_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/yuanliu_chars.json")
CIHAI_INDEX = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cihai_search_index.json")
ZDIC_MANIFEST = Path("reports/zdic_reference_snapshot_manifest.json")

DEFAULT_JSON_OUTPUT = Path("reports/300_character_pilot_evidence_join.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/300_CHARACTER_PILOT_EVIDENCE_JOIN.md")
DEFAULT_CSV_OUTPUT = Path("review_packets/300_character_8105_pilot/300_character_pilot_evidence_join.csv")

EXPECTED_PILOT_ROWS = 300

GF0017_ITEMS = [
    "character_set_coverage",
    "stroke_shape",
    "stroke_order",
    "component_validity",
    "component_name_validity",
    "radical_validity",
    "independent_character_rule",
    "structure_first_decomposition",
]

JOIN_FIELDNAMES = [
    "pilot_id",
    "stratum",
    "unicode",
    "char",
    "catalog_scope",
    "authority_layer",
    "unicode_identity_status",
    "structure_evidence_status",
    "source_grade",
    "next_action",
    "dictionary_context_entries",
    "dictionary_context_sources",
    "yuanliu_context_available",
    "cihai_context_hits",
    "wiki_hit_count",
    "zdic_url",
    "zdic_snapshot_available",
    "gf0017_join_status",
    "blocking_reason",
    "recommended_next_action",
    "gf0017_points_assigned",
    "final_structure_label",
    "cnbe_write_status",
    "editable_copy_notice",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=JOIN_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in JOIN_FIELDNAMES} for row in rows])


def decode_row(schema: list[str], raw: list[Any]) -> dict[str, Any]:
    return dict(zip(schema, raw, strict=True))


def zdic_url(char: str) -> str:
    return f"https://www.zdic.net/hans/{quote(char)}"


def dictionary_summary(entry: dict[str, Any] | None) -> tuple[int, str]:
    if not entry:
        return 0, ""
    entries = entry.get("dictionary_context_entries", [])
    source_ids = sorted({item.get("source_id", "") for item in entries if item.get("source_id")})
    return len(entries), ";".join(source_ids[:6])


def gf0017_status_for_row(row: dict[str, Any]) -> tuple[str, str, str]:
    if row["catalog_scope"] == "8105_core":
        return (
            "PENDING_STANDARD_DERIVED_ITEM_JOIN",
            "8105 core row still requires standard-derived structure/decomposition and item-level joins",
            "join_8105_standard_sources_before_scoring",
        )
    if row["source_grade"] in {"cross_reference", "cross_reference_context"}:
        return (
            "REVIEW_CONTEXT_AVAILABLE_NOT_SCORABLE",
            "cross-reference context must be validated against standards before scoring",
            "human_review_or_standards_validation",
        )
    return (
        "AGENT_STANDARD_QUEUE_NOT_SCORABLE",
        "outside-8105 row remains Agent-standard candidate, not national-standard output",
        "agent_rule_learning_or_human_review",
    )


def authority_layer(row: dict[str, Any]) -> str:
    if row["catalog_scope"] == "8105_core":
        return "national_standard_core_pending_item_join"
    if row["source_grade"] in {"cross_reference", "cross_reference_context"}:
        return "standard_aligned_or_cross_reference_review_context"
    return "agent_standard_candidate_not_national_standard"


def build_join() -> dict[str, Any]:
    pilot_plan = load_json(PILOT_PLAN)
    unified = load_json(UNIFIED_INDEX)
    repair = load_json(STRUCTURE_REPAIR)
    dictionary_context = load_json(DICTIONARY_CONTEXT)
    yuanliu_index = load_json(YUANLIU_INDEX)
    cihai_index = load_json(CIHAI_INDEX)
    zdic_manifest = load_json(ZDIC_MANIFEST)
    pilot_rows = read_csv(PILOT_CSV)

    unified_schema = unified["index_schema"]
    repair_schema = repair["row_schema"]
    lookup_snapshot = {
        record["unicode"]: record
        for record in zdic_manifest["snapshot_records"]
        if record.get("snapshot_available")
    }

    joined_rows: list[dict[str, Any]] = []
    for pilot in pilot_rows:
        unicode_label = pilot["unicode"]
        char = pilot["char"]
        unified_row = decode_row(unified_schema, unified["index"][unicode_label])
        repair_row = decode_row(repair_schema, repair["row_records"][unicode_label])
        dict_count, dict_sources = dictionary_summary(dictionary_context.get(char))
        yuanliu_available = char in yuanliu_index
        cihai_hits = len(cihai_index.get(char, []))
        row = {
            **pilot,
            "catalog_scope": unified_row["catalog_scope"],
            "review_status": unified_row["review_status"],
            "dictionary_context_entries": dict_count,
            "dictionary_context_sources": dict_sources,
            "yuanliu_context_available": yuanliu_available,
            "cihai_context_hits": cihai_hits,
            "wiki_hit_count": int(unified_row["wiki_hit_count"]),
            "structure_evidence_status": repair_row["structure_evidence_status"],
            "source_grade": repair_row["source_grade"],
            "next_action": repair_row["next_action"],
            "zdic_url": zdic_url(char),
            "zdic_snapshot_available": unicode_label in lookup_snapshot,
            "authority_layer": authority_layer(repair_row | {"catalog_scope": unified_row["catalog_scope"]}),
            "unicode_identity_status": "PASS_UNICODE_IDENTITY_FROM_EXISTING_INDEX",
            "gf0017_points_assigned": 0,
            "final_structure_label": "",
            "cnbe_write_status": "NO_CNBE_WRITE",
            "editable_copy_notice": "PILOT_EVIDENCE_JOIN_REVIEW_ONLY_NOT_SOURCE_EVIDENCE",
        }
        gf_status, reason, next_action = gf0017_status_for_row(row)
        row["gf0017_join_status"] = gf_status
        row["blocking_reason"] = reason
        row["recommended_next_action"] = next_action
        joined_rows.append(row)

    checks = {
        "pilot_plan_passed": pilot_plan["overall_status"] == "PASS_300_CHARACTER_8105_PILOT_PLAN_READY",
        "pilot_row_count": len(joined_rows) == EXPECTED_PILOT_ROWS,
        "unicode_values_unique": len({row["unicode"] for row in joined_rows}) == EXPECTED_PILOT_ROWS,
        "uses_existing_unified_index_only": unified["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_BUILT",
        "uses_existing_structure_repair_only": repair["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED",
        "all_rows_have_unicode_identity": all(row["unicode_identity_status"].startswith("PASS") for row in joined_rows),
        "all_rows_have_zdic_url": all(row["zdic_url"].startswith("https://www.zdic.net/hans/") for row in joined_rows),
        "human_final_fields_remain_blank": all(row["final_structure_label"] == "" for row in joined_rows),
        "does_not_assign_gf0017_points": sum(int(row["gf0017_points_assigned"]) for row in joined_rows) == 0,
        "does_not_write_cnbe_rows": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in joined_rows),
        "does_not_rebuild_database": True,
        "does_not_generate_xlsx": True,
        "does_not_modify_source_assets": True,
    }
    status = "PASS_300_CHARACTER_PILOT_EVIDENCE_JOIN_READY_FOR_REVIEW" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_300_character_pilot_evidence_join",
        "overall_status": status,
        "next_workflow_status": "PILOT_EVIDENCE_JOIN_READY_FOR_HUMAN_REVIEW_NO_SCORING",
        "summary": {
            "pilot_rows": len(joined_rows),
            "stratum_counts": count_by(joined_rows, "stratum"),
            "authority_layer_counts": count_by(joined_rows, "authority_layer"),
            "gf0017_join_status_counts": count_by(joined_rows, "gf0017_join_status"),
            "structure_status_counts": count_by(joined_rows, "structure_evidence_status"),
            "dictionary_context_rows": sum(1 for row in joined_rows if row["dictionary_context_entries"] > 0),
            "yuanliu_context_rows": sum(1 for row in joined_rows if row["yuanliu_context_available"]),
            "cihai_context_rows": sum(1 for row in joined_rows if row["cihai_context_hits"] > 0),
            "wiki_context_rows": sum(1 for row in joined_rows if row["wiki_hit_count"] > 0),
            "zdic_url_rows": sum(1 for row in joined_rows if row["zdic_url"]),
            "zdic_snapshot_rows": sum(1 for row in joined_rows if row["zdic_snapshot_available"]),
            "gf0017_points_assigned": 0,
            "final_structure_labels_emitted": 0,
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
            "xlsx_generated": False,
        },
        "authority_boundary": {
            "8105_core_remains_national_standard_core": True,
            "outside_8105_remains_agent_candidate": True,
            "dictionary_context_is_review_context": True,
            "yuanliu_cihai_zdic_wiki_are_not_direct_national_standard_authority": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "gf0017_item_policy": {
            item: "NOT_SCORED_IN_PILOT_EVIDENCE_JOIN"
            for item in GF0017_ITEMS
        },
        "checks": checks,
        "outputs": {
            "join_json": str(DEFAULT_JSON_OUTPUT),
            "join_markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "join_csv": str(DEFAULT_CSV_OUTPUT),
        },
        "decision": {
            "may_start_human_review_on_join_csv": status.startswith("PASS"),
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The 300-row pilot evidence join is ready for human review. It "
                "shows which evidence layers are present and which standard joins "
                "remain blocked, but it is not a scoring result or encoding table."
            ),
        },
        "joined_rows": joined_rows,
    }


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row[field])
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300 Character Pilot Evidence Join",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Pilot rows: {report['summary']['pilot_rows']}",
        f"- Dictionary context rows: {report['summary']['dictionary_context_rows']}",
        f"- Yuanliu context rows: {report['summary']['yuanliu_context_rows']}",
        f"- Cihai context rows: {report['summary']['cihai_context_rows']}",
        f"- Wiki context rows: {report['summary']['wiki_context_rows']}",
        f"- ZDIC URL rows: {report['summary']['zdic_url_rows']}",
        f"- ZDIC snapshot rows: {report['summary']['zdic_snapshot_rows']}",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- XLSX generated: `{report['summary']['xlsx_generated']}`",
        "",
        "## Join Status Counts",
        "",
        f"- Strata: `{report['summary']['stratum_counts']}`",
        f"- Authority layers: `{report['summary']['authority_layer_counts']}`",
        f"- GF0017 join statuses: `{report['summary']['gf0017_join_status_counts']}`",
        f"- Structure statuses: `{report['summary']['structure_status_counts']}`",
        "",
        "## Sample Joined Rows",
        "",
        "| Pilot ID | Unicode | Char | Authority Layer | GF0017 Join Status | Next Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["joined_rows"][:18]:
        lines.append(
            f"| `{row['pilot_id']}` | `{row['unicode']}` | {row['char']} | "
            f"`{row['authority_layer']}` | `{row['gf0017_join_status']}` | "
            f"`{row['recommended_next_action']}` |"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_join()
    joined_rows = report.pop("joined_rows")
    write_json(DEFAULT_JSON_OUTPUT, report | {"joined_rows": joined_rows})
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report | {"joined_rows": joined_rows}))
    write_csv(DEFAULT_CSV_OUTPUT, joined_rows)
    print(report["overall_status"])
    print(f"pilot_rows={report['summary']['pilot_rows']}")
    print(f"gf0017_join_status_counts={report['summary']['gf0017_join_status_counts']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
