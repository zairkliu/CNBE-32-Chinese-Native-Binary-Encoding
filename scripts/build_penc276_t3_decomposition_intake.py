#!/usr/bin/env python3
"""Create a no-write decomposition backlog for PENC_169 through PENC_276."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "evidence" / "8105" / "PENDING_276_ENCODING_INVENTORY.csv"
EXPECTED_SHA256 = "39d7e3295d18d6d262d8049de3465b10a47c760e0358b913276c82920931debf"
BACKLOG = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_DECOMPOSITION_BACKLOG.csv"
REVIEW_PACKET = ROOT / "review_packets" / "pending276" / "PENC276_T3_169_276_DECOMPOSITION_REVIEW_PACKET_EDITABLE.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_T3_169_276_DECOMPOSITION_INTAKE.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_T3_169_276_DECOMPOSITION_INTAKE.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows() -> list[dict[str, str]]:
    if sha256(INVENTORY) != EXPECTED_SHA256:
        raise ValueError("inventory SHA-256 mismatch")
    with INVENTORY.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    subset = [row for row in rows if 169 <= int(row["row_id"].split("_")[1]) <= 276]
    if len(subset) != 108 or any(row["tier"] != "T3" for row in subset):
        raise ValueError("expected exactly 108 T3 rows from PENC_169 through PENC_276")
    if any(row["cjkdecomp_raw"] or row["struct_cjkdecomp"] for row in subset):
        raise ValueError("T3 intake must only contain rows with missing cjk_decomp evidence")
    if any(not row["struct_cjkvi"] for row in subset):
        raise ValueError("T3 intake requires a non-empty cjkvi structure label")
    return subset


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = load_rows()
    backlog_rows = [
        {
            "row_id": row["row_id"],
            "char": row["char"],
            "unicode": row["unicode"],
            "tier": row["tier"],
            "struct_cjkvi": row["struct_cjkvi"],
            "owner_audit_structure_note": "struct_cjkvi_accurate",
            "decomposition_status": "REQUIRED_SECOND_SOURCE_AND_DECOMPOSITION_TREE",
            "candidate_cnbe_status": "NOT_GENERATED",
            "source_boundary": "owner audit confirms the existing cjkvi label; it does not create a second source",
        }
        for row in rows
    ]
    write_csv(BACKLOG, list(backlog_rows[0]), backlog_rows)
    review_rows = [
        {
            **row,
            "review_result": "",
            "review_note": "",
            "reviewer_id": "",
            "review_date": "",
        }
        for row in backlog_rows
    ]
    write_csv(REVIEW_PACKET, list(review_rows[0]), review_rows)
    result = {
        "schema_version": "penc276-t3-169-276-decomposition-intake-v1",
        "input_inventory_sha256": sha256(INVENTORY),
        "scope": {"row_id_start": "PENC_169", "row_id_end": "PENC_276", "tier": "T3", "rows": len(rows)},
        "facts": {
            "cjkdecomp_missing_rows": sum(not row["cjkdecomp_raw"] for row in rows),
            "struct_cjkvi_present_rows": sum(bool(row["struct_cjkvi"]) for row in rows),
            "owner_audit_assertion": "struct_cjkvi_accurate",
        },
        "decision": {
            "status": "BACKLOG_READY_DECOMPOSITION_EVIDENCE_REQUIRED",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_treat_as_dual_source_structure": False,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 T3 第 169–276 行拆解补全队列\n\n"
        f"- 输入清单 SHA-256：`{result['input_inventory_sha256']}`\n"
        "- 行数：`108`，全部为 `T3`。\n"
        "- `cjkdecomp_raw` 缺失：`108 / 108`。\n"
        "- `struct_cjkvi` 有值：`108 / 108`；所有者人工审核结论：`struct_cjkvi_accurate`。\n"
        "- 状态：`BACKLOG_READY_DECOMPOSITION_EVIDENCE_REQUIRED`。\n\n"
        "人工审核结论记录为结构复核上下文，但不构成第二独立来源，也不补写拆解树。"
        "因此本队列不生成 CNBE 候选值、不改源表；下一步是按国家标准 > 核心参考 > 网络交叉"
        "参考顺序补齐逐字拆解树与第二来源。\n",
        encoding="utf-8",
    )
    print("PENC276_T3_DECOMPOSITION_INTAKE: BACKLOG_READY_DECOMPOSITION_EVIDENCE_REQUIRED")


if __name__ == "__main__":
    main()
