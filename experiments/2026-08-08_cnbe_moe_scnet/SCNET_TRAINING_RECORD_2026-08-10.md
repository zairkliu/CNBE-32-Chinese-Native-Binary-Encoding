# SCNet L20 训练记录（2026-08-10）

## 一、任务与环境

| 项目 | 值 |
|---|---|
| 任务名 | CNBE32-MoE64_128 |
| 平台 | SCNet 超算互联网 |
| 区域 | 华东一区【昆山】 |
| 资源组 | 012 组 NVIDIA L20 48GB PCIE |
| 加速卡 | L20 × 1（44GB 可用） |
| 镜像 | PyTorch 2.7.0 + cu118（CUDA 12.4 环境） |
| Python | 3.12.7 |
| 数据路径 | /scnet_upload_package/data（7 个 .cnbe） |

## 二、模型配置（scnet_moe_config_a_l20.yaml）

| 配置项 | 值 |
|---|---:|
| d_model | 512 |
| d_ff | 2048 |
| 层数 | 8 |
| 注意力头 | 8 |
| 专家数 | 128（跨层共享） |
| Top-k | 2 |
| 词汇表 | 10,991 个唯一 CNBE 码 |
| 模型参数量 | 约 0.29B（共享专家后） |
| seq_len | 128 |
| batch_size | 8 |
| grad_accum_steps | 8 |
| 每步有效 token | 8 × 128 × 8 = 8,192 |
| 精度 | bf16 混合精度（torch.autocast） |
| epochs | 2 |
| 总步数 | 46,874 |
| 数据规模 | 24,381,237 CNBE 码 |

## 三、训练进度（接近尾声）

| 指标 | 值 |
|---|---:|
| 当前进度 | step 45,000 / 46,874（约 96%） |
| 训练速度 | 0.71 steps/s（约 1.41 s/step） |
| 吞吐 | 约 5,800 token/s |
| 近期训练 loss | 1.48 ~ 1.56 |
| 随机基线 | log(10,991) ≈ 9.30 |
| 显存使用率 | 20%-30% |
| GPU 使用率 | 80%-100%（checkpoint 时短暂回落） |

## 四、结论与待确认项

1. loss 从约 9.3 收敛到 1.5 附近，说明 CNBE 码流具备可学习结构；
2. bf16 混合精度已启用，无需再次开启；
3. 单卡 L20 + 共享专家模型，0.71 steps/s 属于当前配置的正常水平，
   主要瓶颈是单卡算力和向量化 grouped GEMM；
4. 最终合格与否以训练结束后 `train_metrics.json` 的 next-code、
   struct/radix/strokes 准确率和 expert_gini 为准。

## 五、下一轮优化

- 显存只用了 20%-30%，可在 L20 上增大 batch/seq_len 或专家数；
- 有 Triton 时启用 grouped GEMM kernel，能显著提速；
- 升级 A800 2 卡后可跑 256 共享专家 + 更大 d_model。

## 六、最终结果（2026-08-10 完成）

| 指标 | 值 |
|---|---:|
| eval_loss | 6.5821 |
| next-code 准确率 | 19.12% |
| radix 准确率 | 20.23% |
| struct 准确率 | 34.14% |
| strokes 准确率 | 24.38% |
| expert_gini | 0.2071 |
| 参数量 | 289,920,031 |

结论：CNBE 码流可学习，next-code 达到本地 MoE 水平；struct 与 Gini
未达目标上限，主要受 24M 小语料限制，下一步以扩语料与更大模型为主。

## 七、产物归档（results_2026-08-10/）

| 文件 | 大小 |
|---|---:|
| train_metrics.json | 295 B |
| cnbe_moe_results_2026-08-10.tar.gz | 6,610 B |
| mapping_128.json | 515,938 B |
| mapping_8.json | 104,664 B |
| cnbe_moe_checkpoint_2026-08-10.tar | 3,480,360,960 B |

checkpoint 内含 `output/checkpoints/last.pt`，可用于后续续训或下游实验。
