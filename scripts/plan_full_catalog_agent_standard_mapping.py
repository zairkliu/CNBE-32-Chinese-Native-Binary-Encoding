#!/usr/bin/env python3
"""Plan Agent-standard mapping for outside-8105 full-catalog rows.

This script is intentionally read-only. It consumes the Unicode identity gate
and the source-join batch report, then creates a stratified mapping plan for
rows that are outside the direct 8105 baseline.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

UNICODE_IDENTITY = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
SOURCE_JOIN_BATCH = Path("reports/full_catalog_gf0017_source_join_batch.json")
AGENT_STANDARD = Path("evidence/agent-standard/cnbe_agent_encoding_standard.json")
LEGACY_LOCALIZATION = Path("evidence/agent-standard/cnbe_legacy_structure_localization.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_agent_standard_mapping_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_AGENT_STANDARD_MAPPING_PLAN.md")

EXPECTED_TOTAL_ROWS = 97_686
EXPECTED_OUTSIDE_8105_ROWS = 89_581
SAMPLE_LIMIT_PER_STRATUM = 12
MAX_STRATUM_SAMPLES = 120


UNICODE_BLOCKS = [
    ("CJK Unified Ideographs Extension A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("CJK Compatibility Ideographs", 0xF900, 0xFAFF),
    ("CJK Unified Ideographs Extension B", 0x20000, 0x2A6DF),
    ("CJK Unified Ideographs Extension C", 0x2A700, 0x2B73F),
    ("CJK Unified Ideographs Extension D", 0x2B740, 0x2B81F),
    ("CJK Unified Ideographs Extension E", 0x2B820, 0x2CEAF),
    ("CJK Unified Ideographs Extension F", 0x2CEB0, 0x2EBEF),
    ("CJK Unified Ideographs Extension I", 0x2EBF0, 0x2EE5F),
    ("CJK Compatibility Ideographs Supplement", 0x2F800, 0x2FA1F),
    ("CJK Unified Ideographs Extension G", 0x30000, 0x3134F),
    ("CJK Unified Ideographs Extension H", 0x31350, 0x323AF),
]


GF0017_ITEM_POINTS = {
    "character_set_coverage": 3,
    "stroke_shape": 3,
    "stroke_order": 3,
    "component_validity": 3,
    "component_name_validity": 8,
    "radical_validity": 3,
    "independent_character_rule": 7,
    "structure_first_decomposition": 20,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unicode_block(codepoint: int) -> str:
    for name, start, end in UNICODE_BLOCKS:
        if start <= codepoint <= end:
            return name
    if 0xE000 <= codepoint <= 0xF8FF:
        return "Private Use Area"
    if 0x10000 <= codepoint <= 0x10FFFF:
        return "Other Supplementary Plane"
    return "Other BMP"


def plane_label(codepoint: int) -> str:
    return "BMP" if codepoint <= 0xFFFF else "SUPPLEMENTARY"


def load_identity_by_offset() -> dict[int, dict[str, Any]]:
    identity = load_json(UNICODE_IDENTITY)
    rows = identity["row_identities"]
    return {offset: row for offset, row in enumerate(rows)}


def outside_rows(source_join: dict[str, Any]) -> list[dict[str, Any]]:
    rows = source_join["row_records"]
    return [
        row
        for row in rows
        if row["join_status"] == "OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED"
    ]


def append_sample(bucket: list[dict[str, Any]], sample: dict[str, Any], limit: int = SAMPLE_LIMIT_PER_STRATUM) -> None:
    if len(bucket) < limit:
        bucket.append(sample)


def load_agent_context() -> dict[str, Any]:
    agent_standard = load_json(AGENT_STANDARD)
    localization = load_json(LEGACY_LOCALIZATION)
    return {
        "agent_standard_schema_version": agent_standard.get("schema_version"),
        "agent_standard_status": agent_standard.get("status"),
        "legacy_localization_schema_version": localization.get("schema_version"),
        "legacy_localization_status": localization.get("status"),
    }


def build_strata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    block_counts: Counter[str] = Counter()
    plane_counts: Counter[str] = Counter()
    standard_level_counts: Counter[str] = Counter()
    unicode_range_counts: Counter[str] = Counter()
    compound_counts: Counter[str] = Counter()
    block_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    plane_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    range_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        codepoint = int(row["unicode"][2:], 16)
        block = unicode_block(codepoint)
        plane = plane_label(codepoint)
        standard_level = row["standard_level"]
        range_band = f"U+{(codepoint // 0x1000) * 0x1000:04X}-U+{((codepoint // 0x1000) * 0x1000) + 0xFFF:04X}"
        compound_key = f"{plane}::{block}"
        sample = {
            "offset": row["offset"],
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "block": block,
            "plane": plane,
            "standard_level": standard_level,
        }
        block_counts[block] += 1
        plane_counts[plane] += 1
        standard_level_counts[standard_level] += 1
        unicode_range_counts[range_band] += 1
        compound_counts[compound_key] += 1
        append_sample(block_samples[block], sample)
        append_sample(plane_samples[plane], sample)
        append_sample(range_samples[range_band], sample, limit=3)

    largest_ranges = [
        {"range": key, "count": value, "samples": range_samples[key]}
        for key, value in unicode_range_counts.most_common(20)
    ]
    return {
        "unicode_block_counts": dict(sorted(block_counts.items())),
        "plane_counts": dict(sorted(plane_counts.items())),
        "standard_level_counts": dict(sorted(standard_level_counts.items())),
        "compound_strata_counts": dict(sorted(compound_counts.items())),
        "unicode_block_samples": dict(sorted(block_samples.items())),
        "plane_samples": dict(sorted(plane_samples.items())),
        "largest_unicode_range_bands": largest_ranges,
    }


def deterministic_review_sample(rows: list[dict[str, Any]], strata: dict[str, Any]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for samples in strata["unicode_block_samples"].values():
        for sample in samples[:3]:
            selected[sample["unicode"]] = sample
            if len(selected) >= MAX_STRATUM_SAMPLES:
                return list(selected.values())
    if len(selected) < MAX_STRATUM_SAMPLES:
        step = max(1, len(rows) // (MAX_STRATUM_SAMPLES - len(selected)))
        for row in rows[::step]:
            codepoint = int(row["unicode"][2:], 16)
            selected.setdefault(
                row["unicode"],
                {
                    "offset": row["offset"],
                    "worksheet_row": row["worksheet_row"],
                    "char": row["char"],
                    "unicode": row["unicode"],
                    "block": unicode_block(codepoint),
                    "plane": plane_label(codepoint),
                    "standard_level": row["standard_level"],
                },
            )
            if len(selected) >= MAX_STRATUM_SAMPLES:
                break
    return list(selected.values())


def build_gate_plan(item_statuses: dict[str, str]) -> list[dict[str, Any]]:
    gate_rows: list[dict[str, Any]] = []
    for item, points in GF0017_ITEM_POINTS.items():
        status = item_statuses[item]
        if status == "SOURCE_GAP":
            next_action = "resolve_controlling_source_or_keep_unscored"
            can_score = False
        elif status == "SOURCE_EVIDENCE_REQUIRED":
            next_action = "build_row_level_evidence_join_before_scoring"
            can_score = False
        else:
            next_action = "ready_for_row_level_validation"
            can_score = status in {"direct_standard", "standard_derived"}
        gate_rows.append(
            {
                "item": item,
                "points": points,
                "current_source_status": status,
                "can_assign_points_now": can_score,
                "next_action": next_action,
            }
        )
    return gate_rows


def build_mapping_plan() -> dict[str, Any]:
    source_join = load_json(SOURCE_JOIN_BATCH)
    identity_by_offset = load_identity_by_offset()
    rows = outside_rows(source_join)
    item_statuses = source_join["summary"]["gf0017_source_item_statuses"]
    unicode_identity_gaps = [
        row
        for row in rows
        if row["offset"] not in identity_by_offset
        or identity_by_offset[row["offset"]].get("issues")
    ]
    strata = build_strata(rows)
    review_sample = deterministic_review_sample(rows, strata)
    gate_plan = build_gate_plan(item_statuses)
    blocked_items = [
        row["item"]
        for row in gate_plan
        if row["current_source_status"] in {"SOURCE_GAP", "SOURCE_EVIDENCE_REQUIRED", "EVIDENCE_GAP"}
    ]
    status = (
        "PASS_AGENT_STANDARD_MAPPING_PLAN_READY"
        if len(rows) == EXPECTED_OUTSIDE_8105_ROWS and not unicode_identity_gaps
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_agent_standard_mapping_plan",
        "overall_status": status,
        "next_workflow_status": "ROW_LEVEL_EVIDENCE_JOIN_PLAN_REQUIRED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "agent_context": load_agent_context(),
        "summary": {
            "total_catalog_rows": EXPECTED_TOTAL_ROWS,
            "outside_8105_rows": len(rows),
            "expected_outside_8105_rows": EXPECTED_OUTSIDE_8105_ROWS,
            "unicode_identity_gap_count": len(unicode_identity_gaps),
            "source_join_status": source_join["overall_status"],
            "source_join_next_status": source_join["next_workflow_status"],
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "agent_standard_mapping_design_allowed": status.startswith("PASS"),
            "blocked_gf0017_items": blocked_items,
        },
        "strata": strata,
        "gf0017_gate_plan": gate_plan,
        "review_sample": review_sample,
        "mapping_work_packages": [
            {
                "id": "WP1_unicode_and_scope",
                "purpose": "Preserve Unicode identity and classify each outside-8105 row by Unicode block and plane.",
                "input": "reports/full_catalog_v4_fixed_unicode_identity.json",
                "output_status": "ready",
                "may_write_cnbe_rows": False,
            },
            {
                "id": "WP2_legacy_field_localization",
                "purpose": "Treat legacy CNBE fields as non-authoritative hints and localize only through Agent standard tables.",
                "input": "evidence/agent-standard/cnbe_legacy_structure_localization.json",
                "output_status": "requires_row_level_join",
                "may_write_cnbe_rows": False,
            },
            {
                "id": "WP3_source_evidence_join",
                "purpose": "Join row-level stroke, component, radical, independent-character, and decomposition evidence.",
                "input": "cnbe-research knowledge assets and repository GF0017 source map",
                "output_status": "required_before_scoring",
                "may_write_cnbe_rows": False,
            },
            {
                "id": "WP4_agent_mapping_candidate_generation",
                "purpose": "Generate Agent-standard mapping candidates only after WP3 resolves evidence status per row.",
                "input": "WP3 evidence join output",
                "output_status": "blocked_until_evidence_join",
                "may_write_cnbe_rows": False,
            },
        ],
        "decision": {
            "may_start_row_level_evidence_join_design": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Outside-8105 rows are stratified and ready for row-level evidence join planning. "
                "They remain Agent-standard mapping candidates, not national-standard outputs."
            ),
        },
        "next_artifacts": [
            "scripts/design_full_catalog_agent_mapping_evidence_join.py",
            "reports/full_catalog_agent_mapping_evidence_join_design.json",
            "reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN_DESIGN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Agent-Standard Mapping Plan",
        "",
        "## Purpose",
        "",
        "This report plans the next read-only stage for the 89,581 full-catalog",
        "rows outside the direct 8105 baseline.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- Unicode identity gaps: `{report['summary']['unicode_identity_gap_count']}`",
        f"- Agent-standard mapping design allowed: `{report['summary']['agent_standard_mapping_design_allowed']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "## Plane Counts",
        "",
    ]
    for key, value in report["strata"]["plane_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Unicode Block Counts", ""])
    for key, value in report["strata"]["unicode_block_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## GF0017 Gate Plan", ""])
    for item in report["gf0017_gate_plan"]:
        lines.append(
            f"- `{item['item']}` ({item['points']} pts): "
            f"`{item['current_source_status']}` -> {item['next_action']}"
        )

    lines.extend(["", "## Work Packages", ""])
    for package in report["mapping_work_packages"]:
        lines.append(f"- `{package['id']}`: {package['purpose']}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is a row-level evidence join",
            "design. Formal scoring, database reconstruction, and CNBE row writes",
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
    report = build_mapping_plan()
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
