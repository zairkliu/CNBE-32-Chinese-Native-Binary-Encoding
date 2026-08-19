# V1 老版本 DCU2 受控对比实验包

日期：2026-08-11

## 目的

在 v1 老版本 24M 语料上，用同一套 DDP 训练脚本、同一 eval split，
完成三组/四组对照：

| Arm | 配置 | 编码 |
|---|---|---|
| MoE-128 | `v1_moe128_dcu2.yaml` | CNBE |
| Dense same-config | `v1_dense_dcu2.yaml` | CNBE |
| Dense matched-params（可选） | `v1_dense_matched_dcu2.yaml` | CNBE |
| Unicode Dense | `v1_unicode_dcu2.yaml` | Unicode 码点 |

## 前提

- DCU2 双卡环境，PyTorch 2.9 / DTK 26.04；
- v1 数据目录包含 7 个 .cnbe：
  `zzjh_294/luxun_18/agatha/csbook/jinyong/caixin/sushi`；
- 对应 `data_src/*.chars.txt` 用于生成 Unicode 码点流；
- 脚本会自动查找：
  `/scnet_upload_package_DCU/data` 或 `/scnet_upload_package/data`，
  也可用 `CNBE_V1_DATA_DIR` / `CNBE_V1_TEXT_DIR` 指定。

## 运行

```bash
cd /scnet_upload_package_MERGED_DCU/control_v1_dcu2
bash scripts/run_v1_control_dcu2.sh
```

可选等参数 Dense：

```bash
RUN_MATCHED=1 bash scripts/run_v1_control_dcu2.sh
```

## 输出

```text
output/
├── data_unicode/unicode.u32
├── moe128_metrics.json
├── dense_metrics.json
├── dense_matched_metrics.json
├── unicode_metrics.json
├── moe128_eval_metrics.json
├── dense_eval_metrics.json
├── dense_matched_eval_metrics.json
├── unicode_eval_metrics.json
├── checkpoints/{moe128,dense,dense_matched,unicode}/final.pt
└── comparison_table.md
```

## 控制条件

- 同一训练脚本 `train_distributed.py`；
- 同一评估脚本 `eval.py`；
- 同一 seed 42、同一 train/eval split；
- grad_accum_steps=1，epochs=2，保证“真 2 epoch”语义；
- Unicode 也走同一 DDP 训练入口，保证步数与 batch 一致。

## 判定

`comparison_table.md` 生成后按设计文档门禁判断：

- MoE next-code / struct 不优于 Dense matched-params：停止 MoE 路线；
- CNBE Dense next-code 不优于 Unicode Dense next-token：
  停止“CNBE 优于 Unicode”主张。
