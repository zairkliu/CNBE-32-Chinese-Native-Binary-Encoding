#!/usr/bin/env python3
"""Generate review registry and archive manifest for the 2026-08-06 milestone."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
VALIDATION = REPO / "evidence" / "validation"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    entries = [
        ("2026-08-06", "覆盖缺口人工复核", "10 UPGRADE_REVIEW + 6 INSERT_CANDIDATE", "批准",
         "zairkliu", VALIDATION / "CNBE覆盖缺口人工复核_2026-08-06.xlsx",
         "coverage_remediation_packet.json review records"),
        ("2026-08-06", "批量候选人工复核", "796 UPGRADE_CANDIDATE 全量部首/笔画/结构", "批准",
         "zairkliu", VALIDATION / "CNBE覆盖缺口人工复核_2026-08-06.xlsx",
         "batch_review_summary.json"),
        ("2026-08-06", "部首名回退复核", "66 条 Unihan 回退部首名", "批准",
         "zairkliu", VALIDATION / "CNBE部首名回退复核_2026-08-06.xlsx",
         "fallback_review_summary.json"),
        ("2026-08-06", "运行时库提升", "812 条 provisional 入运行时库", "授权",
         "项目负责人", EXP / "runtime_promotion_2026-08-06.json",
         "0 failures, 0 duplicate CNBE codes"),
        ("2026-08-06", "T1 1.5B 训练", "变体归一化 1.5B QLoRA", "负结果封存",
         "项目负责人", None, "private: outputs/private_training_plans/T1_1.5B_NEGATIVE_RESULT.md"),
    ]
    lines = [
        "# CNBE 项目审核登记 2026-08-06",
        "",
        "| 日期 | 审核项 | 范围 | 结论 | 审核人 | 依据 | 验证 |",
        "|---|---|---|---|---|---|---|",
    ]
    for date, item, scope, decision, reviewer, artifact, verify in entries:
        art = f"[{artifact.name}]({artifact.relative_to(REPO)})" if artifact else "私有文档"
        lines.append(f"| {date} | {item} | {scope} | {decision} | {reviewer} | {art} | {verify} |")
    lines += [
        "",
        "## 归档位置",
        "",
        "- 审核工作簿：`evidence/validation/`",
        "- 审核数据包：`experiments/2026-08-06_variant_normalization/`",
        "- 运行时提升：`experiments/2026-08-06_variant_normalization/runtime_promotion_2026-08-06.json`",
        "- 私有训练记录：`outputs/private_training_plans/`（不上传 GitHub）",
    ]
    registry = VALIDATION / "REVIEW_REGISTRY_2026-08-06.md"
    registry.write_text("\n".join(lines) + "\n", encoding="utf-8")

    files = [
        EXP / "runtime_promotion_2026-08-06.json",
        EXP / "candidate_db_verification.json",
        EXP / "coverage_remediation_packet.json",
        EXP / "variant_pairs.json",
        EXP / "coverage_gap.json",
        EXP / "variant_map.json",
        EXP / "variant_rules.json",
        EXP / "missing_six_candidates.json",
        EXP / "review_authorization.json",
        EXP / "batch_review_summary.json",
        EXP / "fallback_review_summary.json",
        VALIDATION / "CNBE覆盖缺口人工复核_2026-08-06.xlsx",
        VALIDATION / "CNBE部首名回退复核_2026-08-06.xlsx",
        VALIDATION / "REVIEW_REGISTRY_2026-08-06.md",
        REPO / "data" / "cnbe32.db",
        REPO / "src" / "cnbe32" / "data" / "cnbe32.db",
        EXP.parent / "2026-08-06_paddleocr_vl16" / "REPORT.md",
        EXP.parent / "2026-08-06_paddleocr_vl16" / "results.json",
        EXP.parent / "2026-08-05_v1_yongle_ocr_cnbe" / "REPORT.md",
        EXP.parent / "2026-08-05_v1_yongle_ocr_cnbe" / "results.json",
    ]
    manifest = {
        "schema_version": 1,
        "archived_at": "2026-08-06",
        "entries": [
            {"path": str(p.relative_to(REPO)), "size": p.stat().st_size, "sha256": sha256(p)}
            for p in files
            if p.exists()
        ],
    }
    manifest_path = EXP / "ARCHIVE_MANIFEST_2026-08-06.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("registry", registry)
    print("manifest", manifest_path, "entries", len(manifest["entries"]))


if __name__ == "__main__":
    main()
