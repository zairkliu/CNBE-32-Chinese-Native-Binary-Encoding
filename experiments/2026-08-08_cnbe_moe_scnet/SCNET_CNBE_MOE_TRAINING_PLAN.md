# SCNet CNBE-MoE 训练计划

日期：2026-08-08
状态：镜像已构建并验证；训练目标待确认（架构验证 vs 生产模型）

> 镜像 `cnbe-moe-scnet:0.1` 已在 Ubuntu-26.04 完成构建，并用真实 `.cnbe` 跑通 smoke 训练。
> 上传与创建方式见 `IMAGE_BUILD_REPORT.md`。

## 一之二、本实验边界（重要）

当前语料只有 **24,381,237** 个 CNBE 码。按大模型预训练标准，这是极小规模：

- 24M tokens 训练 0.3B-2.2B 模型，只能验证架构与路由，**不能产出可用的语言模型**；
- 若目标是“可用的中文模型”，语料至少需要 10B-100B+ tokens，需要先完成更大规模中文语料的 CNBE 编码；
- 本次 SCNet 试用的正确价值是：验证 CNBE 硬路由、负载均衡、DDP/AMP/checkpoint 栈、Triton kernel 与 MFU，为后续大语料训练铺路。

## 一、目标

在 SCNet 国家计算中心完成 CNBE-MoE 的首次规模化训练，验证：

1. **128/256 专家硬路由**在更大 `d_model` 上仍能维持负载均衡；
2. CNBE 三字段硬路由相比 Dense 基线在 next-code 与字段准确率上继续有增益；
3. 自写 Triton grouped GEMM kernel 在真实 GPU 集群上的吞吐是否超过向量化 `bmm`；
4. 产出可复现的训练包：数据、映射、配置、checkpoint、指标。

## 二、现状基线

已有本地结果（`experiments/2026-08-03_cnbe_moe/`）：

| 模型 | Next-code | 字段头准确率 | 训练期 Gini | 参数量 |
|---|---:|---:|---:|---:|
| Dense | 15.92% | radix 15.91% / struct 42.10% | - | 12.0M |
| MoE-8 | 17.65% | radix 17.75% / struct 43.16% | 0.030 | 28.6M |
| MoE-16 | 17.99% | radix 17.92% / struct 43.40% | 0.162 | 47.5M |
| MoE-64 | 19.18% | radix 19.62% / struct 44.26% | 0.297 | 160.9M |
| MoE-64-3f | 18.98% | 接近 MoE-64 | **0.153** | ~160M |

结论：专家越多 next-code 越高，但负载 Gini 上升；三字段映射是当前最优均衡方案。

## 三、数据

训练码流为 7 个语料 `.cnbe`，共 **24,381,237** 个 32 位 CNBE 码：

| 语料 | 字符数 |
|---|---:|
| zzjh_294（資治通鑑） | 4,558,886 |
| luxun_18（鲁迅全集） | 3,864,304 |
| agatha（阿加莎全集） | 7,804,198 |
| csbook（Linux 程序设计） | 280,766 |
| jinyong（金庸全集） | 7,558,400 |
| caixin（财新合订） | 286,399 |
| sushi（蘇文忠公詩集） | 28,284 |

数据准备：
- 全量 24M 码先切 95/5 train/eval；
- 预先构建唯一码表（预计 1-2 万码）并保存 `vocab.json`；
- 按三字段频率预构建 128/256 专家均衡映射，保存 `mapping_128.json` / `mapping_256.json`；
- 不把私有语料上传 GitHub，训练包只进 SCNet 工作目录。

## 四、推荐训练配置

### 配置 A（首推，预算敏感）

| 项 | 值 |
|---|---|
| 模型 | d_model=512，d_ff=2048，layers=8，heads=8 |
| MoE | 128 专家，Top-2，三字段硬路由 |
| 序列长度 | 256 |
| 每卡 batch | 32 |
| 梯度累积 | 4 |
| 精度 | bf16 mixed precision |
| 训练步数 | 24M tokens / (8×32×256) ≈ 366 步/epoch，跑 2 epoch |
| 参数量 | 约 0.3B（专家权重 0.27B + 共享/注意力/embedding） |
| 路由目标 | 硬查表 + 路由均衡辅助 loss |
| 评估 | next-code、radix/struct/strokes/idx 准确率、Gini、MFU |

### 配置 B（扩容档）

| 项 | 值 |
|---|---|
| 模型 | d_model=1024，d_ff=4096，layers=12，heads=16 |
| MoE | 256 专家，Top-2，三字段硬路由 |
| 序列长度 | 256 |
| 每卡 batch | 16 |
| 梯度累积 | 4 |
| 训练步数 | 24M tokens / (8×16×256) ≈ 733 步/epoch，跑 2 epoch |
| 参数量 | 约 2.2B（专家权重 2.1B + 共享/注意力/embedding） |

### 配置 C（本次试用真正冲规模，推荐替代 B）

| 项 | 值 |
|---|---|
| 模型 | d_model=1024，d_ff=4096，layers=16，heads=16 |
| MoE | 256 专家，Top-2，三字段硬路由 |
| 序列长度 | 256 |
| 每卡 batch | 16 |
| 梯度累积 | 4 |
| 训练步数 | 24M tokens / (8×16×256) ≈ 733 步/epoch，跑 10 epoch ≈ 7,330 步 |
| 参数量 | 约 2.3B |
| 预期用时 | 8×A100 上数小时（数据量仍是瓶颈，不是算力） |

> 配置 C 的意义：在有限数据下把模型推到“架构上可验证、规模上不再是玩具”的档位，
> 同时用 10 epoch 逼近小语料的信息上限。它仍不是生产模型，但足以支撑论文级结论。

## 五、算力与存储预算

建议优先选择 **A100/H800 80GB**，至少 4 卡，首推 1 节点 8 卡。

| 项目 | 建议值 |
|---|---:|
| GPU | A100/H800 80GB × 8 |
| 节点 | 1 |
| 显存 | 80GB/卡 |
| 系统盘 | 50GB |
| 数据盘 | 200GB（代码 + 7 个 `.cnbe` + checkpoint） |
| 时长 | 24-72 小时（实际训练预计数小时，预留调试和排队） |
| 软件栈 | PyTorch 2.3+，CUDA 12.x，Triton，Python 3.10+ |

如果控制台只提供 4 卡档位：
- 配置 A 仍然可行，8→4 卡后全局 batch 减半，步数翻倍；
- 配置 B 需要 8 卡，4 卡跑 256 专家会更慢且显存吃紧。

## 六、购买时在控制台怎么选

进入「模型训练 → 新建训练」后建议：

1. 任务名：`cnbe-moe-128-a100`（或 `-256`）；
2. 计算资源：A100/H800 80GB，数量 8（至少 4）；
3. 运行框架：PyTorch 镜像（CUDA 12.x）；
4. 存储：上传训练包到工作目录，至少 200GB 配额；
5. 运行时长：24h 起步，预留到 72h；
6. 启动命令：先跑 1 分钟 smoke test，通过后再跑正式训练。

如果控制台表单里有我们不认识的字段，把页面选项发我，我再给精确填法。

## 七、代码改造清单（购买后立即执行）

现有 `cnbe_moe_base` 是单进程单卡原型，上集群前需要补齐：

- [ ] `torchrun` DDP 多卡训练入口；
- [ ] bf16 mixed precision + GradScaler 不需要（bf16 直接）；
- [ ] 梯度累积与全局有效 batch；
- [ ] checkpoint / resume，每 N 步保存 optimizer + model + mapping；
- [ ] 评估在验证集上逐 epoch 执行；
- [ ] tensorboard / wandb 指标日志；
- [ ] 预计算全量 vocab 与 128/256 专家映射，避免每进程重复统计；
- [ ] 数据集改用内存映射或分片，24M 码一次性进内存约 190MB，可接受；
- [ ] Triton grouped GEMM kernel 做 GPU 兼容性检测，不支持时回退向量化 `bmm`；
- [ ] 运行脚本输出 `MANIFEST.json`（数据、配置、git hash、依赖版本）。

## 八、执行里程碑

| 阶段 | 内容 | 预计 |
|---|---|---|
| M0 | 本地打包：代码 + 7 语料 + vocab + mapping + 配置 | 购买后第 1 天 |
| M1 | 1 GPU smoke：128 专家跑 50 步，验证 loss/吞吐 | 第 1 天 |
| M2 | SCNet 4/8 卡小跑：1M tokens，检查 Gini 与 MFU | 第 1-2 天 |
| M3 | 正式训练：24M tokens × 2 epoch，配置 A 或 B | 第 2-3 天 |
| M4 | Dense 同规模对照 + 消融：128 vs 256 专家 | 第 3-4 天 |
| M5 | 结果归档：checkpoint、指标、报告 | 第 4 天 |

## 九、成功标准

| 指标 | 目标 |
|---|---|
| Next-code 准确率 | 配置 A ≥ MoE-64 的 19.18%；配置 B 更高 |
| 三字段硬路由 Gini | ≤ 0.20（训练期） |
| 路由加速 | 128 专家下 CNBE 路由 FLOPs 为传统 Top-K 的 E/m 倍 |
| Triton kernel | 与向量化 `bmm` 一致性误差 ≤ 1e-6，吞吐不劣化 |
| 可复现 | 同一 bundle 在 SCNet 重跑，指标差异 ≤ 0.5pp |

## 十、风险与回退

| 风险 | 回退方案 |
|---|---|
| SCNet 镜像无 Triton 或 H800 不支持自写 kernel | 自动回退向量化 grouped GEMM，仍可完成训练 |
| 256 专家显存不足 | 用配置 A（128 专家），或每卡 batch 减半 |
| 24M tokens 数据量小导致过拟合 | 降低 epoch 到 1-2，评估集固定；用 dropout 与正则 |
| 动态 shape 导致 `torch.compile` graph break | 不强制 compile，Triton kernel 单独基准 |
| SCNet 排队超时 | 预留 72h；优先短时小任务占位测试 |
| 用户期望“可用的语言模型” | 24M tokens 无法满足；需先扩展语料并重新规划 100B+ tokens 预训练 |

## 十一、产物

- 训练包：`scnet_cnbe_moe_bundle/`（代码、数据清单、配置、启动脚本）
- Checkpoint：`checkpoints/cnbe_moe_128.pt` 或 `cnbe_moe_256.pt`
- 指标：`outputs/SCNET_TRAIN_METRICS.json`
- 报告：`experiments/2026-08-08_cnbe_moe_scnet/REPORT_SCNET_CNBE_MOE.md`
- 私有数据与训练代码不上 GitHub；公开仓库只保留实验报告与结论。
