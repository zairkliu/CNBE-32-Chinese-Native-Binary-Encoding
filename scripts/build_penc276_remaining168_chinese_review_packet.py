#!/usr/bin/env python3
"""Build a Chinese-only, no-write human-review packet for PENC276's remaining rows."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "evidence" / "8105" / "PENDING_276_ENCODING_INVENTORY.csv"
T3_HUMAN_BASELINE = ROOT / "evidence" / "8105" / "pending276" / "T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.csv"
EXPECTED_INVENTORY_SHA256 = "39d7e3295d18d6d262d8049de3465b10a47c760e0358b913276c82920931debf"
PACKET = ROOT / "review_packets" / "pending276" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_EDITABLE.csv"
REPORT_JSON = ROOT / "reports" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET.json"
REPORT_MARKDOWN = ROOT / "reports" / "PENC276_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET.md"
GUIDE = ROOT / "docs" / "PENC276_REMAINING_168_HUMAN_REVIEW_GUIDE_ZH.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def source_value(value: str) -> str:
    return value if value else "缺失"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if sha256(INVENTORY) != EXPECTED_INVENTORY_SHA256:
        raise ValueError("PENC276 inventory SHA-256 mismatch")

    inventory = read_csv(INVENTORY)
    audited_ids = {row["row_id"] for row in read_csv(T3_HUMAN_BASELINE)}
    if len(inventory) != 276 or len(audited_ids) != 108:
        raise ValueError("unexpected PENC276 inventory or completed human-baseline count")

    remaining = [row for row in inventory if row["row_id"] not in audited_ids]
    if len(remaining) != 168:
        raise ValueError("remaining review packet must contain exactly 168 rows")
    if any(int(row["row_id"].split("_")[1]) >= 169 for row in remaining):
        raise ValueError("completed PENC_169 through PENC_276 rows leaked into remaining packet")

    packet_rows = []
    for sequence, row in enumerate(remaining, start=1):
        packet_rows.append(
            {
                "审核序号": str(sequence),
                "清单编号": row["row_id"],
                "汉字": row["char"],
                "Unicode": row["unicode"],
                "8105序号": row["standard_rank"],
                "规范等级": row["level"],
                "原始分层": row["tier"],
                "现有轨道": row["track"],
                "数据库笔画数": source_value(row["strokes_db"]),
                "基线笔画数": source_value(row["baseline_stroke_count"]),
                "Unihan总笔画": source_value(row["unihan_total_strokes"]),
                "笔画对照状态": source_value(row["strokes_dual"]),
                "cjk-decomp结构": source_value(row["struct_cjkdecomp"]),
                "cjkvi结构": source_value(row["struct_cjkvi"]),
                "结构对照状态": source_value(row["struct_dual"]),
                "Unihan康熙部首号": source_value(row["unihan_kangxi_radical"]),
                "审核结构（填写）": "",
                "审核拆解或部件（填写）": "",
                "审核笔画数（填写）": "",
                "审核部首（填写）": "",
                "审核结论（填写）": "",
                "审核说明（填写）": "",
                "审核人（填写）": "",
                "审核日期（填写）": "",
                "证据边界": "人工审核项目证据；国家规范、Unihan及网络资料仅作对齐参考，不能自动覆盖审核结论。",
                "编码状态": "不生成候选CNBE；不写入源表或数据库",
            }
        )

    write_csv(PACKET, list(packet_rows[0]), packet_rows)
    tier_counts = Counter(row["tier"] for row in remaining)
    report = {
        "schema_version": "penc276-remaining168-chinese-human-review-packet-v1",
        "input_inventory_sha256": sha256(INVENTORY),
        "completed_human_audit_baseline_rows_excluded": len(audited_ids),
        "review_packet_rows": len(packet_rows),
        "tier_counts": dict(sorted(tier_counts.items())),
        "scope": {
            "included": "PENC276 rows outside completed PENC_169 through PENC_276 human-audit baseline",
            "excluded": "108 completed human-audit baseline rows",
        },
        "decision": {
            "status": "PASS_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_READY",
            "may_generate_cnbe_candidates": False,
            "may_modify_source_tables": False,
            "may_modify_sqlite": False,
            "may_claim_national_standard": False,
        },
        "reviewer_conclusion_options": ["通过", "需复核", "无法显示", "不纳入本批"],
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN.write_text(
        "# PENC276 剩余 168 字人工审核包\n\n"
        "- 审核语言：中文。\n"
        f"- 审核行数：`{len(packet_rows)}`。\n"
        "- 已排除：`108` 个已完成人工审核的 `PENC_169`–`PENC_276` T3 字。\n"
        f"- 分层：T0 `{tier_counts['T0']}`、T1 `{tier_counts['T1']}`、T2 `{tier_counts['T2']}`、T3 `{tier_counts['T3']}`、T4 `{tier_counts['T4']}`。\n"
        f"- 输入清单 SHA-256：`{report['input_inventory_sha256']}`。\n"
        "- 状态：`PASS_REMAINING_168_CHINESE_HUMAN_REVIEW_PACKET_READY`。\n\n"
        "## 审核边界\n\n"
        "本包只收集人工审核结论。请首先核对字形与 Unicode，再填写结构、拆解/部件、笔画和部首；"
        "审核结论仅可填写“通过”“需复核”“无法显示”或“不纳入本批”。国家语言文字规范、"
        "Unihan 与网络资料均为对齐参考，不会自动覆盖审核员结论。\n\n"
        "本包不生成 CNBE 候选值，不修改源表或 SQLite 数据库，也不构成国家标准符合性声明。\n",
        encoding="utf-8",
    )
    GUIDE.write_text(
        "# PENC276 剩余 168 字人工审核说明\n\n"
        "## 审核对象与范围\n\n"
        "本包包含 PENC276 清单中除 `PENC_169`–`PENC_276` 已完成 108 字人工审核基线以外的 `168` 行。"
        "其中包括 T0 1 行、T1 124 行、T2 36 行、T3 3 行、T4 4 行。\n\n"
        "## 填写顺序\n\n"
        "1. 先核对“汉字”和“Unicode”；字形无法显示时，在审核结论填写“无法显示”，并在说明中描述显示现象。\n"
        "2. 填写“审核结构（填写）”。结构采用项目既定的独体字或 12 种合体结构分类；不可新增结构类别。\n"
        "3. 填写“审核拆解或部件（填写）”、笔画数与部首；不确定时填写“需复核”，不得以猜测补齐。\n"
        "4. 填写审核人和审核日期。\n\n"
        "## 证据与权限边界\n\n"
        "人工审核是本探索项目的工作结论。8105 与相关国家语言文字规范、Unihan、辞书、"
        "字源资料和网络资料只用于对齐和交叉核验，并非可自动推翻人工结论的金标准。\n\n"
        "本审核包是证据采集表：不会生成 CNBE 编码、不会写入源表或 SQLite，也不会发布国家标准符合性结论。"
        "后续若要合并审核结果，必须先生成单独副本并经过逐行审计。\n",
        encoding="utf-8",
    )
    print(report["decision"]["status"])


if __name__ == "__main__":
    main()
