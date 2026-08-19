# 小规模实验设计：真实 OCR 残差候选重排

日期：2026-08-19  
状态：可执行

## 1. 目标

在真实 OCR 替换对上验证：

- CNBE 结构距离是否能把正确目标字排在候选第 1 位；
- 相对 Unicode 码点距离是否有可复现增益；
- `variant` 与 `shape_confusable` 两类错误上的表现差异。

## 2. 数据

来源：`experiments/2026-08-06_variant_normalization/variant_pairs.json`

- 共 603 个替换对；
- `variant`：354；
- `shape_confusable`：27；
- `other`：81；
- `truth_not_in_standard`：121；
- `truth_not_in_db`：11；
- `ocr_not_in_db`：9。

过滤条件：`ocr` 与 `truth` 都必须存在于 CNBE DB，否则无法计算结构距离。

## 3. 候选列表构造

对每个替换对 `(ocr, truth)`：

1. 候选列表先放入 `truth`；
2. 加入同一页面出现的其他真值字符；
3. 从 CNBE 标准轨随机采样干扰项，直到候选数达到 20；
4. 不把 `ocr` 本身放入候选列表；
5. 固定 seed 42，保证可复现。

## 4. Baseline 与 CNBE 方法

| 方法 | 排序依据 |
|---|---|
| Random | 随机顺序 |
| Unicode | `abs(ord(ocr) - ord(cand))` |
| CNBE weighted | 结构字段加权距离 |
| CNBE hamming | 32-bit 码流汉明距离 |

## 5. 指标

- Top-1 accuracy
- MRR
- Mean Rank

按全部、`variant`、`shape_confusable` 分别报告。

## 6. 预期

1. CNBE hamming 在 `shape_confusable` 上优于 Unicode；
2. `variant` 对可能与结构距离关系较弱，因为异体字未必结构相似；
3. 实验要诚实报告“CNBE 对结构敏感错误有效，不等于对所有 OCR 错误有效”。

## 7. 交付

- `run_experiment.py`
- `results.json`
- `REPORT.md`

## 8. 复现

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/run_experiment.py
```

## 9. 首轮结果（2026-08-19）

### 全部替换对

| 方法 | Top-1 | MRR | Mean Rank |
|---|---:|---:|---:|
| Random | 4.62% | 0.1809 | 10.63 |
| Unicode | 54.53% | 0.6316 | 5.24 |
| CNBE weighted | 21.20% | 0.3296 | 8.48 |
| CNBE hamming | 17.95% | 0.3246 | 7.59 |

### shape_confusable

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Unicode | 88.89% | 0.9383 |
| CNBE weighted | 88.89% | 0.9352 |
| CNBE hamming | 74.07% | 0.8100 |

### 诚实解读

1. 单独使用 CNBE 结构距离没有全面超过 Unicode；
2. 在 shape_confusable 上 CNBE weighted 与 Unicode 打平；
3. 在 variant 上 CNBE 明显落后，因为异体字关系来自 Unihan，不是结构相似性；
4. 结论不是“CNBE 没用”，而是“单靠结构距离不够，必须结合上下文和学习式重排”。

### 下一版实验

- 使用真实 OCR top-N 候选，而不是随机干扰项；
- 增加 Unihan variant map 作为 variant 基线；
- CNBE 字段作为特征输入给小型 re-ranker；
- 对比 ChineseBERT / Glyce / SubChar embedding；
- 增加上下文窗口特征。
