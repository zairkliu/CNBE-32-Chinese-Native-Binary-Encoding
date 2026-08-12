# V1 老版本 DCU2 受控对比结果（最终）

日期：2026-08-12
数据：v1 7 个 .cnbe，train 24,000,000 / eval 381,237

| 指标 | MoE-128 | Dense same-config | Dense matched-params | Unicode Dense |
|---|---:|---:|---:|---:|
| eval_loss | 4.5430 | 7.3033 | 7.2802 | 7.7933 |
| next-code / next-token | 22.96% | 2.61% | 2.61% | 0.0010% |
| radix | 24.52% | 3.10% | 3.10% | N/A |
| struct | 43.05% | 38.41% | 38.41% | N/A |
| strokes | 30.13% | 13.87% | 13.87% | N/A |
| radix head | 22.15% | 0.03% | 0.03% | N/A |
| struct head | 45.81% | 0.64% | 0.64% | N/A |
| strokes head | 27.96% | 0.02% | 0.02% | N/A |
| expert_gini | 0.1472 | null | null | null |
| params | 289,920,031 | 37,954,591 | 289,858,591 | 38,130,891 |
| tokens_evaluated | 381,184 | 381,184 | 381,184 | 381,184 |

## 判定

- H1：MoE-128（22.96%）显著优于等参数 Dense（2.61%），且
  struct 43.05% vs 38.41%，通过；
- H2：CNBE Dense（2.61%）显著优于 Unicode Dense（0.0010%），通过；
- 结论：MoE 与 CNBE 编码在 v1 受控条件下均通过门禁。
