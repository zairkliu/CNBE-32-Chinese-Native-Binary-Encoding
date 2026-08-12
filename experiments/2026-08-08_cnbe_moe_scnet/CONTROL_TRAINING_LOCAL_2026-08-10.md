# P0 控制训练：本地小规模三组对照

日期：2026-08-10
状态：管线已跑通，等待 L20 全量执行

## 一、目的

把“MoE vs Dense、CNBE vs Unicode”两个缺失对照先在本地小规模上跑通，
验证脚本、配置与评估口径，再上 L20 全量执行。

## 二、本地小规模配置

| 项 | 值 |
|---|---:|
| 语料 | zzjh_294（资治通鉴）前 110,000 字 |
| train / eval | 100,000 / 10,000 |
| 模型 | d_model=128，d_ff=256，2 层，4 头 |
| seq_len / batch / steps | 64 / 16 / 40 |
| 随机种子 | 42 |
| 硬件 | NVIDIA（本机 CUDA 12.6） |

## 三、结果

| 模型 | eval_loss | next-token | radix | struct | strokes | Gini | params |
|---|---:|---:|---:|---:|---:|---:|---:|
| MoE-8（CNBE） | 7.3848 | 3.616% | 4.107% | 28.456% | 10.457% | 0.0156 | 1,858,762 |
| Dense（CNBE） | 7.1394 | 3.486% | 3.936% | 28.886% | 9.455% | 0 | 1,463,242 |
| Dense（Unicode） | 7.1237 | 3.526% | 不适用 | 不适用 | 不适用 | 0 | 1,464,527 |

注意：这是 40 步小规模管线验证，不代表 24M 全量结论。当前初步信号是
小规模下 MoE 未优于 Dense，Unicode 与 CNBE Dense 接近；这进一步支持
“先跑全量对照，再决定 MoE 是否继续”的判断。

## 四、产物

| 文件 | 说明 |
|---|---|
| `results_2026-08-10/control_moe8_local.json` | MoE-8 结果 |
| `results_2026-08-10/control_dense_local.json` | CNBE Dense 结果 |
| `results_2026-08-10/control_unicode_local.json` | Unicode Dense 结果 |
| `config_src/scnet_moe_config_control_*.yaml` | 三组本地配置 |

## 五、L20 全量执行命令

```bash
export CNBE_DATA=/scnet_upload_package/data
export CNBE_TXT=/scnet_upload_package/data_src
export CNBE_OUT=/scnet_upload_package/output

# 1. Dense same-config（CNBE 码流）
python scripts/train_distributed.py \
  --config config/scnet_moe_config_dense_l20.yaml \
  --cnbe-paths $CNBE_DATA/*.cnbe \
  --output $CNBE_OUT/dense_metrics.json \
  --checkpoint-dir $CNBE_OUT/dense_checkpoints

# 2. Unicode same-config
python scripts/build_unicode_dataset.py \
  --chars-paths $CNBE_TXT/*.chars.txt \
  --output-dir $CNBE_OUT/data_unicode

python scripts/train_unicode_baseline.py \
  --config config/scnet_moe_config_unicode_l20.yaml \
  --codepoint-paths $CNBE_OUT/data_unicode/unicode.u32 \
  --output $CNBE_OUT/unicode_metrics.json \
  --checkpoint-dir $CNBE_OUT/unicode_checkpoints
```

判定门禁：

- MoE next-code / struct ≤ Dense：停止 MoE 路线；
- CNBE next-code ≤ Unicode next-token：停止“CNBE 优于 Unicode”主张；
- 两组都通过，才允许进入 P1（修 MoE 实现）后的规模化实验。
