# CNBE P1 外部独立评审执行包（Execution Kit）

**English summary:** This kit operationalizes the [P1 External Review Method](../specification/P1_EXTERNAL_REVIEW_METHOD.md) ([中文版](../specification/P1_EXTERNAL_REVIEW_METHOD_ZH.md)). It tells an external reviewer how to verify the 600 blinded rows of the [review packet](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv), what to fill in, how to return the file, and how the maintainers will run the reconciliation audit. P1 metrics stay blocked until the audit passes.

**方法依据：** 本执行包不改变 [P1 自验证与外部独立审阅方法](../specification/P1_EXTERNAL_REVIEW_METHOD_ZH.md) 的任何规则，只把它落到可执行的收发流程。若本文与方法文档冲突，以方法文档为准。

---

## 1. 评审任务概览

| 项目 | 内容 |
|---|---|
| 评审文件 | [`P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv`](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv) |
| 行数 | **600 行**（`P1_EXT_001`–`P1_EXT_600`） |
| 关系类型 | 三类各 200 行：部首/部件（`shared_radical_component`）、结构（`same_reviewed_structure`）、笔画数（`stroke_count_within_tolerance`） |
| 来源等级 | 全部 `standard_derived`（由国家标准相关数据派生），Unicode 身份核验全部通过 |
| 需要填写的列 | 5 列，详见 §4；其余列**一律不得改动** |
| 预计工作量 | 每行约 20–40 秒，全卷约 3–5 小时；可分次完成 |

**盲审纪律：** 评审过程中请**不要**试图查找本项目内部的既有结论、标签、切分或数学分数，也**不要**用 CNBE 编码字段反推答案。你的每一行结论必须独立来自来源文件本身。

## 2. 评审前准备

1. **取得评审人编号**：由项目维护者分配，形如 `REV_A`、`REV_B`。全部填在 `external_reviewer_id` 列。
2. **打开文件**：CSV 为 UTF-8 编码。Excel 请用「数据 → 从文本/CSV → 编码选 65001 (UTF-8)」导入，WPS 同理；直接双击打开可能出现乱码。**保存时保持 UTF-8 CSV 格式**，不要另存为 xlsx。
3. **不要改动**：`external_review_id` 及前 12 列任何内容；行顺序可以调整以便工作，但提交前请确认 600 行齐全、ID 未变。

## 3. 逐行评审三步

对每一行：

1. **核对身份**：确认 `query_char` / `candidate_char` 两个汉字与 `query_unicode` / `candidate_unicode` 码位一致（查字形即可，两列已预先通过机器核验，你需要的是人工确认"字没有张冠李戴"）。
2. **核对关系声明**：**只依据** `source_document` 和 `source_locator` 定位到的来源内容，判断 `relation_claim_to_verify` 是否成立。三类声明的含义：
   - `radical=X`（部首类）：查询字与候选字是否**同属于部首 X**。例：`P1_EXT_129` 三 / 两，声明 `radical=一`。
   - `candidate_structure_label=S`（结构类）：候选字的字形结构是否为 S（如 `左右`、`上下`、`全包围`、`左上包` 等）。例：`P1_EXT_216` 束 / 木，声明候选字结构为 `镶嵌`。
   - `stroke_count=N`（笔画类）：查询字与候选字的笔画数是否**均为 N 画**。例：`P1_EXT_401` 捣 / 砾，声明 `stroke_count=10`。
3. **填写结论**：按 §4 规则填 5 列。

## 4. 填表规则（只允许这些值）

| 列 | 允许值 | 含义 |
|---|---|---|
| `external_relation_label` | `positive` / `negative` / `exclude` | 关系声明成立 / 不成立 / 无法评审 |
| `external_source_confirmation` | `confirmed` / `unclear` / `conflict` | 来源可确认 / 来源不清楚 / 来源间冲突 |
| `external_reviewer_id` | 你的评审人编号 | 每行都填 |
| `external_review_decision` | 简短文本（如 `approve` / `reject` / `abstain`） | 你的处理决定 |
| `external_review_notes` | 自由文本，可空 | 依据、疑点、来源页码等 |

**硬性规则：**

- 来源定位不到、来源之间冲突、Unicode 身份拿不准 → 填 `exclude`，**不得猜测**。
- 拿不准不等于 `negative`：`negative` 只用于你能确认声明**不成立**的情况。
- 允许使用字典、字源工具辅助定位字形与笔画，但每行结论必须由评审人本人逐行确认；**不接受未经逐行人工确认的批量自动填写**。

## 5. 提交方式

1. 填写完成后，将文件重命名为：
   `P1_EXTERNAL_REVIEW_RETURN_<评审人编号>_<YYYYMMDD>.csv`
   例：`P1_EXTERNAL_REVIEW_RETURN_REV_A_20260810.csv`
2. 通过项目维护者约定的渠道返回（邮件或仓库 PR 均可）。
3. **允许分批提交**（如前 200 行先行返回）；但在你的批次完成协调审计前，对应指标保持阻断，这不影响其他评审人的进度。

## 6. 回收与协调审计（维护者侧流程）

1. **逐行比对**：维护者将回收的外部结论与内部账本逐行比对，统计四类数量：一致（agreement）、冲突（conflict）、外部排除（exclusion）、缺失（missing）。
2. **停止条件**（任一触发，P1 指标继续阻断）：
   - 存在任何未解决的冲突行；
   - 存在来源未确认（`unclear`/`conflict`）且未裁决的行；
   - 缺少独立评审的困难负例或固定候选池。
3. **冲突裁决**：冲突行单独成表，可能请你或其他评审人复核一次；裁决过程留痕，原始外部包与内部账本均不覆盖。
4. **审计通过后**：才生成 P1 指标输入，并按 WS-4 预注册（`docs/benchmarks/WS4_BENCHMARK_PRE_REGISTRATION.md`）计算检索指标；`standard_derived` 来源等级单独报告。

## 7. 常见问题

- **Q：某行我觉得声明"差不多对"但不确定？** 填 `exclude` + `unclear`，并在 notes 写明疑点。宁可排除，不可猜测。
- **Q：可以只审一部分吗？** 可以分批，见 §5.3。单批行数不限。
- **Q：两人同审一卷可以吗？** 欢迎。项目会对重叠行做评审人间一致性统计，这是加分项。
- **Q：来源文件拿不到怎么办？** 该批行填 `exclude` 并注明 `source unavailable`，同时告知维护者——这本身是有价值的审计信号。

---

*本执行包版本：v1.0（2026-07-25）。修订仅通过仓库提交进行。*
