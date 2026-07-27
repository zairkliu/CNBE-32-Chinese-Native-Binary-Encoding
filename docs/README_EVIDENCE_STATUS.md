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

## 模型实验的证据边界

仓库目前同时存在“5,000 步”描述和一份记录“1,000 步完成”的训练报告；字段评测补充文件的 66.0%、92.7% 等数值也没有在同一份不可变实验清单中绑定完整数据切分、随机种子、模型制品哈希和测试输出。因此：

1. README 不把上述数值表述为已确认的项目性能结论。
2. 模型入口可保留为实验制品入口，但必须标注“研究性候选预测器”。
3. 任何模型输出不得自动写入运行时编码表。
4. 重新发布性能数字前，必须提交训练配置、数据清单、切分与种子、模型或适配器校验和、原始评测 JSON、复现实验命令及基线比较。

## 维护要求

- `README.md` 与 `README_EN.md` 为英文主文档和英文镜像，内容必须一致。
- `README_ZH.md`、报告、白皮书、部署和治理材料以中文为主。
- PyPI 包内数据库的实际条目数须由发布制品审计确认；在确认前，README 仅说明仓库检入运行时的条目数。
