#!/usr/bin/env python3
"""Join owner-supplied T3 decompositions to the fixed PENC276 backlog."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_DECOMPOSITION_BACKLOG.csv"
HUMAN_INPUT = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_DECOMPOSITION_INPUT.csv"
LEDGER = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_DECOMPOSITION_LEDGER.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_DECOMPOSITION_INTAKE.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_DECOMPOSITION_INTAKE.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    backlog = read_csv(BACKLOG)
    supplied = read_csv(HUMAN_INPUT)
    if len(backlog) != 108 or len(supplied) != 108:
        raise ValueError("both input sets must contain exactly 108 rows")
    backlog_by_char = {row["char"]: row for row in backlog}
    if len(backlog_by_char) != 108 or set(backlog_by_char) != {row["char"] for row in supplied}:
        raise ValueError("human decomposition characters do not exactly match the T3 backlog")

    ledger_rows = []
    for supplied_row in supplied:
        backlog_row = backlog_by_char[supplied_row["char"]]
        pending = not supplied_row["component_1"] or "possible_" in supplied_row["human_note"]
        ledger_rows.append(
            {
                "row_id": backlog_row["row_id"],
                "char": supplied_row["char"],
                "unicode": backlog_row["unicode"],
                "struct_name_human_approved": backlog_row["struct_cjkvi"],
                "component_1": supplied_row["component_1"],
                "component_2": supplied_row["component_2"],
                "human_note": supplied_row["human_note"],
                "decomposition_status": "PENDING_CLARIFICATION" if pending else "HUMAN_DECOMPOSITION_RECORDED",
                "evidence_level": "human_reviewed_project_evidence",
                "candidate_cnbe_status": "NOT_GENERATED",
                "source_table_write_authorized": "false",
            }
        )
    approved = [row for row in ledger_rows if row["decomposition_status"] == "HUMAN_DECOMPOSITION_RECORDED"]
    pending = [row for row in ledger_rows if row["decomposition_status"] == "PENDING_CLARIFICATION"]
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ledger_rows[0]))
        writer.writeheader()
        writer.writerows(ledger_rows)
    result = {
        "schema_version": "penc276-t3-169-276-human-decomposition-intake-v1",
        "inputs": {str(BACKLOG.relative_to(ROOT)): sha256(BACKLOG), str(HUMAN_INPUT.relative_to(ROOT)): sha256(HUMAN_INPUT)},
        "rows": len(ledger_rows),
        "human_decomposition_recorded": len(approved),
        "pending_clarification": [{"row_id": row["row_id"], "char": row["char"], "note": row["human_note"]} for row in pending],
        "decision": {
            "status": "PARTIAL_HUMAN_DECOMPOSITION_RECORDED_CLARIFICATION_REQUIRED" if pending else "PASS_HUMAN_DECOMPOSITION_RECORDED",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_claim_national_standard": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending_names = "、".join(f"{row['row_id']} {row['char']}" for row in pending)
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 第 169–276 行人工拆解录入报告\n\n"
        f"- 人工拆解已录入：`{len(approved)} / {len(ledger_rows)}`。\n"
        f"- 待澄清：`{len(pending)}` 行（{pending_names}）。\n"
        f"- 状态：`{result['decision']['status']}`。\n\n"
        "本记录是项目人审证据，不是国家标准直接证据。所有 CNBE 候选与源表写入仍被禁止；"
        "待澄清行解决、部首双源与笔画门通过后，才可进入后续 dry-run。\n",
        encoding="utf-8",
    )
    print(result["decision"]["status"])


if __name__ == "__main__":
    main()
