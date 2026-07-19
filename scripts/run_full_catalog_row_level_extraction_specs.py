#!/usr/bin/env python3
"""Run read-only row-level extraction-spec availability over outside-8105 rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EVIDENCE_JOIN = Path("reports/full_catalog_agent_mapping_evidence_join.json")
EXTRACTION_SPECS = Path("reports/full_catalog_row_level_extraction_specs.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_row_level_extraction_results.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_RESULTS.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581
EXPECTED_SPEC_COUNT = 7
SAMPLE_LIMIT = 20


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_availability(spec: dict[str, Any]) -> tuple[str, list[str]]:
    missing = [
        source["relative_path"]
        for source in spec["input_source_paths"]
        if not source["exists"]
    ]
    if missing:
        return "SOURCE_PATH_MISSING", missing
    return "SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING", []


def extraction_status_for_spec(spec: dict[str, Any]) -> dict[str, Any]:
    status, missing = source_availability(spec)
    return {
        "spec_id": spec["spec_id"],
        "output_table": spec["output_table"],
        "extraction_status": status,
        "missing_source_paths": missing,
        "failure_codes_available": spec["failure_codes"],
        "validation_rules_available": len(spec["validation_rules"]),
        "can_assign_points": False,
    }


def build_extraction_results() -> dict[str, Any]:
    evidence_join = load_json(EVIDENCE_JOIN)
    extraction_specs = load_json(EXTRACTION_SPECS)
    specs = extraction_specs["extraction_specs"]
    row_records: list[dict[str, Any]] = []
    item_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    output_table_counts: Counter[str] = Counter()
    row_status_counts: Counter[str] = Counter()
    missing_source_paths: set[str] = set()
    samples: dict[str, list[dict[str, Any]]] = {
        "available_extraction_pending_rows": [],
        "missing_source_rows": [],
    }

    spec_status_templates = {
        spec["gf0017_item"]: extraction_status_for_spec(spec)
        for spec in specs
    }
    for status in spec_status_templates.values():
        missing_source_paths.update(status["missing_source_paths"])

    for row in evidence_join["row_records"]:
        per_item = {
            item: dict(status)
            for item, status in spec_status_templates.items()
        }
        for item, status in per_item.items():
            item_status_counts[item][status["extraction_status"]] += 1
            output_table_counts[status["output_table"]] += 1
        row_has_missing_source = any(status["missing_source_paths"] for status in per_item.values())
        row_status = (
            "ROW_EXTRACTION_SOURCE_MISSING"
            if row_has_missing_source
            else "ROW_EXTRACTION_SOURCES_AVAILABLE_PENDING"
        )
        row_status_counts[row_status] += 1
        record = {
            "offset": row["offset"],
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "unicode_block": row["unicode_block"],
            "unicode_plane": row["unicode_plane"],
            "standard_level": row["standard_level"],
            "row_extraction_status": row_status,
            "gf0017_item_extraction_statuses": per_item,
            "score": None,
            "score_status": "NOT_SCORED_EXTRACTION_STATUS_ONLY",
        }
        row_records.append(record)
        sample = {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "row_extraction_status": row_status,
        }
        if row_has_missing_source and len(samples["missing_source_rows"]) < SAMPLE_LIMIT:
            samples["missing_source_rows"].append(sample)
        if not row_has_missing_source and len(samples["available_extraction_pending_rows"]) < SAMPLE_LIMIT:
            samples["available_extraction_pending_rows"].append(sample)

    status = (
        "PASS_ROW_LEVEL_EXTRACTION_STATUS_MATERIALIZED"
        if len(row_records) == EXPECTED_OUTSIDE_8105_ROWS
        and len(specs) == EXPECTED_SPEC_COUNT
        and extraction_specs["overall_status"] == "PASS_ROW_LEVEL_EXTRACTION_SPECS_READY"
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_row_level_extraction_results",
        "overall_status": status,
        "next_workflow_status": "EVIDENCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED",
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
            "spec_count": len(specs),
            "row_status_counts": dict(row_status_counts),
            "item_status_counts": {
                item: dict(counter)
                for item, counter in sorted(item_status_counts.items())
            },
            "output_table_counts": dict(sorted(output_table_counts.items())),
            "missing_source_paths": sorted(missing_source_paths),
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
        },
        "samples": samples,
        "row_records": row_records,
        "decision": {
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "may_start_evidence_review_plan": status.startswith("PASS"),
            "reason": (
                "Extraction-status rows have been materialized from read-only specs. "
                "They confirm source availability and pending extraction work, but do not assign evidence values or points."
            ),
        },
        "next_artifacts": [
            "scripts/plan_full_catalog_evidence_review.py",
            "reports/full_catalog_evidence_review_plan.json",
            "reports/FULL_CATALOG_EVIDENCE_REVIEW_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Row-Level Extraction Results",
        "",
        "## Purpose",
        "",
        "This report materializes read-only extraction-status rows for the seven",
        "automatable GF0017 evidence items.",
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

    lines.extend(["", "## Item Status Counts", ""])
    for item, counts in report["summary"]["item_status_counts"].items():
        rendered = ", ".join(f"`{status}`={count}" for status, count in counts.items())
        lines.append(f"- `{item}`: {rendered}")

    lines.extend(["", "## Output Table Counts", ""])
    for table, count in report["summary"]["output_table_counts"].items():
        lines.append(f"- `{table}`: {count}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is an evidence-review plan.",
            "Formal scoring, database reconstruction, and CNBE row writes remain",
            "blocked.",
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
    report = build_extraction_results()
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
