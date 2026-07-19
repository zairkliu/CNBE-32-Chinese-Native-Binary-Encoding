#!/usr/bin/env python3
"""Verify the CNBE Hanzi structure Agent runtime gates.

This script is read-only with respect to source data. It checks that existing
Agent, GF0017, knowledge-inventory, and full-catalog reports agree with the
current workflow contract before the project proceeds to source-evidence
preflight work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AGENT_REPORT = Path("evidence/agent-standard/cnbe20902_agent_preencoding_test.json")
AGENT_CHECKPOINT = Path("evidence/agent-standard/cnbe20902_agent_preencoding_checkpoint.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")
SCHEMA_REPORT = Path("reports/full_catalog_excel_schema_comparison.json")
SAMPLE_REPORT = Path("reports/full_catalog_v4_fixed_sample_rows.json")
UNICODE_IDENTITY_REPORT = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
GF0017_REPORT = Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json")

DEFAULT_JSON_OUTPUT = Path("reports/cnbe_agent_runtime_logic_verification.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/CNBE_AGENT_RUNTIME_LOGIC_VERIFICATION.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, ok: str, fail: str) -> dict[str, Any]:
    return {
        "status": "PASS" if condition else "FAIL",
        "message": ok if condition else fail,
    }


def build_verification() -> dict[str, Any]:
    agent = load_json(AGENT_REPORT)
    checkpoint = load_json(AGENT_CHECKPOINT)
    inventory = load_json(KNOWLEDGE_INVENTORY)
    schema = load_json(SCHEMA_REPORT)
    sample = load_json(SAMPLE_REPORT)
    identity = load_json(UNICODE_IDENTITY_REPORT)
    gf0017 = load_json(GF0017_REPORT)

    agent_summary = agent["summary"]
    inventory_gates = inventory["gates"]
    gf_summary = gf0017["summary"]

    gates = {
        "unicode_first_agent_gate": check(
            agent_summary["row_count"] == 20902
            and agent_summary["unicode_status_counts"] == {"PASS": 20902}
            and agent_summary["duplicate_chars"] == 0
            and agent_summary["duplicate_codepoints"] == 0
            and agent_summary["first_blocker_offset"] is None,
            "20,902 legacy CNBE rows have unique Unicode identity and no Unicode blocker.",
            "Agent Unicode identity gate did not pass cleanly.",
        ),
        "legacy_structure_localization_gate": check(
            agent_summary["structure_source_counts"] == {"english_alias": 20902}
            and agent_summary["issue_counts"]["structure_label_requires_localization"] == 20902,
            "All legacy English structure labels are localized and preserved as review signals.",
            "Legacy structure localization coverage is incomplete.",
        ),
        "cnbe32_carrier_separation_gate": check(
            agent_summary["bitfield_status_counts"]["PASS"] == 8038
            and agent_summary["bitfield_status_counts"]["REVIEW_REQUIRED"] == 12864
            and agent_summary["issue_counts"]["struct_type_name_mismatch_after_normalization"] == 12864,
            "CNBE32 bitfield review is separated from Unicode identity and cannot silently repair rows.",
            "CNBE32 review signals were not preserved as separate gate output.",
        ),
        "checkpoint_resume_gate": check(
            checkpoint["last_verified_offset"] == 20901
            and checkpoint["blocker_offset"] is None
            and checkpoint["resume_from"] == 20902,
            "Checkpoint reports a complete no-blocker scan and a resume offset after the final row.",
            "Checkpoint state is inconsistent with the Agent scan.",
        ),
        "knowledge_asset_stop_gate": check(
            inventory_gates["asset_confirmation_status"] in {"ACTION_REQUIRED", "PASS_WITH_NOTES"}
            and inventory_gates["encoding_generation_gate"] in {"NO_GO", "REVIEW_REQUIRED"}
            and inventory_gates["sqlite_build_gate"] in {"NO_GO", "REVIEW_REQUIRED"}
            and inventory_gates["external_assets_imported"] is False,
            "Knowledge assets preserve a gated state before scoring or database generation.",
            "Knowledge asset gate did not preserve the required gated state.",
        ),
        "full_catalog_pre_gf0017_gate": check(
            schema["summary"]["status"] == "PASS"
            and sample["summary"]["status"] == "PASS"
            and identity["summary"]["status"] == "PASS"
            and identity["summary"]["data_rows"] == 97686
            and identity["summary"]["unique_unicode"] == 97686
            and identity["summary"]["unique_char"] == 97686
            and identity["summary"]["issue_counts"] == {},
            "Full catalog preparation passes schema, sample, and Unicode identity gates.",
            "Full catalog preparation gate is not clean enough for GF0017 preflight planning.",
        ),
        "gf0017_status_preservation_gate": check(
            gf_summary["row_count"] == 8105
            and gf_summary["overall_status_counts"]["EVIDENCE_GAP"] > 0
            and gf_summary["overall_status_counts"]["REVIEW_REQUIRED"] > 0
            and gf_summary["repair_class_counts"]["CNBE32_FIELD_REPAIR_CANDIDATE"] > 0,
            "GF0017 scoring preserves EVIDENCE_GAP, REVIEW_REQUIRED, and repair-candidate statuses.",
            "GF0017 output does not preserve the expected non-pass status classes.",
        ),
    }

    failed_gates = [name for name, row in gates.items() if row["status"] != "PASS"]
    expected_no_go_reasons = [
        item for item in inventory.get("action_items", []) if item.get("severity") == "BLOCKER"
    ]

    return {
        "report_schema_version": "1.0",
        "agent": "cnbe-hanzi-structure-encoding-agent",
        "mode": "read_only_runtime_logic_verification",
        "overall_status": "PASS" if not failed_gates else "FAIL",
        "next_workflow_status": "PREFLIGHT_ALLOWED_BATCH_SCORING_BLOCKED" if not failed_gates else "BLOCKED",
        "failed_gates": failed_gates,
        "expected_no_go_reasons": expected_no_go_reasons,
        "inputs": {
            "agent_report": str(AGENT_REPORT),
            "agent_checkpoint": str(AGENT_CHECKPOINT),
            "knowledge_inventory": str(KNOWLEDGE_INVENTORY),
            "schema_report": str(SCHEMA_REPORT),
            "sample_report": str(SAMPLE_REPORT),
            "unicode_identity_report": str(UNICODE_IDENTITY_REPORT),
            "gf0017_report": str(GF0017_REPORT),
        },
        "gates": gates,
        "key_counts": {
            "agent_rows": agent_summary["row_count"],
            "agent_unicode_pass": agent_summary["unicode_status_counts"]["PASS"],
            "legacy_structure_localization_required": agent_summary["issue_counts"][
                "structure_label_requires_localization"
            ],
            "cnbe32_review_required": agent_summary["bitfield_status_counts"]["REVIEW_REQUIRED"],
            "full_catalog_rows": identity["summary"]["data_rows"],
            "gf0017_rows": gf_summary["row_count"],
            "knowledge_blockers": inventory_gates["blocker_count"],
            "knowledge_warnings": inventory_gates["warning_count"],
        },
        "blocker_assertion_policy": {
            "source": str(KNOWLEDGE_INVENTORY),
            "current_inventory_blocker_count": inventory_gates["blocker_count"],
            "current_inventory_warning_count": inventory_gates["warning_count"],
            "current_encoding_generation_gate": inventory_gates["encoding_generation_gate"],
            "current_sqlite_build_gate": inventory_gates["sqlite_build_gate"],
            "test_rule": "assert inventory consistency and named critical blockers",
            "do_not_hardcode_historical_blocker_totals": True,
            "review_required_semantics": (
                "A REVIEW_REQUIRED source gate permits read-only evidence-index design. "
                "It does not permit formal scoring, CNBE row writes, or database reconstruction."
            ),
            "reason": (
                "Knowledge-asset blockers can be resolved by authorized repairs. "
                "Regression tests should fail only when the current inventory and "
                "runtime report disagree, or when a known critical blocker disappears "
                "without an explicit repair record."
            ),
            "critical_blockers_to_preserve_until_resolved": [],
            "resolved_historical_blocker_classes": [
                "structured/base_character_data.json 8105 count mismatch",
                "structured/cnbe_character_knowledge.json 8105 count mismatch",
                "legacy Unihan.zip invalid archive when canonical Unihan2.zip passes",
            ],
        },
        "decision": {
            "may_start_gf0017_preflight_plan": not failed_gates,
            "may_start_batch_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_publish_release": False,
            "reason": (
                "Runtime logic passes, but source evidence mapping and review-required asset notes must be handled "
                "before batch scoring or database reconstruction."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CNBE Agent Runtime Logic Verification",
        "",
        "## Purpose",
        "",
        "This report verifies that the CNBE Hanzi structure Agent follows the",
        "current runtime gate order before the project moves from preparation",
        "into source-evidence and GF0017 preflight planning.",
        "",
        "The verification is read-only. It does not generate CNBE rows, rebuild",
        "databases, modify workbooks, create tags, publish releases, or upload to",
        "PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- May start GF0017 preflight plan: `{report['decision']['may_start_gf0017_preflight_plan']}`",
        f"- May start batch GF0017 scoring: `{report['decision']['may_start_batch_gf0017_scoring']}`",
        f"- May rebuild database: `{report['decision']['may_rebuild_database']}`",
        "",
        "## Gate Results",
        "",
        "| Gate | Status | Meaning |",
        "|---|:---:|---|",
    ]
    for name, row in report["gates"].items():
        lines.append(f"| `{name}` | {row['status']} | {row['message']} |")

    lines.extend(
        [
            "",
            "## Key Counts",
            "",
        ]
    )
    for key, value in report["key_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(
        [
            "",
            "## Expected NO-GO Reasons",
            "",
        ]
    )
    if report["expected_no_go_reasons"]:
        for item in report["expected_no_go_reasons"]:
            lines.append(
                f"- `{item['asset']}`: {item['issue']} -> {item['next_step']}"
            )
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The Agent runtime logic is acceptable for the next preflight planning",
            "step, but it correctly blocks batch scoring and database reconstruction.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_verification()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"next_workflow_status={report['next_workflow_status']}")
    if report["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
