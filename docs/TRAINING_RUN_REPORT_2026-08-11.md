# CNBE-MoE 合并语料训练启动报告

日期：2026-08-11
状态：云端训练已稳定运行

## 一、训练配置

| 项 | 值 |
|---|---|
| 实验名 | cnbe-moe-merged-dcu2-128 |
| 配置 | `scnet_moe_config_merged_dcu2.yaml` |
| 模型 | d_model=1024，d_ff=2048，12 层，16 头 |
| MoE | 128 共享专家，Top-2，三字段硬路由 |
| 数据 | 1244 个 .cnbe |
| 总 tokens | 544,003,069 |
| 唯一 CNBE 码 | 17,474 |
| train / eval | 516,802,915 / 27,200,154 |
| seq_len / batch / grad_accum | 256 / 8 / 1 |
| epochs | 1 |
| 总步数 | 125,976 |
| checkpoint | 每 10000 步（实际 config） |

## 二、云端环境

| 项 | 值 |
|---|---|
| 资源组 | 113 组 `hx1hgbwnormal` |
| 加速卡 | 异构加速卡 BW × 2 |
| 显存 | 256GB（工具面板） |
| CPU / 内存 | 30 核 / 118GB |
| 镜像 | `jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel` |
| Python / PyTorch / DTK | 3.11 / 2.9.0 / 26.04 |

## 三、启动与修复记录

### 1. 路径问题

包解压在 `/scnet_upload_package_MERGED_DCU`，不是 `/root/...`；
已修正为实际路径。

### 2. grad_accum 步数问题

原配置 `grad_accum_steps: 8` 时，`steps_per_epoch` 未按累积折算，
125,976 步实际会循环约 8 遍数据，预计 4.8 天。

修复：改为 `grad_accum_steps: 1`，真正 1 epoch。

### 3. CodeDataset 性能问题

5.16 亿 token 使用 Python 列表推导逐字映射，长时间无输出。

修复：改为 `np.searchsorted` 向量化映射，5 份代码副本同步。

### 4. HIP OOM

首个 forward 在 `_vectorized` 的 `baddbmm` 处 OOM。

排查：

- 发现上一轮残留进程仍在 CPU 建数据；
- 按 PID 杀掉 14219 / 14290 / 14291；
- `rocm-smi` 确认两卡 VRAM 0%；
- 设置 `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:64`；
- 原配置重启后不再 OOM。

## 四、当前运行状态（2026-08-11 01:11 起）

| 指标 | 值 |
|---|---:|
| train_windows | 2,015,624 |
| steps_per_epoch | 125,976 |
| 速度 | 约 1.85 steps/s |
| loss 前 130 步 | 4.8-7.9，整体下行 |
| 随机基线 | log(17474) ≈ 9.77 |
| ETA | 125,976 / 1.85 ≈ 18.9 小时 |

## 五、产物与路径

```text
D:\训练语料\
├── 出版物训练.zip                       # 原始 1.1GB
├── 出版物训练_extracted\               # 解压后 MD
├── 出版物训练_clean\                   # 清洗纯文本
├── 出版物训练_cnbe\                    # CNBE 码流
├── corpus_assets_merged\               # 合并 vocab/mapping
├── merged_training_package\            # 数据+assets+配置
└── scnet_upload_package_MERGED_DCU.tar.gz  # 约 1.5GB 上传包
```

云端输出：

```text
/scnet_upload_package_MERGED_DCU/output/
├── smoke_metrics.json
├── mappings/
└── checkpoints/last.pt
```

## 六、项目当前状态

### 已完成

- CNBE-32 编码规范、Python/C/Rust SDK；
- RISC-V / Verilog / Linux 内核验证闭环；
- GF 0011 部首表与 8105 标准轨；
- 五层模拟器全 PASS；
- 数学实验：伪度量、格论、信息论；
- 本地 MoE 8/16/64 与云端 128 第一轮；
- 55+1281 本出版物清洗与 CNBE 编码；
- 5.44 亿 token 合并语料；
- CNBE Knowledge Bridge MVP；
- 云端 128 专家合并语料训练已启动。

### 进行中

- 云端 128 专家 1 epoch 训练（预计 2026-08-12 上午完成）；
- 出版物未知字与覆盖率复核；
- Dense / Unicode 对照实验准备。

### 下一步

1. 等 1 epoch 指标：next-code、radix/struct/strokes、Gini；
2. 对比 Dense / Unicode 基线；
3. 评估是否进入 Structure-MLM 与对比学习；
4. 128 结果有正向证据后再考虑 256 专家。

## 七、风险与注意

- 21.6% 码流为 code 0（标点/西文/未知），后续结构任务需单独处理；
- `field_weighted_distance` 仍有反向碰撞，对比学习前必须先修度量；
- DCU 上 `_vectorized` 全专家 padding 显存效率低，规模继续放大前
  应改为只计算非空专家。

## 八、最终训练结果（2026-08-11 21:00）

续训完成：从 `last.pt`（step 120000）恢复到 step 125976，
`final.pt` 已保存（7.1GB），训练内置评估已写出
`output/train_metrics.json`。

| 指标 | 本轮 DCU 128 | L20 128 对照 |
|---|---:|---:|
| eval_loss | 4.5914 | 6.5821 |
| next-code | 23.55% | 19.12% |
| radix | 24.09% | 20.23% |
| struct | 44.08% | 34.14% |
| strokes | 26.06% | 24.38% |
| expert_gini | 0.2971 | 0.2071 |
| params | 626,435,442 | 289,920,031 |

说明：两轮模型规模与语料不同，本轮为 d_model=1024 / 12 层 /
128 专家 / 5.44 亿 token，直接对比仅作参考。struct 从 34.14%
提升到 44.08%，说明更大语料对结构字段泛化有明显帮助；
Gini 0.297 说明路由集中度升高，后续需要路由均衡正则。

`eval.py` 完整单卡评估已完成（27,000,000 eval token），
`output/eval_metrics.json` 结果：

| 指标 | 值 |
|---|---:|
| eval_loss | 4.5915 |
| next-code | 23.56% |
| radix（解码字段） | 24.09% |
| struct（解码字段） | 44.07% |
| strokes（解码字段） | 26.04% |
| radix head | 24.18% |
| struct head | 47.10% |
| strokes head | 27.27% |
| expert_gini | 0.2971 |
| tokens_evaluated | 26,999,808 |

完整 JSON 归档：
`experiments/2026-08-08_cnbe_moe_scnet/results_2026-08-11/`
