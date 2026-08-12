# CNBE-MoE 三档训练结果导出

日期：2026-08-11

## 一、实际检查点说明

当前训练脚本每 1000 步覆盖保存 `last.pt`，因此远端不存在
`step_*.pt` 序列。本轮实际只有：

```text
output/checkpoints/final.pt   # step 125976 最终模型
output/checkpoints/last.pt    # 被 final.pt 覆盖前的最后常规保存
```

三档导出会按真实文件处理，并生成 `checkpoint_list.txt`。

## 二、输出目录

```text
8-11_0.544Btest/
├── README.md
├── MANIFEST.json
├── core/          # final.pt + config + vocab + mapping
├── normal/        # core + train/eval metrics + training.log
└── full/          # normal + code + 全部现有检查点 + data manifest + system info
```

同时生成三个 tar：

```text
8-11_0.544Btest_core.tar
8-11_0.544Btest_normal.tar
8-11_0.544Btest_full.tar
```

README 为完整训练报告，包含训练环境、时间线、模型配置、最终指标、
L20 对比、情况分析、MoE 分析与下一轮训练要求。

## 三、运行

上传 zip 到 `/scnet_upload_package_MERGED_DCU/` 后：

```bash
cd /scnet_upload_package_MERGED_DCU
unzip -o scnet_export_3tier_patch_2026-08-11_*.zip

python code/scripts/export_training_results.py \
  --root "$PWD" \
  --target "$PWD/8-11_0.544Btest" \
  --skip-hash
```

第一次运行会从 `data/*.cnbe` 构建合并语料 vocab（约几分钟），
保存到 `output/assets/vocab_merged.json`，后续直接复用。

如需 gzip 压缩：

```bash
python code/scripts/export_training_results.py \
  --root "$PWD" \
  --target "$PWD/8-11_0.544Btest" \
  --skip-hash \
  --gzip
```

如需生成 SHA256 清单（7.1GB 模型会额外花时间）：

```bash
python code/scripts/export_training_results.py \
  --root "$PWD" \
  --target "$PWD/8-11_0.544Btest"
```

## 四、下一轮使用 core

下一轮续训时，将 core 里的权重放回检查点目录：

```bash
cp "$PWD/8-11_0.544Btest/core/final.pt" \
   "$PWD/output/checkpoints/last.pt"
```

然后按 `--resume` 续训；vocab 和 mapping 也一并保留在 core 中，
保证后续训练与本轮词表/路由一致。
