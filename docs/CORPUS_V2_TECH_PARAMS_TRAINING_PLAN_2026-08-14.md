# CNBE 中文语料库 v2 技术参数与训练计划

日期：2026-08-14
状态：v2 已冻结；训练计划待执行

## 1 目标

本文档汇总 CNBE 中文语料库 v2 的冻结技术参数、模型配置、训练资源与实验计划，供 GitHub 发布、算力申请与训练执行使用。论文正文暂不随本文档发布。

## 2 语料库 v2 技术参数

### 2.1 组成与规模

| 项目 | 值 |
|---|---:|
| 总文件数 | 15,589 |
| core / technical | 14,665 / 924 |
| v1 出版物与古籍 | 14,383 |
| 国家法律法规（全国人大/常委会） | 734 |
| 国务院令 | 472 |
| 总字符 | 5,152,417,784 |

国家级文件全部保留，不按低中文占比剔除；含 ASCII 税表的现行法律（如车船税法、资源税法、印花税法）归入 technical 分桶。

### 2.2 切分与 token

| 集合 | 文件数 | 内容 token | 物理词数（含分隔符） |
|---|---:|---:|---:|
| train | 15,288 | 5,069,636,759 | 5,069,667,334 |
| eval | 145 | 47,611,070 | 47,611,359 |
| val | 156 | 35,169,957 | 35,170,268 |
| 合计 | 15,589 | 5,152,417,786 | 5,152,448,961 |

切分规则：`sha256(slug|42) mod 10000`，eval 1%、val 1%、train 98%，按文件切分。

### 2.3 编码与路由

| 项目 | 值 |
|---|---:|
| 唯一非空 CNBE 码 | 20,534 |
| 冻结词表（含 code 0） | 20,535 |
| CNBE 码表覆盖率 | 96.95% |
| mapping 模板 | 14,248 |
| 专家数 | 128 |
| mapping 模式 | `(radix, struct, strokes)` 频率贪心均衡 |

### 2.4 质量校准

| 指标 | 值 |
|---|---:|
| CJK 覆盖 core / technical | 99.9996% / 99.9984% |
| H(radix) / H(strokes) / H(struct) | 5.8894 / 3.6896 / 2.1068 |
| core/technical KL 散度均值 | 0.2093 |
| 500 对 max Jaccard | 0.0027 |
| Jaccard > 0.3 对数 | 0 |
| manifest 完整性 | 15,589 / 15,589 |
| 缺失 / 孤儿文件 | 0 / 0 |

### 2.5 code-0 策略

| 集合 | code-0 token | 占比 |
|---|---:|---:|
| train | 909,980,600 | 17.9496% |
| eval | 9,199,423 | 19.322% |
| val | 6,120,227 | 17.401% |

决策：next-code 语言建模保留 code 0；Structure-MLM / 字段头训练对 code 0 的字段 loss 置零。

### 2.6 冻结产物

- `canonical_manifest.json`：文件级切分与完整性记录
- `train.cnbe` / `eval.cnbe` / `val.cnbe`：CNBE uint32 大端码流
- `vocab.json`：20,535 词表
- `mapping_128.json`：14,248 模板 / 128 专家
- `code0_strategy.json` 与 `scnet_moe_config_corpus_v2_frozen.yaml`
- `verify_frozen.py`：严格一致性校验

校验口径：

- 物理词数 = `.cnbe` 文件大小 / 4
- 内容 token = 物理词数 - 书间分隔符
- 三集合物理词数与 `encode_stats.json` 完全一致

## 3 模型技术参数

### 3.1 CNBE-MoE-128（主实验）

| 参数 | 值 |
|---|---:|
| d_model / d_ff | 1024 / 2048 |
| 层数 / 头数 | 12 / 16 |
| 专家数 | 128 |
| Top-k | 2 |
| 路由 | 硬路由 |
| seq_len | 256 |
| batch_size / GPU | 8（可按显存调为 16） |
| grad_accum_steps | 1 |
| epochs | 1 |
| 学习率 | 3e-4 |
| warmup_steps | 100 |
| precision | bf16 |
| balance_weight | 0.02 |
| aux_loss_weight | 0.1 |
| seed | 42 |

### 3.2 对照实验

| 条件 | 说明 |
|---|---|
| CNBE-Dense matched-params | 与 MoE-128 等参数量 |
| CNBE-Dense 同配置 | 相同 d_model/layers，非等参数 |
| Unicode-Dense | Unicode 码点输入，配置与早期实验一致 |

## 4 训练计划

### 4.1 优先级

| 优先级 | 实验 | 目的 |
|---|---|---|
| P0 | CNBE-MoE-128 1 epoch | 验证 v2 全量码流收敛与最终指标 |
| P1 | Dense matched-params | 验证 MoE 在大规模上的持续优势 |
| P1 | Unicode-Dense | 验证 CNBE 编码在大规模上的持续优势 |
| P2 | code-0 mask 消融 | 验证 17.9496% code-0 对字段学习的稀释程度 |
| P2 | balance_weight 0.01/0.03/0.05 | 平衡 eval_loss 与 expert Gini |
| P2 | 128/256 专家对比 | 验证专家数与数据规模的匹配 |

### 4.2 资源配置

| 实验 | 推荐硬件 | 预计时间 |
|---|---|---:|
| MoE-128 1 epoch | 4x/8x A800 80GB 或 8x DCU | 约 2-3 天 |
| Dense matched-params | 4x/8x A800 或 8x DCU | 约 1-2 天 |
| Unicode-Dense | 4x/8x A800 或 8x DCU | 约 1-2 天 |
| 消融实验 | 4x A800 或 8x DCU（并行） | 约 1-2 天 |

### 4.3 预期指标

以下为基于 24M -> 544M 趋势的预期，不作为已实验结论：

| 指标 | 544M 实测 | v2 全量预期 |
|---|---:|---:|
| eval_loss | 4.5915 | 3.8-4.2 |
| next-code | 23.56% | 26-30% |
| struct | 44.07% | 48-52% |
| expert_gini | 0.2971 | 0.20-0.25 |

### 4.4 防错要求

1. 最终 checkpoint 必须先于任何 collective 保存；
2. 中间 checkpoint 独立保存，不覆盖 `last.pt`；
3. 每步写 `step_metrics.jsonl`，日志通过 `tee` 落盘；
4. 训练启动前先 smoke：100 步 + resume 测试；
5. 冻结包的 vocab/mapping/配置与训练脚本版本一致；
6. 设置 `NCCL_TIMEOUT=1800`，避免 barrier 超时丢状态。

## 5 风险与缓解

| 风险 | 缓解 |
|---|---|
| NCCL 超时 | 设置超时并强制保存 final.pt |
| expert Gini 偏高 | balance_weight 从 0.02 提升至 0.03-0.05 |
| 显存不足 | 4x A800 80GB；必要时 batch=8 + grad_accum=2 |
| 语料加载 I/O | 预加载码流到内存或使用高速 SSD |
| 训练口径不一致 | 使用冻结包中的物理词数与严格校验脚本 |

## 6 GitHub 发布边界

本次发布仅包含技术参数与训练计划文档。暂不发布：

- 论文正文与 Word 版；
- `.cnbe` 语料码流；
- 10.3GB SCNet 冻结包；
- 模型权重与中间 checkpoint。
