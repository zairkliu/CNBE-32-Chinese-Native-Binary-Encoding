---
name: cnbe-moe-boundary
description: CNBE-MoE 实验边界与算力纪律。当用户讨论 CNBE-MoE 训练、专家数扩展、语料扩量、云算力投入、128/256 专家复盘或“要不要继续训练”时使用。核心作用是把“CNBE 编码验证”和“中文语言模型训练”划清边界，防止重复实验与重叠专家浪费。
tags: [CNBE-32, MoE, Training, Boundary, SCNet]
---

# CNBE-MoE 实验边界

## 项目范围

CNBE-MoE 只回答编码层问题，不负责生产中文语言模型：

1. CNBE 结构码流是否比 Unicode 码点更可预测；
2. 字段硬路由是否优于 Dense 与随机/学习路由；
3. radix / struct / strokes 字段的可学习性与泛化；
4. CNBE-32 在未见文本上的覆盖与稳定性。

超出以上范围的任务（通用中文生成、大语料预训练、可用产品模型）
不属于本项目，默认不投入云训练。

## 红线

- 没有 Dense same-config 对照，不训练；
- 没有 Unicode same-config 对照，不训练；
- 没有 a priori 停止条件，不训练；
- 只增加专家数、不增加决策信息，不训练；
- 已有结论在不同数据上重复跑，不训练；
- 私有语料、checkpoint、mapping 不进 GitHub；
- 语料扩量默认不启动，除非编码覆盖/泛化成为瓶颈并有实验卡支撑。

## 云训练启动门禁

每次上云前先填写 `EXPERIMENT_CARD.md` 模板，至少包含：

| 必填项 | 要求 |
|---|---|
| 假设 | 一句话，可证伪 |
| 对照 | 同配置 Dense；涉及编码时加 Unicode |
| 非重叠点 | 与 8/16/64/128 已有实验明确不同 |
| 预算 | 硬件、时长、金额上限 |
| 预期产出 | 可写成一页结论，而不是“跑通了” |
| 停止条件 | 训练前写死，达标或失败都停止 |

## 128 专家复盘要点（2026-08-10）

- 24M 语料、128 共享专家、46,874 步：next-code 19.12%，
  struct 34.14%，eval_loss 6.58，Gini 0.207；
- 本地 MoE-64（6M 字 / 1200 步）next-code 19.18%、struct 44.26%；
  非严格同配置，但足以否定“堆专家一定变好”；
- 该轮证明的是训练栈可跑通，不是新结论。

## 重叠专家浪费（必须自查）

用 `scripts_src/analyze_moe_waste.py` 检查每次实验：

- 第二专家是否只是 `(primary + 1) % E`：是则不是语义分工；
- 是否 8 层共用同一路由：是则专家-上下文槽位从 E×L 塌缩为 E；
- 向量化 grouped GEMM 的 padding 倍数：128 专家实测约 4.2x；
- 任何超过 1.5x padding 的实现都应先修复再谈扩大规模。

## 相关文件

- 复盘：`experiments/2026-08-08_cnbe_moe_scnet/RETRO_128_EXPERIMENT_2026-08-10.md`
- 计划：`experiments/2026-08-08_cnbe_moe_scnet/NEXT_PHASE_PLAN_2026-08-10.md`
- 实验卡：`experiments/2026-08-08_cnbe_moe_scnet/EXPERIMENT_CARD.md`
- 分析脚本：`experiments/2026-08-08_cnbe_moe_scnet/scripts_src/analyze_moe_waste.py`

## P0 控制训练状态（2026-08-10）

- 本地小规模三组对照已跑通：MoE-8 / Dense(CNBE) / Dense(Unicode)；
- 全量 Dense / Unicode 对照命令已就绪，等待 L20 执行；
- 全量对照通过前，不启动 256 专家、不启动盲扩语料。

## SCNet 云环境（2026-08-10 登记）

- 资源组：113 组 `hx1hgbwnormal`；
- 加速卡：异构加速卡 BW × 2，面板显示总显存 256GB；CPU 30 核，内存 118GB；
- 镜像：`jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel`；
- 启动：`scnet_startup_dcu2.sh`；
- 出版物合并流程：清洗纯文本 → CNBE 编码 → 覆盖率复核 → 合并 24M →
  重建 vocab/mapping → 2 卡 BW 训练。
