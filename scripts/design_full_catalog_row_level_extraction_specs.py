#!/usr/bin/env python3
"""Design row-level extraction specs for automatable GF0017 evidence items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SOURCE_RESOLUTION = Path("reports/full_catalog_source_resolution_plan.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_row_level_extraction_specs.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_SPECS.md")

AUTOMATABLE_ITEMS = [
    "stroke_shape",
    "stroke_order",
    "component_validity",
    "component_name_validity",
    "radical_validity",
    "independent_character_rule",
    "structure_first_decomposition",
]


EXTRACTION_SPEC_TEMPLATES = {
    "stroke_shape": {
        "spec_id": "extract_stroke_shape_evidence_v1",
        "parser_strategy": "normalize folded-stroke evidence into per-character stroke-shape status",
        "output_table": "stroke_evidence",
        "output_fields": ["unicode", "char", "stroke_shape", "stroke_shape_source", "source_grade", "source_anchor"],
        "validation_rules": [
            "unicode must match source character when present",
            "stroke_shape must be non-empty before item validation",
            "cross-reference evidence cannot become direct_standard without source anchor",
        ],
        "failure_codes": ["MISSING_STROKE_SHAPE", "AMBIGUOUS_STROKE_SHAPE", "SOURCE_ANCHOR_MISSING"],
    },
    "stroke_order": {
        "spec_id": "extract_stroke_order_evidence_v1",
        "parser_strategy": "join stroke_order_8105-style records and source markdown anchors by Unicode",
        "output_table": "stroke_evidence",
        "output_fields": ["unicode", "char", "stroke_count", "stroke_order", "stroke_order_source", "source_grade"],
        "validation_rules": [
            "stroke_order length must equal stroke_count when both are present",
            "stroke order values must use the normalized stroke code domain",
            "missing outside-8105 evidence remains ROW_LEVEL_EVIDENCE_JOIN_PENDING",
        ],
        "failure_codes": ["MISSING_STROKE_ORDER", "STROKE_COUNT_ORDER_MISMATCH", "INVALID_STROKE_CODE"],
    },
    "component_validity": {
        "spec_id": "extract_component_inventory_v1",
        "parser_strategy": "join component_db, cjk-decomp, and decomposition dictionaries by Unicode",
        "output_table": "component_evidence",
        "output_fields": ["unicode", "char", "components", "basic_components", "component_source", "source_grade"],
        "validation_rules": [
            "component list must preserve raw source form",
            "component evidence must distinguish standard-derived and contextual sources",
            "unknown decomposition markers remain blockers",
        ],
        "failure_codes": ["MISSING_COMPONENTS", "UNKNOWN_COMPONENT_MARKER", "CONTEXT_ONLY_COMPONENTS"],
    },
    "component_name_validity": {
        "spec_id": "extract_component_name_validation_v1",
        "parser_strategy": "validate component names against GF0014-derived component-name inventory",
        "output_table": "component_evidence",
        "output_fields": ["unicode", "char", "component_names", "name_source", "source_grade"],
        "validation_rules": [
            "component names must be traceable to component-name inventory",
            "OCR-only names remain review aids",
            "name mismatch does not auto-repair CNBE rows",
        ],
        "failure_codes": ["MISSING_COMPONENT_NAMES", "COMPONENT_NAME_MISMATCH", "OCR_ONLY_NAME"],
    },
    "radical_validity": {
        "spec_id": "extract_radical_evidence_v1",
        "parser_strategy": "join GG0011, Kangxi radical data, Unicode RSIndex, and legacy numeric radical field",
        "output_table": "radical_evidence",
        "output_fields": ["unicode", "char", "radical", "radical_code", "rs_index", "source_grade"],
        "validation_rules": [
            "numeric radical code must be validated separately from radical text",
            "RSIndex is cross-reference unless promoted by explicit project policy",
            "radical mismatch remains a repair candidate only after evidence review",
        ],
        "failure_codes": ["MISSING_RADICAL", "RADICAL_CODE_MISMATCH", "RSINDEX_ONLY"],
    },
    "independent_character_rule": {
        "spec_id": "extract_independent_character_status_v1",
        "parser_strategy": "join GF0013/GF0014 independent-character evidence with component evidence",
        "output_table": "structure_evidence",
        "output_fields": ["unicode", "char", "independent_status", "component_split_allowed", "source_grade"],
        "validation_rules": [
            "independent characters must not be split into invalid non-stroke components",
            "unknown independent status remains pending",
            "structure labels do not override independent-character evidence",
        ],
        "failure_codes": ["MISSING_INDEPENDENT_STATUS", "INVALID_INDEPENDENT_SPLIT", "CONFLICTING_COMPONENT_STATUS"],
    },
    "structure_first_decomposition": {
        "spec_id": "extract_structure_decomposition_v1",
        "parser_strategy": "join Agent 13-label localization with standard-backed decomposition evidence",
        "output_table": "structure_evidence",
        "output_fields": ["unicode", "char", "structure_label", "decomposition", "source_grade", "source_anchor"],
        "validation_rules": [
            "final structure label must be one of the 13 approved Agent labels",
            "legacy English labels must be preserved as raw evidence",
            "decomposition ambiguity blocks scoring",
        ],
        "failure_codes": ["MISSING_STRUCTURE", "STRUCTURE_LABEL_OUT_OF_SET", "AMBIGUOUS_DECOMPOSITION"],
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_paths_for_item(resolution_item: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "relative_path": source["relative_path"],
            "kind": source["kind"],
            "exists": source["exists"],
            "grade_status": source["grade_status"],
        }
        for source in resolution_item["source_paths"]
    ]


def build_specs() -> dict[str, Any]:
    resolution = load_json(SOURCE_RESOLUTION)
    resolution_items = {
        item["item"]: item
        for item in resolution["resolution_items"]
    }
    specs: list[dict[str, Any]] = []
    for item in AUTOMATABLE_ITEMS:
        template = EXTRACTION_SPEC_TEMPLATES[item]
        resolution_item = resolution_items[item]
        specs.append(
            {
                "gf0017_item": item,
                "points": resolution_item["points"],
                "blocked_rows": resolution_item["blocked_rows"],
                "resolution_class": resolution_item["resolution_class"],
                "spec_id": template["spec_id"],
                "parser_strategy": template["parser_strategy"],
                "join_key": "unicode",
                "input_source_paths": source_paths_for_item(resolution_item),
                "output_table": template["output_table"],
                "output_fields": template["output_fields"],
                "validation_rules": template["validation_rules"],
                "failure_codes": template["failure_codes"],
                "can_assign_points_after_extraction": False,
                "next_gate": "ROW_LEVEL_EVIDENCE_JOIN_RUNNER",
            }
        )
    status = (
        "PASS_ROW_LEVEL_EXTRACTION_SPECS_READY"
        if resolution["overall_status"] == "PASS_SOURCE_RESOLUTION_PLAN_READY"
        and len(specs) == len(AUTOMATABLE_ITEMS)
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_row_level_extraction_specs",
        "overall_status": status,
        "next_workflow_status": "ROW_LEVEL_EVIDENCE_JOIN_RUNNERS_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": resolution["summary"]["outside_8105_rows"],
            "spec_count": len(specs),
            "automatable_items": AUTOMATABLE_ITEMS,
            "policy_decision_items": resolution["summary"]["policy_decision_items"],
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
        },
        "extraction_specs": specs,
        "agent_model_stage": {
            "stage_id": "row_level_extraction_specs",
            "input": str(SOURCE_RESOLUTION),
            "outputs": [str(DEFAULT_JSON_OUTPUT), str(DEFAULT_MARKDOWN_OUTPUT)],
            "invariants": [
                "specs_are_read_only",
                "unicode_is_join_key",
                "policy_items_are_not_automated",
                "extraction_does_not_assign_points",
            ],
        },
        "decision": {
            "may_implement_row_level_evidence_join_runners": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Extraction specifications are ready for read-only evidence join runners. "
                "Formal scoring remains blocked until runner output is reviewed and policy items are resolved."
            ),
        },
        "next_artifacts": [
            "scripts/run_full_catalog_row_level_extraction_specs.py",
            "reports/full_catalog_row_level_extraction_results.json",
            "reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_RESULTS.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Row-Level Extraction Specs",
        "",
        "## Purpose",
        "",
        "This report defines read-only extraction specifications for the seven",
        "automatable GF0017 evidence items identified by the source-resolution",
        "plan.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- Extraction specs: `{report['summary']['spec_count']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Extraction Specs",
        "",
    ]
    for spec in report["extraction_specs"]:
        lines.append(
            f"- `{spec['gf0017_item']}`: `{spec['spec_id']}` -> `{spec['output_table']}`; "
            f"blocked_rows={spec['blocked_rows']}"
        )

    lines.extend(["", "## Validation Rules", ""])
    for spec in report["extraction_specs"]:
        lines.append(f"### {spec['gf0017_item']}")
        for rule in spec["validation_rules"]:
            lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is a read-only evidence join",
            "runner. Formal scoring, database reconstruction, and CNBE row writes",
            "remain blocked.",
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in report["next_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_specs()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"next_workflow_status={report['next_workflow_status']}")
    if not report["overall_status"].startswith("PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
