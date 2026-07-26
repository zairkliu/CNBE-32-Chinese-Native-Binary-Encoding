#!/usr/bin/env python3
"""Record owner approval for T3 components that cannot be rendered in the current display set."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_DECOMPOSITION_LEDGER.csv"
RESOLUTION = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.md"
APPROVAL_REFERENCE = "project_owner_human_audit_2026-07-26"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with LEDGER.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    pending = [row for row in rows if row["decomposition_status"] == "PENDING_CLARIFICATION"]
    expected_ids = {"PENC_194", "PENC_247", "PENC_271"}
    if {row["row_id"] for row in pending} != expected_ids:
        raise ValueError("expected exactly the three approved non-renderable component rows")

    resolution_rows = [
        {
            "row_id": row["row_id"],
            "char": row["char"],
            "unicode": row["unicode"],
            "original_component_1": row["component_1"],
            "component_2": row["component_2"],
            "prior_note": row["human_note"],
            "resolution_status": "HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPH",
            "resolution_reason": "component glyph unavailable, blank, or malformed in the current decomposition display set",
            "approval_reference": APPROVAL_REFERENCE,
            "component_substitution": "PROHIBITED",
            "candidate_cnbe_status": "NOT_GENERATED",
            "source_table_write_authorized": "false",
        }
        for row in pending
    ]
    RESOLUTION.parent.mkdir(parents=True, exist_ok=True)
    with RESOLUTION.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(resolution_rows[0]))
        writer.writeheader()
        writer.writerows(resolution_rows)
    result = {
        "schema_version": "penc276-t3-nonrenderable-component-resolution-v1",
        "input_ledger_sha256": sha256(LEDGER),
        "approved_rows": len(resolution_rows),
        "approval_reference": APPROVAL_REFERENCE,
        "decision": {
            "status": "PASS_HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPHS",
            "may_use_human_decomposition_for_review": True,
            "may_substitute_missing_component_glyphs": False,
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 不可显现部件字形人审处置\n\n"
        "- 通过行：`3 / 3`。\n"
        "- 状态：`PASS_HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPHS`。\n"
        "- 原因：当前拆解显示集合无法可靠呈现部件字形，可能显示为空白、替代字形或错误字形。\n"
        "- 禁止：将显示结果（例如口、空白或乱码）替换为未经来源支持的真实部件。\n\n"
        "本处置仅解除人审拆解记录的显示缺口；它不补造部件、不构成国家标准直接证据，"
        "也不授权 CNBE 候选、源表或 SQLite 写入。\n",
        encoding="utf-8",
    )
    print("PENC276_T3_NONRENDERABLE: PASS_HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPHS")


if __name__ == "__main__":
    main()
