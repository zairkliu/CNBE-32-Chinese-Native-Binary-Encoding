#!/usr/bin/env python3
"""Perform read-only ZDIC/Unihan radical adjudication for the T3 audit batch."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "cnbe32.db"
INVENTORY = ROOT / "evidence" / "8105" / "PENDING_276_ENCODING_INVENTORY.csv"
ZDIC = ROOT / "evidence" / "8105" / "pending276" / "zdic" / "T3_169_276_ZDIC_CROSS_REFERENCE.csv"
EVIDENCE_DIR = ROOT / "evidence" / "8105" / "pending276"
MAPPING = EVIDENCE_DIR / "radical_name_to_kangxi.json"
ADJUDICATION = EVIDENCE_DIR / "T3_169_276_RADICAL_ADJUDICATION.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_RADICAL_ADJUDICATION.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_RADICAL_ADJUDICATION.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def build_mapping() -> dict[str, list[int]]:
    values: dict[str, set[int]] = defaultdict(set)
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as connection:
        for name, radix in connection.execute(
            "select radix_name, radix from cnbe32 where track = 'standard' and radix_name is not null and radix is not null"
        ):
            values[name].add(radix)
    return {name: sorted(radixes) for name, radixes in sorted(values.items())}


def main() -> None:
    zdic_rows = {row["char"]: row for row in read_csv(ZDIC)}
    inventory_rows = [
        row
        for row in read_csv(INVENTORY)
        if 169 <= int(row["row_id"].split("_")[1]) <= 276
    ]
    if len(inventory_rows) != 108 or set(zdic_rows) != {row["char"] for row in inventory_rows}:
        raise ValueError("ZDIC output must cover the exact 108-row T3 batch")
    mapping = build_mapping()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    MAPPING.write_text(
        json.dumps(
            {
                "schema_version": "penc276-radical-name-to-kangxi-v1",
                "source": "read-only data/cnbe32.db standard-track (radix_name, radix) pairs",
                "mapping": mapping,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    records = []
    for inventory in inventory_rows:
        zdic = zdic_rows[inventory["char"]]
        radical = zdic["zdic_radical"]
        options = mapping.get(radical, [])
        if not radical:
            status, mapped = "RADICAL_ZDIC_GAP", ""
        elif len(options) != 1:
            status, mapped = "RADICAL_UNMAPPED_OR_AMBIGUOUS", ""
        else:
            mapped = str(options[0])
            status = "RADICAL_CONFIRMED" if mapped == inventory["unihan_kangxi_radical"] else "RADICAL_DUAL_DISAGREE"
        records.append(
            {
                "row_id": inventory["row_id"],
                "char": inventory["char"],
                "unicode": inventory["unicode"],
                "zdic_radical": radical,
                "zdic_kangxi_radical": mapped,
                "unihan_kangxi_radical": inventory["unihan_kangxi_radical"],
                "parse_status": zdic["parse_status"],
                "status": status,
                "evidence_level": "cross_reference_dual" if status == "RADICAL_CONFIRMED" else "source_gap_or_disagreement",
                "candidate_cnbe_status": "NOT_GENERATED",
            }
        )
    with ADJUDICATION.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    counts = {status: sum(row["status"] == status for row in records) for status in sorted({row["status"] for row in records})}
    report = {
        "schema_version": "penc276-t3-radical-adjudication-v1",
        "records": len(records),
        "counts": counts,
        "decision": {
            "status": "PASS_T3_RADICAL_ADJUDICATION_REVIEW_ONLY",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_claim_national_standard": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 第 169–276 行部首双源裁决\n\n"
        "- 总行数：`108`。\n"
        + "".join(f"- `{status}`：`{count}`。\n" for status, count in counts.items())
        + "\nZDIC 与 Unihan 均为交叉参考；本裁决仅供后续人审，不生成 CNBE 候选或写源表。\n",
        encoding="utf-8",
    )
    print(report["decision"]["status"])


if __name__ == "__main__":
    main()
