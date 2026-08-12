# V1 老版本 DCU2 受控对比结果（修正数据口径）

日期：2026-08-12
数据：v1 7 个 .cnbe，train 24,000,000 / eval 381,237

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

## 判定

- H1 MoE-128 vs Dense same-config：MoE 全面大幅领先，但 Dense 参数量
  仅 37.95M，尚未完成等参数 Dense 对照；
- H2 CNBE vs Unicode：CNBE Dense 2.61% vs Unicode Dense 0.001%，
  CNBE 编码优势显著；
- 结论：MoE 与 CNBE 编码均通过当前门禁，建议继续；仍需
  `RUN_MATCHED=1` 补等参数 Dense 才能完全归因 MoE。
