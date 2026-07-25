# CNBE P1 自验证与外部独立审阅方法

**英文对应：** [CNBE P1 Self-Validation and External Independent Review Method](P1_EXTERNAL_REVIEW_METHOD.md)

## 目的

P1 的独立审核以外部审阅为入口。内部自验证只检查工件是否完整、一致、可复现和无泄漏；它不能确认汉字关系或来源本身正确。外部审阅者必须在不读取既有批准结论的情况下，独立核对每一条来源定位和关系主张。

## 工件顺序

1. 内部正关系账本：`P1_INDEPENDENT_RELATION_LEDGER_HUMAN_APPROVED.csv`。
2. 自验证报告：`P1_SELF_VALIDATION_AND_EXTERNAL_REVIEW_PACKAGE.md`。
3. 去除内部结论的外部审阅包：[P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv)。
4. 外部完成后，创建单独的协调审计输入；不得覆盖原始账本或外部包。

## 外部审阅规则

- 每行先核对查询字、候选字和 Unicode 身份。
- 只根据 `source_document` 与 `source_locator` 复核 `relation_claim_to_verify`。
- `external_relation_label` 只能填写 `positive`、`negative` 或 `exclude`。
- `external_source_confirmation` 只能填写 `confirmed`、`unclear` 或 `conflict`。
- 无法定位、来源冲突或 Unicode 不清楚时填写 `exclude`，不得猜测。
- 审阅者不得读取内部批准标签、部件族、切分和数学分数；不得用 CNBE 运行时字段确认关系。

## 协调与停止条件

外部审阅完成后，协调审计必须逐行比较内部与外部结论，报告一致、冲突、排除和缺失数量。任何冲突、缺少来源确认、缺少独立困难负例或候选池时，P1 指标保持阻断。

只有来源等级、关系标签、部件族切分、目标字段屏蔽、负例来源和固定候选池全部通过审计后，才可创建 P1 指标输入。即使通过，也必须分开报告 `standard_derived` 与其他来源等级。

## 可复现命令

```bash
python3 experiments/morphology_computing/scripts/build_p1_self_validation_and_external_review_package.py
python3 -m pytest tests/test_morphology_computing_p1_self_validation_external_review.py -q
```

构建脚本与测试随形态计算实验包存放，待实验轨合并时一并入库；工件 1、2 同包存放。外部审阅包（工件 3）已在本仓库上方链接提供。
