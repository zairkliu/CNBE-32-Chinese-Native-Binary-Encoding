# SegmentFault 帖子更新稿

日期：2026-08-19  
用途：回复原问题帖，更新训练进展与新的实验结果。

---

先谢谢 @42 和各位答主，愿意花时间把原帖的问题拆得这么细。我按大家的意见把项目重新理了一遍，有些地方确实是我之前想得太大，先认个错。

## 1. 原帖里有个说法不准确

我原来写“模型看到的是 Unicode 编号”，这个说法不准确。

实际流程是：

```text
Unicode 码点 -> tokenizer -> embedding lookup
```

模型看到的不是码点整数，而是 embedding 表里的一个向量。U+4E00 和 U+4E01 数值只差 1，这件事模型并不会感知。

更准确的说法应该是：

> 默认 tokenizer 会把汉字当成一个原子 token，结构相似性不会自动出现在输入层。

## 2. 我现在理解的方向

您说得对：CNBE 不应该定位成“重新发明中文底层编码”。

我现在的定位是：

> CNBE 是面向结构敏感任务的可计算结构指纹层，也可以作为 MoE 的确定性路由先验。

写论文时我会按这个方向来，不再用“替代 Unicode”这种说法。

## 3. 训练进展

A800×2 的 5.4B / 128 专家 MoE 训练已经跑起来了：

- 12 层、d_model 1024、128 专家、Top-2 硬路由；
- 全局 batch 8192 token/step；
- 每 1 步记录 loss，每 10,000 步保存 checkpoint；
- 目前已完成 250,578 步，约 40.5%；
- 最低训练 loss 4.0943，中位数 5.6690；
- 相对波动 0.1093。

补充一句：4.09 是训练 loss，比上一轮 544M 实验的最终 eval_loss 4.5915 低，但两者不是一回事，最后还是要等 eval 结果。

## 4. 这段时间又补了一些实验

### 4.1 真实 OCR 候选重排

| 方法 | Top-1 |
|---|---:|
| Unicode | 50.42% |
| GBDT + CNBE 字段 + 上下文 | 66.39% |

### 4.2 DeepSeek V4 API 提示对照

只统计能正常解析的样本：

| 条件 | Top-1 |
|---|---:|
| plain | 71.43% |
| Unicode | 85.71% |
| CNBE | 92.31% |

### 4.3 Embedding 对照

同一个任务上，直接用字符 embedding 排序：

| 表示 | Top-1 |
|---|---:|
| raw CNBE hamming | 15.94% |
| ChineseBERT | 18.12% |
| bert-base-chinese | 40.58% |

说实话，这个结果挺有意思：raw CNBE 距离并不如 pretrained embedding，但 CNBE 作为特征进入 reranker 后反而更好。这正好说明 CNBE 适合当特征层，不适合直接当排序器。

### 4.4 古籍 OCR

- 316 个古籍 PDF，约 46.49GB；
- 用 `pdftoppm` 渲染 + `deepseek-ocr` 识别；
- 测试页的汉字全部能命中 CNBE 标准轨；
- 37 页永乐大典端到端：基线 90.91%，用 Unihan variant map 修正后 92.64%。

## 5. 原帖里几个问题的更新

### 5.1 Dense matched

已经补跑了：

```text
eval_loss 7.2802
next-code 2.61%
struct 38.41%
params 289.86M
```

### 5.2 Unicode baseline

原帖里 Unicode 0.001% 这个数我现在不太敢信，大概率是实验设置有问题。后面会重跑，暂时不用“2600 倍”这种说法。

### 5.3 MoE Gini

不再继续调 aux loss 权重。后面准备试：

- DeepSeek-V3 的 aux-loss-free bias update；
- z-loss；
- device-balance loss。

### 5.4 code 0

这不是 bug，是类别不平衡。论文里会同时报 with-mask 和 without-mask，也会给标点/数字/英文单独命名空间，并补非零码上的 struct accuracy。

### 5.5 NCCL 超时

会开 `NCCL_ASYNC_ERROR_HANDLING=1`，加 NaN 检查和 SIGTERM checkpoint。当前 A800 脚本已经有 step checkpoint、resume 和 final 先保存。

## 6. 下一步

1. 先把 Unicode baseline 修掉，再补条件 struct accuracy；
2. 古籍 OCR 从 37 页扩到 70 页；
3. 找机会补 Glyce / SubChar / CNM-BERT 的直接对照；
4. 等 A800×2 跑完，用最终 eval 结果回填论文。

所有实验脚本和结果都在仓库里：

https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding
