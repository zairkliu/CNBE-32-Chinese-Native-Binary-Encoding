#!/usr/bin/env python3
"""Merge the bounded human-audit artifacts for PENC_169 through PENC_276."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRUCTURE = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_STRUCTURE_OWNER_APPROVAL.csv"
DECOMPOSITION = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_DECOMPOSITION_LEDGER.csv"
NONRENDERABLE = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_NONRENDERABLE_COMPONENT_RESOLUTION.csv"
MERGED = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_HUMAN_AUDIT_MERGED.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_AUDIT_MERGE.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_HUMAN_AUDIT_MERGE.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    structure_rows = read_csv(STRUCTURE)
    decomposition_rows = read_csv(DECOMPOSITION)
    nonrenderable_rows = read_csv(NONRENDERABLE)
    if len(structure_rows) != 108 or len(decomposition_rows) != 108 or len(nonrenderable_rows) != 3:
        raise ValueError("unexpected audit artifact counts")
    structure_by_id = {row["row_id"]: row for row in structure_rows}
    decomposition_by_id = {row["row_id"]: row for row in decomposition_rows}
    nonrenderable_by_id = {row["row_id"]: row for row in nonrenderable_rows}
    if set(structure_by_id) != set(decomposition_by_id) or len(structure_by_id) != 108:
        raise ValueError("structure and decomposition rows must have the same 108 row IDs")

    merged_rows = []
    for row_id in sorted(structure_by_id, key=lambda value: int(value.split("_")[1])):
        structure = structure_by_id[row_id]
        decomposition = decomposition_by_id[row_id]
        resolution = nonrenderable_by_id.get(row_id)
        merged_rows.append(
            {
                "row_id": row_id,
                "char": structure["char"],
                "unicode": structure["unicode"],
                "struct_name_human_approved": structure["approved_struct_name"],
                "structure_status": "HUMAN_APPROVED",
                "component_1": decomposition["component_1"],
                "component_2": decomposition["component_2"],
                "decomposition_status": resolution["resolution_status"] if resolution else decomposition["decomposition_status"],
                "human_note": decomposition["human_note"],
                "component_substitution": resolution["component_substitution"] if resolution else "NOT_APPLICABLE",
                "evidence_level": "human_reviewed_project_evidence",
                "candidate_cnbe_status": "NOT_GENERATED",
                "source_table_write_authorized": "false",
            }
        )
    MERGED.parent.mkdir(parents=True, exist_ok=True)
    with MERGED.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(merged_rows[0]))
        writer.writeheader()
        writer.writerows(merged_rows)

    regular = sum(row["decomposition_status"] == "HUMAN_DECOMPOSITION_RECORDED" for row in merged_rows)
    display_gap = sum(row["decomposition_status"] == "HUMAN_APPROVED_NONRENDERABLE_COMPONENT_GLYPH" for row in merged_rows)
    result = {
        "schema_version": "penc276-t3-169-276-human-audit-merge-v1",
        "inputs": {str(path.relative_to(ROOT)): sha256(path) for path in (STRUCTURE, DECOMPOSITION, NONRENDERABLE)},
        "summary": {
            "rows": len(merged_rows),
            "human_approved_structure_rows": len(merged_rows),
            "human_decomposition_recorded_rows": regular,
            "human_approved_nonrenderable_component_rows": display_gap,
        },
        "decision": {
            "status": "PASS_HUMAN_AUDIT_MERGED_EVIDENCE_GATES_REMAINING",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_claim_national_standard": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 第 169–276 行人工审核合并报告\n\n"
        f"- 合并行数：`{len(merged_rows)} / 108`。\n"
        f"- 人工审核结构通过：`{len(merged_rows)} / 108`。\n"
        f"- 明确人工拆解：`{regular} / 108`。\n"
        f"- 人审通过的不可显现部件字形：`{display_gap} / 108`。\n"
        "- 状态：`PASS_HUMAN_AUDIT_MERGED_EVIDENCE_GATES_REMAINING`。\n\n"
        "本合并账本保留所有人审结论和不可替换字形缺口，但不绕过部首双源、笔画裁决、"
        "CNBE dry-run 或源表写入授权。\n",
        encoding="utf-8",
    )
    print(result["decision"]["status"])


if __name__ == "__main__":
    main()
