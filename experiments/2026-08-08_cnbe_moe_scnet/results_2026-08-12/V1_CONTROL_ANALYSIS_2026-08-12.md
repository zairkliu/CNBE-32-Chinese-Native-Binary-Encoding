# V1 老版本 DCU2 对照结果分析

日期：2026-08-12

## 一、有效结果

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

## 二、结论

1. **MoE-128 显著优于 Dense same-config**：
   next-code 22.96% vs 2.61%，struct 43.05% vs 38.41%；
2. **CNBE 显著优于 Unicode**：
   CNBE Dense 2.61% vs Unicode Dense 0.001%；
3. **MoE 字段头学习能力突出**：
   struct head 45.81%，而 Dense 仅 0.64%；
4. **路由均衡良好**：Gini 0.1472；
5. **等参数 Dense 已完成**：289,858,591 参数，与 MoE-128
   （289,920,031）基本对齐；
6. 等参数 Dense next-code 仍为 2.61%、struct 38.41%，
   远低于 MoE-128 的 22.96% / 43.05%；
7. **H1 通过**：MoE 架构优势在等参数条件下成立。

## 三、下一步

- 四组对照已完成，`comparison_table.md` 已更新；
- 下一轮可进入 544M 语料上的三组/四组扩展验证；
- 考虑 256 专家与路由均衡优化。
