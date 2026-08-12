# V1 老版本受控对比实验设计

日期：2026-08-11
状态：设计稿，待执行

## 一、目的

在 v1 老版本（24M token，L20 第一轮同源数据）上完成三组受控对照，
回答两个问题：

1. CNBE-MoE-128 是否优于同配置/同参数 Dense；
2. CNBE 码流是否优于 Unicode 码点流。

结论将决定下一轮是否继续 MoE、是否继续主张“CNBE 优于 Unicode”。

## 二、对照组设计

| Arm | 模型 | 编码 | 目的 |
|---|---|---|---|
| A | MoE-128（已有 L20 结果） | CNBE | 本轮基线 |
| B1 | Dense same-config | CNBE | MoE 架构对照 |
| B2 | Dense matched-params | CNBE | 等参数量公平对照 |
| C | Dense same-config | Unicode 码点 | 编码对照 |

说明：

- A 已有第一轮结果：eval_loss 6.5821、next-code 19.12%、
  radix 20.23%、struct 34.14%、strokes 24.38%、Gini 0.2071、
  params 289,920,031；
- B2 为推荐新增项，将 Dense 宽度扩到约 290M 参数，避免
  “MoE 参数多所以赢”的质疑；
- C 只报告 eval_loss 与 next-token，不适用 radix/struct/strokes。

## 三、数据与切分

### 3.1 v1 CNBE 数据

- 7 个 .cnbe 文件，共 24,381,237 个码；
- max_train_tokens = 24,000,000；
- max_eval_tokens = 1,200,000；
- eval split = codes[24,000,000 : 25,200,000]；
- 随机种子统一 42。

### 3.2 Unicode 数据

- 使用与 CNBE 完全相同的清洗后文本；
- 按 Unicode 码点顺序生成 4 字节码点流；
- 训练/评估切分与 CNBE 对齐：前 24,000,000 个码点训练，
  24,000,000-25,200,000 评估；
- 产物：`unicode.u32`、`vocab.json`、`meta.json`。

### 3.3 对齐校验

执行前必须校验：

- CNBE 文本字符数 == Unicode 码点数；
- 同一位置字符的 CNBE 与 Unicode 码点一一对应；
- 校验通过后才允许开始训练。

## 四、模型与训练配置

除编码和 MoE 开关外，三组保持同一配置：

| 项 | 值 |
|---|---|
| d_model | 512 |
| d_ff | 2048 |
| n_layers | 8 |
| n_heads | 8 |
| seq_len | 128 |
| batch_size | 8 |
| grad_accum_steps | 8 |
| epochs | 2 |
| lr | 3e-4 |
| weight_decay | 0.01 |
| grad_clip | 1.0 |
| precision | bf16 |
| seed | 42 |
| MoE | A: 128 专家 Top-2；B/C: Dense |
| balance_weight | A: 0.01；B/C: 0 |
| aux_loss_weight | A: 0.1；B/C: 0 |

## 五、评估指标

CNBE 三组统一输出：

| 指标 | 说明 |
|---|---|
| eval_loss | 交叉熵 |
| next-code | 下一码准确率 |
| radix / struct / strokes | 解码字段准确率 |
| radix / struct / strokes head | 字段头准确率 |
| expert_gini | 路由均衡 |
| params | 参数量 |

Unicode Dense 输出：

| 指标 | 说明 |
|---|---|
| eval_loss | 交叉熵 |
| next-token | 下一码点准确率 |
| params | 参数量 |

## 六、假设与门禁

| 假设 | 通过条件 | 不通过动作 |
|---|---|---|
| H1：MoE 优于 Dense | MoE next-code ≥ Dense matched-params，且 struct ≥ Dense | 停止 MoE 路线 |
| H2：CNBE 优于 Unicode | CNBE Dense next-code ≥ Unicode Dense next-token | 停止“CNBE 优于 Unicode”主张 |

门禁至少观察 eval_loss 与 next-token 两列，不只看单项。

## 七、目录结构

```text
repo/experiments/2026-08-08_cnbe_moe_scnet/control_experiments_v1/
├── README.md
├── configs/
│   ├── moe128_l20.yaml
│   ├── dense_l20.yaml
│   ├── dense_matched_l20.yaml
│   └── unicode_l20.yaml
├── scripts/
│   ├── 01_prepare_v1_data.py
│   ├── 02_train_moe128.sh
│   ├── 03_train_dense.sh
│   ├── 04_train_unicode.sh
│   ├── 05_eval_all.py
│   └── 06_make_comparison_table.py
├── data/
│   ├── cnbe_v1/              # 7 个 .cnbe
│   └── unicode_v1/           # unicode.u32 + vocab.json + meta.json
├── runs/
│   ├── moe128/
│   ├── dense_same/
│   ├── dense_matched/
│   └── unicode_dense/
└── results/
    ├── moe128_metrics.json
    ├── dense_same_metrics.json
    ├── dense_matched_metrics.json
    ├── unicode_dense_metrics.json
    └── comparison_table.md
```

## 八、执行步骤

1. 准备 v1 数据：确认 7 个 .cnbe 与清洗文本同源；
2. 生成 Unicode 数据：`build_unicode_dataset.py --chars-paths ...`；
3. 训练 A：已有结果可直接复用；如代码版本变化，则统一重跑；
4. 训练 B1：`train_distributed.py --config dense_l20.yaml`；
5. 训练 B2：新增 matched-params 配置后训练；
6. 训练 C：`train_unicode_baseline.py --config unicode_l20.yaml`；
7. 统一评估：CNBE 用 `eval.py`，Unicode 用对应评估入口；
8. 生成 `comparison_table.md` 并记录决策。

## 九、资源与时间估算

单卡 L20：

| Arm | 预计步数 | 预计时间 |
|---|---:|---:|
| MoE-128 | 46,874 | 约 18 小时 |
| Dense same-config | 46,874 | 预计 6-10 小时 |
| Dense matched-params | 46,874 | 预计 12-18 小时 |
| Unicode Dense | 46,874 | 预计 6-10 小时 |

若复用已有 MoE 结果，新增实验约 1-2 天；若全部重跑约 2-3 天。

## 十、产出物

- 4 个 arm 的 `*_metrics.json`；
- `comparison_table.md`；
- 每组 checkpoint 与日志；
- 本设计文档的最终执行记录；
- 下一轮 MoE 是否继续的决策依据。
