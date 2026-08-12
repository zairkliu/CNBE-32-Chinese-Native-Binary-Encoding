# SCNet CNBE-MoE 断点续训补丁

日期：2026-08-11

## 背景

DCU 训练跑到 125,975/125,976 步后，训练本体已完成，但末尾的
`dist.barrier()` 评估 allreduce 超时，进程崩溃，`train_metrics.json`
没有写出。`output/checkpoints/last.pt` 保存了 step 125000 的
模型和优化器状态，全量训练没有丢。

## 本补丁做了什么

1. 修改 `train_distributed.py`：
   - 支持 `--resume` 从 `last.pt` 继续训练；
   - 训练跑满后强制保存 `last.pt` 和 `final.pt`；
   - 去掉末尾 DDP barrier，避免再次卡死；
2. 修改 `eval.py`：
   - 使用 uint32 低内存加载；
   - 优先复用已保存 vocab，避免每次都全量排序；
3. 新增 `scnet_resume_dcu2.sh`：一键续训 + 评估。

## 补丁内容

```text
code/scripts/train_distributed.py
code/scripts/eval.py
scnet_resume_dcu2.sh
```

## 使用

上传 zip 到 `/scnet_upload_package_MERGED_DCU/` 后：

```bash
cd /scnet_upload_package_MERGED_DCU
unzip -o scnet_resume_patch_2026-08-11.zip

export CNBE_MOE_ROOT="$PWD/code"
export CNBE_DATA_DIR="$PWD/data"
export CNBE_OUTPUT_DIR="$PWD/output"
export CNBE_MOE_CONFIG=scnet_moe_config_merged_dcu2.yaml

# 只续训，不自动评估
SKIP_EVAL=1 bash "$PWD/scnet_resume_dcu2.sh"

# 续训并自动评估
bash "$PWD/scnet_resume_dcu2.sh"
```

续训只跑 step 125001-125976，约 976 步；`final.pt` 保存后
即使评估阶段失败，模型也已经完整落盘。
