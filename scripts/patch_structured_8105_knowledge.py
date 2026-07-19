#!/usr/bin/env python3
"""Patch structured 8105 knowledge files after human authorization.

This script writes only to the two authorized structured knowledge files under
`cnbe-research/knowledge/structured`. It does not modify CNBE encoding tables,
workbooks, databases, releases, tags, or PyPI artifacts.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
BASELINE = Path("evidence/8105/cnbe8105_standard_baseline.json")
BASE_CHARACTER_DATA = RESEARCH_ROOT / "knowledge/structured/base_character_data.json"
ENRICHED_KNOWLEDGE = RESEARCH_ROOT / "knowledge/structured/cnbe_character_knowledge.json"

DEFAULT_JSON_OUTPUT = Path("reports/structured_8105_knowledge_patch_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURED_8105_KNOWLEDGE_PATCH_REPORT.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def expected_unicode(char: str) -> str:
    return f"U+{ord(char):04X}"


def ordered_baseline_rows(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(baseline["characters"].values())
    return sorted(rows, key=lambda row: row.get("standard_rank") or 999999)


def base_row_from_baseline(row: dict[str, Any]) -> dict[str, Any]:
    char = row["char"]
    return {
        "char": char,
        "stroke_count": row.get("stroke_count"),
        "stroke_order": row.get("stroke_order") or [],
        "stroke_order_str": row.get("stroke_order_str") or "",
        "standard_rank": row.get("standard_rank"),
        "unicode": expected_unicode(char),
        "level": row.get("level"),
    }


def is_missing_value(value: Any) -> bool:
    return value is None or value == ""


def normalize_base_rows(
    baseline_rows: list[dict[str, Any]],
    current_rows: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    current_chars = {char for char in current_rows if len(char) == 1}
    baseline_chars = {row["char"] for row in baseline_rows}
    missing = sorted(baseline_chars - current_chars, key=ord)
    extra = sorted(current_chars - baseline_chars, key=ord)
    unicode_repairs = 0
    output: dict[str, dict[str, Any]] = {}
    for row in baseline_rows:
        char = row["char"]
        if char in current_rows:
            new_row = dict(current_rows[char])
            before = new_row.get("unicode")
            new_row["char"] = char
            new_row["unicode"] = expected_unicode(char)
            if before != new_row["unicode"]:
                unicode_repairs += 1
            for key, value in base_row_from_baseline(row).items():
                if key not in new_row or is_missing_value(new_row[key]):
                    new_row[key] = value
        else:
            new_row = base_row_from_baseline(row)
        output[char] = new_row
    return output, {
        "missing_before": missing,
        "extra_before": extra,
        "unicode_repairs": unicode_repairs,
        "rows_after": len(output),
    }


def keyed_enriched(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for row in rows:
        char = row.get("char")
        if isinstance(char, str) and len(char) == 1 and char not in keyed:
            keyed[char] = row
    return keyed


def enriched_row_from_baseline(row: dict[str, Any], template_keys: list[str]) -> dict[str, Any]:
    base = base_row_from_baseline(row)
    enriched_defaults: dict[str, Any] = {
        "has_dictionary_entry": False,
        "definition_sample": "",
        "wiki_summary": "",
        "has_wiki_entry": False,
        "kangxi_def": "",
        "kangxi_volume": "",
        "zhonghua_def": "",
    }
    output: dict[str, Any] = {}
    for key in template_keys:
        if key in base:
            output[key] = base[key]
        else:
            output[key] = enriched_defaults.get(key)
    for key, value in base.items():
        output.setdefault(key, value)
    for key, value in enriched_defaults.items():
        output.setdefault(key, value)
    return output


def normalize_enriched_rows(
    baseline_rows: list[dict[str, Any]],
    current_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    current_by_char = keyed_enriched(current_rows)
    current_chars = set(current_by_char)
    baseline_chars = {row["char"] for row in baseline_rows}
    missing = sorted(baseline_chars - current_chars, key=ord)
    extra = sorted(current_chars - baseline_chars, key=ord)
    template_keys = list(current_rows[0].keys()) if current_rows else list(base_row_from_baseline(baseline_rows[0]))
    unicode_repairs = 0
    output: list[dict[str, Any]] = []
    for row in baseline_rows:
        char = row["char"]
        if char in current_by_char:
            new_row = dict(current_by_char[char])
            before = new_row.get("unicode")
            new_row["char"] = char
            new_row["unicode"] = expected_unicode(char)
            if before != new_row["unicode"]:
                unicode_repairs += 1
            for key, value in base_row_from_baseline(row).items():
                if key not in new_row or is_missing_value(new_row[key]):
                    new_row[key] = value
        else:
            new_row = enriched_row_from_baseline(row, template_keys)
        output.append(new_row)
    return output, {
        "missing_before": missing,
        "extra_before": extra,
        "unicode_repairs": unicode_repairs,
        "rows_after": len(output),
    }


def backup_file(path: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"{path.name}.bak.{stamp}")
    shutil.copy2(path, backup)
    return str(backup)


def build_patch(*, apply: bool) -> dict[str, Any]:
    baseline = load_json(BASELINE)
    base_rows = load_json(BASE_CHARACTER_DATA)
    enriched_rows = load_json(ENRICHED_KNOWLEDGE)
    baseline_rows = ordered_baseline_rows(baseline)

    normalized_base, base_summary = normalize_base_rows(baseline_rows, base_rows)
    normalized_enriched, enriched_summary = normalize_enriched_rows(baseline_rows, enriched_rows)
    backups: dict[str, str] = {}
    if apply:
        backups["base_character_data"] = backup_file(BASE_CHARACTER_DATA)
        backups["cnbe_character_knowledge"] = backup_file(ENRICHED_KNOWLEDGE)
        write_json(BASE_CHARACTER_DATA, normalized_base)
        write_json(ENRICHED_KNOWLEDGE, normalized_enriched)

    return {
        "report_schema_version": "1.0",
        "mode": "apply_patch" if apply else "dry_run",
        "overall_status": "PASS",
        "authority_boundary": {
            "modified_authorized_structured_knowledge": apply,
            "does_not_modify_cnbe_encoding_tables": True,
            "does_not_score_rows": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
        },
        "inputs": {
            "baseline": str(BASELINE),
            "base_character_data": str(BASE_CHARACTER_DATA),
            "cnbe_character_knowledge": str(ENRICHED_KNOWLEDGE),
        },
        "backups": backups,
        "summary": {
            "baseline_rows": len(baseline_rows),
            "base_character_data": base_summary,
            "cnbe_character_knowledge": enriched_summary,
            "source_write_applied": apply,
            "batch_scoring_allowed": False,
        },
        "next_steps": [
            "rerun structured 8105 diff packet",
            "rerun cnbe-research source audit",
            "rerun knowledge inventory",
            "rerun GF0017 readiness gates",
            "then evaluate whether batch scoring can start",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structured 8105 Knowledge Patch Report",
        "",
        "## Purpose",
        "",
        "This report records the authorized repair of structured 8105 knowledge",
        "files under `cnbe-research/knowledge/structured`.",
        "",
        "It does not modify CNBE encoding tables, score rows, rebuild databases,",
        "create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Source write applied: `{report['summary']['source_write_applied']}`",
        f"- Baseline rows: `{report['summary']['baseline_rows']}`",
        f"- Batch scoring allowed by this patch: `{report['summary']['batch_scoring_allowed']}`",
        "",
        "## Dataset Repairs",
        "",
        "| Dataset | Missing before | Extra before | Unicode repairs | Rows after |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ["base_character_data", "cnbe_character_knowledge"]:
        summary = report["summary"][key]
        lines.append(
            f"| `{key}` | {len(summary['missing_before'])} | {len(summary['extra_before'])} | "
            f"{summary['unicode_repairs']} | {summary['rows_after']} |"
        )
    if report["backups"]:
        lines.extend(["", "## Backups", ""])
        for key, path in report["backups"].items():
            lines.append(f"- `{key}`: `{path}`")
    lines.extend(["", "## Next Steps", ""])
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write authorized structured knowledge repairs")
    args = parser.parse_args()
    report = build_patch(apply=args.apply)
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"mode={report['mode']}")
    if report["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
