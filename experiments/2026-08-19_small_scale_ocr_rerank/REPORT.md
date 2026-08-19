# 小规模真实 OCR 残差重排：首轮结果

日期：2026-08-19  
状态：首轮 pilot，明确后续修正方向

## 1. 数据

- 来源：37 页永乐大典 VL-1.6 残差；
- 全部替换对：603；
- 可评估对：585；
- 标签：variant 350、shape_confusable 27、other 81、truth_not_in_standard 127。

## 2. 方法

- 候选列表 = 真值字 + 同页真值字符 + 20 个标准轨随机干扰项；
- 排序方法：Random / Unicode / CNBE weighted / CNBE hamming；
- 指标：Top-1、MRR、Mean Rank；
- seed 42。

## 3. 总体结果

| 方法 | Top-1 | MRR | Mean Rank |
|---|---:|---:|---:|
| Random | 4.62% | 0.1809 | 10.63 |
| Unicode | 54.53% | 0.6316 | 5.24 |
| CNBE weighted | 21.20% | 0.3296 | 8.48 |
| CNBE hamming | 17.95% | 0.3246 | 7.59 |

## 4. shape_confusable

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Unicode | 88.89% | 0.9383 |
| CNBE weighted | 88.89% | 0.9352 |
| CNBE hamming | 74.07% | 0.8100 |

## 5. variant

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Unicode | 62.00% | 0.6946 |
| CNBE weighted | 16.86% | 0.2921 |
| CNBE hamming | 12.57% | 0.2757 |

## 6. 结论

1. 结构距离单独使用不足以成为 OCR 重排主排序器；
2. shape_confusable 上 CNBE weighted 与 Unicode 打平，说明字段信息有效但未形成增益；
3. variant 错误应使用 Unihan variant map，而不是结构距离；
4. 下一版必须把 CNBE 字段作为特征输入学习式 re-ranker，并加入上下文。

## 7. 下一版设计

- 真实 OCR top-N 候选；
- Unihan variant map baseline；
- CNBE 字段 + 上下文 + 学习式排序；
- ChineseBERT / Glyce / SubChar 对照；
- 报告按 label 分层。

## 8. 复现

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/extract_substitutions.py
python experiments/2026-08-19_small_scale_ocr_rerank/run_experiment.py
```

## 9. 学习式 re-ranker 首轮

新增 Logistic Regression re-ranker，按 page 切分 train/test：

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Random | 3.36% | 0.1459 |
| Unicode | 50.42% | 0.5700 |
| CNBE weighted | 21.85% | 0.3187 |
| CNBE hamming | 19.33% | 0.3062 |
| Learned (LR) | 42.86% | 0.5219 |

结论：简单 LR 仍低于 Unicode。说明当前特征和候选构造还不够，需要：

- 真实 OCR top-N；
- 上下文特征；
- 更强模型；
- Unihan variant map 单独处理 variant 错误。

复现：

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/build_features.py
python experiments/2026-08-19_small_scale_ocr_rerank/train_reranker.py
```

## 10. 第二轮：上下文 + GBDT

加入：

- 左右上下文 Unicode；
- 候选与左右字的 CNBE 距离；
- Unihan variant map baseline；
- HistGradientBoostingClassifier。

总体结果（已移除目标字频率等泄漏特征）：

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Random | 3.36% | 0.1459 |
| Unicode | 50.42% | 0.5700 |
| CNBE weighted | 21.85% | 0.3187 |
| CNBE hamming | 19.33% | 0.3062 |
| Variant map | 41.18% | 0.4853 |
| Learned LR | 44.54% | 0.5483 |
| Learned GBDT | 66.39% | 0.7123 |
| Learned MLP | 62.18% | 0.6649 |
| Rank fusion ensemble | 57.14% | 0.6576 |
| Learned stacking | 65.55% | 0.7023 |

按 label 看：

| 类型 | Unicode Top-1 | GBDT Top-1 | Variant map Top-1 |
|---|---:|---:|---:|
| variant | 56.90% | 87.93% | 79.31% |
| shape_confusable | 90.00% | 80.00% | 10.00% |
| other | 15.38% | 19.23% | 3.85% |

结论：

1. GBDT 加上下文特征后总体超过 Unicode；
2. variant 错误由 variant map 和 GBDT 共同覆盖；
3. shape_confusable 上 Unicode/MLP 仍更强；
4. 简单 rank fusion 没有超过 GBDT，说明应继续用学习式融合；
5. learned stacking 与 GBDT 接近，说明当前特征集下单模型已接近上限；
6. 下一步用真实 OCR top-N 和更强上下文模型继续提升。
