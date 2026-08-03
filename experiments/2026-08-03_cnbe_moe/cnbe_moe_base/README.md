# CNBE-MoE Phase 0/1/2 原型

目标：用真实 `cnbe32.db` 与已验证专家映射表，跑通小型 CNBE-MoE，并和
Dense 基座在同一 CNBE 码流数据上对比 next-code 预测质量与真实训练吞吐。

```bash
python run.py
```

最终结果：`outputs/cnbe_moe_final_result.json`

关键结论（6M 字 / 1200 步）：MoE-64 的 next-code 准确率 19.18% vs Dense
15.92%，字段准确率全面更高；专家越多质量越好，但 64 专家负载 Gini 0.30，
需在训练损失中加入路由均衡项。grouped GEMM 后 64 专家吞吐仍仅 5 steps/s，
需生产级融合内核。

Triton grouped GEMM kernel 已实现并通过前向/反向一致性测试（误差 1e-7），
在 Ubuntu 26.04 上完成 MoE-64 训练，指标与向量化一致；当前小模型规模下
Triton 未超过向量化 bmm（4.02 vs 9.02 steps/s），需扩大规模后比较。
