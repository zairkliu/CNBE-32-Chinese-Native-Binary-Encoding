# CNBE 形式化公式统一验证报告

## 总结

- 公式数学或数值验证：`13 / 13` 通过。
- 科学性能结论：`0` 项已验证。
- 总状态：`PASS_ALL_SUPPLIED_FORMULAS_MATHEMATICALLY_VERIFIED`。

数学验证表示公式在声明的有限输入、定义域与参考实现中满足可逆性、恒等性、对称性、有界性、归一化或确定性等性质。它不表示字段正确、权重具有语言学意义、模型有任务增益或性能优于基线。

## 附件原始 13 个公式

| 编号 | 公式 | 验证内容 | 状态 |
|---|---|---|---|
| F01 | Extract(c, M_k, S_k) | P0 bitfield and golden-vector conformance | `PASS` |
| F02 | Phi(c) | E1 32-bit round trip | `PASS_E1_BIT_VECTOR_CONFORMANCE` |
| F03 | D_morph formal weighted Hamming | E2 identity, symmetry, bounds, field isolation | `PASS_E2_WEIGHTED_HAMMING_ALGEBRA` |
| F04 | Poincare geodesic distance | E3 domain, identity, symmetry, triangle samples | `PASS` |
| F05 | Mobius addition | E3 ball closure and zero identity | `PASS` |
| F06 | exp_0 | E3 zero identity and ball-domain output | `PASS` |
| F07 | z_c hyperbolic composition | E3 deterministic composition stays in ball | `PASS` |
| F08 | hyperbolic alignment loss | E3 finite non-negative all-pairs loss | `PASS` |
| F09 | e_pred(c) | E4 radix modulo expert count | `PASS` |
| F10 | P(e \| x, c) | E4 normalization, non-negativity, alpha endpoints | `PASS` |
| F11 | Pi^p | E5 cyclic permutation composition | `PASS` |
| F12 | H(c) | E5 deterministic +/-1 encoding | `PASS` |
| F13 | Sim_HDC | E5 self-similarity, symmetry, bounds | `PASS` |

## 本项目额外偏旁辅助公式

- `D_not_radical` 与 `A_radical`：`PASS_RADICAL_MASKED_MATH_VERIFICATION`。
- 用途仅为已有来源锚点候选的人工复核排序，不能确认偏旁或修复编码。

## 仍被阻断的科学验证

- `linguistic_weight_validity`。
- `morphology_retrieval_quality`。
- `hyperbolic_advantage_over_euclidean_baseline`。
- `moe_routing_quality_or_latency_advantage`。
- `hdc_quality_or_resource_advantage`。

下一科学阶段状态：`BLOCKED_INDEPENDENT_SOURCE_ANCHORED_RELATION_LABELS_REQUIRED`。在独立、来源锚定、与被测字段无泄漏的关系标签集建立前，不计算 P1 检索指标，不比较欧氏/双曲模型，不作 MoE 或 HDC 性能结论。
