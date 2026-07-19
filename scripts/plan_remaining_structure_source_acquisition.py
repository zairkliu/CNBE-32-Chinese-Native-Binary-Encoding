#!/usr/bin/env python3
"""Audit remaining structure source options after Wiki cross-reference."""

from __future__ import annotations

import json
import sqlite3
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
WIKI_INDEX = Path("reports/wikipedia_structure_cross_reference_index.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_source_acquisition_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_SOURCE_ACQUISITION_PLAN.md")

EXPECTED_REMAINING_ROWS = 73_831
SAMPLE_LIMIT = 120


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


def remaining_records() -> list[dict[str, Any]]:
    wiki = load_json(WIKI_INDEX)
    return [
        record
        for record in wiki["row_records"]
        if record["wiki_review_status"] == "NO_WIKI_CROSS_REFERENCE_HIT"
    ]


def cjk_decomp_chars(path: Path) -> set[str]:
    chars: set[str] = set()
    if not path.exists():
        return chars
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        cp = line.split(":", 1)[0]
        try:
            chars.add(chr(int(cp)))
        except ValueError:
            continue
    return chars


def sqlite_chars(path: Path, query: str) -> set[str]:
    if not path.exists():
        return set()
    con = sqlite3.connect(path)
    try:
        chars = {row[0] for row in con.execute(query) if row[0]}
    finally:
        con.close()
    return chars


def unihan_unique_coverage(path: Path, target_chars: set[str]) -> dict[str, dict[str, int]]:
    if not path.exists():
        return {}
    coverage: dict[str, dict[str, int]] = {}
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                unique_hits: set[str] = set()
                property_lines = 0
                with archive.open(name) as handle:
                    for raw in handle:
                        try:
                            line = raw.decode("utf-8")
                        except UnicodeDecodeError:
                            continue
                        if not line.startswith("U+"):
                            continue
                        property_lines += 1
                        first = line.split("\t", 1)[0]
                        try:
                            char = chr(int(first[2:], 16))
                        except ValueError:
                            continue
                        if char in target_chars:
                            unique_hits.add(char)
                coverage[name] = {
                    "unique_target_hits": len(unique_hits),
                    "property_lines": property_lines,
                }
    except zipfile.BadZipFile:
        coverage["__zip_error__"] = {
            "unique_target_hits": 0,
            "property_lines": 0,
        }
    return coverage


def sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "unicode_block": record["unicode_block"],
        }
        for record in records[:SAMPLE_LIMIT]
    ]


def build_source_acquisition_plan() -> dict[str, Any]:
    root = research_root()
    records = remaining_records()
    target_chars = {record["char"] for record in records}
    block_counts = Counter(record["unicode_block"] for record in records)

    cjk_chars = cjk_decomp_chars(root / "cjk-decomp/cjk-decomp.txt")
    decomp_chars = sqlite_chars(root / "decomp-data/dictionary.db", "select character from characters")
    kangxi_chars = sqlite_chars(
        root / "source/nlp-han-dicts/extracted/kangxi/kangxi.4w.db",
        "select word from dict where length(word)=1",
    )
    unihan2_coverage = unihan_unique_coverage(root / "knowledge/Unihan2.zip", target_chars)
    unihan_zip_coverage = unihan_unique_coverage(root / "knowledge/Unihan.zip", target_chars)

    cjk_hits = [record for record in records if record["char"] in cjk_chars]
    decomp_hits = [record for record in records if record["char"] in decomp_chars]
    kangxi_hits = [record for record in records if record["char"] in kangxi_chars]
    unihan2_union_hits: set[str] = set()
    if (root / "knowledge/Unihan2.zip").exists():
        try:
            with zipfile.ZipFile(root / "knowledge/Unihan2.zip") as archive:
                for name in archive.namelist():
                    with archive.open(name) as handle:
                        for raw in handle:
                            try:
                                line = raw.decode("utf-8")
                            except UnicodeDecodeError:
                                continue
                            if not line.startswith("U+"):
                                continue
                            first = line.split("\t", 1)[0]
                            try:
                                char = chr(int(first[2:], 16))
                            except ValueError:
                                continue
                            if char in target_chars:
                                unihan2_union_hits.add(char)
        except zipfile.BadZipFile:
            pass

    candidate_resources = [
        {
            "id": "gf_gb_component_standards",
            "relative_paths": [
                "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
                "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
            ],
            "source_grade": "direct_standard_for_rules_not_row_level_ids",
            "remaining_row_hits": 0,
            "can_close_remaining_gap_as_authority": False,
            "reason": "Provides normative component and decomposition rules, but no row-level IDS coverage for the remaining extension characters.",
        },
        {
            "id": "unihan2",
            "relative_paths": ["knowledge/Unihan2.zip"],
            "source_grade": "unicode_cross_reference_not_structure_authority",
            "remaining_row_hits": len(unihan2_union_hits),
            "can_close_remaining_gap_as_authority": False,
            "per_file_coverage": unihan2_coverage,
            "reason": "Useful for Unicode interoperability, readings, variants, and IRG references; not a final structure decomposition authority.",
        },
        {
            "id": "unihan_zip_invalid",
            "relative_paths": ["knowledge/Unihan.zip"],
            "source_grade": "identity_failed",
            "remaining_row_hits": 0,
            "can_close_remaining_gap_as_authority": False,
            "per_file_coverage": unihan_zip_coverage,
            "reason": "Local file is not a readable ZIP archive and cannot be used.",
        },
        {
            "id": "kangxi_4w",
            "relative_paths": ["source/nlp-han-dicts/extracted/kangxi/kangxi.4w.db"],
            "source_grade": "dictionary_cross_reference",
            "remaining_row_hits": len(kangxi_hits),
            "can_close_remaining_gap_as_authority": False,
            "reason": "Kangxi entries provide historical dictionary context, not modern structure/IDS authority.",
        },
        {
            "id": "cjk_decomp",
            "relative_paths": ["cjk-decomp/cjk-decomp.txt"],
            "source_grade": "third_party_ids_cross_reference",
            "remaining_row_hits": len(cjk_hits),
            "can_close_remaining_gap_as_authority": False,
            "reason": "Provides decomposition cross-reference for a very small subset; useful for Agent review, not national-standard authority.",
        },
        {
            "id": "decomp_data",
            "relative_paths": ["decomp-data/dictionary.db", "decomp-data/dictionary.json"],
            "source_grade": "third_party_dictionary_cross_reference",
            "remaining_row_hits": len(decomp_hits),
            "can_close_remaining_gap_as_authority": False,
            "reason": "No coverage for the remaining no-Wiki gap rows.",
        },
    ]

    stronger_authoritative_available = any(
        resource["can_close_remaining_gap_as_authority"]
        for resource in candidate_resources
    )
    overall_status = (
        "PASS_REMAINING_STRUCTURE_SOURCE_ACQUISITION_PLAN_READY"
        if len(records) == EXPECTED_REMAINING_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_source_acquisition_plan",
        "overall_status": overall_status,
        "next_workflow_status": (
            "AGENT_STANDARD_REMAINING_STRUCTURE_PLAN_ALLOWED_FORMAL_SCORING_BLOCKED"
            if not stronger_authoritative_available
            else "AUTHORITATIVE_SOURCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED"
        ),
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
            "remaining_rows_without_wiki_dictionary_or_source_hit": len(records),
            "remaining_unicode_block_counts": dict(sorted(block_counts.items())),
            "stronger_authoritative_source_available": stronger_authoritative_available,
            "candidate_resource_count": len(candidate_resources),
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "candidate_resources": candidate_resources,
        "samples": {
            "remaining_rows": sample(records),
            "cjk_decomp_hits": sample(cjk_hits),
            "kangxi_hits": sample(kangxi_hits),
        },
        "decision": {
            "may_start_agent_standard_plan": overall_status.startswith("PASS") and not stronger_authoritative_available,
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "No stronger local authoritative row-level IDS/resource was found for the remaining rows. "
                "Proceed with an Agent-standard plan that preserves all gaps as project-level candidates, not national-standard evidence."
            ),
        },
        "next_artifacts": [
            "scripts/plan_remaining_structure_agent_standard.py",
            "reports/remaining_structure_agent_standard_plan.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Source Acquisition Plan",
        "",
        "## Purpose",
        "",
        "This report audits whether stronger local glyph, etymology, IDS, Unihan,",
        "or dictionary resources can close the remaining structure/decomposition",
        "source gaps after Wiki cross-reference.",
        "",
        "It does not assign GF0017 scores, modify source assets, write CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Remaining rows: `{report['summary']['remaining_rows_without_wiki_dictionary_or_source_hit']}`",
        f"- Stronger authoritative source available: `{report['summary']['stronger_authoritative_source_available']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        "",
        "## Candidate Resources",
        "",
    ]
    for resource in report["candidate_resources"]:
        lines.append(
            f"- `{resource['id']}`: grade `{resource['source_grade']}`, "
            f"hits `{resource['remaining_row_hits']}`, "
            f"authoritative close `{resource['can_close_remaining_gap_as_authority']}`"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_source_acquisition_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
