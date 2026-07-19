#!/usr/bin/env python3
"""Design Agent-standard rule learning for remaining structure candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

AGENT_STANDARD_PLAN = Path("reports/remaining_structure_agent_standard_plan.json")
BASELINE_8105 = Path("evidence/8105/cnbe8105_standard_baseline.json")
GF0017_8105 = Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json")
LEGACY_LOCALIZATION = Path("evidence/agent-standard/cnbe_legacy_structure_localization.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_rule_learning_design.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_RULE_LEARNING_DESIGN.md")

EXPECTED_RULE_LEARNING_CANDIDATES = 5_885
EXPECTED_EXTENSION_REVIEW_CANDIDATES = 67_946
SAMPLE_LIMIT = 120


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def structure_distribution(characters: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in characters.values():
        structure = record.get("structure") or record.get("raw_structure") or "UNRESOLVED"
        counts[str(structure)] += 1
    return dict(sorted(counts.items()))


def gf0017_status_distribution(characters: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in characters.values():
        counts[record.get("comparison_status", "UNKNOWN")] += 1
    return dict(sorted(counts.items()))


def queue_sample(queue: dict[str, Any]) -> list[dict[str, Any]]:
    return queue.get("samples", [])[:SAMPLE_LIMIT]


def build_rule_learning_design() -> dict[str, Any]:
    plan = load_json(AGENT_STANDARD_PLAN)
    baseline = load_json(BASELINE_8105)
    gf0017 = load_json(GF0017_8105)
    localization = load_json(LEGACY_LOCALIZATION)

    queues = {queue["queue"]: queue for queue in plan["queues"]}
    rule_learning_count = queues["agent_standard_rule_learning_candidate"]["row_count"]
    extension_review_count = queues["agent_standard_extension_review_candidate"]["row_count"]
    baseline_structures = structure_distribution(baseline["characters"])
    gf0017_statuses = gf0017_status_distribution(gf0017["characters"])
    localization_counts = {
        str(item["agent_structure"]): item["row_count"]
        for item in localization["mapping"]
    }

    learning_features = [
        {
            "feature": "unicode_identity",
            "source": "reports/wikipedia_structure_cross_reference_index.json and previous Unicode gates",
            "purpose": "guarantee candidate identity before rule learning",
            "can_assign_points": False,
        },
        {
            "feature": "allowed_13_structure_labels",
            "source": "evidence/agent-standard/cnbe_legacy_structure_localization.json",
            "purpose": "restrict candidate output labels to the approved Agent structure set",
            "can_assign_points": False,
        },
        {
            "feature": "8105_structure_distribution",
            "source": "evidence/8105/cnbe8105_standard_baseline.json",
            "purpose": "learn review priors from national-standard baseline distribution",
            "can_assign_points": False,
        },
        {
            "feature": "gf0017_8105_issue_distribution",
            "source": "evidence/gf0017/cnbe8105_gf0017_normativity_scores.json",
            "purpose": "reuse known risk classes without applying scores to remaining rows",
            "can_assign_points": False,
        },
        {
            "feature": "cross_reference_presence",
            "source": "Unihan, Kangxi, cjk-decomp, Wiki, dictionary review packets",
            "purpose": "rank review priority, not determine final structure",
            "can_assign_points": False,
        },
    ]

    design_phases = [
        {
            "phase": 1,
            "name": "feature_table_design",
            "input_rows": rule_learning_count,
            "output": "read_only_agent_standard_feature_table_schema",
            "allowed": True,
            "assigns_points": False,
            "writes_cnbe_rows": False,
        },
        {
            "phase": 2,
            "name": "8105_rule_prior_design",
            "input_rows": rule_learning_count,
            "output": "review_prior_rules_with_support_counts",
            "allowed": True,
            "assigns_points": False,
            "writes_cnbe_rows": False,
        },
        {
            "phase": 3,
            "name": "candidate_bucket_design",
            "input_rows": rule_learning_count,
            "output": "candidate_buckets_no_final_structure",
            "allowed": True,
            "assigns_points": False,
            "writes_cnbe_rows": False,
        },
        {
            "phase": 4,
            "name": "extension_review_holding_design",
            "input_rows": extension_review_count,
            "output": "extension_review_holding_queue",
            "allowed": True,
            "assigns_points": False,
            "writes_cnbe_rows": False,
        },
    ]

    status = (
        "PASS_AGENT_STANDARD_RULE_LEARNING_DESIGN_READY"
        if plan["overall_status"] == "PASS_REMAINING_STRUCTURE_AGENT_STANDARD_PLAN_READY"
        and rule_learning_count == EXPECTED_RULE_LEARNING_CANDIDATES
        and extension_review_count == EXPECTED_EXTENSION_REVIEW_CANDIDATES
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_agent_standard_rule_learning_design",
        "overall_status": status,
        "next_workflow_status": "AGENT_STANDARD_FEATURE_TABLE_RUNNER_ALLOWED_FORMAL_SCORING_BLOCKED",
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
            "rule_learning_candidates": rule_learning_count,
            "extension_review_candidates": extension_review_count,
            "standard_level": "agent_standard_candidate_not_national_standard",
            "baseline_8105_rows": baseline["summary"]["row_count"],
            "baseline_structure_distribution": baseline_structures,
            "gf0017_8105_status_distribution": gf0017_statuses,
            "legacy_localization_distribution": localization_counts,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "learning_features": learning_features,
        "design_phases": design_phases,
        "review_policy": {
            "candidate_output_level": "agent_standard_candidate_not_national_standard",
            "may_emit_final_structure_label": False,
            "may_emit_review_prior": True,
            "may_emit_confidence_bucket": True,
            "may_assign_gf0017_score": False,
            "may_write_cnbe32_fields": False,
            "required_human_review_before_acceptance": True,
        },
        "samples": {
            "agent_standard_rule_learning_candidate": plan["samples"]["agent_standard_rule_learning_candidate"][:SAMPLE_LIMIT],
            "agent_standard_extension_review_candidate": plan["samples"]["agent_standard_extension_review_candidate"][:SAMPLE_LIMIT],
        },
        "decision": {
            "may_build_agent_standard_feature_table_runner": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Agent-standard rule-learning design is ready. The next runner may build read-only feature tables and review priors, "
                "but must not emit final structures, scores, or CNBE rows."
            ),
        },
        "next_artifacts": [
            "scripts/run_remaining_structure_agent_standard_feature_table.py",
            "reports/remaining_structure_agent_standard_feature_table.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_FEATURE_TABLE.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Rule-Learning Design",
        "",
        "## Purpose",
        "",
        "This report designs read-only Agent-standard rule learning for remaining",
        "structure/decomposition candidates. It uses the audited 8105 baseline as",
        "a learning reference while preserving all remaining rows as project-level",
        "Agent-standard candidates, not national-standard outputs.",
        "",
        "It does not assign GF0017 scores, emit final structure labels, modify",
        "source assets, write CNBE rows, rebuild databases, create tags, publish",
        "releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Rule-learning candidates: `{report['summary']['rule_learning_candidates']}`",
        f"- Extension-review candidates: `{report['summary']['extension_review_candidates']}`",
        f"- Standard level: `{report['summary']['standard_level']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        "",
        "## Design Phases",
        "",
    ]
    for phase in report["design_phases"]:
        lines.append(
            f"- Phase {phase['phase']} `{phase['name']}`: {phase['input_rows']} rows; "
            f"output `{phase['output']}`"
        )
    lines.extend(["", "## Review Policy", ""])
    for key, value in report["review_policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_rule_learning_design()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
