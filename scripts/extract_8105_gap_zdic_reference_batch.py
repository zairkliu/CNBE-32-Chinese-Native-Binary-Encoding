#!/usr/bin/env python3
"""Extract ZDIC cross-reference records for the 8105 gap queue.

This is a review-support cache builder. ZDIC records are network
cross-reference context only; they do not become national-standard evidence,
GF0017 points, CNBE rows, or database records.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.extract_zdic_structure_references import extract_for_char, unicode_label

GAP_QUEUE = Path("review_packets/8105_full/8105_full_zdic_gap_queue.csv")
CACHE_DIR = Path("reports/zdic_8105_gap_cache")
JSON_OUTPUT = Path("reports/8105_gap_zdic_reference_batch.json")
CSV_OUTPUT = Path("review_packets/8105_full/8105_gap_zdic_reference_batch.csv")
MD_OUTPUT = Path("reports/8105_GAP_ZDIC_REFERENCE_BATCH.md")
MAX_WORKERS = 8


def read_gap_chars(path: Path = GAP_QUEUE) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    chars: list[str] = []
    for row in rows:
        char = row["character"]
        if char not in chars:
            chars.append(char)
    return chars


def cache_path(char: str) -> Path:
    return CACHE_DIR / f"{unicode_label(char).replace('+', '_')}.json"


def read_or_fetch(char: str, timeout: int, refresh: bool) -> dict[str, Any]:
    path = cache_path(char)
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    record = extract_for_char(char, allow_online=True, timeout=timeout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields", {})
    return {
        "character": record["character"],
        "unicode_codepoint": record["unicode_codepoint"],
        "parse_status": record["parse_status"],
        "source_kind": record["source_kind"],
        "radical": fields.get("radical", ""),
        "total_strokes": fields.get("total_strokes", ""),
        "unicode_value": fields.get("unicode_value", ""),
        "stroke_order": fields.get("stroke_order", ""),
        "raw_structure": fields.get("raw_structure", ""),
        "normalized_structure": fields.get("normalized_structure", ""),
        "glyph_analysis": fields.get("glyph_analysis", ""),
        "authority_boundary": record["authority_boundary"],
        "zdic_url": record["zdic_url"],
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        writer.writerows(rows)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Gap ZDIC Reference Batch",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Requested rows: {report['summary']['requested_rows']}",
        f"- Parsed with normalized structure: {report['summary']['parsed_with_structure']}",
        f"- Records with any fields: {report['summary']['records_with_any_fields']}",
        f"- Failed or missing records: {report['summary']['failed_or_missing_records']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "ZDIC remains `network_cross_reference` only. It may reduce manual lookup",
        "work, but it cannot assign national-standard structure, GF0017 points,",
        "or CNBE rows without later standard-aware review.",
        "",
        "## Status Counts",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["parse_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def build_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(record["parse_status"] for record in records)
    checks = {
        "all_records_are_cross_reference_only": all(
            record["authority_boundary"] == "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD"
            for record in records
        ),
        "does_not_assign_gf0017_points": True,
        "does_not_write_cnbe_rows": True,
        "does_not_rebuild_database": True,
    }
    return {
        "report_schema_version": "1.0",
        "mode": "8105_gap_zdic_reference_batch",
        "overall_status": "PASS_8105_GAP_ZDIC_REFERENCE_BATCH_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "requested_rows": len(records),
            "parsed_with_structure": status_counts["PARSED_WITH_STRUCTURE"],
            "records_with_any_fields": sum(1 for record in records if record["found_field_count"] > 0),
            "failed_or_missing_records": len(records) - status_counts["PARSED_WITH_STRUCTURE"],
            "parse_status_counts": dict(status_counts),
            "gf0017_points_assigned": 0,
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "records": records,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "csv": str(CSV_OUTPUT),
            "markdown_report": str(MD_OUTPUT),
            "cache_dir": str(CACHE_DIR),
        },
        "decision": {
            "may_use_as_network_cross_reference": all(checks.values()),
            "may_promote_to_national_standard": False,
            "may_assign_gf0017_points_directly": False,
            "may_write_cnbe_rows": False,
        },
    }


def run(limit: int | None, timeout: int, workers: int, refresh: bool) -> dict[str, Any]:
    chars = read_gap_chars()
    if limit is not None:
        chars = chars[:limit]
    records_by_char: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(read_or_fetch, char, timeout, refresh): char for char in chars}
        for future in as_completed(futures):
            char = futures[future]
            try:
                records_by_char[char] = future.result()
            except Exception as exc:  # noqa: BLE001 - preserve extraction gaps.
                records_by_char[char] = {
                    "character": char,
                    "unicode_codepoint": unicode_label(char),
                    "zdic_url": "",
                    "source_kind": "batch_exception",
                    "source_path": "",
                    "source_level": "network_cross_reference",
                    "authority_boundary": "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD",
                    "fields": {},
                    "found_field_count": 0,
                    "found_fields": [],
                    "parse_status": "NETWORK_OR_PARSE_GAP",
                    "error": f"{type(exc).__name__}: {exc}",
                }
    records = [records_by_char[char] for char in chars]
    report = build_report(records)
    write_json(JSON_OUTPUT, report)
    write_csv(CSV_OUTPUT, [flatten_record(record) for record in records])
    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run(args.limit, args.timeout, args.workers, args.refresh)
    print(report["overall_status"])
    print(f"requested_rows={report['summary']['requested_rows']}")
    print(f"parsed_with_structure={report['summary']['parsed_with_structure']}")
    print(f"failed_or_missing_records={report['summary']['failed_or_missing_records']}")


if __name__ == "__main__":
    main()
