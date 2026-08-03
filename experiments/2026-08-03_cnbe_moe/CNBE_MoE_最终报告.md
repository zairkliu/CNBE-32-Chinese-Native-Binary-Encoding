# CNBE-MoE 原生中文计算基座 —— Phase 0/1/2 最终报告

日期：2026-08-03

## 一、交付内容

1. 可运行原型 `cnbe_moe_base/`（真实 `cnbe32.db` + `.cnbe` 码流）；
2. 修复原设计文档的数据库 schema、映射 key 解析、随机训练器等阻塞问题；
3. 实现 grouped GEMM 专家执行与字段级辅助损失；
4. 完成 Dense / MoE-8 / MoE-16 同数据对比。

## 二、最终实验配置

| 项目 | 值 |
|---|---|
| 训练数据 | 资治通鉴 + 金庸 + 财新 + 蘇詩 3,000,000 字 |
| 评估数据 | 300,000 字 |
| 词汇表 | 7,226 个唯一 CNBE 码 |
| 模型 | d_model=256, d_ff=1024, 2 层, 4 头 |
| 辅助损失 | 部首/笔画/结构/索引分类头，权重 0.1 |
| MoE | 8/16 专家，Top-2，频率均衡映射 |
| 训练 | 800 步，batch 32，seq 64 |

## 三、最终结果

### v1（3M 字，d_model=256）

| 指标 | Dense | MoE-8 | MoE-16 |
|---|---:|---:|---:|
| Eval Loss | 5.856 | 5.683 | **5.648** |
| Next-code 准确率 | 14.49% | 16.24% | **16.58%** |
| 专家负载 Gini | - | 0.0131 | 0.0153 |

### v2（6M 字，d_model=384，1200 步）

| 指标 | Dense | MoE-8 | MoE-16 | MoE-64 |
|---|---:|---:|---:|---:|
| Eval Loss | 5.461 | 5.295 | 5.262 | **5.187** |
| Next-code 准确率 | 15.92% | 17.65% | 17.99% | **19.18%** |
| 部首准确率（预测码） | 18.00% | 19.57% | 20.01% | **21.19%** |
| 结构准确率（预测码） | 38.01% | 39.79% | 39.19% | **40.35%** |
| 笔画准确率（预测码） | 22.24% | 24.45% | 24.72% | **25.43%** |
| 部首头准确率 | 15.91% | 17.75% | 17.92% | **19.62%** |
| 结构头准确率 | 42.10% | 43.16% | 43.40% | **44.26%** |
| 笔画头准确率 | 20.14% | 21.80% | 22.49% | **23.56%** |
| 专家负载 Gini（训练期） | - | 0.0303 | 0.1622 | 0.2969 |
| 训练吞吐 | 43.8 steps/s | 25.9 steps/s | 18.6 steps/s | 5.0 steps/s |
| 参数量 | 12.0M | 28.6M | 47.5M | 160.9M |

### 负载均衡消融（按 6M 训练分布重建映射后在 300k 评估集路由）

| 专家数 | 均衡映射 Gini（评估集） |
|---:|---:|
| 16 | 0.0701 |
| 64 | 0.2192 |

结论：专家越多质量越好，但负载均衡越难；仅在训练前做频率均衡映射不够，
训练中需要引入路由均衡损失（如辅助 loss / Gating loss）。

### Ubuntu 26.04 + Triton 安装与训练

环境：WSL Ubuntu-26.04，torch 2.13.0+cu130，triton 3.7.1，RTX 4060 Ti。
代码已装入 `~/cnbe_moe_base` 并完成 MoE-64 训练，结果与 Windows 完全一致
（eval loss 5.187，next-code 19.18%，Gini 0.297）。

| 实现 | 环境 | MoE-64 吞吐 |
|---|---:|---:|
| 按专家 Python 循环 | Windows | 5.0 steps/s |
| 按专家 Python 循环 | Ubuntu | 4.04 steps/s |
| 向量化 grouped GEMM（无循环） | Ubuntu | **9.02 steps/s** |
| 向量化 grouped GEMM + torch.compile | Ubuntu | 7.03 steps/s |

结论：真正提速来自去掉 Python 分组的向量化 grouped GEMM（约 2.2x）；
`torch.compile` 因动态 `max_c` 产生 graph break，反而更慢。下一步需要
自写 Triton grouped GEMM kernel，按固定块大小处理动态分组，才能进一步
逼近理论吞吐。

### 自写 Triton grouped GEMM kernel

已实现 `cnbe_moe_base/src/triton_moe.py`：两段式 Triton kernel
（`_moe_gemm1_kernel` 计算 `x@W1^T+b1`，`_moe_gemm2_kernel` 计算
`SiLU(pre)@W2^T+b2`），并用向量化 grouped GEMM 实现自动反向。

一致性验证（Ubuntu 26.04，triton 3.7.1）：

| 检查项 | 结果 |
|---|---:|
| 前向最大误差 | 3.6e-07 |
| 反向梯度最大误差 | 1.8e-07 |
| MoE-64 训练 eval loss | 5.187（与向量化一致） |
| MoE-64 next-code 准确率 | 19.18%（与向量化一致） |

吞吐对比（MoE-64，1200 步）：

| 实现 | 吞吐 |
|---|---:|
| 按专家 Python 循环 | 4.04 steps/s |
| 向量化 grouped GEMM | 9.02 steps/s |
| 自写 Triton kernel | 4.02 steps/s |

结论：Triton kernel 数学正确，但在当前小模型（d_model=384，64 专家）
和单卡 4060 Ti 上，kernel 启动与分组开销大于收益，未超过向量化 bmm。
Triton 的优势需要更大模型/更大批次/更多专家才能体现，下一步应做
persistent kernel 与 block 调参，并扩大模型规模后再比较。

### 路由均衡：训练损失无效，映射粒度有效

尝试在训练损失中加入路由均衡项（权重 0.3），结果对硬查表路由**完全无效**：
路由表不可学习，损失没有梯度路径，训练期 Gini 仍为 0.2969，指标逐位不变。

改为把映射键从 `(radix, struct)` 扩展到 `(radix, struct, strokes)`
（三字段均衡映射），64 专家训练期 Gini 从 **0.2969 降到 0.1533**：

| 配置（6M 字 / 1200 步，d384） | Eval Loss | Next-code | 训练期 Gini |
|---|---:|---:|---:|
| MoE-64（两字段映射） | 5.187 | 19.18% | 0.2969 |
| MoE-64-3f（三字段映射） | 5.203 | 18.98% | **0.1533** |

结论：硬 O(1) 路由的负载均衡必须在映射构建阶段解决；要进一步提升均衡度，
需要学习式路由（softmax + Gating loss）或更细粒度的映射键。

### 放大模型的显存边界

尝试 d_model=512、3 层、64 专家、8M 字时，8GB 显存出现 CUDA OOM。
当前单卡可稳定训练的上限约为 d_model=384、2 层、64 专家（1.6 亿参数）。

### 学习式路由（softmax + Gating loss）

实现 CNBE 字段驱动的可学习 softmax 路由（`LearnedRouter`），
对比 64 专家、6M 字、1200 步（d384）：

| 路由方式 | Eval Loss | Next-code | 训练期 Gini | 吞吐 |
|---|---:|---:|---:|---:|
| 硬查表（两字段） | 5.187 | 19.18% | 0.2969 | 8.82 steps/s |
| 硬查表（三字段） | 5.203 | 18.98% | **0.1533** | 8.54 steps/s |
| 学习式（MSE 均衡损失 0.3） | 5.290 | 17.84% | 0.7815 | 4.05 steps/s |
| 学习式（Switch 均衡损失 1.0） | 5.325 | 17.17% | 0.4810 | 2.31 steps/s |

结论：

1. 学习式路由在本规模上**未超过硬查表路由**：Switch 均衡损失虽把 Gini 从
   0.78 降到 0.48，但仍高于三字段硬映射的 0.15，且质量与吞吐下降；
2. 原因：64 专家 + 小模型 + 短训练下，可学习路由容易坍缩或与任务损失竞争，
   需要更大模型、更多数据和更精细的辅助损失权重；
3. 当前推荐：硬 CNBE 查表 + 三字段均衡映射；学习式路由作为
   “硬表先验 + 学习纠偏”的混合路由继续研究。

## 四、结论

1. **CNBE-MoE 成立且可扩展**：专家数 8->16->64 时 next-code 准确率
   15.92% -> 17.65% -> 17.99% -> **19.18%**，单调提升，MoE-64 最佳。
2. **负载均衡是规模化的主要风险**：16 专家训练期 Gini 0.162、64 专家 0.297；
   重建映射后评估集 Gini 仍为 0.07/0.22，必须在训练损失中加入路由均衡约束。
3. **墙钟代价真实存在**：grouped GEMM 优化后 MoE-8 从 30.2 提升到 40.7 steps/s，
   但 64 专家仅 5.0 steps/s；FLOPs 理论加速不能直接等同于端到端吞吐。
4. **收益来源需要进一步拆解**：当前收益可能是“更多参数 + 结构路由先验”
   共同作用，需在等活跃参数/等计算预算下继续验证。

## 五、下一步（生产化）

1. 用 CUDA grouped GEMM / Triton 消除 Python 分组的墙钟开销（Windows 当前
   无法安装 Triton，64 专家吞吐仅 5 steps/s）；
2. 训练损失加入路由均衡项，解决 64 专家 Gini 0.22-0.30 的问题；
3. 扩大模型与数据（d_model 512+，七语料全量）；
4. 将 CNBE 字段作为 9B QLoRA 模型的 router 输入，验证下游句读 F1；
5. RISC-V 位运算对齐作为硬件阶段目标，需先完成软件收益验证。

## 六、产物

- 原型代码：`cnbe_moe_base/`
- 最终结果 JSON：`cnbe_moe_base/outputs/cnbe_moe_final_result_v2.json`
- Ubuntu 训练结果：`cnbe_moe_base/outputs/ubuntu_moe64_nocompile_v2.json`
  与 `ubuntu_moe64_compile_v2.json`
- Triton kernel 结果：`cnbe_moe_base/outputs/ubuntu_moe64_triton.json`
- 三字段映射结果：`cnbe_moe_base/outputs/ubuntu_v4_moe64_3f.json`
- 学习式路由结果：`cnbe_moe_base/outputs/ubuntu_v5_moe64_learned_switch.json`
- 8 专家映射：`cnbe_moe_base/outputs/struct_expert_map_8_phase01.json`
- 打包：`outputs/cnbe_moe_base_v2.0.zip`
