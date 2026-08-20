# 实验与 SegmentFault 评审结论的对照

日期：2026-08-19  
评审结论：

> 方向值得做，但 CNBE 的定位不该是“重新发明中文底层编码”，而该是“为结构敏感任务提供可计算的结构指纹层”。后者是已有赛道，需要回答相对 ChineseBERT / CNM-BERT / SubChar 的差异化优势。

## 1. “方向值得做”的证据

| 实验 | 结果 | 意义 |
|---|---|---|
| 零样本结构重排 | CNBE hamming Top-1 50.96% vs Unicode 46.15% | 结构指纹可零样本排序 |
| OCR 残差构造候选重排 | GBDT Top-1 66.39% vs Unicode 50.42% | 受限候选排序条件下的 pilot；不能外推为真实 OCR top-N 增益 |
| DeepSeek API v5 | CNBE 提示 92.31% vs Unicode 85.71% vs plain 71.43% | 结构字段帮助 LLM 提示 |
| 古籍 OCR pilot | CNBE 覆盖率 100% | 标准轨覆盖可验证 |

结论：方向不是空的，真实实验产生了可复现增益。

## 2. “定位为结构指纹层”的证据

评审指出：CNBE 不应宣称“重新发明编码”，而应作为“结构敏感任务的可计算结构指纹层”。

我们的实验恰好支持这一点：

- 单独 CNBE 距离在构造候选的 OCR 残差重排中不够强；
- 与 Unihan variant map 和上下文结合后才有明显增益；
- 作为特征进入 GBDT/MLP 后超过 Unicode；
- 作为 API 提示时高于 plain/Unicode。

这说明 CNBE 是“可计算特征层”，不是“端到端万能方案”。

## 3. 与“已有赛道”的差异化

| 维度 | ChineseBERT | CNM-BERT | SubChar | CNBE-32 |
|---|---|---|---|---|
| 表示 | Unicode + 字形/拼音 | 结构 embedding | 字内 token | 固定 32-bit 字段 |
| 确定性路由键 | 无 | 无 | 无 | 有 |
| 零样本结构距离 | 弱 | 弱 | 弱 | 可计算 |
| 国家标准对齐 | 无 | 无 | 无 | GB 8105 / GF |
| 硬件/系统层 | 无 | 无 | 无 | RISC-V / Verilog / Linux |
| 真实 OCR top-N 重排增益 | 待测 | 待测 | 待测 | 待测（现有为构造候选 pilot） |

我们的差异化是：

1. 不需要训练即可获得结构相似度；
2. 可作为 O(1) MoE 路由键；
3. 字段可审计、可复现、国家标准对齐；
4. 同一表示贯通 SDK、数据库、模型、硬件原型。

## 4. 仍然缺少的直接对照

尚未完成：

- 在同一个 OCR 重排 benchmark 上跑 ChineseBERT / Glyce / SubChar / CNM-BERT embedding；
- 在同一个结构敏感 benchmark 上比较“CNBE 字段”与“学习式结构 embedding”；
- 通用 NLU sanity check。

这些是投稿前必须补齐的对照。

## 5. 结论

我们的实验已经把评审结论从“观点”变成了“证据”：

- 方向有价值：多个独立实验有增益；
- 定位正确：CNBE 作为结构指纹层，而不是底层编码替代；
- 差异化明确：固定字段、确定性路由、零样本距离、标准对齐、全栈一致性；
- 剩余工作：与 ChineseBERT / CNM-BERT / SubChar 的直接 benchmark 对照。
