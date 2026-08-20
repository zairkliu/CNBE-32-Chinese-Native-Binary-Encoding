# CNBE-MoE CCF-A 材料包

日期：2026-08-18  
用途：从整轮对话和 output 目录产出物提炼出的论文、白皮书、蓝皮书、数据链与技术数据库。

## 文件

| 文件 | 内容 |
|---|---|
| `OUTPUT_AUDIT_2026-08-18.md` | output 目录 163 个文件的完整审计与缺口 |
| `TECHNICAL_PAPER_CNBE_MOE_2026-08-18.md` | CCF-A 技术论文草稿（已按审稿意见修订） |
| `REVIEW_RESPONSE_2026-08-18.md` | 审稿意见逐条响应表 |
| `SEGMENTFAULT_REVIEW_ANALYSIS_2026-08-19.md` | 外部专业评审分析：有效观点与必须修复的 fatal gaps |
| `SEGMENTFAULT_PUBLIC_CORRECTION_2026-08-19.md` | 公开问题页的二次更正稿与逐项编辑清单 |
| `CNBE_POSITIONING_ANALYSIS_2026-08-19.md` | CNBE 通用 NLU vs 结构敏感任务定位分析与差异化 |
| `CNBE_EXISTING_WORK_AND_DIFFERENTIATION_2026-08-19.md` | 已有工作、他人未尝试原因、ChineseBERT/Glyce/SubChar 对比与方向判断 |
| `PROJECT_COMPARISON_LESSONS_2026-08-19.md` | 已有项目情况分析及对 CNBE 项目的启示 |
| `EXPERIMENTS_VS_SEGMENTFAULT_REVIEW_2026-08-19.md` | 实验证据与 SegmentFault 评审结论的对照 |
| `PROJECT_NEXT_DEVELOPMENT_2026-08-19.md` | 项目预期、风险与下一步发展评估 |
| `A800_TRAINING_PROGRESS_MODEL_2026-08-18.md` | 基于 184,482 步损失分布的训练进度与稳定性模型 |
| `A800_TRAINING_PROGRESS_MODEL_2026-08-19.md` | 基于 250,578 步损失分布的最新训练进度与稳定性模型 |
| `WHITEPAPER_CNBE_FULL_JOURNEY_2026-08-18.md` | 国标对齐到 A800 的全链路白皮书 |
| `BLUEPRINT_CNBE_MOE_2026-08-18.md` | 长期路线图与决策门 |
| `DATA_CHAIN_CNBE_MOE_2026-08-18.md` | 从国家标准到论文指标的完整数据链 |
| `TECHNICAL_DATABASE.json` | 结构化技术数据库 |

## 核心事实

- 国标：GB 8105 + GF 系列；
- 编码库：21,178 行，标准轨 7,602；
- 七语料：24,381,237 字；
- V2 冻结：5,069,667,334 train tokens；
- 对比：MoE-128 4.543 vs Dense 7.303；
- 1.5B 训练：负结果，eval_loss 0.0918；
- A800×2：smoke 通过，正式训练就绪。

## 下一步

1. 启动 A800×2 正式训练；
2. 收集 step 曲线与 checkpoint；
3. 补齐 Dense matched 和下游 benchmark；
4. 使用本包材料完成论文终稿。
