# CNBE 项目审核登记 2026-08-06

| 日期 | 审核项 | 范围 | 结论 | 审核人 | 依据 | 验证 |
|---|---|---|---|---|---|---|
| 2026-08-06 | 覆盖缺口人工复核 | 10 UPGRADE_REVIEW + 6 INSERT_CANDIDATE | 批准 | zairkliu | [CNBE覆盖缺口人工复核_2026-08-06.xlsx](evidence\validation\CNBE覆盖缺口人工复核_2026-08-06.xlsx) | coverage_remediation_packet.json review records |
| 2026-08-06 | 批量候选人工复核 | 796 UPGRADE_CANDIDATE 全量部首/笔画/结构 | 批准 | zairkliu | [CNBE覆盖缺口人工复核_2026-08-06.xlsx](evidence\validation\CNBE覆盖缺口人工复核_2026-08-06.xlsx) | batch_review_summary.json |
| 2026-08-06 | 部首名回退复核 | 66 条 Unihan 回退部首名 | 批准 | zairkliu | [CNBE部首名回退复核_2026-08-06.xlsx](evidence\validation\CNBE部首名回退复核_2026-08-06.xlsx) | fallback_review_summary.json |
| 2026-08-06 | 运行时库提升 | 812 条 provisional 入运行时库 | 授权 | 项目负责人 | [runtime_promotion_2026-08-06.json](experiments\2026-08-06_variant_normalization\runtime_promotion_2026-08-06.json) | 0 failures, 0 duplicate CNBE codes |
| 2026-08-06 | T1 1.5B 训练 | 变体归一化 1.5B QLoRA | 负结果封存 | 项目负责人 | 私有文档 | 私有记录，不上传 GitHub |
| 2026-08-06 | GF0011/GF0013 正式锚定 | 812 条 provisional 按 GF0011 201 部首表名称/附形匹配 | 805 条锚定，7 条待 GF0012 归部复核 | zairkliu | [gf0011_201_radicals.json](data\gf0011_201_radicals.json) + [gf0011_0013_anchoring_packet.json](experiments\2026-08-06_variant_normalization\gf0011_0013_anchoring_packet.json) | GF0011 按公开转载表核对；GF0013 笔画仅 Unihan 交叉参考，待权威逐字表 |
| 2026-08-06 | 8105 legacy 剩余行人工审核 | 8105 内 491 行 legacy 轨 | 待人工审核 | 项目负责人 | [CNBE8105_LEGACY_REVIEW_2026-08-06.xlsx](evidence\validation\CNBE8105_LEGACY_REVIEW_2026-08-06.xlsx) | review_authorization_legacy.json，只读包未写发布库 |

## 归档位置

- 审核工作簿：`evidence/validation/`
- 审核数据包：`experiments/2026-08-06_variant_normalization/`
- 运行时提升：`experiments/2026-08-06_variant_normalization/runtime_promotion_2026-08-06.json`
- GF 锚定表：`data/gf0011_201_radicals.json`
- GF 锚定数据包：`experiments/2026-08-06_variant_normalization/gf0011_0013_anchoring_packet.json`
- 8105 legacy 复核包：`evidence/8105/8105_REMAINING_503_COMPLETION_PACKET.json`
- 私有训练记录：仅存本地，不上传 GitHub
