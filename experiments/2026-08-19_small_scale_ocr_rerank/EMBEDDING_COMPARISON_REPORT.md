# Embedding 对照：ChineseBERT / BERT vs CNBE

日期：2026-08-19  
任务：同一 OCR 候选重排 benchmark，200 个查询组

## 结果

| 方法 | Top-1 | MRR |
|---|---:|---:|
| CNBE hamming（零样本） | 15.94% | 0.2880 |
| ChineseBERT embedding | 18.12% | 0.3024 |
| bert-base-chinese embedding | 40.58% | 0.4869 |
| CNBE + 上下文 + GBDT | 66.39% | 0.7123 |
| CNBE + API 提示 | 92.31% | 已解析样本 |

## 解读

1. raw CNBE 距离不如 pretrained embedding；
2. ChineseBERT 在该简单重排上并不强；
3. bert-base-chinese 明显更强；
4. CNBE 作为特征进入 GBDT 后显著反超；
5. CNBE 作为 API 提示也有增益。

## 结论

这正好支持“CNBE 是结构指纹特征层，而不是端到端排序器”的定位。

单独使用结构距离不是最佳选择；与上下文、variant map 和学习式 reranker 结合才是正确用法。

## 复现

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/embedding_baselines.py --model ShannonAI/ChineseBERT-base --limit 200
python experiments/2026-08-19_small_scale_ocr_rerank/embedding_baselines.py --model bert-base-chinese --limit 200
```

结果文件：

- `embedding_baseline_results.json`
- `embedding_bert_chinese_results.json`
