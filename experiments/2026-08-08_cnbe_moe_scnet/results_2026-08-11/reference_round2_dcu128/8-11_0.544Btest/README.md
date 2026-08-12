# CNBE-MoE 训练结果 - 2026-08-11 5.44B Token

生成时间：2026-08-11 22:55:52

## 一、训练概况

| 项目 | 值 |
|---|---|
| 本轮实验 | round2-dcu128 |
| 语料 | 5.44 亿 Token，1244 个 .cnbe 文件 |
| 唯一 CNBE 码 | 17,474 |
| 模型 | d_model=1024，d_ff=2048，12 层，16 头 |
| MoE | 128 专家，Top-2，三字段硬路由 |
| 参数量 | 626,435,442 |
| 总步数 | 125,976 |
| 最终检查点 | final.pt（step 125976） |
| 最终 eval_loss | 4.591474966106527 |

## 二、训练环境

| 项目 | 值 |
|---|---|
| 平台 | SCNet 国家超算互联网平台 |
| 资源组 | 113 组 hx1hgbwnormal |
| 加速卡 | 异构加速卡 BW x 2（实际单卡 63GB，面板 256GB） |
| CPU / 内存 | 30 核 / 118GB |
| 镜像 | jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel |
| Python | 3.11.9 |
| PyTorch | 2.9.0 |
| DTK | 26.04 |

## 三、训练配置

| 配置项 | 值 |
|---|---|
| seq_len | 256 |
| batch_size | 8 |
| grad_accum_steps | 1 |
| epochs | 1 |
| optimizer | AdamW |
| lr | 3e-4 |
| weight_decay | 0.01 |
| grad_clip | 1.0 |
| precision | bf16 |
| top_k | 2 |
| learned_router | false |
| balance_weight | 0.01 |
| aux_loss_weight | 0.1 |

## 四、时间线与用时

| 时间 | 事件 |
|---|---|
| 2026-08-11 01:11 | 正式训练启动，grad_accum=1 |
| 2026-08-11 19:34 | 到达 125,975 步，末尾 NCCL barrier 超时 |
| 2026-08-11 20:03 | 补丁后从 last.pt（step 120,000）续训 |
| 2026-08-11 21:00 | 续训完成 step 125,976，保存 final.pt |
| 2026-08-11 22:25 | eval.py 全量评估完成 |

有效训练约 125,976 步，按约 1.92 steps/s 折算约 18.2 小时；
加上数据预热与全量评估，实际墙钟约 21.3 小时。

## 五、最终评估指标

| 指标 | 值 |
|---|---:|
| eval_loss | 4.591474966106527 |
| next-code | 23.56% |
| radix（解码字段） | 24.09% |
| struct（解码字段） | 44.07% |
| strokes（解码字段） | 26.04% |
| radix head | 24.18% |
| struct head | 47.10% |
| strokes head | 27.27% |
| expert_gini | 0.297105073928833 |
| 参数量 | 626,435,442 |
| 评估 Token | 26,999,808 |

## 六、与 L20 128 第一轮对比

| 指标 | 本轮 DCU 128 | L20 128 |
|---|---:|---:|
| eval_loss | 4.591474966106527 | 6.5821259756709525 |
| next-code | 23.56% | 19.12% |
| radix | 24.09% | 20.23% |
| struct | 44.07% | 34.14% |
| strokes | 26.04% | 24.38% |
| expert_gini | 0.297105073928833 | 0.2070654034614563 |
| 参数量 | 626,435,442 | 289,920,031 |

说明：两轮模型规模与语料不同，直接对比仅作参考，正式结论需同参数 Dense 对照。

## 七、情况分析

1. **struct 显著提升**：解码字段 44.07%、head 47.10%，已超过 40% 目标，
   说明 5.44 亿语料和更大模型对结构字段泛化帮助明显。
2. **next-code 提升**：23.56%，高于 L20 的 19.12%，但距离可用语义模型仍有距离。
3. **Gini 升高**：0.2971 高于上一轮 0.2071，说明路由集中度上升，
   少数专家承担了更多 token，需要路由均衡。
4. **训练尾部风险**：末尾 NCCL barrier 超时，但通过续训 + final.pt 强制保存
   解决了模型丢失问题；后续训练必须先保存最终检查点再进入任何 collectives。
5. **检查点策略不足**：当前脚本每 1000 步覆盖 last.pt，无法恢复任意中间状态；
   下一轮必须按 step_XXXX.pt 分别保存。

## 八、MoE 分析

- 路由方式：CNBE 三字段 (radix, struct, strokes) 频率均衡硬路由，Top-2；
- 第二专家为 (primary + 1) % 128，属于简单互补路由；
- balance_loss 采用负载平方偏差，weight=0.01；
- Gini 0.297 说明负载方差偏大，建议下一轮 balance_weight 提到 0.02-0.05，
  或改用 learned router 学习结构到专家的软路由；
- 128 专家在本轮验证了可训练性和结构学习能力，但 256 专家应在
  路由均衡达标后再评估。

## 九、下一轮训练要求

1. 以 core/final.pt 作为初始权重继续训练；
2. 保持同一 eval split（27,000,000 token）以严格对比；
3. 先跑同参数 Dense 对照，验证 MoE 相对收益；
4. balance_weight 提升至 0.02-0.05，目标 expert_gini <= 0.20；
5. 增加学习率 warmup/decay；
6. 按 step_XXXX.pt 保存全部检查点，并强制保存 final.pt；
7. 考虑对 code 0（约 21.6%）单独处理，避免污染结构任务；
8. 路由均衡达标后再评估 256 专家；
9. 每次实验保留 config、vocab、mapping、data manifest 与日志。

## 十、三档版本说明

| 版本 | 用途 | 包含内容 |
|---|---|---|
| core/ | 续训/微调起点 | final.pt + config + vocab + mapping |
| normal/ | 训练记录查看 | core + metrics + log |
| full/ | 审计归档 | normal + code + 全部现有检查点 + data manifest |

## 十一、当前实际检查点

- final.pt
- last.pt

注意：当前训练脚本每 1000 步覆盖 last.pt，因此不存在 step_*.pt 序列；
完整中间状态无法恢复，下一步训练请保留本导出目录并增加分步 checkpoint 保存。
