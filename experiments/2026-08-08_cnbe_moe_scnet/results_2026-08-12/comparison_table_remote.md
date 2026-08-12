# V1 老版本 DCU2 受控对比结果

| 指标 | MoE-128 | Dense same-config | Dense matched-params | Unicode Dense |
|---|---:|---:|---:|---:|
| eval_loss | 4.543038 | 7.303338 | N/A | N/A |
| next-code / next-token | 22.96% | 2.61% | N/A | N/A |
| radix | 24.52% | 3.10% | N/A | N/A |
| struct | 43.05% | 38.41% | N/A | N/A |
| strokes | 30.13% | 13.87% | N/A | N/A |
| radix head | 22.15% | 0.03% | N/A | N/A |
| struct head | 45.81% | 0.64% | N/A | N/A |
| strokes head | 27.96% | 0.02% | N/A | N/A |
| expert_gini | 0.147240 | N/A | N/A | N/A |
| params | 289,920,031 | 37,954,591 | N/A | N/A |

## 判定

- H1 MoE vs Dense matched-params：比较 next-code 与 struct；
- H2 CNBE Dense vs Unicode Dense：比较 next-code / next-token；
- 任一假设不通过，按设计文档执行停止/调整动作。
