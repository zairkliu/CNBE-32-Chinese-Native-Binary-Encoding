#!/usr/bin/env python3
"""Record the owner-approved structure gate for the T3 decomposition backlog."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_DECOMPOSITION_BACKLOG.csv"
APPROVAL_LEDGER = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_STRUCTURE_OWNER_APPROVAL.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_STRUCTURE_APPROVAL.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_STRUCTURE_APPROVAL.md"
APPROVAL_REFERENCE = "project_owner_human_audit_2026-07-25"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with BACKLOG.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 108 or any(row["tier"] != "T3" for row in rows):
        raise ValueError("expected the fixed 108-row T3 backlog")
    if {row["owner_audit_structure_note"] for row in rows} != {"struct_cjkvi_accurate"}:
        raise ValueError("backlog does not carry the expected owner audit assertion")

    ledger_rows = [
        {
            "row_id": row["row_id"],
            "char": row["char"],
            "unicode": row["unicode"],
            "approved_struct_name": row["struct_cjkvi"],
            "approval_scope": "structure_label_only",
            "approval_reference": APPROVAL_REFERENCE,
            "decomposition_status": "PENDING_DECOMPOSITION_TREE",
            "radical_status": "PENDING_DUAL_SOURCE",
            "stroke_status": "USE_INVENTORY_STATUS_NOT_APPROVED_HERE",
            "candidate_cnbe_status": "NOT_GENERATED",
            "source_table_write_authorized": "false",
        }
        for row in rows
    ]
    APPROVAL_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with APPROVAL_LEDGER.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ledger_rows[0]))
        writer.writeheader()
        writer.writerows(ledger_rows)

    result = {
        "schema_version": "penc276-t3-169-276-owner-structure-approval-v1",
        "input_backlog_sha256": sha256(BACKLOG),
        "approved_rows": len(ledger_rows),
        "approval_scope": "structure_label_only",
        "approval_reference": APPROVAL_REFERENCE,
        "decision": {
            "status": "PASS_STRUCTURE_HUMAN_APPROVED_DECOMPOSITION_AND_EVIDENCE_PENDING",
            "may_use_structure_label_in_future_review": True,
            "may_treat_as_dual_source_structure": False,
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 第 169–276 行结构人工审核授权\n\n"
        "- 通过行：`108 / 108`。\n"
        "- 授权范围：`structure_label_only`。\n"
        f"- 授权记录：`{APPROVAL_REFERENCE}`。\n"
        "- 状态：`PASS_STRUCTURE_HUMAN_APPROVED_DECOMPOSITION_AND_EVIDENCE_PENDING`。\n\n"
        "该授权允许后续审阅使用已审核的 `struct_cjkvi` 结构标签，但不将其伪装成双源证据。"
        "逐字拆解树、部首双源、笔画裁决和源表写入仍未获授权；CNBE 候选值保持未生成。\n",
        encoding="utf-8",
    )
    print("PENC276_T3_STRUCTURE_APPROVAL: PASS_STRUCTURE_HUMAN_APPROVED_DECOMPOSITION_AND_EVIDENCE_PENDING")


if __name__ == "__main__":
    main()
