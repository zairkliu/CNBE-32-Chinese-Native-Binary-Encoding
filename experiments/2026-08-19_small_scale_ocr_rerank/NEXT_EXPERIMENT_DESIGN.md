# 下一版实验：CNBE 字段 + 学习式 Re-ranker

日期：2026-08-19  
状态：开始实现

## 1. 为什么需要学习式

首轮结果显示 CNBE 结构距离单独使用不足以全面超过 Unicode。因此下一版把 CNBE 字段作为特征，训练一个轻量 re-ranker，并保持与规则 baseline 对比。

## 2. 数据

- `all_substitutions.json`：603 个真实 OCR 替换对；
- 对每个替换对构造候选列表；
- 正样本：`(ocr, truth)`;
- 负样本：同页真值字符 + 标准轨干扰项。

## 3. 特征

| 特征 | 说明 |
|---|---|
| unicode_abs_diff | `abs(ord(ocr)-ord(cand))` |
| cnbe_weighted | 结构字段加权距离 |
| cnbe_hamming | 32-bit 码流汉明距离 |
| radix_same | 部首是否相同 |
| stroke_same | 笔画是否相同 |
| struct_same | 结构是否相同 |
| idx_same | 索引是否相同 |
| ocr_in_standard | OCR 字是否在标准轨 |
| truth_in_standard | 目标字是否在标准轨 |

## 4. 模型

- 首版：Logistic Regression；
- 后续：GBDT / MLP / 上下文 Transformer。

## 5. 切分

- 按 page 分组切分 train/test，避免同页泄漏；
- seed 42。

## 6. 指标

- Top-1 accuracy
- MRR
- Mean Rank

与 Random / Unicode / CNBE weighted / CNBE hamming 对比。

## 7. 交付

- `build_features.py`
- `train_reranker.py`
- `features.jsonl`
- `learner_results.json`
- 更新 `REPORT.md`
