# CCF-A 审稿意见响应表

日期：2026-08-18  
论文：CNBE-MoE: Structural Encoding and Expert Routing for Native Chinese Language Modeling

## P0：已完成

| 意见 | 修改 |
|---|---|
| 标题缺乏科学主张 | 改为 “Structural Encoding and Expert Routing” |
| 摘要缺乏叙事 | 重写为“问题-方法-核心发现-规模效应-开放结论” |
| Introduction 未解释结构价值 | 增加 `戊/戌/戎` 例子、科学问题与 claim |
| Related Work 太薄 | 扩到 6 个子节，覆盖结构表征、中文语料、数据质量 |
| Method 缺 loss 与硬件 | 增加 3.6 loss 公式和 3.7 环境表 |
| Results 像实验报告 | 重构为 5.1 实验设计 + 5.2-5.6 科学论证 |
| Analysis 太浅 | 增加“MoE 为什么有效”、“1.5B 为什么失败”、“5.4B 收敛特征” |
| Limitations 太泛 | 改为 6 条可执行限制 |
| Conclusion 缺科学启示 | 强化“结构学习需要专门架构”的结论 |
| 参考文献不足 | 扩充到 30 条，并标注投稿前用 Zotero 核验 |

## P1：待完成

| 项 | 状态 |
|---|---|
| 5.4B 最终 eval_loss | 训练进行中，约 29.8% |
| Dense matched-params | 待跑 |
| 下游任务 1-2 个 | 待设计 |
| 3 seeds 标准差 | 待跑 |
| 最终 Figure 1 | 待正式训练结束 |

## P2：建议

- 使用 Zotero/JabRef 统一参考文献；
- 增加 expert specialization 热力图；
- 增加 tokenizer/BPE 公平对比；
- 公开去敏数据与评估协议。
