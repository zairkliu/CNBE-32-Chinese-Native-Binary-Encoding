#!/usr/bin/env python3
"""Run Phase 1 read-only structure/decomposition evidence parsing.

This parser materializes candidate structure/decomposition evidence for
outside-8105 rows. It is intentionally conservative: it does not assign GF0017
points, modify source assets, write CNBE rows, or rebuild databases.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
EVIDENCE_JOIN = Path("reports/full_catalog_agent_mapping_evidence_join.json")
PARSER_PLAN = Path("reports/full_catalog_parser_implementation_plan.json")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_evidence_parser.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_EVIDENCE_PARSER.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581
REVIEW_SAMPLE_LIMIT = 300

IDS_TO_STRUCTURE = {
    "⿰": "左右",
    "⿱": "上下",
    "⿲": "左中右",
    "⿳": "上中下",
    "⿴": "全包围",
    "⿵": "上三包",
    "⿶": "下三包",
    "⿷": "左三包",
    "⿸": "左上包",
    "⿹": "右上包",
    "⿺": "左下包",
    "⿻": "镶嵌",
}

ALLOWED_STRUCTURES = {
    "独体字",
    "上下",
    "上中下",
    "左右",
    "左中右",
    "左上包",
    "右上包",
    "左三包",
    "左下包",
    "上三包",
    "下三包",
    "全包围",
    "镶嵌",
}

STRUCTURE_TO_TYPE = {
    "独体字": 0,
    "上下": 1,
    "上中下": 2,
    "左右": 3,
    "左中右": 4,
    "左上包": 5,
    "右上包": 6,
    "左三包": 7,
    "左下包": 8,
    "上三包": 9,
    "下三包": 10,
    "全包围": 11,
    "镶嵌": 12,
}

CJK_DECOMP_RE = re.compile(r"^(?P<codepoint>[0-9]+):(?P<relation>.+)$")
RELATION_RE = re.compile(r"^(?P<relation>[a-z0-9/]+)\((?P<body>.*)\)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def research_root() -> Path:
    config = load_json(SOURCE_CONFIG)
    root = Path(config["source_root"])
    if not root.exists():
        raise FileNotFoundError(f"research source root not found: {root}")
    return root


def load_dictionary(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "decomp-data/dictionary.json"
    records = load_json(path)
    return {
        record["character"]: record
        for record in records
        if isinstance(record, dict) and record.get("character")
    }


def load_component_db(root: Path) -> dict[str, Any]:
    return load_json(root / "knowledge/component_db.json")


def load_cjk_decomp(root: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    path = root / "cjk-decomp/cjk-decomp.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CJK_DECOMP_RE.match(line.strip())
        if not match:
            continue
        try:
            char = chr(int(match.group("codepoint")))
        except ValueError:
            continue
        records[char] = match.group("relation")
    return records


def ids_operator(raw_decomposition: str | None) -> str | None:
    if not raw_decomposition:
        return None
    for char in raw_decomposition:
        if char in IDS_TO_STRUCTURE:
            return char
    return None


def components_from_ids(raw_decomposition: str | None) -> list[str]:
    if not raw_decomposition:
        return []
    return [
        char
        for char in raw_decomposition
        if char not in IDS_TO_STRUCTURE and char not in {"?", "(", ")", ",", " "}
    ]


def components_from_cjk_relation(raw_relation: str | None) -> list[str]:
    if not raw_relation:
        return []
    match = RELATION_RE.match(raw_relation)
    if not match:
        return []
    body = match.group("body")
    parts = [part.strip() for part in body.split(",") if part.strip()]
    return [
        part
        for part in parts
        if not part.isdigit() and part != "?"
    ]


def cjk_relation_label(raw_relation: str | None) -> str | None:
    if not raw_relation:
        return None
    match = RELATION_RE.match(raw_relation)
    if not match:
        return None
    relation = match.group("relation").split("/")[0]
    return {
        "a": "左右",
        "d": "上下",
        "w": "全包围",
        "stl": "左上包",
        "str": "右上包",
        "sl": "左三包",
        "s": "全包围",
    }.get(relation)


def select_structure(
    dictionary_record: dict[str, Any] | None,
    component_parts: list[str],
    cjk_relation: str | None,
) -> tuple[str | None, str, list[str]]:
    issues: list[str] = []
    raw_decomposition = None
    if dictionary_record:
        raw_decomposition = dictionary_record.get("decomposition")
    operator = ids_operator(raw_decomposition)
    if operator:
        return IDS_TO_STRUCTURE[operator], "dictionary_ids_operator", issues
    if component_parts and len(component_parts) == 1:
        return "独体字", "component_single_part", issues
    cjk_label = cjk_relation_label(cjk_relation)
    if cjk_label:
        issues.append("CJK_DECOMP_RELATION_IS_CROSS_REFERENCE")
        return cjk_label, "cjk_decomp_relation_cross_reference", issues
    if component_parts and len(component_parts) > 1:
        issues.append("COMPONENTS_WITHOUT_STRUCTURE_OPERATOR")
        return None, "component_parts_without_operator", issues
    return None, "no_structure_evidence", issues


def build_record(
    row: dict[str, Any],
    dictionary: dict[str, dict[str, Any]],
    component_mappings: dict[str, list[str]],
    cjk_decomp: dict[str, str],
) -> dict[str, Any]:
    char = row["char"]
    dictionary_record = dictionary.get(char)
    dictionary_decomposition = None
    dictionary_radical = None
    if dictionary_record:
        dictionary_decomposition = dictionary_record.get("decomposition")
        dictionary_radical = dictionary_record.get("radical")

    component_parts = component_mappings.get(char, [])
    cjk_relation = cjk_decomp.get(char)
    structure_label, structure_rule, issues = select_structure(
        dictionary_record,
        component_parts,
        cjk_relation,
    )
    ids_components = components_from_ids(dictionary_decomposition)
    cjk_components = components_from_cjk_relation(cjk_relation)
    component_candidates = component_parts or ids_components or cjk_components

    failure_codes: list[str] = []
    if structure_label is None:
        failure_codes.append("MISSING_STRUCTURE")
    elif structure_label not in ALLOWED_STRUCTURES:
        failure_codes.append("STRUCTURE_LABEL_OUT_OF_SET")
    if dictionary_decomposition and "?" in dictionary_decomposition:
        failure_codes.append("AMBIGUOUS_DECOMPOSITION")
    if cjk_relation and "?" in cjk_relation:
        failure_codes.append("AMBIGUOUS_DECOMPOSITION")
    if not component_candidates:
        failure_codes.append("MISSING_DECOMPOSITION_COMPONENTS")

    source_hits = {
        "dictionary_record": dictionary_record is not None,
        "component_mapping": bool(component_parts),
        "cjk_decomp": cjk_relation is not None,
    }
    if dictionary_record and structure_label and not failure_codes:
        evidence_status = "STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW"
        source_grade = "cross_reference"
    elif structure_label and component_candidates:
        evidence_status = "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED"
        source_grade = "cross_reference"
    else:
        evidence_status = "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP"
        source_grade = "unresolved"

    return {
        "offset": row["offset"],
        "worksheet_row": row["worksheet_row"],
        "char": char,
        "unicode": row["unicode"],
        "unicode_block": row["unicode_block"],
        "unicode_plane": row["unicode_plane"],
        "standard_level": row["standard_level"],
        "gf0017_item": "structure_first_decomposition",
        "evidence_status": evidence_status,
        "structure_label": structure_label,
        "structure_type": STRUCTURE_TO_TYPE.get(structure_label),
        "structure_rule": structure_rule,
        "decomposition": dictionary_decomposition or cjk_relation,
        "components": component_candidates,
        "dictionary_radical": dictionary_radical,
        "source_grade": source_grade,
        "source_hits": source_hits,
        "source_anchor": {
            "dictionary": "decomp-data/dictionary.json" if dictionary_record else None,
            "component_db": "knowledge/component_db.json" if component_parts else None,
            "cjk_decomp": "cjk-decomp/cjk-decomp.txt" if cjk_relation else None,
        },
        "failure_codes": sorted(set(failure_codes)),
        "issues": sorted(set(issues)),
        "score": None,
        "score_status": "NOT_SCORED_PHASE_1_EVIDENCE_ONLY",
    }


def sample_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    samples: dict[str, list[dict[str, Any]]] = {
        "ready_for_review": [],
        "partial_review_required": [],
        "evidence_gap": [],
        "ambiguous_decomposition": [],
    }
    status_to_bucket = {
        "STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW": "ready_for_review",
        "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED": "partial_review_required",
        "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP": "evidence_gap",
    }
    for record in records:
        sample = {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "structure_label": record["structure_label"],
            "decomposition": record["decomposition"],
            "components": record["components"],
            "failure_codes": record["failure_codes"],
        }
        bucket = status_to_bucket[record["evidence_status"]]
        if len(samples[bucket]) < REVIEW_SAMPLE_LIMIT:
            samples[bucket].append(sample)
        if "AMBIGUOUS_DECOMPOSITION" in record["failure_codes"] and len(samples["ambiguous_decomposition"]) < REVIEW_SAMPLE_LIMIT:
            samples["ambiguous_decomposition"].append(sample)
    return samples


def build_structure_decomposition_report() -> dict[str, Any]:
    root = research_root()
    plan = load_json(PARSER_PLAN)
    evidence_join = load_json(EVIDENCE_JOIN)
    dictionary = load_dictionary(root)
    component_db = load_component_db(root)
    cjk_decomp = load_cjk_decomp(root)
    component_mappings = component_db.get("char_mappings", {})

    records = [
        build_record(row, dictionary, component_mappings, cjk_decomp)
        for row in evidence_join["row_records"]
    ]

    status_counts = Counter(record["evidence_status"] for record in records)
    structure_counts = Counter(record["structure_label"] or "UNRESOLVED" for record in records)
    failure_counts = Counter(
        failure
        for record in records
        for failure in record["failure_codes"]
    )
    source_hit_counts = Counter()
    for record in records:
        for source, hit in record["source_hits"].items():
            if hit:
                source_hit_counts[source] += 1

    overall_status = (
        "PASS_PHASE_1_STRUCTURE_DECOMPOSITION_EVIDENCE_PARSED"
        if len(records) == EXPECTED_OUTSIDE_8105_ROWS
        and plan["overall_status"] == "PASS_PARSER_IMPLEMENTATION_PLAN_READY"
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_phase_1_structure_decomposition_evidence_parser",
        "overall_status": overall_status,
        "next_workflow_status": "PHASE_1_EVIDENCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED",
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
            "outside_8105_rows": len(records),
            "gf0017_item": "structure_first_decomposition",
            "review_sample_limit": REVIEW_SAMPLE_LIMIT,
            "evidence_status_counts": dict(sorted(status_counts.items())),
            "structure_label_counts": dict(sorted(structure_counts.items())),
            "failure_code_counts": dict(sorted(failure_counts.items())),
            "source_hit_counts": dict(sorted(source_hit_counts.items())),
            "allowed_structure_set_size": len(ALLOWED_STRUCTURES),
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "samples": sample_records(records),
        "row_records": records,
        "decision": {
            "may_start_phase_1_evidence_review": overall_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Phase 1 parser produced read-only structure/decomposition evidence statuses. "
                "Human evidence review is required before any GF0017 score assignment or CNBE row repair."
            ),
        },
        "next_artifacts": [
            "reports/STRUCTURE_DECOMPOSITION_EVIDENCE_REVIEW.md",
            "reports/structure_decomposition_evidence_review.json",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Evidence Parser",
        "",
        "## Purpose",
        "",
        "This report is Phase 1 of the full-catalog parser workflow. It parses",
        "structure and decomposition evidence for outside-8105 Agent-standard",
        "candidate rows.",
        "",
        "It does not assign GF0017 scores, modify cnbe-research source assets,",
        "modify CNBE rows, rebuild databases, create tags, publish releases, or",
        "upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- GF0017 item: `{report['summary']['gf0017_item']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Source asset write allowed: `{report['summary']['source_asset_write_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Evidence Status Counts",
        "",
    ]
    for status, count in report["summary"]["evidence_status_counts"].items():
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Failure Code Counts", ""])
    if report["summary"]["failure_code_counts"]:
        for code, count in report["summary"]["failure_code_counts"].items():
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Source Hit Counts", ""])
    for source, count in report["summary"]["source_hit_counts"].items():
        lines.append(f"- `{source}`: {count}")

    lines.extend(["", "## Structure Label Counts", ""])
    for label, count in report["summary"]["structure_label_counts"].items():
        lines.append(f"- `{label}`: {count}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "Next allowed work is Phase 1 evidence review. Formal GF0017 scoring,",
            "CNBE row writes, source-asset edits, and database rebuilds remain",
            "blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_structure_decomposition_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
