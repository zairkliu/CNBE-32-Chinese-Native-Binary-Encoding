# CNBE-MoE 完整数据链

日期：2026-08-18  
目标：让从“国家标准”到“论文表格”的每一个数据转换都有路径、有校验、有产出。

## 1. 数据链总览

```text
GB 8105 / GF 标准
    -> cnbe32.db (21,178 rows)
    -> CNBE-32 编码表 / vocab
    -> 七语料 .cnbe (24,381,237 chars)
    -> V1 实验子集 (24M / 544M)
    -> V2 冻结语料 (5,152,417,786 content tokens)
    -> mapping_128.json / vocab.json
    -> CNBE-MoE 训练
    -> step_metrics.jsonl / checkpoints / eval_metrics.json
    -> 论文曲线 / 技术报告
```

## 2. 第一段：国家标准到编码库

### 2.1 输入

- GB 8105 通用规范汉字表；
- GF 0011/0012/0013/0017/0023；
- Unicode 码位；
- 人工审核记录。

### 2.2 产出

| 资产 | 数值 |
|---|---:|
| cnbe32.db 总行数 | 21,178 |
| 8105 基线行数 | 8,105 |
| 标准轨行数 | 7,602 |
| 授权 PENC276 编码 | 276 |

### 2.3 校验

每行编码重建通过 13 道门禁，包括 Unicode 身份、国标证据、笔画、结构、部首、人工授权。

## 3. 第二段：编码库到七语料

### 3.1 输入

七类语料：

- 资治通鉴
- 鲁迅全集
- 阿加莎全集
- Linux 程序设计
- 金庸全集
- 财新周刊
- 骆文忠公奏稿

### 3.2 产出

| 指标 | 值 |
|---|---:|
| 总字符数 | 24,381,237 |
| CNBE 覆盖率 | 99.98%-100% |
| `.cnbe` 码流 | 已生成 |
| 专家映射 | 16/64 专家 |
| 路由基准 | 74%-84% |

## 4. 第三段：七语料到 V2 冻结语料

### 4.1 分片

| 分片 | 物理 token | 内容 token | 分隔符 |
|---|---:|---:|---:|
| train | 5,069,667,334 | 5,069,636,759 | 30,575 |
| eval | 47,611,359 | 47,611,070 | 289 |
| val | 35,170,268 | 35,169,957 | 311 |

### 4.2 恒等式

```text
physical_tokens = file_size / 4
physical_tokens = content_tokens + separator_tokens
```

### 4.3 确定性切分

```text
split = sha256(slug || "42") mod 10000
```

## 5. 第四段：V2 冻结语料到训练资产

| 资产 | 值 |
|---|---:|
| vocab.json | 20,535 |
| mapping_128.json | 14,248 |
| train.cnbe | 20,278,669,336 bytes |
| eval.cnbe | 190,445,436 bytes |
| val.cnbe | 140,681,072 bytes |

校验命令：

```bash
python scripts/verify_frozen.py /path/to/frozen
```

预期：

```text
train physical_tokens 5069667334 content_tokens 5069636759 separators 30575
eval physical_tokens 47611359 content_tokens 47611070 separators 289
val physical_tokens 35170268 content_tokens 35169957 separators 311
vocab 20535 mapping_templates 14248
```

## 6. 第五段：训练数据消费

### 6.1 流式读取

19G 级 `.cnbe` 文件禁止 `read_bytes()`，使用：

- `load_codes_partial(paths, max_tokens)`
- `StreamCodeDataset` + `np.memmap`

### 6.2 训练批次

```text
global_batch = seq_len * batch_per_gpu * gpus
global_batch = 256 * 16 * 2 = 8192
total_steps ≈ floor(5,069,667,334 / 8192) = 618,750
```

### 6.3 输出

```text
step_metrics.jsonl    每 1 步
training.log          完整日志
step_*.pt             每 10,000 步
final.pt              训练结束
train_metrics.json    训练指标
eval_metrics.json     最终评估
```

## 7. 第六段：指标到论文

### 7.1 直接可用指标

- eval_loss
- next-code accuracy
- radix/struct/strokes accuracy
- expert_gini
- params
- tokens_evaluated

### 7.2 曲线转换

```bash
python tools/extract_step_curves.py \
  --input step_metrics.jsonl \
  --tag a800_5_4b \
  --output-dir step_curves
```

## 8. 数据链审计表

| 环节 | 输入 | 输出 | 校验 |
|---|---|---|---|
| 国标对齐 | GB/GF 标准 | cnbe32.db | 13 道门禁 |
| 七语料 | 原始文本 | `.cnbe` 流 | 覆盖率 |
| V1 实验 | 子集 | metrics | tokens_evaluated |
| V2 冻结 | 全量语料 | train/eval/val | token 恒等式 |
| A800 训练 | 冻结资产 | step/checkpoint/eval | verify_frozen |
| 论文 | metrics | 图表 | 路径与哈希核对 |

## 9. 缺失环节

1. 下游 benchmark 数据链尚未建立；
2. Dense matched-params 数据缺失；
3. 多 seed 重复实验数据缺失；
4. 发布用去敏数据集尚未形成。
