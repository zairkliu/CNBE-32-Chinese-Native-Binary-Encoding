#!/usr/bin/env python3
"""Plan dictionary-context import without writing CNBE research knowledge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EVALUATION = Path("reports/external_dictionary_source_candidate_evaluation.json")

DEFAULT_JSON_OUTPUT = Path("reports/external_dictionary_context_import_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/EXTERNAL_DICTIONARY_CONTEXT_IMPORT_PLAN.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_import_plan() -> dict[str, Any]:
    evaluation = load_json(EVALUATION)
    nlp = evaluation["candidates"]["leechenhwa2_nlp_han_dicts"]
    kr = evaluation["candidates"]["kanripo_KR1j0048"]
    he = evaluation["candidates"]["he426100_kangxi"]

    staging_schema = {
        "table": "dictionary_context_entries",
        "primary_key": ["source_id", "char"],
        "fields": [
            {"name": "source_id", "type": "text", "description": "e.g. nlp_han_dicts_kangxi_4w"},
            {"name": "source_repo", "type": "text"},
            {"name": "source_commit", "type": "text"},
            {"name": "license", "type": "text"},
            {"name": "source_grade", "type": "text", "value": "cross_reference_dictionary_context"},
            {"name": "char", "type": "text"},
            {"name": "unicode", "type": "text"},
            {"name": "content", "type": "text"},
            {"name": "content_preview", "type": "text"},
            {"name": "word1", "type": "text"},
            {"name": "word2", "type": "text"},
            {"name": "volume", "type": "text"},
            {"name": "import_status", "type": "text"},
            {"name": "review_notes", "type": "text"},
        ],
    }
    source_priority = [
        {
            "source_id": "nlp_han_dicts_kangxi_4w",
            "role": "primary_structured_kangxi_context",
            "repo": nlp["repo"],
            "commit": nlp["head"],
            "license": nlp["license"],
            "path": nlp["kangxi_db"]["path"],
            "row_count": nlp["kangxi_db"]["dict_count"],
            "allowed_use": "dictionary context and human-review evidence discovery",
            "forbidden_use": "national-standard structure authority or formal GF0017 point assignment",
        },
        {
            "source_id": "nlp_han_dicts_zhonghua_dazidian",
            "role": "primary_structured_zhonghua_dazidian_context",
            "repo": nlp["repo"],
            "commit": nlp["head"],
            "license": nlp["license"],
            "path": nlp["zhonghua_dazidian_db"]["path"],
            "row_count": nlp["zhonghua_dazidian_db"]["dict_count"],
            "allowed_use": "dictionary context and human-review evidence discovery",
            "forbidden_use": "national-standard structure authority or formal GF0017 point assignment",
        },
        {
            "source_id": "kanripo_kr1j0048_text_witness",
            "role": "supporting_primary_text_witness_after_parser_design",
            "repo": kr["repo"],
            "commit": kr["head"],
            "license": kr["license"],
            "path": kr["local_path"],
            "row_count": None,
            "allowed_use": "spot validation against Kangxi source text after parser design",
            "forbidden_use": "bulk structured import before parser and license review",
        },
        {
            "source_id": "he426100_kangxi_secondary",
            "role": "secondary_comparison_only",
            "repo": he["repo"],
            "commit": he["head"],
            "license": he["license"],
            "path": he["local_path"],
            "row_count": he["sql_word_count"],
            "allowed_use": "secondary comparison only",
            "forbidden_use": "primary source, formal scoring, or production import before license resolution",
        },
    ]
    checks = {
        "evaluation_passed": evaluation["overall_status"] == "PASS_EXTERNAL_DICTIONARY_SOURCE_EVALUATION_READY",
        "primary_source_has_license": nlp["license"] == "BSD-2-Clause",
        "primary_kangxi_rows_available": nlp["kangxi_db"]["dict_count"] > 40_000,
        "primary_zhonghua_rows_available": nlp["zhonghua_dazidian_db"]["dict_count"] > 19_000,
        "staging_schema_declared": True,
        "knowledge_write_blocked": True,
        "formal_scoring_blocked": True,
    }
    status = "PASS_DICTIONARY_CONTEXT_IMPORT_PLAN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_external_dictionary_context_import_plan",
        "overall_status": status,
        "next_workflow_status": "STAGING_DICTIONARY_CONTEXT_BUILD_ALLOWED_KNOWLEDGE_WRITE_BLOCKED",
        "authority_boundary": {
            "dictionary_sources_are_cross_reference_context": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_research_knowledge": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_cnbe_database": True,
        },
        "summary": {
            "recommended_primary_source": "leechenhwa2/nlp-han-dicts",
            "recommended_supporting_source": "kanripo/KR1j0048",
            "recommended_secondary_comparison_source": "he426100/kangxi",
            "planned_staging_output": "build/dictionary_context_staging/dictionary_context_entries.sqlite",
            "planned_manifest": "reports/external_dictionary_context_import_manifest.json",
            "knowledge_write_allowed": False,
            "formal_gf0017_scoring_allowed": False,
        },
        "checks": checks,
        "staging_schema": staging_schema,
        "source_priority": source_priority,
        "next_step": {
            "script": "scripts/build_external_dictionary_context_staging.py",
            "allowed": status.startswith("PASS"),
            "writes_only_to_build_staging": True,
            "requires_authorization_before_cnbe_research_knowledge_write": True,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# External Dictionary Context Import Plan",
        "",
        "## Purpose",
        "",
        "This plan selects dictionary context sources for a staging database. It",
        "does not write `cnbe-research/knowledge`, assign GF0017 scores, emit",
        "final structure labels, write CNBE rows, or rebuild CNBE databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Primary source: `{report['summary']['recommended_primary_source']}`",
        f"- Supporting source: `{report['summary']['recommended_supporting_source']}`",
        f"- Secondary comparison source: `{report['summary']['recommended_secondary_comparison_source']}`",
        f"- Planned staging output: `{report['summary']['planned_staging_output']}`",
        "",
        "## Source Priority",
        "",
    ]
    for source in report["source_priority"]:
        lines.append(
            f"- `{source['source_id']}`: {source['role']}; license `{source['license']}`; "
            f"allowed use: {source['allowed_use']}."
        )
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Next Step", "", f"- `{report['next_step']['script']}`", ""])
    return "\n".join(lines)


def main() -> None:
    report = build_import_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
