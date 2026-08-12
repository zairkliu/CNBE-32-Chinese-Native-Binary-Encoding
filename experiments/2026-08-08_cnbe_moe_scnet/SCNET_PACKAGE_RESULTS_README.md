# SCNet 训练结果打包脚本

日期：2026-08-11

## 作用

在远端一键打包本轮 DCU 128 训练结果，并生成：

- `ROUND_REPORT.md`：详细训练结果报告；
- `ROUND_KNOWLEDGE.json`：结构化知识档案，供下一轮训练继承；
- `TRAINING_LOG.md`：训练时间线日志；
- `artifacts/`：train/eval metrics、mapping、config、训练与评估脚本、
  `final.pt`；
- `round2-dcu128_2026-08-11.tar`：整体 tar 包。

## 运行

上传 zip 到 `/scnet_upload_package_MERGED_DCU/` 后：

```bash
cd /scnet_upload_package_MERGED_DCU
unzip -o scnet_package_results_patch_2026-08-11.zip

export CNBE_MOE_ROOT="$PWD/code"
export CNBE_DATA_DIR="$PWD/data"
export CNBE_OUTPUT_DIR="$PWD/output"

python "$CNBE_MOE_ROOT/scripts/package_results.py" \
  --root "$PWD" \
  --output-dir "$CNBE_OUTPUT_DIR/package_round2_dcu128"
```

如需跳过模型哈希以节省时间：

```bash
python "$CNBE_MOE_ROOT/scripts/package_results.py" \
  --root "$PWD" \
  --output-dir "$CNBE_OUTPUT_DIR/package_round2_dcu128" \
  --skip-hash
```

如需 gzip 压缩 tar：

```bash
python "$CNBE_MOE_ROOT/scripts/package_results.py" \
  --root "$PWD" \
  --output-dir "$CNBE_OUTPUT_DIR/package_round2_dcu128" \
  --gzip
```

如需排除 7.1GB 的 `final.pt`，只打指标和报告：

```bash
python "$CNBE_MOE_ROOT/scripts/package_results.py" \
  --root "$PWD" \
  --output-dir "$CNBE_OUTPUT_DIR/package_round2_dcu128" \
  --no-checkpoint
```

## 下一轮继承方式

下一轮训练开始时：

1. 使用本轮 `final.pt` 作为初始权重；
2. 保持同一 eval split（27,000,000 token）以严格对比；
3. 先跑同参数 Dense 对照；
4. 提高 balance_weight，目标 expert_gini <= 0.20；
5. 路由均衡达标后再评估 256 专家。
