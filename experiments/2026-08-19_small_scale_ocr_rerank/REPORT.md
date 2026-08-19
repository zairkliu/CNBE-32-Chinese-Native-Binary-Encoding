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
