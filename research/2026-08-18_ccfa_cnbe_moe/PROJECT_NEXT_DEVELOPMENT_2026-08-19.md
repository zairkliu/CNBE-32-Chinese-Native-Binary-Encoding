# CNBE-MoE 项目预期与下一步发展

日期：2026-08-19  
状态：A800×2 5.4B 训练进行中；论文与古籍语料并行推进

## 1. 当前仓库状态

- 主分支：`main`
- 远程分支：数量较多，主要来自历史实验、文档和发布工作；
- README：README / README_EN / README_ZH 以同一证据状态表约束主张；
- 论文包：`research/2026-08-18_ccfa_cnbe_moe/`
- 实验包：OCR rerank、embedding 对照、古籍 PDF、永乐大典 37 页评估。

## 2. 项目预期

### 2.1 已形成的定位

CNBE 是面向结构敏感任务、国家标准对齐、可计算、可审计的固定 32-bit 结构指纹层，并可作为 MoE 确定性路由先验。

### 2.2 已形成的证据

- A800×2 5.4B 训练进行中；
- 构造候选的 OCR 残差 pilot 中，GBDT + CNBE 特征高于 Unicode 距离；
- DeepSeek V4 API 小样本、条件化结果已记录，尚不构成稳定比较结论；
- ChineseBERT / bert-base-chinese embedding 对照已跑；
- 古籍 PDF OCR pilot 已跑通；
- 37 页永乐大典端到端已评估。

### 2.3 尚未形成

- A800 最终 eval_loss；
- Glyce / SubChar / CNM-BERT 直接对照；
- CLUE sanity check；
- 多 seed 统计显著性；
- 可发布的去敏语料与 benchmark。

## 3. 下一步发展

### 3.1 主线：建立真实 OCR benchmark

- 固定 OCR 引擎实际 top-N 候选，而非真值派生候选；
- 按卷或来源冻结测试集，并发布清单、配置和错误分析；
- 先验证结构特征的实际任务边界，再扩大模型或算力规模。

### 3.2 模型线：完成可解释对照

- 重跑 Unicode baseline；
- 报告非零码条件 struct accuracy；
- 补等计算预算、多种子和直接基线；
- 在同一 benchmark 上补 Glyce / SubChar / CNM-BERT 或可复现替代基线。

### 3.3 训练线：完成 A800×2 5.4B

- 等待正式训练完成；
- 收集最终 eval_metrics、step_metrics、final.pt；
- 回填论文；
- 形成最终收敛曲线与模型分析。

### 3.4 数据线：古籍语料化

- 37 页 -> 70 页 -> 更多 PDF；
- 建立 PDF 清单、OCR 文本、真值、CNBE 编码、质量报告；
- 形成可复现的古籍 OCR 后处理 benchmark。

### 3.5 工程线：仓库整理

- 合并或归档历史分支；
- 清理未推送的本地产物；
- 保持 README 三语同步；
- 明确 release 与 research 边界。

## 4. 风险

| 风险 | 影响 | 处理 |
|---|---|---|
| A800 训练结果不达预期 | 论文主结果受影响 | 将其作为负结果记录，不以旧实验替代未完成验证 |
| Unicode baseline 未修复 | headline 被质疑 | 重跑并降级宣传 |
| Glyce/SubChar 未对照 | 差异化不足 | 补齐 benchmark |
| 古籍数据版权 | 无法公开 | 只发布清单、脚本和去敏结果 |
| 分支过多 | 仓库维护成本高 | 定期合并/归档 |

## 5. 建议

接下来按证据依赖关系推进：

1. 建立真实 OCR top-N benchmark；
2. 修 Unicode baseline 并报告条件指标；
3. 在同一 benchmark 上补强基线与多种子；
4. 收口 A800 最终评估；
5. 以 70 页古籍真值闭环验证可复用流程。

这些步骤完成后，论文与产品入口才有共同、可审计的证据基础。
