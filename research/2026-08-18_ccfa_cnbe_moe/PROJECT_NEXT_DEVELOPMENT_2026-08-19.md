# CNBE-MoE 项目预期与下一步发展

日期：2026-08-19  
状态：A800×2 5.4B 训练进行中；论文与古籍语料并行推进

## 1. 当前仓库状态

- 主分支：`main`
- 远程分支：数量较多，主要来自历史实验、文档和发布工作；
- README：README / README_EN / README_ZH 三语已同步；
- 论文包：`research/2026-08-18_ccfa_cnbe_moe/`
- 实验包：OCR rerank、embedding 对照、古籍 PDF、永乐大典 37 页评估。

## 2. 项目预期

### 2.1 已形成的定位

CNBE 是面向结构敏感任务、国家标准对齐、可计算、可审计的固定 32-bit 结构指纹层，并可作为 MoE 确定性路由先验。

### 2.2 已形成的证据

- A800×2 5.4B 训练进行中；
- GBDT + CNBE 特征在 OCR rerank 上超过 Unicode；
- DeepSeek V4 API 提示中 CNBE 高于 Unicode 和 plain；
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

### 3.1 主线：完成 A800×2 5.4B

- 等待正式训练完成；
- 收集最终 eval_metrics、step_metrics、final.pt；
- 回填论文；
- 形成最终收敛曲线与模型分析。

### 3.2 论文线：补齐 CCF-A 证据

- 重跑 Unicode baseline；
- 报告非零码条件 struct accuracy；
- 补 Glyce / SubChar / CNM-BERT 对照；
- 补 CLUE sanity；
- 补多 seed；
- 最终定稿 CCF-A 论文。

### 3.3 数据线：古籍语料化

- 37 页 -> 70 页 -> 更多 PDF；
- 建立 PDF 清单、OCR 文本、真值、CNBE 编码、质量报告；
- 形成可复现的古籍 OCR 后处理 benchmark。

### 3.4 工程线：仓库整理

- 合并或归档历史分支；
- 清理未推送的本地产物；
- 保持 README 三语同步；
- 明确 release 与 research 边界。

## 4. 风险

| 风险 | 影响 | 处理 |
|---|---|---|
| A800 训练结果不达预期 | 论文主结果受影响 | 已有 544M/受控对比兜底 |
| Unicode baseline 未修复 | headline 被质疑 | 重跑并降级宣传 |
| Glyce/SubChar 未对照 | 差异化不足 | 补齐 benchmark |
| 古籍数据版权 | 无法公开 | 只发布清单、脚本和去敏结果 |
| 分支过多 | 仓库维护成本高 | 定期合并/归档 |

## 5. 建议

接下来只做四件事：

1. 跑完 A800×2；
2. 修 Unicode baseline；
3. 补 Glyce / SubChar 对照；
4. 把古籍 70 页语料化跑通。

这四件事完成后，论文和产品入口都会自然成型。
