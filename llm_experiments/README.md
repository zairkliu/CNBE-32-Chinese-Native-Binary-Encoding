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

## See Also

- `riscv/` directory: Hardware implementation results (v7 series)
- `docs/` directory: System architecture and design documents
- `hardware/` directory: Original Spike patches (v2)
- `experiments/` directory: Python experiment scripts
- `src/` directory: CNBE encoding tools
