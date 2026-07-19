#!/usr/bin/env python3
"""Run a read-only row-level evidence-status join for outside-8105 rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SOURCE_JOIN_BATCH = Path("reports/full_catalog_gf0017_source_join_batch.json")
MAPPING_PLAN = Path("reports/full_catalog_agent_standard_mapping_plan.json")
JOIN_DESIGN = Path("reports/full_catalog_agent_mapping_evidence_join_design.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_agent_mapping_evidence_join.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581
SAMPLE_LIMIT = 20


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def item_status_for_row(item_design: dict[str, Any]) -> dict[str, Any]:
    source_status = item_design["current_source_status"]
    if source_status == "SOURCE_GAP":
        evidence_status = "SOURCE_GAP_NOT_SCORABLE"
    elif source_status == "SOURCE_EVIDENCE_REQUIRED":
        evidence_status = "ROW_LEVEL_EVIDENCE_JOIN_PENDING"
    else:
        evidence_status = "READY_FOR_ROW_LEVEL_VALIDATION"
    return {
        "source_status": source_status,
        "evidence_status": evidence_status,
        "can_assign_points": False,
        "blocker_code": item_design["blocker_code"],
    }


def unicode_block_from_plan(mapping_plan: dict[str, Any], unicode_label: str) -> tuple[str, str]:
    for sample in mapping_plan["review_sample"]:
        if sample["unicode"] == unicode_label:
            return sample["block"], sample["plane"]
    codepoint = int(unicode_label[2:], 16)
    plane = "BMP" if codepoint <= 0xFFFF else "SUPPLEMENTARY"
    for block, samples in mapping_plan["strata"]["unicode_block_samples"].items():
        if any(sample["unicode"] == unicode_label for sample in samples):
            return block, plane
    if 0x3400 <= codepoint <= 0x4DBF:
        return "CJK Unified Ideographs Extension A", plane
    if 0x4E00 <= codepoint <= 0x9FFF:
        return "CJK Unified Ideographs", plane
    if 0x20000 <= codepoint <= 0x2A6DF:
        return "CJK Unified Ideographs Extension B", plane
    if 0x2A700 <= codepoint <= 0x2B73F:
        return "CJK Unified Ideographs Extension C", plane
    if 0x2B740 <= codepoint <= 0x2B81F:
        return "CJK Unified Ideographs Extension D", plane
    if 0x2B820 <= codepoint <= 0x2CEAF:
        return "CJK Unified Ideographs Extension E", plane
    if 0x2CEB0 <= codepoint <= 0x2EBEF:
        return "CJK Unified Ideographs Extension F", plane
    if 0x2EBF0 <= codepoint <= 0x2EE5F:
        return "CJK Unified Ideographs Extension I", plane
    if 0x30000 <= codepoint <= 0x3134F:
        return "CJK Unified Ideographs Extension G", plane
    if 0x31350 <= codepoint <= 0x323AF:
        return "CJK Unified Ideographs Extension H", plane
    return "Other", plane


def outside_rows(source_join: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in source_join["row_records"]
        if row["join_status"] == "OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED"
    ]


def build_evidence_join() -> dict[str, Any]:
    source_join = load_json(SOURCE_JOIN_BATCH)
    mapping_plan = load_json(MAPPING_PLAN)
    join_design = load_json(JOIN_DESIGN)
    rows = outside_rows(source_join)
    item_designs = {
        item["item"]: item
        for item in join_design["gf0017_item_join_designs"]
    }
    row_records: list[dict[str, Any]] = []
    item_evidence_counts: dict[str, Counter[str]] = defaultdict(Counter)
    plane_counts: Counter[str] = Counter()
    block_counts: Counter[str] = Counter()
    row_status_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, Any]]] = {
        "source_gap_rows": [],
        "row_evidence_pending_rows": [],
    }

    for row in rows:
        block, plane = unicode_block_from_plan(mapping_plan, row["unicode"])
        plane_counts[plane] += 1
        block_counts[block] += 1
        item_statuses = {
            item: item_status_for_row(design)
            for item, design in item_designs.items()
        }
        for item, status in item_statuses.items():
            item_evidence_counts[item][status["evidence_status"]] += 1
        has_source_gap = any(status["evidence_status"] == "SOURCE_GAP_NOT_SCORABLE" for status in item_statuses.values())
        has_pending = any(
            status["evidence_status"] == "ROW_LEVEL_EVIDENCE_JOIN_PENDING"
            for status in item_statuses.values()
        )
        row_status = "ROW_EVIDENCE_JOIN_PENDING"
        if has_source_gap:
            row_status = "ROW_SOURCE_GAP_AND_EVIDENCE_JOIN_PENDING"
        row_status_counts[row_status] += 1
        record = {
            "offset": row["offset"],
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "unicode_block": block,
            "unicode_plane": plane,
            "standard_level": "agent_standard_candidate_not_national_standard",
            "row_evidence_status": row_status,
            "gf0017_item_evidence_statuses": item_statuses,
            "score": None,
            "score_status": "NOT_SCORED_EVIDENCE_JOIN_ONLY",
        }
        row_records.append(record)
        sample = {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "unicode_block": block,
            "row_evidence_status": row_status,
        }
        if has_source_gap and len(samples["source_gap_rows"]) < SAMPLE_LIMIT:
            samples["source_gap_rows"].append(sample)
        if has_pending and len(samples["row_evidence_pending_rows"]) < SAMPLE_LIMIT:
            samples["row_evidence_pending_rows"].append(sample)

    status = (
        "PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED"
        if len(row_records) == EXPECTED_OUTSIDE_8105_ROWS
        and join_design["overall_status"] == "PASS_EVIDENCE_JOIN_DESIGN_READY"
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_agent_mapping_evidence_join",
        "overall_status": status,
        "next_workflow_status": "FORMAL_SCORING_BLOCKED_ROW_EVIDENCE_REQUIRES_SOURCE_RESOLUTION",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": len(row_records),
            "row_status_counts": dict(row_status_counts),
            "plane_counts": dict(sorted(plane_counts.items())),
            "unicode_block_counts": dict(sorted(block_counts.items())),
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "item_evidence_counts": {
                item: dict(counter)
                for item, counter in sorted(item_evidence_counts.items())
            },
        },
        "samples": samples,
        "row_records": row_records,
        "decision": {
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "may_start_source_resolution_plan": status.startswith("PASS"),
            "reason": (
                "Row-level evidence statuses have been materialized. Formal scoring remains blocked "
                "because SOURCE_GAP and ROW_LEVEL_EVIDENCE_JOIN_PENDING statuses remain for every outside-8105 row."
            ),
        },
        "next_artifacts": [
            "scripts/plan_full_catalog_source_resolution.py",
            "reports/full_catalog_source_resolution_plan.json",
            "reports/FULL_CATALOG_SOURCE_RESOLUTION_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Agent Mapping Evidence Join",
        "",
        "## Purpose",
        "",
        "This report materializes row-level evidence statuses for the 89,581",
        "outside-8105 rows.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Row Status Counts",
        "",
    ]
    for key, value in report["summary"]["row_status_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Plane Counts", ""])
    for key, value in report["summary"]["plane_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## GF0017 Item Evidence Counts", ""])
    for item, counts in report["summary"]["item_evidence_counts"].items():
        rendered = ", ".join(f"`{status}`={count}" for status, count in counts.items())
        lines.append(f"- `{item}`: {rendered}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed step is a source-resolution plan. Formal scoring,",
            "database reconstruction, and CNBE row writes remain blocked.",
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
    report = build_evidence_join()
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
