#!/usr/bin/env python3
"""Collect cached ZDIC cross-reference evidence for the human-audited T3 batch."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract_zdic_structure_references import parse_zdic_text, zdic_url

MERGED = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_AUDIT_MERGED.csv"
INVENTORY = ROOT / "evidence" / "8105" / "PENDING_276_ENCODING_INVENTORY.csv"
OUTPUT_DIR = ROOT / "evidence" / "8105" / "pending276" / "zdic"
JSON_OUTPUT = OUTPUT_DIR / "T3_169_276_ZDIC_CROSS_REFERENCE.json"
CSV_OUTPUT = OUTPUT_DIR / "T3_169_276_ZDIC_CROSS_REFERENCE.csv"
REPORT_OUTPUT = ROOT / "reports" / "PENC276_T3_169_276_ZDIC_CROSS_REFERENCE.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def fetch_and_cache(char: str) -> dict[str, object]:
    from scripts.extract_zdic_structure_references import fetch_online

    cache_path = OUTPUT_DIR / "raw" / f"{ord(char):X}.html"
    if cache_path.exists():
        return parse_zdic_text(char, cache_path.read_text(encoding="utf-8"), "local_cache", str(cache_path))
    try:
        raw, url = fetch_online(char, timeout=12)
    except Exception as exc:  # noqa: BLE001 - evidence gaps are explicit output.
        return {
            "character": char,
            "unicode_codepoint": f"U+{ord(char):04X}",
            "zdic_url": zdic_url(char),
            "source_kind": "online_fetch_failed",
            "source_path": "",
            "source_level": "network_cross_reference",
            "authority_boundary": "ZDIC_STRUCTURE_REFERENCE_NOT_NATIONAL_STANDARD",
            "fields": {},
            "parse_status": "NETWORK_OR_PARSE_GAP",
            "error": f"{type(exc).__name__}: {exc}",
        }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(raw, encoding="utf-8")
    return parse_zdic_text(char, raw, "online_fetch", url)


def main() -> None:
    merged_rows = read_csv(MERGED)
    inventory_by_char = {row["char"]: row for row in read_csv(INVENTORY)}
    if len(merged_rows) != 108:
        raise ValueError("expected 108 merged T3 audit rows")
    records = []
    for row in merged_rows:
        record = fetch_and_cache(row["char"])
        fields = record.get("fields", {})
        inventory = inventory_by_char[row["char"]]
        zdic_structure = fields.get("normalized_structure", "")
        records.append(
            {
                "row_id": row["row_id"],
                "char": row["char"],
                "unicode": row["unicode"],
                "human_structure": row["struct_name_human_approved"],
                "zdic_radical": fields.get("radical", ""),
                "zdic_total_strokes": fields.get("total_strokes", ""),
                "zdic_structure": zdic_structure,
                "structure_relation": "AGREE" if zdic_structure == row["struct_name_human_approved"] else "GAP_OR_DISAGREE",
                "inventory_unihan_radical": inventory["unihan_kangxi_radical"],
                "inventory_baseline_strokes": inventory["baseline_stroke_count"],
                "inventory_unihan_strokes": inventory["unihan_total_strokes"],
                "parse_status": record["parse_status"],
                "source_kind": record["source_kind"],
                "zdic_url": record["zdic_url"],
            }
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "rows": len(records),
        "records_with_zdic_radical": sum(bool(record["zdic_radical"]) for record in records),
        "records_with_zdic_strokes": sum(bool(record["zdic_total_strokes"]) for record in records),
        "structure_agree": sum(record["structure_relation"] == "AGREE" for record in records),
        "structure_gap_or_disagree": sum(record["structure_relation"] != "AGREE" for record in records),
        "parse_gaps": sum(record["parse_status"] == "NETWORK_OR_PARSE_GAP" for record in records),
    }
    report = {
        "schema_version": "penc276-t3-zdic-cross-reference-v1",
        "scope": "network_cross_reference_only",
        "summary": summary,
        "records": records,
        "decision": {
            "status": "PASS_ZDIC_T3_CROSS_REFERENCE_COLLECTED",
            "may_promote_to_national_standard": False,
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
        },
    }
    JSON_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_OUTPUT.write_text(
        "# PENC276 T3 第 169–276 行 ZDIC 交叉参考采集\n\n"
        f"- 处理行：`{summary['rows']}`。\n"
        f"- 取得 ZDIC 部首：`{summary['records_with_zdic_radical']}`。\n"
        f"- 取得 ZDIC 总笔画：`{summary['records_with_zdic_strokes']}`。\n"
        f"- 与人工结构一致：`{summary['structure_agree']}`；缺口或分歧：`{summary['structure_gap_or_disagree']}`。\n"
        f"- 网络或解析缺口：`{summary['parse_gaps']}`。\n\n"
        "ZDIC 仅作为网络交叉参考。该采集不生成 CNBE 候选，不提升为国家标准，不写源表。\n",
        encoding="utf-8",
    )
    print(report["decision"]["status"])


if __name__ == "__main__":
    main()
