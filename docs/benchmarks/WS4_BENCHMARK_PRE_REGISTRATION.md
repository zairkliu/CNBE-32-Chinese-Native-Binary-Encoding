# WS-4 Benchmark Pre-Registration

**Status:** Pre-registered before any benchmark execution. No retrieval, geometry, routing, or HDC task metric has been computed under this registration.
**Decision recorded:** D4 (model selection) — resolved as **dual-track evaluation**, not a single-model bet. See §2.
**Governing documents:** [Formal Mathematical Specification](../specification/CNBE_FORMAL_MATHEMATICAL_SPECIFICATION.md) · [P1 External Review Method](../specification/P1_EXTERNAL_REVIEW_METHOD.md) · [Formula Verification Report](../../experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md)

> 中文摘要：本文件在执行任何基准之前预注册四个基准族（形态检索、双曲 vs 欧氏几何、比特级 MoE 路由、HDC 表征）的冻结输入、泄漏控制、指标、基线与停止条件。D4 裁决为双轨评估：欧氏学习基线与 Poincaré 候选同时评测，均不预设优越性。在 P1 外部独立审阅的协调审计通过前，所有检索类指标保持阻断。

---

## 1. Scope

Four benchmark families, matching the four unverified claim families recorded in the [verification manifest](../../experiments/morphology_computing/reports/formal_formula_verification_manifest.json):

| ID | Family | Claim under test | Manifest gate |
|---|---|---|---|
| B1 | Morphology retrieval | `morphology_retrieval_quality` | Blocked until P1 external reconciliation passes |
| B2 | Geometry (hyperbolic vs Euclidean) | `hyperbolic_advantage_over_euclidean_baseline` | Blocked |
| B3 | Bitwise MoE routing | `moe_routing_quality_or_latency_advantage` | Blocked |
| B4 | HDC representation | `hdc_quality_or_resource_advantage` | Blocked |

A fifth family, `linguistic_weight_validity` (the D_morph weight vector), is explicitly **out of scope** for WS-4: it requires independently validated linguistic ground truth and is deferred to a later workstream with the university collaborations.

## 2. D4 resolution — dual-track evaluation

**Decision:** B2 evaluates a learned Euclidean embedding baseline and the Poincaré-ball candidate side by side, under identical data splits, budgets, and metrics. Neither is pre-committed as the project direction.

**Rationale:**

1. The verification manifest states `hyperbolic_advantage_over_euclidean_baseline` is unvalidated; choosing one geometry now would be an evidence-free commitment.
2. The current hyperbolic inputs are deterministic synthetic tangent fixtures, not learned embeddings; there is no trained artifact to protect.
3. A benchmark that cannot falsify its own candidate is not a benchmark. Dual-track registration makes the Euclidean outcome as publishable as the hyperbolic one.

**Consequence:** if the Euclidean baseline matches or beats the Poincaré candidate on the registered metrics, the project reports that result and re-scopes the hyperbolic layer as a rejected candidate. This clause is binding.

## 3. Frozen inputs

| Input | Frozen reference | Rows |
|---|---|---|
| P0 bitfield conformance records | `experiments/morphology_computing/manifests/p0_8105_bitfield_conformance_manifest.json` (SHA-256 `0c4fcc9e…3739`, research branch until experiment-track merge) | 6,568 |
| Cross-language golden vectors | `spec/golden_vectors.json` (main) | 11 |
| Standard-track character scope | 8105 national-standard core; runtime rows per WS-7/WS-8 track column (`standard` 7,327 / `provisional` 275 / `legacy` 13,576 — legacy excluded from all WS-4 pools) | 7,327 + 275 |
| External relation labels | [P1 external review packet](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv) (600 blinded rows) after reconciliation per the [P1 method](../specification/P1_EXTERNAL_REVIEW_METHOD.md) | 600 → post-audit subset |

Candidate pools for every benchmark must be enumerable, committed, and hash-pinned before execution. Pools are drawn only from `standard` and `provisional` tracks; `legacy` rows are excluded from WS-4 evidence.

## 4. Leakage controls

1. **Component-family splits.** Train/test separation by component/radical family, so no test character shares a structural family with a training character. Family IDs come from the reviewed relation ledger, not from CNBE runtime fields.
2. **Target-field masking.** When a benchmark evaluates a field (e.g. `radix`), that field is masked out of all model inputs and similarity computations, following the `later_masked_cnbe_field` discipline of the external review packet.
3. **Source-grade separation.** `standard_derived` labels are reported separately from any other source grade, per the P1 method.
4. **Negative provenance.** Hard negatives must carry independently reviewed provenance; model-mined negatives are not admissible.
5. **Blinding.** Benchmark executors do not read external review decisions in progress; partially reviewed packets yield partially blocked metrics.

## 5. Metrics and baselines

### B1 — Morphology retrieval (blocked until P1 reconciliation passes)

- Task: given a query character, retrieve characters sharing a reviewed relation (shared radical/component, reviewed structure, stroke tolerance).
- Labels: externally reconciled packet rows only; conflicts and `exclude` rows are dropped from metric input and counted in the audit.
- Metrics: Recall@10, Recall@50, MRR, nDCG@50, reported per relation type and per source grade.
- Comparators: (a) D_morph with the registered research weights (0.4/0.2/0.2/0.1/0.1); (b) uniform-weight D_morph ablation; (c) per-field ablations (radix-only, struct-only, stroke-only); (d) baselines in §5.5.
- Pre-registered success bar: none. B1 is measurement, not a target; no superiority claim will be made from a single run.

### B2 — Geometry (dual-track)

- Models: Poincaré candidate (composition z_c, alignment loss L_hyperbolic) vs learned Euclidean embedding of identical dimension and parameter budget.
- Training: same optimizer steps, same family splits, seeds frozen in the run manifest.
- Metrics: held-out alignment loss, distance-rank correlation (Kendall τ) against externally reviewed relations, mean distortion on held-out pairs.
- Report: both models' numbers side by side; the binding consequence clause of §2 applies.

### B3 — Bitwise MoE routing

- Comparators: bitwise pre-router (α = 1), learned gate (α = 0), and the interpolation at registered α values {0.1, 0.3, 0.5}.
- Metrics: downstream task quality delta on a frozen probe task, expert load-balance (max/mean expert load), measured latency per token on registered hardware, all against a single shared-expert baseline.
- No claim from synthetic fixtures; only end-to-end measurements count.

### B4 — HDC representation

- Comparators: H(c) similarity vs D_morph and vs externally reviewed relations; dimension ablation D ∈ {1,000; 4,000; 10,000}.
- Metrics: similarity-rank correlation, memory footprint, encode/decode throughput.
- Baselines in §5.5 apply.

### 5.5 Shared baselines (per the repository roadmap)

Every family reports against the same baseline set where applicable: Unicode codepoint embedding, one-hot field encoding, IDS (ideographic description sequence) features, and a learned Euclidean embedding trained on the same splits.

## 6. Execution discipline

- Deterministic seeds recorded per run; run manifests hash-pinned like the formula verification manifest.
- Raw outputs and result artifacts committed alongside any reported number.
- Train/test separation documented per run; any deviation voids the run.
- One registration amendment requires a new committed version of this document with a dated changelog; silent metric drift is not permitted.

## 7. Stop conditions

All stop conditions in the [P1 External Review Method](../specification/P1_EXTERNAL_REVIEW_METHOD.md) are inherited. In addition, WS-4 execution halts and reports `BLOCKED` when:

1. the external reconciliation audit reports any unresolved conflict or missing source confirmation;
2. independently reviewed hard negatives or frozen candidate pools are missing for the family being run;
3. any runtime CNBE field is found feeding a label, split, or negative for the benchmark that evaluates that field (leakage);
4. the repository database migration (WS-7/WS-8 `--apply`) has not been executed — track-column integrity is a prerequisite, so B1–B4 pools cannot be certified before the governed migration lands.

## 8. Current state

- This registration: committed, no runs executed.
- P1 external review: packet published, external labels empty, reconciliation not started — **all retrieval metrics remain blocked**.
- Prerequisite: WS-7/WS-8 governed migration awaiting owner approval (`--apply --with-insertions`).

---

*Pre-registered as WS-4 of the phase-2 PDR. Amendments only via committed, dated revisions of this file.*
