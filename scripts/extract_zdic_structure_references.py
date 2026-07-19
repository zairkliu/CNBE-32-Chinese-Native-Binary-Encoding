#!/usr/bin/env python3
"""Extract ZDIC structure cross-reference fields into a bounded cache.

ZDIC is useful for automated review support, but it is not promoted to
national-standard authority by this script. The extractor reads local browser
snapshots first and can optionally try online fetches. Network failures are
recorded as field gaps rather than filled by inference.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

SNAPSHOT_DIR = Path("reports/zdic_snapshots")
DEFAULT_PACKET = Path("review_packets/300_character_8105_pilot/8105_no_legacy_human_recheck_packet.csv")
JSON_OUTPUT = Path("reports/zdic_structure_reference_extraction.json")
MARKDOWN_OUTPUT = Path("reports/ZDIC_STRUCTURE_REFERENCE_EXTRACTION.md")
CSV_OUTPUT = Path("review_packets/300_character_8105_pilot/zdic_structure_reference_extraction.csv")

ALLOWED_NORMALIZED_STRUCTURES = {
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

STRUCTURE_NORMALIZATION = {
    "单一结构": "独体字",
    "独体结构": "独体字",
    "独体字结构": "独体字",
    "上下结构": "上下",
    "上中下结构": "上中下",
    "左右结构": "左右",
    "左中右结构": "左中右",
    "左上包围结构": "左上包",
    "右上包围结构": "右上包",
    "左三包围结构": "左三包",
    "左下包围结构": "左下包",
    "上三包围结构": "上三包",
    "下三包围结构": "下三包",
    "全包围结构": "全包围",
    "镶嵌结构": "镶嵌",
}


def zdic_url(char: str) -> str:
    return f"https://www.zdic.net/hans/{quote(char)}"


def unicode_label(char: str) -> str:
    return f"U+{ord(char):04X}"


def snapshot_path(char: str) -> Path:
    return SNAPSHOT_DIR / f"{unicode_label(char).replace('+', '_')}_dom_snapshot.txt"


def read_packet_chars(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    chars: list[str] = []
    for row in rows:
        char = row.get("character") or row.get("char") or ""
        if char and char not in chars:
            chars.append(char)
    return chars


def visible_text_from_html(raw: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return compact_text(text)


def compact_text(raw: str) -> str:
    text = raw.replace("\u3000", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def find_after_label(text: str, label: str, value_pattern: str, stop_labels: list[str]) -> str:
    stop_pattern = "|".join(re.escape(item) for item in stop_labels)
    pattern = rf"{re.escape(label)}\s*(?P<value>{value_pattern})(?=\s*(?:{stop_pattern})|\n|$)"
    match = re.search(pattern, text)
    return match.group("value").strip() if match else ""


def extract_radical(raw: str) -> str:
    match = re.search(r"部首\s+\d+\s+link\s+Description:\s*(?P<value>[\u3400-\u9fff\U00020000-\U0003ffff⺀-⿿一-龥])", raw)
    if match:
        return match.group("value")
    match = re.search(r"部首\s+(?:link\s+Description:\s*)?\"?(?P<value>[\u3400-\u9fff\U00020000-\U0003ffff⺀-⿿一-龥])\"?", raw)
    if match:
        return match.group("value")
    match = re.search(r"部首\s*\n?\s*(?P<value>[\u3400-\u9fff\U00020000-\U0003ffff⺀-⿿一-龥])", raw)
    return match.group("value") if match else ""


def normalize_structure(raw_structure: str) -> str:
    if not raw_structure:
        return ""
    value = raw_structure.strip()
    if value in STRUCTURE_NORMALIZATION:
        return STRUCTURE_NORMALIZATION[value]
    value = value.replace("结构", "")
    return value if value in ALLOWED_NORMALIZED_STRUCTURES else ""


def parse_zdic_text(char: str, raw: str, source_kind: str, source_path: str) -> dict[str, Any]:
    text = compact_text(raw)
    if "<html" in raw.lower() or "</" in raw:
        text = visible_text_from_html(raw)
    stop_labels = ["部外", "总笔画", "统一码", "笔顺", "字形结构", "字形分析", "异体", "基本解释"]
    total_strokes = find_after_label(text, "总笔画", r"[0-9]+", stop_labels)
    unicode_value = find_after_label(text, "统一码", r"(?:CJK(?:-[A-Z])?\s*)?[0-9A-Fa-f]+", stop_labels)
    stroke_order = find_after_label(text, "笔顺", r"[0-9]+", stop_labels)
    raw_structure = find_after_label(text, "字形结构", r"[\u4e00-\u9fff]+结构|[\u4e00-\u9fff]+", stop_labels)
    glyph_analysis = find_after_label(text, "字形分析", r"[\u4e00-\u9fff]+", stop_labels)
    radical = extract_radical(text)
    normalized_structure = normalize_structure(raw_structure)
    fields = {
        "radical": radical,
        "total_strokes": total_strokes,
        "unicode_value": unicode_value,
        "stroke_order": stroke_order,
        "raw_structure": raw_structure,
        "normalized_structure": normalized_structure,
        "glyph_analysis": glyph_analysis,
    }
    found_fields = [key for key, value in fields.items() if value]
    return {
        "character": char,
        "unicode_codepoint": unicode_label(char),
        "zdic_url": zdic_url(char),
        "source_kind": source_kind,
        "source_path": source_path,
        "source_level": "network_cross_reference",
        "authority_boundary": "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD",
        "fields": fields,
        "found_field_count": len(found_fields),
        "found_fields": found_fields,
        "parse_status": "PARSED_WITH_STRUCTURE" if normalized_structure else "PARSED_WITHOUT_NORMALIZED_STRUCTURE",
    }


def fetch_online(char: str, timeout: int) -> tuple[str, str]:
    import requests

    response = requests.get(
        zdic_url(char),
        timeout=timeout,
        headers={"User-Agent": "CNBE research structure reference extractor"},
    )
    response.raise_for_status()
    return response.text, response.url


def extract_for_char(char: str, allow_online: bool, timeout: int) -> dict[str, Any]:
    path = snapshot_path(char)
    if path.exists():
        return parse_zdic_text(char, path.read_text(encoding="utf-8"), "local_snapshot", str(path))
    if allow_online:
        try:
            text, url = fetch_online(char, timeout)
            return parse_zdic_text(char, text, "online_fetch", url)
        except Exception as exc:  # noqa: BLE001 - network errors are recorded as evidence gaps.
            return {
                "character": char,
                "unicode_codepoint": unicode_label(char),
                "zdic_url": zdic_url(char),
                "source_kind": "online_fetch_failed",
                "source_path": "",
                "source_level": "network_cross_reference",
                "authority_boundary": "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD",
                "fields": {},
                "found_field_count": 0,
                "found_fields": [],
                "parse_status": "NETWORK_OR_PARSE_GAP",
                "error": f"{type(exc).__name__}: {exc}",
            }
    return {
        "character": char,
        "unicode_codepoint": unicode_label(char),
        "zdic_url": zdic_url(char),
        "source_kind": "missing_snapshot_online_disabled",
        "source_path": "",
        "source_level": "network_cross_reference",
        "authority_boundary": "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD",
        "fields": {},
        "found_field_count": 0,
        "found_fields": [],
        "parse_status": "SNAPSHOT_GAP",
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "character",
        "unicode_codepoint",
        "zdic_url",
        "source_kind",
        "parse_status",
        "radical",
        "total_strokes",
        "unicode_value",
        "stroke_order",
        "raw_structure",
        "normalized_structure",
        "glyph_analysis",
        "authority_boundary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for record in records:
            fields = record.get("fields", {})
            writer.writerow({
                "character": record["character"],
                "unicode_codepoint": record["unicode_codepoint"],
                "zdic_url": record["zdic_url"],
                "source_kind": record["source_kind"],
                "parse_status": record["parse_status"],
                "radical": fields.get("radical", ""),
                "total_strokes": fields.get("total_strokes", ""),
                "unicode_value": fields.get("unicode_value", ""),
                "stroke_order": fields.get("stroke_order", ""),
                "raw_structure": fields.get("raw_structure", ""),
                "normalized_structure": fields.get("normalized_structure", ""),
                "glyph_analysis": fields.get("glyph_analysis", ""),
                "authority_boundary": record["authority_boundary"],
            })


def build_report(chars: list[str], allow_online: bool, timeout: int) -> dict[str, Any]:
    records = [extract_for_char(char, allow_online, timeout) for char in chars]
    parsed_with_structure = [
        record for record in records
        if record["parse_status"] == "PARSED_WITH_STRUCTURE"
    ]
    checks = {
        "bounded_character_list": len(chars) <= 200,
        "does_not_assign_gf0017_points": True,
        "does_not_write_cnbe_rows": True,
        "does_not_rebuild_database": True,
        "zdic_is_network_cross_reference_only": True,
    }
    return {
        "report_schema_version": "1.0",
        "mode": "zdic_structure_reference_extraction",
        "overall_status": "PASS_ZDIC_STRUCTURE_REFERENCE_EXTRACTION_READY" if all(checks.values()) else "BLOCKED",
        "next_workflow_status": "ZDIC_STRUCTURE_REFERENCES_AVAILABLE_FOR_REVIEW_NOT_SCORING",
        "summary": {
            "requested_chars": len(chars),
            "parsed_with_structure": len(parsed_with_structure),
            "records_with_any_fields": sum(1 for record in records if record["found_field_count"] > 0),
            "online_fetch_enabled": allow_online,
            "gf0017_points_assigned": 0,
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "records": records,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MARKDOWN_OUTPUT),
            "csv": str(CSV_OUTPUT),
        },
        "decision": {
            "may_use_as_network_cross_reference": True,
            "may_promote_to_national_standard": False,
            "may_assign_gf0017_points_directly": False,
            "may_write_cnbe_rows": False,
            "reason": (
                "ZDIC fields are now machine-extracted as network cross-reference "
                "evidence. They can reduce manual lookup work but still require "
                "standards-aware review before scoring or encoding changes."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZDIC Structure Reference Extraction",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Requested characters: {report['summary']['requested_chars']}",
        f"- Parsed with normalized structure: {report['summary']['parsed_with_structure']}",
        f"- Records with any fields: {report['summary']['records_with_any_fields']}",
        f"- Online fetch enabled: `{report['summary']['online_fetch_enabled']}`",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        "",
        "ZDIC is machine-extracted as `network_cross_reference` only. It is not",
        "national-standard authority and does not directly assign scores.",
        "",
        "## Extracted Rows",
        "",
        "| Char | Unicode | Status | Structure | Radical | Strokes | URL |",
        "|---|---|---|---|---|---:|---|",
    ]
    for record in report["records"]:
        fields = record.get("fields", {})
        lines.append(
            f"| {record['character']} | `{record['unicode_codepoint']}` | `{record['parse_status']}` | "
            f"`{fields.get('raw_structure', '')}` | `{fields.get('radical', '')}` | "
            f"`{fields.get('total_strokes', '')}` | {record['zdic_url']} |"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chars", nargs="*", default=[])
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--timeout", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chars = list(dict.fromkeys(args.chars or read_packet_chars(args.packet)))
    report = build_report(chars, args.online, args.timeout)
    write_json(JSON_OUTPUT, report)
    write_text(MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(CSV_OUTPUT, report["records"])
    print(report["overall_status"])
    print(f"requested_chars={report['summary']['requested_chars']}")
    print(f"parsed_with_structure={report['summary']['parsed_with_structure']}")
    print(f"csv={CSV_OUTPUT}")


if __name__ == "__main__":
    main()
