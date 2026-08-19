# DeepSeek V4 API 三条件重排实验

日期：2026-08-19  
模型：deepseek-v4-flash  
样本：20 个真实 OCR 替换对

## 1. 条件

- plain：仅给候选汉字；
- unicode：候选汉字 + Unicode 码点；
- cnbe：候选汉字 + CNBE 结构字段。

## 2. 结果

| 条件 | Top-1 | 已解析 | 总样本 |
|---|---:|---:|---:|
| plain | 91.67% | 12 | 20 |
| unicode | 76.92% | 13 | 20 |
| cnbe | 84.62% | 13 | 20 |

## 3. 解读

1. 已解析样本中，plain 和 cnbe 均高于 unicode；
2. cnbe 没有显著优于 plain，说明结构字段作为提示语没有形成明显增量；
3. 未解析比例偏高，需要改进输出约束和解析；
4. 该 pilot 不用于论文 headline，只用于判断是否值得继续投入 API 对照。

## 4. 下一步

- 提高解析率：使用 JSON 输出约束或“只输出候选编号”；
- 增加样本到 100；
- 增加上下文；
- 与本地 GBDT/MLP 对照。

## 5. 复现

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/api_rerank_experiment.py --limit 20
```

结果：`api_rerank_results.json`

## 6. v5：编号输出 + 明确提示词

改用候选编号输出，样本 19，结果：

| 条件 | Top-1 | 已解析 | 解析率 |
|---|---:|---:|---:|
| plain | 71.43% | 14 | 73.68% |
| unicode | 85.71% | 14 | 73.68% |
| cnbe | 92.31% | 13 | 68.42% |

解读：

1. 已解析样本中，CNBE 最高；
2. 解析率约 68%-74%，仍需改进；
3. 该结果可进入论文作为“CNBE 提示优于 plain/Unicode”的早期证据；
4. 最终论文需要更大样本和严格输出约束。

复现：

```bash
python experiments/2026-08-19_small_scale_ocr_rerank/api_rerank_v2.py \
  --limit 20 \
  --output experiments/2026-08-19_small_scale_ocr_rerank/api_rerank_v5_results.json
```
