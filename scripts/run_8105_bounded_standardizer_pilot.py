#!/usr/bin/env python3
"""Build a bounded 8105 standardizer pilot review packet.

This script is intentionally conservative. It reads the existing 100-row 8105
handoff packet and cnbe-research structured knowledge, then emits a copied
review packet with component/decomposition candidates. It does not write CNBE
source rows, emit final structure labels, assign new GF0017 points, or rebuild
the packaged SQLite database.

Legacy CNBE structure fields are deliberately not read. The pilot uses only the
three-tier evidence path: national-standard 8105 comparison evidence, core
reference knowledge files, and network/dictionary cross-reference context.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
HANDOFF_CSV = Path("review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv")
PARTIAL_SCORE_CSV = Path("review_packets/300_character_8105_pilot/8105_core_pilot_gf0017_partial_scoring.csv")
ENCODING_COMPARISON = Path("evidence/8105/cnbe8105_encoding_comparison.json")

JSON_OUTPUT = Path("reports/8105_core_bounded_standardizer_pilot.json")
MARKDOWN_OUTPUT = Path("reports/8105_CORE_BOUNDED_STANDARDIZER_PILOT.md")
REVIEW_PACKET_CSV = Path("review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.csv")
REVIEW_PACKET_XLSX = Path("review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.xlsx")
COPIED_WORK_TABLE = Path("outputs/8105_core_bounded_standardizer_work_table.csv")

EXPECTED_ROWS = 100
AGENT_VERSION = "CNBE 8105 bounded standardizer pilot v2-no-legacy-structure"


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
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def research_root() -> Path:
    config = load_json(SOURCE_CONFIG)
    root = Path(config["source_root"])
    if not root.exists():
        raise FileNotFoundError(f"cnbe-research source root not found: {root}")
    return root


def knowledge_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        row["char"]: row
        for row in records
        if isinstance(row, dict) and row.get("char")
    }


def truncate(value: Any, limit: int = 180) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def recursive_basic_components(
    char: str,
    mappings: dict[str, list[str]],
    seen: set[str] | None = None,
    depth: int = 0,
) -> list[str]:
    if seen is None:
        seen = set()
    if char in seen or depth >= 3:
        return [char]
    seen.add(char)
    parts = mappings.get(char, [])
    if not parts or parts == [char]:
        return [char]
    result: list[str] = []
    for part in parts:
        result.extend(recursive_basic_components(part, mappings, set(seen), depth + 1))
    compact: list[str] = []
    for part in result:
        if part not in compact:
            compact.append(part)
    return compact


def classify_components(
    components: list[str],
    chengzi: set[str],
    feichengzi: set[str],
) -> tuple[list[str], list[str], list[str]]:
    character_components = [part for part in components if part in chengzi]
    non_character_components = [part for part in components if part in feichengzi]
    unknown_components = [
        part
        for part in components
        if part not in chengzi and part not in feichengzi
    ]
    return character_components, non_character_components, unknown_components


def load_inputs() -> dict[str, Any]:
    root = research_root()
    component_db = load_json(root / "knowledge/component_db.json")
    base_data = load_json(root / "knowledge/structured/base_character_data.json")
    knowledge = knowledge_index(load_json(root / "knowledge/structured/cnbe_character_knowledge.json"))
    encoding_comparison = load_json(ENCODING_COMPARISON)
    partial_scores = {
        row["row_id"]: row
        for row in read_csv(PARTIAL_SCORE_CSV)
    }
    return {
        "component_db": component_db,
        "base_data": base_data,
        "knowledge": knowledge,
        "encoding_comparison": encoding_comparison,
        "partial_scores": partial_scores,
    }


def candidate_status(components: list[str], knowledge: dict[str, Any]) -> str:
    has_dictionary = bool(knowledge.get("has_dictionary_entry"))
    if components and has_dictionary:
        return "CANDIDATE_COMPONENTS_WITH_DICTIONARY_CONTEXT_REVIEW_REQUIRED"
    if components:
        return "CANDIDATE_COMPONENTS_REVIEW_REQUIRED"
    if has_dictionary:
        return "DICTIONARY_CONTEXT_ONLY_REVIEW_REQUIRED"
    return "STANDARDIZER_EVIDENCE_GAP"


def build_review_rows() -> list[dict[str, Any]]:
    inputs = load_inputs()
    component_db = inputs["component_db"]
    mappings = component_db["char_mappings"]
    chengzi = set(component_db["components"]["chengzi"])
    feichengzi = set(component_db["components"]["feichengzi"])
    base_data = inputs["base_data"]
    knowledge = inputs["knowledge"]
    comparison_chars = inputs["encoding_comparison"]["characters"]
    partial_scores = inputs["partial_scores"]

    handoff_rows = read_csv(HANDOFF_CSV)
    if len(handoff_rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} handoff rows, got {len(handoff_rows)}")

    review_rows: list[dict[str, Any]] = []
    for row in handoff_rows:
        char = row["char"]
        row_id = row["row_id"]
        base = base_data.get(char, {})
        knowledge_row = knowledge.get(char, {})
        comparison = comparison_chars.get(char, {})
        standard = comparison.get("standard", {})
        score = partial_scores.get(row_id, {})
        direct_components = standard.get("components") or mappings.get(char, [])
        standard_structure = standard.get("structure", "")
        standard_decomposition = standard.get("decomposition", "")
        standard_radical = standard.get("radical", "")
        standard_evidence_status = standard.get("evidence_status", "")
        basic_components = recursive_basic_components(char, mappings)
        character_components, non_character_components, unknown_components = classify_components(
            direct_components,
            chengzi,
            feichengzi,
        )
        status = candidate_status(direct_components, knowledge_row)
        blocker = []
        if status == "STANDARDIZER_EVIDENCE_GAP":
            blocker.append("NO_COMPONENT_OR_DICTIONARY_CONTEXT")
        if unknown_components:
            blocker.append("UNKNOWN_COMPONENT_CLASS_REVIEW_REQUIRED")
        blocker.extend([
            "FINAL_STRUCTURE_LABEL_NOT_ASSIGNED",
            "CNBE32_NOT_PROPOSED",
            "HUMAN_REVIEW_REQUIRED",
        ])
        review_rows.append({
            "row_id": row_id,
            "character": char,
            "unicode_codepoint": row["unicode"],
            "decimal_codepoint": row["codepoint"],
            "scope": "8105_national_standard_core",
            "standard_level": base.get("level", ""),
            "standard_rank": base.get("standard_rank", ""),
            "source_level": "national_standard_then_core_reference_then_network_cross_reference",
            "proposed_cnbe32": "",
            "proposed_cnbe32_status": "NO_PROPOSED_CNBE32_BEFORE_REVIEW",
            "candidate_structure_label": standard_structure,
            "candidate_structure_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if standard_structure
                else "NOT_FINAL_STRUCTURE_LABEL"
            ),
            "candidate_decomposition": standard_decomposition,
            "candidate_decomposition_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if standard_decomposition
                else "DECOMPOSITION_REVIEW_REQUIRED"
            ),
            "direct_component_candidates": " ".join(direct_components),
            "character_component_candidates": " ".join(character_components),
            "non_character_component_candidates": " ".join(non_character_components),
            "unknown_component_candidates": " ".join(unknown_components),
            "basic_component_candidates": " ".join(basic_components),
            "component_source": "8105_encoding_comparison.standard.components; " + component_db["source"],
            "radical": standard_radical,
            "radical_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if standard_radical
                else "RADICAL_STANDARD_SOURCE_CHECK_REQUIRED"
            ),
            "stroke_count": base.get("stroke_count", ""),
            "stroke_order": base.get("stroke_order_str", ""),
            "stroke_order_status": score.get("stroke_order_status", "PASS_STANDARD_DERIVED_STROKE_ORDER"),
            "gf0017_existing_score": score.get("assigned_score", "6"),
            "gf0017_existing_max": score.get("assigned_max", "6"),
            "gf0017_formal_total": "50",
            "gf0017_new_points_assigned": "0",
            "dictionary_context_status": "HAS_DICTIONARY_CONTEXT" if knowledge_row.get("has_dictionary_entry") else "NO_DICTIONARY_CONTEXT",
            "kangxi_volume": knowledge_row.get("kangxi_volume", ""),
            "kangxi_excerpt": truncate(knowledge_row.get("kangxi_def")),
            "zhonghua_excerpt": truncate(knowledge_row.get("zhonghua_def")),
            "wiki_context_status": "HAS_WIKI_CONTEXT" if knowledge_row.get("has_wiki_entry") else "NO_WIKI_CONTEXT",
            "candidate_status": status,
            "standard_evidence_status": standard_evidence_status,
            "blocked_items": ";".join(blocker),
            "review_status": "HUMAN_REVIEW_REQUIRED",
            "cnbe_write_status": "NO_CNBE_WRITE",
            "database_rebuild_status": "NO_DATABASE_REBUILD",
            "agent_version": AGENT_VERSION,
        })
    return review_rows


def build_report(review_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(row["candidate_status"] for row in review_rows)
    component_count = sum(1 for row in review_rows if row["direct_component_candidates"])
    dictionary_count = sum(1 for row in review_rows if row["dictionary_context_status"] == "HAS_DICTIONARY_CONTEXT")
    standard_structure_count = sum(1 for row in review_rows if row["candidate_structure_label"])
    standard_decomposition_count = sum(1 for row in review_rows if row["candidate_decomposition"])
    checks = {
        "bounded_row_count_is_100": len(review_rows) == EXPECTED_ROWS,
        "all_rows_are_8105_core": all(row["scope"] == "8105_national_standard_core" for row in review_rows),
        "all_rows_keep_unicode_identity": all(row["unicode_codepoint"].startswith("U+") for row in review_rows),
        "no_proposed_cnbe32_written": all(not row["proposed_cnbe32"] for row in review_rows),
        "no_new_gf0017_points_assigned": all(row["gf0017_new_points_assigned"] == "0" for row in review_rows),
        "no_cnbe_source_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in review_rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in review_rows),
        "legacy_structure_fields_absent": all("legacy_structure_label" not in row for row in review_rows),
        "legacy_cnbe_fields_absent": all("legacy_cnbe32" not in row for row in review_rows),
    }
    overall_status = "PASS_8105_BOUNDED_STANDARDIZER_PILOT_REVIEW_PACKET_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_8105_standardizer_candidate_review",
        "agent_version": AGENT_VERSION,
        "overall_status": overall_status,
        "next_workflow_status": "READY_FOR_HUMAN_REVIEW_OF_8105_BOUNDED_STANDARDIZER_PACKET",
        "authority_boundary": {
            "reads_100_row_handoff_only": True,
            "does_not_read_full_97686_catalog": True,
            "does_not_read_legacy_cnbe_structure": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "candidate_structure_is_review_only": True,
            "does_not_assign_new_gf0017_points": True,
            "dictionary_context_is_cross_reference_only": True,
        },
        "summary": {
            "review_rows": len(review_rows),
            "rows_with_component_candidates": component_count,
            "rows_with_dictionary_context": dictionary_count,
            "rows_with_standard_structure_candidates": standard_structure_count,
            "rows_with_standard_decomposition_candidates": standard_decomposition_count,
            "candidate_status_counts": dict(status_counts),
            "gf0017_existing_score_per_row": 6,
            "gf0017_new_points_assigned": 0,
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MARKDOWN_OUTPUT),
            "review_packet_csv": str(REVIEW_PACKET_CSV),
            "optional_review_packet_xlsx": str(REVIEW_PACKET_XLSX),
            "copied_work_table_csv": str(COPIED_WORK_TABLE),
        },
        "decision": {
            "may_start_human_review": overall_status.startswith("PASS"),
            "may_use_packet_for_candidate_repair": overall_status.startswith("PASS"),
            "may_assign_more_gf0017_points": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The packet contains candidate decomposition/component evidence only. "
                "Legacy CNBE structure fields are not read. Human review and "
                "standards-source adjudication are required before GF0017 points "
                "or CNBE32 values can be promoted."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Core Bounded Standardizer Pilot",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Review rows: {report['summary']['review_rows']}",
        f"- Rows with component candidates: {report['summary']['rows_with_component_candidates']}",
        f"- Rows with dictionary context: {report['summary']['rows_with_dictionary_context']}",
        f"- Rows with standard structure candidates: {report['summary']['rows_with_standard_structure_candidates']}",
        f"- Rows with standard decomposition candidates: {report['summary']['rows_with_standard_decomposition_candidates']}",
        f"- New GF0017 points assigned: {report['summary']['gf0017_new_points_assigned']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "This is a bounded 100-row candidate review packet. It fully discards",
        "legacy CNBE structure fields and uses only national-standard, core",
        "reference, and network/dictionary cross-reference evidence. Candidate",
        "structure values are review-only; the script does not write CNBE32",
        "values or rebuild the SQLite database.",
        "",
        "## Candidate Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["candidate_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend([
        "",
        "## Outputs",
        "",
        f"- JSON report: `{report['outputs']['json_report']}`",
        f"- Markdown report: `{report['outputs']['markdown_report']}`",
        f"- Review packet CSV: `{report['outputs']['review_packet_csv']}`",
        f"- Optional review packet XLSX: `{report['outputs']['optional_review_packet_xlsx']}`",
        f"- Copied work table CSV: `{report['outputs']['copied_work_table_csv']}`",
        "",
        "## Decision",
        "",
        report["decision"]["reason"],
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    rows = build_review_rows()
    report = build_report(rows)
    write_csv(REVIEW_PACKET_CSV, rows)
    COPIED_WORK_TABLE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REVIEW_PACKET_CSV, COPIED_WORK_TABLE)
    write_json(JSON_OUTPUT, report)
    write_text(MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"review_rows={report['summary']['review_rows']}")
    print(f"component_candidates={report['summary']['rows_with_component_candidates']}")
    print(f"dictionary_context={report['summary']['rows_with_dictionary_context']}")
    print(f"review_packet={REVIEW_PACKET_CSV}")


if __name__ == "__main__":
    main()
