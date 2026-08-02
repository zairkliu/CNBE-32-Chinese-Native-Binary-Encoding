# CNBE-32 LLM Experiment Results (v1-v6)

This directory contains historical exploratory experiment artifacts from v1 to v6.

These files are retained for provenance and auditability.

They should not be read as confirmatory evidence, production readiness claims, or universal CNBE effectiveness claims.

For redesigned confirmatory protocols, see:

- `v1_v4_redesign/`
- `v5_v10_redesign/`

## Directory Structure

| Directory | Versions | Content Description |
|-----------|:--------:|--------------------|
| `v1_v4_validation/` | v1-v4 | Single char, sentence, format, paper understanding |
| `v5_model_comparison/` | v5-v5.9 | Model comparison (7 models, 0.8B-20B) |
| `v6_numerical_features/` | v6-v6.6 | Numerical format, Unicode comparison, hard tasks |
| `results/` | All | Raw Excel results for all experiments |
| `2026-08-02_yongle_failures/` | 2026-08-02 | Yongle OCR failure postmortem, punctuation pivot, 14B training plan, boundary analysis |

## Historical Series Overview

```
v1  (0.8B)  [Single char]   exploratory single-character response behavior
v2  (0.8B)  [Sentence]      exploratory sentence-level response-rate change
v3  (0.8B)  [Format]        exploratory annotation-format comparison
v4  (0.8B)  [Long text]     exploratory long-text response behavior
v5a (0.8B)  [Messy text]    Annotation inflation threshold observed
v5b (8B)    [Messy text]    Marginal benefit decreases with model size
v5.5 (9B)   [Messy text]    9B same as 8B, CNBE no additional help
v5.6 (4B)   [All tasks]     exploratory CNBE versus Unicode comparison
v5.7 (2B)   [Qwen compare]  Qwen 2B Unicode comparison
v5.8 (4B)   [Qwen compare]  Qwen 4B cross-architecture comparison
v5.9 (20B)  [All models]    7-model full comparison, CN vs foreign
v6.0 (Skill) [Skill table]  historical skill-table implementation check
v6.1 (Qwen) [Long text]     Qwen family 4-model comparison
v6.2 (6 models) [Long text] CN vs foreign comparison
v6.3 (0.8B) [Numerical]     93% -> 87%, numerical features viable
v6.4 (0.8B) [Numerical]     C/B ratio 106.9%, result reproducible
v6.5 (0.8B) [Format F]      exploratory bare-number format comparison
v6.5.1 (Daodejing) [Format] exploratory ancient-text format comparison
v6.5.2 (CNBE vs Unicode)    exploratory CNBE versus Unicode comparison
v6.5.3 (Hard tasks)         exploratory rare/hard-character comparison
v6.6 (Multi-model)          5-model hard task comparison
```

## Historical Observations

| Observation | Evidence Boundary |
|-----------|----------|
| Small models appeared more sensitive to annotation | Requires redesigned v1-v6 confirmation |
| Prompt format changed output behavior | Requires same-length and shuffled controls |
| Numerical fields appeared usable in some prompts | Requires cost-adjusted ablation |
| Model-family behavior varied | Requires fixed model matrix |
| Skill-table implementation was explored | Requires separate artifact and fixture validation |
| Hardware integration was explored elsewhere | Requires v7/v8 conformance protocol |

## Results Data

Raw experiment spreadsheets are in the `results/` directory as Excel files.

Those spreadsheets are historical source material for future reruns.

They are not by themselves confirmatory evidence.

## 2026-08-02 永乐大典失败实验

2026-08-02 完成《永乐大典》37 页人工校订实验，确认 1.5B 无法做整页 OCR
转录（精确匹配约 20%），并基于识典古籍交叉验证（逐字一致 100%）把大模型
重新定位为古籍句读专家。完整失败总结、白皮书、14B 训练配置与能力边界
讨论见 `2026-08-02_yongle_failures/`。

## See Also

- `riscv/` directory: Hardware implementation results (v7 series)
- `docs/` directory: System architecture and design documents
- `hardware/` directory: Original Spike patches (v2)
- `experiments/` directory: Python experiment scripts
- `src/` directory: CNBE encoding tools
