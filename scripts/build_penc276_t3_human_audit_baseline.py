#!/usr/bin/env python3
"""Build the final exploratory baseline view without overriding human audit records."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_AUDIT_MERGED.csv"
RADICALS = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_RADICAL_ADJUDICATION.csv"
OUTPUT = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.csv"
REPORT = ROOT / "reports" / "PENC276_T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    audit = read_csv(AUDIT)
    radicals = {row["row_id"]: row for row in read_csv(RADICALS)}
    if len(audit) != 108 or set(radicals) != {row["row_id"] for row in audit}:
        raise ValueError("human audit and radical evidence must cover the same 108 rows")
    rows = []
    for row in audit:
        radical = radicals[row["row_id"]]
        rows.append(
            {
                "row_id": row["row_id"],
                "char": row["char"],
                "unicode": row["unicode"],
                "final_project_basis": "HUMAN_AUDIT",
                "structure": row["struct_name_human_approved"],
                "decomposition_status": row["decomposition_status"],
                "external_reference_role": "ALIGNMENT_ONLY_NOT_GOLD_STANDARD",
                "unihan_zdic_radical_status": radical["status"],
                "candidate_cnbe_status": "NOT_GENERATED",
                "source_table_write_authorized": "false",
            }
        )
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "schema_version": "penc276-t3-final-human-audit-baseline-v1",
        "rows": len(rows),
        "final_project_basis": "HUMAN_AUDIT",
        "external_reference_role": "ALIGNMENT_ONLY_NOT_GOLD_STANDARD",
        "decision": {
            "status": "PASS_HUMAN_AUDIT_FINAL_EXPLORATORY_BASELINE",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_claim_national_standard": False,
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["decision"]["status"])


if __name__ == "__main__":
    main()
