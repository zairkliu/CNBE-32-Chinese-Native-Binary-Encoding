# A800 双卡 5.4B 预训练前置准备与防错设计

日期：2026-08-14
状态：准备阶段，尚未提交 GitHub

## 一、前两次训练错误复盘

### 1.1 第一轮：SCNet L20 24M（2026-08-10）

| 错误 | 表现 | 根因 | 修复 |
|---|---|---|---|
| grad_accum 步数计算错误 | 46,874 步实际循环约 8 遍数据 | `steps_per_epoch = len(sampler)//batch_size` 未按 grad_accum 折算 | 后续统一 `grad_accum_steps=1`，按真 epoch 计算 |
| 训练日志未落盘 | 论文需要的 step 曲线无法找回 | 只输出到终端，没有 `tee` | 本轮强制 `2>&1 | tee training.log` |
| checkpoint 覆盖 | 只有 `last.pt`，无中间 step | 每 N 步覆盖同一文件 | 本轮改为 `step_%06d.pt` 独立保存 |

### 1.2 第二轮：SCNet DCU 544M（2026-08-11/12）

| 错误 | 表现 | 根因 | 修复 |
|---|---|---|---|
| 训练尾部 NCCL barrier 超时 | 125,975/125,976 步崩溃，无 `train_metrics.json` | 训练结束后先 `dist.barrier()` 再保存最终 checkpoint | 先保存 `final.pt`，再进入任何 collective；单进程评估 |
| 修补耗时约 4 小时 | 只能从 step 120,000 续训 | checkpoint 每 10,000 步覆盖，丢失中间状态 | 独立 step checkpoint + 续训冒烟测试 |
| HIP OOM | 首轮 forward 的 `baddbmm` OOM | 残留进程占用显存；全专家 padding 显存效率低 | 杀残留进程、设置 allocator、后续只计算非空专家 |
| CodeDataset 过慢 | 5 亿 token 数据预热极慢 | Python 列表推导逐 token 映射 | `np.searchsorted` 向量化 |
| 论文 step 数据丢失 | 需要收敛曲线时无日志 | 没有独立保存 per-step 指标 | 本轮单独保存 `step_metrics.jsonl` 与 CSV/JSON |

### 1.3 跨流程错误补充（L20 → DCU 双卡全过程）

| 错误类型 | 具体表现 | 根因 | 防错要求 |
|---|---|---|---|
| 上传/解压路径混乱 | tar/zip 找不到；解压后没有顶层目录导致 `cd` 失败 | 文件没上传到目标位置；zip 内路径不规范 | 上传后先 `find / -name`；zip 必须有顶层目录；解压后用 `ls` 验证 |
| 脚本版本漂移 | `eval.py` 旧版/新版混用；`train_distributed.py` 缺 `--seed`；mapping 用了 6351 旧版 | 多份代码副本不同步 | 统一从冻结包运行；记录代码 SHA256；替换脚本后 `head -5` 验证 |
| 数据路径不一致 | v1 数据实际在 MERGED/data，脚本默认 DCU/data | 路径写死且未自动探测 | 使用 `CNBE_V1_DATA` 环境变量或自动 `find`，禁止写死 |
| 大数组全量排序过慢 | `np.unique` 对 5.43 亿码耗时被误判卡死 | int64 内存大、无进度提示 | 用 uint32 读取；首次构建 vocab 后缓存；打印“需要几分钟” |
| 残留进程占显存 | HIP OOM，首轮 forward 失败 | 上一轮进程未清理 | 启动前 `ps aux | grep python`；`pkill` 后 `rocm-smi` 确认 VRAM 0 |
| 复制粘贴损坏 | heredoc/base64 被截断；`/找到的路径/` 占位符被执行 | 终端复制不稳定 | 长内容用文件上传或 base64+gzip；执行前 `head` 校验 |
| 指标文件版本错误 | `dense_eval_metrics (1)` 是旧 MERGED 数据结果 | 下载/收集时混入旧产物 | 按 checkpoint 路径和 `tokens_evaluated=381184` 校验后再入档 |
| 初始 steps/s 异常 | resume 后显示 13995 steps/s | `t0` 重置且 elapsed 极小 | 属显示问题，不修改；等稳定后读数 |

## 二、5.4B A800 双卡训练目标

| 项 | 值 |
|---|---:|
| 训练语料 | v2 train 全量 |
| 内容 token | 5,069,636,759 |
| 物理词数 | 5,069,667,334 |
| 模型 | d_model=1024、12 层、128 专家（或按资源调整） |
| 训练卡 | A800 × 2 |
| 目标 | 1 epoch，完整记录与可恢复 |

## 三、崩溃必须不再发生的要求

### 3.1 Checkpoint 设计（最高优先级）

1. 每 1,000 步保存 `step_%06d.pt`，不覆盖；
2. 每 10,000 步保存 `checkpoint_%06d.pt` 到独立目录；
3. 训练结束时强制保存 `final.pt`，必须先于任何 `dist.barrier()`；
4. 保存内容包括：model、optimizer、step、vocab_size、config、mapping；
5. `--resume` 必须从最近的 `step_*.pt` 恢复，且恢复后先跑 10 步冒烟验证 loss 正常。

### 3.2 尾部收尾设计

1. 去掉训练末尾 DDP barrier；
2. 最终评估由单进程完成，不参与 NCCL collective；
3. 评估完成后再 `destroy_process_group()` 或直接退出；
4. 即使评估失败，`final.pt` 与 `train_metrics.json` 也必须已经落盘。

### 3.3 数据加载与内存

1. 使用 `np.searchsorted` 向量化 `CodeDataset`；
2. 训练前先构建并缓存 `vocab.json`、`mapping_128.json`、`ids.npy`；
3. 启动前 `ps aux | grep python` 确认无残留进程；
4. 设置 `PYTORCH_ALLOC_CONF` 或 `PYTORCH_CUDA_ALLOC_CONF`；
5. 记录峰值显存，超过 90% 时停止并调整 batch。

### 3.4 日志与论文资料独立保存（本轮强制）

所有输出同时写入独立目录，不允许只留在终端：

```text
output/run_2026-08-14/
├── training.log                 # torchrun 2>&1 全量输出
├── step_metrics.jsonl           # 每一步：step/loss/throughput/lr/gini
├── step_curve.csv
├── step_curve.json
├── final.pt
├── step_000000.pt ... step_*.pt
├── train_metrics.json
├── eval_metrics.json
├── MANIFEST.json                # 环境、数据、配置、脚本、checkpoint 哈希
├── ENVIRONMENT.md
└── REPRODUCE.md
```

启动命令统一：

```bash
mkdir -p /output/run_2026-08-14
torchrun ... 2>&1 | tee /output/run_2026-08-14/training.log
```

### 3.5 路径与版本纪律

1. 数据、代码、配置、checkpoint 一律从冻结包读取，禁止在训练目录临时拼路径；
2. 上传/解压后先验证：`find / -name "expected_file"`、`head -5 script.py`、
   `sha256sum config.yaml`；
3. 所有脚本统一从仓库/冻结包同步，不允许多份手改副本；
4. mapping、vocab、metrics 入档前校验 `entries` 与 `tokens_evaluated`。

## 四、5.4B 规模估算（供资源决策）

| 配置 | 每步 token | 总步数 | 估算时间 |
|---|---:|---:|---:|
| batch=8/GPU，seq=256，2 卡 | 4,096 | 1,237,499 | 约 7-14 天 |
| batch=16/GPU，seq=256，2 卡 | 8,192 | 618,749 | 约 3.5-7 天 |
| batch=32/GPU，seq=256，2 卡 | 16,384 | 309,375 | 约 2-4 天 |

建议先做 100 步 smoke 测速，再用实测 steps/s 修正。若 2×A800 无法在可接受时限内完成，考虑 4/8 卡或先跑 544M 子集验证配置。

## 五、启动前检查清单

- [ ] 数据冻结：v2 train/eval/val 三段 `.cnbe` 存在且 SHA256 一致
- [ ] vocab/mapping 已冻结并校验
- [ ] 代码快照与 MANIFEST 记录一致
- [ ] smoke：2 卡 100 步跑通，loss 下降，无 OOM
- [ ] checkpoint：每 100 步保存，能 resume
- [ ] 日志：`training.log` 与 `step_metrics.jsonl` 实时写入
- [ ] 显存：峰值 < 90%
- [ ] 尾部：保存 final.pt 后再评估
- [ ] 论文资料：step_curve、metrics、config、hashes 全部落盘
- [ ] 路径纪律：数据/代码/配置来自冻结包，不临时写死
- [ ] 版本纪律：脚本 SHA 一致，mapping/vocab 校验通过
- [ ] 启动前 `ps aux` 无残留进程，`rocm-smi`/`nvidia-smi` VRAM 正常

## 六、结论

前两轮的核心教训可归纳为三句话：

1. 最终 checkpoint 必须先于任何 collective 保存；
2. 中间 checkpoint 必须独立保存，不能只靠 `last.pt`；
3. 训练日志与 per-step 指标必须直接落盘，不能只靠终端。

本轮 A800 训练把这三条固化为运行脚本和目录规范，不再依赖人工补救。
