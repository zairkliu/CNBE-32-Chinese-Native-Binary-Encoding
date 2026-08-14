#!/usr/bin/env python3
"""Apply reviewer-requested edits to the CNBE corpus v2 paper."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", type=Path, required=True)
    args = ap.parse_args()

    p = args.paper
    s = p.read_text(encoding="utf-8")

    old1 = "已完成的两轮模型验证显示，CNBE-MoE-128 在 24M 与 544M 语料上的 next-code 准确率分别达到 19.12% 与 23.56%，struct 字段准确率由 34.14% 提升到 44.07%，并在等语料受控对比中显著优于 Dense 与 Unicode 基线。这些实验基于 v2 构建过程中的早期子集，验证了 v2 所采用的数据构建方法论有效；v2 全量规模的固定配置验证列为后续工作（见 7.6 节）。"
    new1 = "在 v2 正式冻结前，我们在 v2 构建过程中的早期子集（24M 与 544M）上完成了两轮前置验证：CNBE-MoE-128 的 next-code 准确率分别达到 19.12% 与 23.56%，struct 字段准确率由 34.14% 提升到 44.07%，并在等语料受控对比中显著优于 Dense 与 Unicode 基线。这些实验验证了 v2 所采用的数据构建方法论有效；v2 全量规模的固定配置验证列为后续工作（见 7.6 节）。"

    old2 = "并为模型配置、字段预测与路由均衡提供方向性证据。第一轮"
    new2 = (
        "并为模型配置、字段预测与路由均衡提供方向性证据。这些早期子集与 v2 全量"
        "同源（同一来源、清洗与编码管道），但规模不同，因此不能直接外推为 v2 全量"
        "结果。第一轮"
    )

    old3 = "早期版本未保存逐 step 训练曲线，收敛曲线将在 v2 全量实验中记录并补充。"
    new3 = "逐 step 收敛曲线正在从训练日志提取，v2 全量实验将记录完整收敛曲线并补充。"

    old4 = "路由集中度随训练规模上升，是 v2 全量实验的消融重点。"
    new4 = (
        "图中阴影区为理想控制区间 0.15-0.25，544M 已超出该区间；路由集中度随训练"
        "规模上升，是 v2 全量实验的消融重点。"
    )

    replacements = [(old1, new1), (old2, new2), (old3, new3), (old4, new4)]
    for old, new in replacements:
        if old not in s:
            raise SystemExit(f"pattern not found: {old[:40]}")
        s = s.replace(old, new)

    fig4 = (
        "\n\n![图 4：CNBE-MoE-128 模型架构](figures/fig4_architecture.png)\n\n"
        "**图 4：CNBE-MoE-128 模型架构。** 输入为 32 位 CNBE 码流；Embedding 后按 "
        "(radix, struct, strokes) 提取三字段模板并映射到 128 个专家；MoE 层采用 "
        "Top-2 硬路由；输出层包含 next-code 与 radix/struct/strokes 字段头。"
    )
    s = s.replace(new4 + "\n\n", new4 + fig4 + "\n\n", 1)

    p.write_text(s, encoding="utf-8")
    print("updated", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
