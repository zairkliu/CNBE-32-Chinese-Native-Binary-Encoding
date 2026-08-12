# SCNet CNBE-MoE 后补评估补丁

日期：2026-08-11

## 背景

DCU 双卡训练跑到 125,975 步后，训练循环最后的
`dist.barrier()` / 最终评估 allreduce 超时，进程以 SIGABRT 退出，
因此没有写出 `train_metrics.json`。`output/checkpoints/last.pt`
已正常保存（训练时每 1000 步覆盖，当前为 step 125000）。

本补丁提供单卡后补评估，不再走 DDP，可稳定输出最终指标。

## 补丁内容

```text
code/scripts/eval.py         # 单卡 checkpoint 评估
scnet_eval_dcu2.sh           # 远端一键评估脚本
```

## 上传方式

在本地解压 `scnet_eval_patch_2026-08-11.zip` 后，将两个文件放入
远端对应位置：

```bash
# 假设远端包根目录为 /scnet_upload_package_MERGED_DCU
cp code/scripts/eval.py /scnet_upload_package_MERGED_DCU/code/scripts/eval.py
cp scnet_eval_dcu2.sh /scnet_upload_package_MERGED_DCU/scnet_eval_dcu2.sh
chmod +x /scnet_upload_package_MERGED_DCU/scnet_eval_dcu2.sh
```

## 快速验证（少量批次）

```bash
cd /scnet_upload_package_MERGED_DCU
export CNBE_MOE_ROOT="$PWD/code"
export CNBE_DATA_DIR="$PWD/data"
export CNBE_OUTPUT_DIR="$PWD/output"
export CNBE_MOE_CONFIG=scnet_moe_config_merged_dcu2.yaml
LIMIT_BATCHES=100 bash "$PWD/scnet_eval_dcu2.sh"
```

## 全量评估

```bash
cd /scnet_upload_package_MERGED_DCU
export CNBE_MOE_ROOT="$PWD/code"
export CNBE_DATA_DIR="$PWD/data"
export CNBE_OUTPUT_DIR="$PWD/output"
export CNBE_MOE_CONFIG=scnet_moe_config_merged_dcu2.yaml
bash "$PWD/scnet_eval_dcu2.sh"
```

结果写入 `$CNBE_OUTPUT_DIR/eval_metrics.json`。

注意：全量评估集为 105,468 个窗口，单卡预计需要一段时间；
建议先跑 `LIMIT_BATCHES=100` 验证脚本，再用 `nohup` 或终端会话
跑全量。
