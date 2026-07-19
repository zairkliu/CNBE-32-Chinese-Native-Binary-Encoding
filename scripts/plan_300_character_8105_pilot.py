#!/usr/bin/env python3
"""Plan a bounded 300-character pilot around the frozen 8105 core.

The pilot is a review plan, not an encoding run. It selects 100 8105 core
control rows, 100 outside-8105 rows with stronger dictionary/origin context,
and 100 outside-8105 extension or evidence-gap rows. It does not assign GF0017
points, write final structure labels, write CNBE rows, rebuild databases, or
duplicate the full 97,686-row catalog.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

CORE_PLAN = Path("reports/8105_core_rule_to_full_catalog_encoding_plan.json")
UNIFIED_INDEX = Path("reports/unified_hanzi_evidence_index.json")
STRUCTURE_REPAIR = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")

DEFAULT_JSON_OUTPUT = Path("reports/300_character_8105_pilot_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/300_CHARACTER_8105_PILOT_PLAN.md")
DEFAULT_CSV_OUTPUT = Path("review_packets/300_character_8105_pilot/300_character_8105_pilot_plan.csv")

TOTAL_ROWS = 97_686
PILOT_ROWS = 300
STRATUM_SIZE = 100

PILOT_FIELDNAMES = [
    "pilot_id",
    "stratum",
    "unicode",
    "char",
    "codepoint",
    "catalog_offset",
    "worksheet_row",
    "catalog_scope",
    "review_status",
    "structure_evidence_status",
    "source_grade",
    "next_action",
    "dictionary_source_count",
    "has_origin_context",
    "cihai_hit_count",
    "wiki_hit_count",
    "dictionary_review_status",
    "wiki_review_status",
    "feature_review_queue",
    "evidence_role",
    "pilot_reason",
    "human_review_status",
    "human_structure_label",
    "human_decomposition",
    "human_notes",
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PILOT_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in PILOT_FIELDNAMES} for row in rows])


def decode_row(schema: list[str], raw: list[Any]) -> dict[str, Any]:
    return dict(zip(schema, raw, strict=True))


def codepoint_from_unicode(unicode_label: str) -> int:
    return int(unicode_label[2:], 16)


def deterministic_spread(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(rows) < count:
        raise ValueError(f"not enough rows for deterministic sample: needed {count}, got {len(rows)}")
    if count == 1:
        return [rows[0]]
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    last_index = len(rows) - 1
    for position in range(count):
        index = round(position * last_index / (count - 1))
        row = rows[index]
        if row["unicode"] in used:
            for fallback in rows:
                if fallback["unicode"] not in used:
                    row = fallback
                    break
        selected.append(row)
        used.add(row["unicode"])
    return selected


def build_joined_rows() -> list[dict[str, Any]]:
    unified = load_json(UNIFIED_INDEX)
    repair = load_json(STRUCTURE_REPAIR)
    unified_schema = unified["index_schema"]
    repair_schema = repair["row_schema"]
    repair_records = repair["row_records"]

    rows: list[dict[str, Any]] = []
    for unicode_label, raw in unified["index"].items():
        unified_row = decode_row(unified_schema, raw)
        repair_row = decode_row(repair_schema, repair_records[unicode_label])
        codepoint = codepoint_from_unicode(unicode_label)
        rows.append(
            {
                "unicode": unicode_label,
                "char": unified_row["char"],
                "codepoint": codepoint,
                "catalog_offset": unified_row["catalog_offset"],
                "worksheet_row": unified_row["worksheet_row"],
                "catalog_scope": unified_row["catalog_scope"],
                "review_status": unified_row["review_status"],
                "dictionary_source_count": int(unified_row["dictionary_source_count"]),
                "has_origin_context": bool(unified_row["has_origin_context"]),
                "cihai_hit_count": int(unified_row["cihai_hit_count"]),
                "wiki_hit_count": int(unified_row["wiki_hit_count"]),
                "structure_evidence_status": repair_row["structure_evidence_status"],
                "source_grade": repair_row["source_grade"],
                "next_action": repair_row["next_action"],
                "dictionary_review_status": repair_row["dictionary_review_status"],
                "wiki_review_status": repair_row["wiki_review_status"],
                "feature_review_queue": repair_row["feature_review_queue"],
            }
        )
    return sorted(rows, key=lambda row: (row["codepoint"], row["unicode"]))


def pilot_row(source: dict[str, Any], stratum: str, index: int, reason: str, evidence_role: str) -> dict[str, Any]:
    return {
        **source,
        "pilot_id": f"{stratum}_{index:03d}",
        "stratum": stratum,
        "evidence_role": evidence_role,
        "pilot_reason": reason,
        "human_review_status": "待审核",
        "human_structure_label": "",
        "human_decomposition": "",
        "human_notes": "",
        "editable_copy_notice": "PILOT_REVIEW_COPY_NOT_SOURCE_EVIDENCE",
    }


def select_pilot_rows(joined_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    core_candidates = [
        row
        for row in joined_rows
        if row["catalog_scope"] == "8105_core"
    ]
    strong_context_candidates = [
        row
        for row in joined_rows
        if row["catalog_scope"] == "outside_8105_agent_candidate"
        and (
            row["dictionary_source_count"] > 0
            or row["has_origin_context"]
            or row["cihai_hit_count"] > 0
        )
    ]
    extension_gap_candidates = [
        row
        for row in joined_rows
        if row["catalog_scope"] == "outside_8105_agent_candidate"
        and row["codepoint"] > 0xFFFF
        and row["dictionary_source_count"] == 0
        and not row["has_origin_context"]
        and row["cihai_hit_count"] == 0
        and row["structure_evidence_status"]
        in {
            "STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY",
            "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT",
        }
    ]

    selected: list[dict[str, Any]] = []
    strata = [
        (
            "8105_core_control",
            deterministic_spread(core_candidates, STRATUM_SIZE),
            "8105 national-standard core control row; validates source joins before scoring",
            "national_standard_core_control",
        ),
        (
            "outside_8105_strong_dictionary_context",
            deterministic_spread(strong_context_candidates, STRATUM_SIZE),
            "outside-8105 row with dictionary/origin context for 8105-aligned rule transfer review",
            "standard_aligned_review_candidate",
        ),
        (
            "outside_8105_extension_or_gap",
            deterministic_spread(extension_gap_candidates, STRATUM_SIZE),
            "outside-8105 extension or source-gap row for stop-gate and review-queue stress testing",
            "cross_reference_or_source_gap_review_candidate",
        ),
    ]
    seen: set[str] = set()
    for stratum, rows, reason, evidence_role in strata:
        for index, row in enumerate(rows, start=1):
            if row["unicode"] in seen:
                raise ValueError(f"duplicate pilot unicode selected: {row['unicode']}")
            seen.add(row["unicode"])
            selected.append(pilot_row(row, stratum, index, reason, evidence_role))
    return selected


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row[field])
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def build_plan() -> dict[str, Any]:
    core_plan = load_json(CORE_PLAN)
    joined_rows = build_joined_rows()
    pilot_rows = select_pilot_rows(joined_rows)
    checks = {
        "core_plan_ready": core_plan["overall_status"] == "PASS_8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN_READY",
        "source_rows_match_full_catalog": len(joined_rows) == TOTAL_ROWS,
        "pilot_row_count_is_300": len(pilot_rows) == PILOT_ROWS,
        "each_stratum_has_100_rows": set(count_by(pilot_rows, "stratum").values()) == {STRATUM_SIZE},
        "unicode_values_unique": len({row["unicode"] for row in pilot_rows}) == PILOT_ROWS,
        "core_stratum_is_8105_only": all(
            row["catalog_scope"] == "8105_core"
            for row in pilot_rows
            if row["stratum"] == "8105_core_control"
        ),
        "outside_strata_are_not_national_standard": all(
            row["catalog_scope"] == "outside_8105_agent_candidate"
            for row in pilot_rows
            if row["stratum"] != "8105_core_control"
        ),
        "human_fields_blank": all(
            row["human_structure_label"] == "" and row["human_decomposition"] == ""
            for row in pilot_rows
        ),
        "does_not_assign_gf0017_points": True,
        "does_not_emit_final_structure_labels": True,
        "does_not_write_cnbe_rows": True,
        "does_not_rebuild_database": True,
        "does_not_generate_xlsx": True,
    }
    status = "PASS_300_CHARACTER_8105_PILOT_PLAN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_300_character_8105_pilot_plan",
        "overall_status": status,
        "next_workflow_status": "READY_FOR_300_CHARACTER_PILOT_EVIDENCE_JOIN_NO_SCORING",
        "purpose": (
            "Create a bounded pilot queue to test the 8105-core rewrite workflow "
            "before any full-catalog encoding, scoring, CNBE row write, or database rebuild."
        ),
        "summary": {
            "source_rows": len(joined_rows),
            "pilot_rows": len(pilot_rows),
            "stratum_counts": count_by(pilot_rows, "stratum"),
            "catalog_scope_counts": count_by(pilot_rows, "catalog_scope"),
            "structure_status_counts": count_by(pilot_rows, "structure_evidence_status"),
            "source_grade_counts": count_by(pilot_rows, "source_grade"),
            "gf0017_points_assigned": 0,
            "final_structure_labels_emitted": 0,
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
            "xlsx_generated": False,
        },
        "authority_boundary": {
            "uses_8105_as_national_standard_core": True,
            "outside_8105_rows_are_agent_candidates": True,
            "dictionary_context_is_standard_aligned_support": True,
            "zdic_and_wiki_are_cross_reference_only": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "sampling_policy": {
            "method": "deterministic_spread_by_unicode_codepoint",
            "strata": [
                {
                    "name": "8105_core_control",
                    "rows": STRATUM_SIZE,
                    "selection": "catalog_scope == 8105_core",
                },
                {
                    "name": "outside_8105_strong_dictionary_context",
                    "rows": STRATUM_SIZE,
                    "selection": "outside_8105 with dictionary, Cihai, or origin context",
                },
                {
                    "name": "outside_8105_extension_or_gap",
                    "rows": STRATUM_SIZE,
                    "selection": "outside_8105 supplementary-plane rows with source-gap or Agent queue status",
                },
            ],
        },
        "checks": checks,
        "outputs": {
            "plan_json": str(DEFAULT_JSON_OUTPUT),
            "plan_markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "pilot_csv": str(DEFAULT_CSV_OUTPUT),
        },
        "decision": {
            "may_run_pilot_evidence_join": status.startswith("PASS"),
            "may_start_full_catalog_encoding": False,
            "may_start_formal_gf0017_scoring": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The bounded 300-character pilot is ready for read-only evidence "
                "join testing. It is not an encoding result and cannot be used as "
                "a source table until a later human review and merge-audit gate."
            ),
        },
        "pilot_rows": pilot_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300 Character 8105 Pilot Plan",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Source rows referenced: {report['summary']['source_rows']}",
        f"- Pilot rows: {report['summary']['pilot_rows']}",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- XLSX generated: `{report['summary']['xlsx_generated']}`",
        "",
        "## Strata",
        "",
        "| Stratum | Rows | Selection |",
        "|---|---:|---|",
    ]
    for stratum in report["sampling_policy"]["strata"]:
        lines.append(f"| `{stratum['name']}` | {stratum['rows']} | {stratum['selection']} |")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Catalog scopes: `{report['summary']['catalog_scope_counts']}`",
            f"- Structure statuses: `{report['summary']['structure_status_counts']}`",
            f"- Source grades: `{report['summary']['source_grade_counts']}`",
            "",
            "## Sample Rows",
            "",
            "| Pilot ID | Unicode | Char | Scope | Structure Status | Evidence Role |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in report["pilot_rows"][:18]:
        lines.append(
            f"| `{row['pilot_id']}` | `{row['unicode']}` | {row['char']} | "
            f"`{row['catalog_scope']}` | `{row['structure_evidence_status']}` | `{row['evidence_role']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_plan()
    pilot_rows = report.pop("pilot_rows")
    write_json(DEFAULT_JSON_OUTPUT, report | {"pilot_rows": pilot_rows})
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report | {"pilot_rows": pilot_rows}))
    write_csv(DEFAULT_CSV_OUTPUT, pilot_rows)
    print(report["overall_status"])
    print(f"pilot_rows={report['summary']['pilot_rows']}")
    print(f"strata={report['summary']['stratum_counts']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
