# SegmentFault 帖子更新稿

日期：2026-08-19  
用途：回复原问题帖，更新训练进展、实验证据与定位修正。

---

先感谢 @42 和各位答主的专业评审。这篇回复不是反驳，而是按评审意见把项目重新校准后的更新。

## 1. 首先承认原帖里一个关键表述不准确

原帖说“模型看到的是 Unicode 编号”，这个说法不对。真实管线是：

```text
Unicode 码点 -> tokenizer -> embedding lookup
```

模型看到的不是码点整数，而是一个从数据中学出来的原子 token 向量。因此“U+4E00 和 U+4E01 只差 1”这件事，模型本身并不会感知。

更准确的表述应该是：

> 在默认 tokenizer 下，汉字被当作原子 token，结构相似性不会自动出现在 embedding 输入层。

## 2. 对评审结论的接受

我完全接受评审的核心结论：

> CNBE 不应该定位为“重新发明中文底层编码”，而应该定位为“面向结构敏感任务的可计算结构指纹层”。

项目现已按这个方向重写论文 framing，不再宣称替代 Unicode，也不再用通用 NLU 作为主卖点。

## 3. 当前训练状态：A800×2 5.4B / 128 专家 MoE

正式训练已经启动：

- 模型：d_model=1024、12 层、16 头、128 专家、Top-2 硬路由
- 数据：v2 冻结语料，train 5,069,667,334 物理 token
- 全局 batch：8,192 token/step
- 总步数：约 618,750
- checkpoint：每 10,000 步独立保存
- step 指标：每 1 步写入 `step_metrics.jsonl`

截至最新快照：

| 指标 | 值 |
|---|---:|
| 已完成步数 | 250,578 |
| 完成度 | 40.5% |
| 最小训练 loss | 4.0943 |
| 中位数 loss | 5.6690 |
| 相对波动 | 0.1093 |

当前最小训练 loss 已低于上一轮 544M 实验的最终 eval_loss 4.5915。

## 4. 评审后新完成的实验

### 4.1 零样本结构重排

| 方法 | Top-1 |
|---|---:|
| Unicode 码点距离 | 46.15% |
| CNBE hamming | 50.96% |

### 4.2 真实 OCR 残差重排

| 方法 | Top-1 | MRR |
|---|---:|---:|
| Unicode | 50.42% | 0.5700 |
| GBDT + CNBE 特征 + 上下文 | 66.39% | 0.7123 |

### 4.3 DeepSeek V4 API 提示对照

| 条件 | Top-1 | 说明 |
|---|---:|---|
| plain | 71.43% | 已解析样本 |
| Unicode | 85.71% | 已解析样本 |
| CNBE | 92.31% | 已解析样本 |

### 4.4 Embedding 对照

| 表示 | Top-1 | MRR |
|---|---:|---:|
| raw CNBE hamming | 15.94% | 0.2880 |
| ChineseBERT | 18.12% | 0.3024 |
| bert-base-chinese | 40.58% | 0.4869 |
| GBDT + CNBE + 上下文 | 66.39% | 0.7123 |

这个结果很诚实：raw CNBE 距离不如 pretrained embedding；但 CNBE 作为特征进入学习式 reranker 后显著反超。这正好支持“CNBE 是结构指纹特征层，不是端到端排序器”的定位。

### 4.5 古籍 PDF pilot

- 316 个古籍 PDF，约 46.49GB；
- `pdftoppm` 渲染 + Ollama `deepseek-ocr` 识别；
- 页面汉字全部命中 CNBE 标准轨，覆盖率 100%；
- 37 页永乐大典端到端：基线 90.91%，Unihan variant map 修正后 92.64%。

## 5. 对原帖子问题的更新回答

### 5.1 方向是否有价值

有，但要收敛在结构敏感任务：

- 形近字消歧；
- OOV / 生僻字；
- OCR 候选重排；
- 古籍校勘；
- 确定性 MoE 路由。

不再宣称“CNBE 对通用 NLU 有显著提升”。

### 5.2 核心问题在哪

- 生态锁定、字段标准成本、缺少结构敏感 benchmark；
- 大模型会隐式重建结构；
- 单独结构距离不够，必须进入学习式系统；
- 32-bit 字段存在碰撞/lossy 风险，需要持续审计。

### 5.3 下一步怎么走

- 当前重点：A800×2 5.4B 正式训练；
- 并行：真实 OCR top-N、ChineseBERT/Glyce/SubChar 直接对照、CLUE sanity；
- 论文定位：结构敏感任务应用，不是底层编码方案。

### 5.4 对照实验是否足以支撑论文

目前仍不能直接投 CCF-A，必须补：

- Unicode baseline 重跑：当前 0.001% 被我们视为 instrumentation artifact，不再作为 headline；
- Dense matched 已经补跑：eval_loss 7.2802、next-code 2.61%、struct 38.41%、289.86M 参数；
- 非零码上的条件 struct accuracy；
- ChineseBERT / Glyce / SubChar / CNM-BERT 直接对照；
- 通用 NLU sanity check。

## 6. 技术子问题更新

### 6.1 MoE Gini

不再继续调 aux loss 权重。改用：

- DeepSeek-V3 aux-loss-free bias update；
- z-loss 防止 router logit 爆涨；
- device-balance loss 处理双卡专家不均衡。

### 6.2 code 0

- 不是 bug，是类别不平衡；
- 论文会同时报告 with-mask / without-mask；
- 给标点、数字、英文建立独立命名空间；
- 报告非零码条件 struct accuracy。

### 6.3 NCCL 超时

- 开启 `NCCL_ASYNC_ERROR_HANDLING=1`；
- 加 NaN grad hook；
- 加 SIGTERM checkpoint；
- A800 脚本已实现 step checkpoint + resume + final 先保存。

## 7. 定位总结

> CNBE 是面向结构敏感任务、国家标准对齐、可计算、可审计的固定 32-bit 结构指纹层，并可作为 MoE 确定性路由先验。

它不是一个“更聪明的 Unicode”，也不是一个“更聪明的 tokenizer”，而是一个可以被模型、系统、硬件和数据库共同消费的结构计算层。

所有实验脚本、结果和论文草稿均已公开在仓库：

https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding

## 8. 下一步处理

### 8.1 立即执行

1. 重跑 Unicode baseline，修正 `0.001%` 的可疑结果；
2. 报告非零码条件 `struct accuracy`；
3. 将 OCR rerank 升级为真实 OCR top-N 候选；
4. 扩展古籍 OCR 到 70 页卷981真值闭环；
5. 发布本更新稿。

### 8.2 需要算力或模型

1. Glyce / SubChar / CNM-BERT 直接 embedding 对照；
2. CLUE 子集 sanity check；
3. A800×2 5.4B 最终训练指标。

### 8.3 投稿门槛

- A800×2 最终 eval_loss 与收敛曲线；
- Dense matched-params 复核；
- Unicode baseline 修正；
- ChineseBERT / Glyce / SubChar / CNM-BERT 对照；
- 下游 benchmark；
- 多 seed 统计显著性。

### 8.4 推荐顺序

1. 今天：修 Unicode baseline + 条件 struct accuracy + 发布帖子；
2. 本周：古籍 70 页 OCR + Glyce/SubChar 对照；
3. A800 训练完成：回填最终指标并定稿 CCF-A 论文。
