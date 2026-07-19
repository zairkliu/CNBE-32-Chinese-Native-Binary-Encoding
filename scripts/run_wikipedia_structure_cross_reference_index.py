#!/usr/bin/env python3
"""Run a read-only offline-Wikipedia cross-reference index for source gaps."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_CONFIG = Path("data/sources/cnbe-research-local.json")
INDEX_PLAN = Path("reports/wikipedia_structure_cross_reference_index_plan.json")
DICTIONARY_EXTRACTOR = Path("reports/structure_decomposition_dictionary_gap_extractor.json")

DEFAULT_JSON_OUTPUT = Path("reports/wikipedia_structure_cross_reference_index.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/WIKIPEDIA_STRUCTURE_CROSS_REFERENCE_INDEX.md")

EXPECTED_TARGET_ROWS = 84_939
MAX_HITS_PER_CHAR = 3
SNIPPET_RADIUS = 60
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


def target_records() -> list[dict[str, Any]]:
    extractor = load_json(DICTIONARY_EXTRACTOR)
    return [
        record
        for record in extractor["row_records"]
        if record["review_status"] == "NO_DICTIONARY_REVIEW_HIT"
    ]


def snippet_for_char(text: str, char: str) -> str:
    index = text.find(char)
    if index < 0:
        return ""
    start = max(0, index - SNIPPET_RADIUS)
    end = min(len(text), index + SNIPPET_RADIUS + 1)
    return text[start:end].replace("\n", " ")


def char_hit_record(item: dict[str, Any], char: str, field: str) -> dict[str, Any]:
    text = item.get(field, "") or ""
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "field": field,
        "tags": (item.get("tags") or "")[:240],
        "snippet": snippet_for_char(text, char),
        "text_len": len(item.get("text", "") or ""),
        "source_grade": "lowest_tier_cross_reference",
        "can_assign_points": False,
    }


def matching_target_chars(item: dict[str, Any], pending_chars: set[str]) -> dict[str, str]:
    fields = {
        "title": item.get("title", "") or "",
        "tags": item.get("tags", "") or "",
        "text": item.get("text", "") or "",
    }
    matches: dict[str, str] = {}
    for field_name, text in fields.items():
        for char in set(text) & pending_chars:
            matches.setdefault(char, field_name)
    return matches


def build_wikipedia_index(max_articles: int | None = None) -> dict[str, Any]:
    root = research_root()
    plan = load_json(INDEX_PLAN)
    wiki_path = root / "knowledge/wikipedia-zh-cn-20260501.json"
    targets = target_records()
    target_by_char = {record["char"]: record for record in targets}
    pending_chars = set(target_by_char)
    hits_by_char: dict[str, list[dict[str, Any]]] = {char: [] for char in pending_chars}
    article_count = 0
    invalid_json_lines = 0
    start_time = time.time()

    with wiki_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if max_articles is not None and article_count >= max_articles:
                break
            line = line.strip()
            if not line:
                continue
            article_count += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_lines += 1
                continue
            matches = matching_target_chars(item, pending_chars)
            for char, field in matches.items():
                if len(hits_by_char[char]) >= MAX_HITS_PER_CHAR:
                    continue
                hits_by_char[char].append(char_hit_record(item, char, field))
                if len(hits_by_char[char]) >= MAX_HITS_PER_CHAR:
                    pending_chars.discard(char)
            if not pending_chars:
                break

    row_records: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    unicode_block_counts: Counter[str] = Counter()
    for record in targets:
        hits = hits_by_char[record["char"]]
        status = "WIKI_CROSS_REFERENCE_HIT" if hits else "NO_WIKI_CROSS_REFERENCE_HIT"
        status_counts[status] += 1
        unicode_block_counts[record["unicode_block"]] += 1
        row_records.append(
            {
                "offset": record["offset"],
                "worksheet_row": record["worksheet_row"],
                "char": record["char"],
                "unicode": record["unicode"],
                "unicode_block": record["unicode_block"],
                "source_gap_failure_codes": record["source_gap_failure_codes"],
                "wiki_review_status": status,
                "wiki_hits": hits,
                "source_grade": "lowest_tier_cross_reference",
                "can_assign_points": False,
                "score": None,
                "score_status": "NOT_SCORED_WIKI_CROSS_REFERENCE_ONLY",
            }
        )

    hit_rows = [record for record in row_records if record["wiki_hits"]]
    elapsed = round(time.time() - start_time, 3)
    full_run = max_articles is None
    overall_status = (
        "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_READY"
        if plan["overall_status"] == "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_PLAN_READY"
        and len(row_records) == EXPECTED_TARGET_ROWS
        else "BLOCKED"
    )
    if not full_run:
        overall_status = "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_SAMPLE_READY"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_wikipedia_structure_cross_reference_index",
        "overall_status": overall_status,
        "next_workflow_status": "WIKI_CROSS_REFERENCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED",
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
            "target_rows": len(row_records),
            "unique_target_chars": len(target_by_char),
            "articles_scanned": article_count,
            "invalid_json_lines": invalid_json_lines,
            "max_articles": max_articles,
            "max_hits_per_char": MAX_HITS_PER_CHAR,
            "elapsed_seconds": elapsed,
            "wiki_review_status_counts": dict(sorted(status_counts.items())),
            "target_unicode_block_counts": dict(sorted(unicode_block_counts.items())),
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "samples": {
            "wiki_cross_reference_hits": hit_rows[:SAMPLE_LIMIT],
            "no_wiki_cross_reference_hit": [
                {
                    "offset": record["offset"],
                    "worksheet_row": record["worksheet_row"],
                    "char": record["char"],
                    "unicode": record["unicode"],
                    "unicode_block": record["unicode_block"],
                }
                for record in row_records
                if not record["wiki_hits"]
            ][:SAMPLE_LIMIT],
        },
        "row_records": row_records,
        "decision": {
            "may_start_wiki_cross_reference_review": overall_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Offline Wiki cross-references have been materialized as lowest-tier review aids only. "
                "They do not authorize scoring, source-asset edits, CNBE row writes, or database rebuilds."
            ),
        },
        "next_artifacts": [
            "reports/WIKIPEDIA_STRUCTURE_CROSS_REFERENCE_REVIEW.md",
            "reports/wikipedia_structure_cross_reference_review.json",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Wikipedia Structure Cross-Reference Index",
        "",
        "## Purpose",
        "",
        "This report materializes lowest-tier offline-Wikipedia cross-references",
        "for structure/decomposition source-gap rows that lacked dictionary or",
        "character-origin review hits.",
        "",
        "It does not assign GF0017 scores, modify source assets, write CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Target rows: `{report['summary']['target_rows']}`",
        f"- Articles scanned: `{report['summary']['articles_scanned']}`",
        f"- Invalid JSON lines: `{report['summary']['invalid_json_lines']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        "",
        "## Wiki Review Status Counts",
        "",
    ]
    for status, count in report["summary"]["wiki_review_status_counts"].items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-articles", type=int, default=None)
    args = parser.parse_args()
    report = build_wikipedia_index(max_articles=args.max_articles)
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
