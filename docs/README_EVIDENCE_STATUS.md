# README 证据状态说明

**状态：文档维护基线**  
**日期：2026-07-28**

本说明规定项目首页可以使用的事实范围。README 只汇总可以定位到仓库内已提交报告、数据迁移记录或可复现命令的事实；无法核验的结论必须保留在实验记录中，并标记为待复核。

## 已可在首页陈述的仓库事实

| 主题 | 当前可引用表述 | 证据入口 |
|---|---|---|
| 项目定位 | CNBE-32 是 Unicode 兼容层之上的研究性结构特征编码，不替代 Unicode。 | `docs/CNBE_RESEARCH_POSITION_STATEMENT.md` |
| 标准核心 | 8105 是项目发布轨道的国家标准核心；项目处于“对齐中”，不声明已整体符合国家标准。 | `docs/CNBE_STANDARDS_COMPLIANCE_STATEMENT.md` |
| 运行时数据 | 已提交的 v1.1 迁移记录报告 21,178 条运行时记录（standard 7,602 / legacy 13,576），并记录 PENC276 的 276 条授权写入。 | `reports/MIGRATION_V1_1_WS7WS8.md`、`reports/PENC276_AUTHORIZED_ENCODING_APPLY.md` |
| 数学程序 | 13 组公式性质测试通过；这仅验证实现性质，不验证语言学正确性或任务性能。 | `experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md` |
| 外部评审 | P1 独立评审仍是待完成门禁。 | `docs/review/P1_EXTERNAL_REVIEW_EXECUTION_KIT.md` |

## 模型发布基线与边界

项目所有者指定 [ModelScope 发布页](https://www.modelscope.cn/models/zairkliu/CNBE-32) 及其 GGUF 文件为当前 v11 模型发布基线：DeepSeek-R1-Distill-Qwen-1.5B 的 5,000 步 QLoRA 制品。该文件的大小与 SHA-256 固定于 [ModelScope 制品对齐清单](./MODELSCOPE_MODEL_ARTIFACT_MANIFEST_v1.1.md)。

仓库中记录 1,000 步的 DeepSeek 训练报告属于模型上传过程的临时历史材料，不覆盖当前发布基线。重编码前的 Qwen3.5-0.8B 训练、日志和旧编码实验已迁移到 [test/legacy-ai-encoding-baseline](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/tree/test/legacy-ai-encoding-baseline) 分支，不参与当前模型和数据主线。

README 可引用 ModelScope 发布基线中列出的训练与评测摘要，但必须同时保留以下限制：

1. 模型为研究性候选预测器，不是语言文字标准的权威解释器。
2. 任何模型输出不得自动写入运行时编码表。
3. 评测数字仅适用于模型卡定义的实验任务、样本与制品版本，不外推为逐字编码正确率、国家标准符合性或通用 OCR 性能。
4. 后续重新训练或替换 GGUF 时，必须更新制品 SHA-256、模型卡和发布基线文件。

## 维护要求

- `README.md` 与 `README_EN.md` 为英文主文档和英文镜像，内容必须一致。
- `README_ZH.md`、报告、白皮书、部署和治理材料以中文为主。
- PyPI 包内数据库的实际条目数须由发布制品审计确认；在确认前，README 仅说明仓库检入运行时的条目数。
