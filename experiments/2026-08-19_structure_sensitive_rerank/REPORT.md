# CNBE 结构敏感候选重排实验

日期：2026-08-19  
类型：零样本确定性实验，无模型训练

## 1. 目的

回答外部评审提出的定位问题：CNBE 的价值是否真的集中在结构敏感任务上？

本实验不训练任何模型，直接用 CNBE 结构距离对“OCR 形近字纠错”的候选列表重排，并与 Unicode 码点距离、随机基线对比。

## 2. 任务设定

对每个形近字族，构造 OCR 纠错场景：

- 观测字：族内一个字符（模拟 OCR 识别错误）；
- 目标字：族内另一个字符（模拟正确字符）；
- 候选列表：族内除观测字外的全部字符 + 20 个标准轨随机干扰项；
- 任务：把目标字排在候选列表第 1 位。

该设定避免“查询字本身在候选里”的自证陷阱。

## 3. 方法

| 方法 | 打分 |
|---|---|
| Random | 随机顺序 |
| Unicode | `abs(ord(query) - ord(cand))` |
| CNBE weighted | 结构字段加权距离 |
| CNBE hamming | 32-bit 码流汉明距离 |

## 4. 结果

| 方法 | Top-1 | MRR | Mean Rank |
|---|---:|---:|---:|
| Random | 2.88% | 0.1599 | 11.57 |
| Unicode | 46.15% | 0.5928 | 4.47 |
| CNBE weighted | 48.08% | 0.6070 | 4.35 |
| CNBE hamming | 50.96% | 0.6402 | 3.80 |

## 5. 解读

1. CNBE bit Hamming 距离把 Top-1 从 Unicode 的 46.15% 提升到 50.96%（+4.8pp）；
2. CNBE Hamming MRR 0.6402 优于 Unicode 0.5928；
3. CNBE 不需要训练即可获得结构敏感的候选排序；
4. 收益来自结构字段，而不是码点数字接近性；
5. 该实验支持论文定位：CNBE 是“结构敏感任务的计算结构指纹层”。

## 6. 与已有证据的关系

- API 形近字消歧：CNBE hint 0.933 vs plain 0.600（+33.3pp）；
- 1.5B 模型形近字区分：92.7%；
- 本实验：零样本结构距离在候选重排上仍优于 Unicode 码点距离。

## 7. 局限

1. Unicode baseline 是码点数字距离，不是训练后的 embedding；
2. 未与 ChineseBERT / Glyce / SubChar / CNM-BERT 的学习式编码对比；
3. 形近字族为人工构造，规模有限；
4. 尚未做通用 NLU sanity check。

## 8. 下一步

- 增加 500+ 真实 OCR 替换对；
- 对比 ChineseBERT / Glyce / SubChar embedding；
- 用 CNBE Hamming + weighted 混合排序；
- 在 CLUE 子集上确认通用 NLU 无显著回退。

## 9. 复现

```bash
python experiments/2026-08-19_structure_sensitive_rerank/run_rerank_experiment.py
```

结果文件：`results.json`
