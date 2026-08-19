# A800 训练前错误复盘与补丁清单

日期：2026-08-14

## 一、必须记住的三条

1. **最终 checkpoint 必须先于任何 collective 保存**；
2. **中间 checkpoint 必须独立保存，不能只靠 `last.pt`**；
3. **日志与 per-step 指标必须直接落盘，不能只靠终端**。

## 二、错误对照与修复

| 问题 | 历史表现 | 修复后 |
|---|---|---|
| 训练日志丢失 | L20/DCU 训练只输出终端，论文 step 曲线找不到 | `2>&1 \| tee training.log` |
| per-step 指标丢失 | 需要收敛曲线时无数据 | `step_metrics.jsonl` 每 log 步写入 |
| checkpoint 覆盖 | 只有 `last.pt`，无法恢复中间状态 | 每 10,000 步保存 `step_%06d.pt` |
| resume 只能读 last.pt | 崩溃后从旧 step 续训 | `--resume` 自动找最新 `step_*.pt` |
| 末尾 NCCL barrier 崩溃 | 仅差 6 步崩溃，修了约 4 小时 | 先保存 `final.pt`，再进 collective；最终评估单进程 |
| vocab/mapping 未接入冻结包 | 训练现场重建，版本不一致 | `vocab_path` / `mapping_path` 优先读取冻结文件 |
| 大数组构建慢 | 5.43 亿码 `np.unique` 被误判卡死 | uint32 读取 + vocab 缓存 + 进度提示 |
| 路径/版本不一致 | v1 数据在 MERGED，脚本找 DCU；mapping 用了旧版 | 冻结包统一路径，脚本 SHA 校验 |
| 残留进程占显存 | HIP OOM | 启动前 `ps aux`，`rocm-smi`/`nvidia-smi` 确认 VRAM 0 |
| 复制粘贴损坏 | heredoc/base64 截断、占位符被执行 | 长内容用文件上传；执行前 `head` 校验 |
| verify_frozen 路径错误 | 找不到 `canonical_manifest.json` | 脚本同时查找根目录与 `manifest/` 子目录 |
| 无卡/解压启动问题 | 只上传未解压，或解压路径不对 | 先 `tar -xzf`，再 `ls` 验证目录与 data 文件 |

## 三、启动前检查清单

- [ ] 数据/vocab/mapping/脚本全部来自冻结包
- [ ] `training.log` 与 `step_metrics.jsonl` 路径存在
- [ ] 无残留 python 进程
- [ ] 2 卡 smoke 100 步通过
- [ ] resume 测试通过
- [ ] checkpoint 目录可写，磁盘空间足够
- [ ] 已执行 `tar -xzf` 且 `data/train.cnbe` 存在
- [ ] `verify_frozen.py` 能找到 manifest（根目录或 `manifest/`）

## 四、补丁包

`A800_PATCH_2026-08-14.zip` 包含：

```text
code/scripts/train_distributed.py
code/scripts/eval.py
tools/extract_step_curves.py
docs/A800_CORRECTIONS_AND_LESSONS_2026-08-14.md
docs/A800_PRETRAIN_PREP_2026-08-14.md
docs/A800_5_4B_TRAINING_PLAN_REVIEW_2026-08-14.md
```
