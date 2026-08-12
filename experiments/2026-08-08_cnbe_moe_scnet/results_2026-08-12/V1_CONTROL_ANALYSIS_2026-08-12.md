# V1 老版本 DCU2 对照结果分析

日期：2026-08-12

## 一、有效结果

| 指标 | MoE-128 | Dense same-config | Unicode Dense |
|---|---:|---:|---:|
| eval_loss | 4.5430 | 7.3033 | 7.7933 |
| next-code / next-token | 22.96% | 2.61% | 0.001% |
| radix | 24.52% | 3.10% | N/A |
| struct | 43.05% | 38.41% | N/A |
| strokes | 30.13% | 13.87% | N/A |
| radix head | 22.15% | 0.03% | N/A |
| struct head | 45.81% | 0.64% | N/A |
| strokes head | 27.96% | 0.02% | N/A |
| expert_gini | 0.1472 | null | null |
| params | 289,920,031 | 37,954,591 | 38,130,891 |
| tokens_evaluated | 381,184 | 381,184 | 381,184 |

## 二、结论

1. **MoE-128 显著优于 Dense same-config**：
   next-code 22.96% vs 2.61%，struct 43.05% vs 38.41%；
2. **CNBE 显著优于 Unicode**：
   CNBE Dense 2.61% vs Unicode Dense 0.001%；
3. **MoE 字段头学习能力突出**：
   struct head 45.81%，而 Dense 仅 0.64%；
4. **路由均衡良好**：Gini 0.1472；
5. Dense same-config 仅 37.95M 参数，MoE 289.9M；
   要证明 MoE 架构本身的价值，仍需等参数 Dense 对照。

## 三、下一步

- 运行 `v1_dense_matched_dcu2.yaml`（d_ff=32768，约 290M 参数）；
- 完成后用 `make_v1_table.py` 重新生成对比表；
- 若 matched Dense next-code/struct 仍低于 MoE，则 H1 通过。
