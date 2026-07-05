# CNBE-32 LLM Experiment Results (v1-v6)

This directory contains the complete experimental results from v1 to v6,
covering the CNBE-32 encoding scheme's effectiveness across multiple
LLM architectures and text types.

## Directory Structure

| Directory | Versions | Content Description |
|-----------|:--------:|--------------------|
| `v1_v4_validation/` | v1-v4 | Single char, sentence, format, paper understanding |
| `v5_model_comparison/` | v5-v5.9 | Model comparison (7 models, 0.8B-20B) |
| `v6_numerical_features/` | v6-v6.6 | Numerical format, Unicode comparison, hard tasks |
| `results/` | All | Raw Excel results for all experiments |

## Experiment Series Overview

```
v1  (0.8B)  [Single char]   CNBE zero-shot understood, 100% effective
v2  (0.8B)  [Sentence]      48% -> 87% (+81%), significant improvement
v3  (0.8B)  [Format]        Format A best: 87% effective, 9% distraction
v4  (0.8B)  [Long text]     90.9% -> 100% (+9.1%), valid for real text
v5a (0.8B)  [Messy text]    Annotation inflation threshold observed
v5b (8B)    [Messy text]    Marginal benefit decreases with model size
v5.5 (9B)   [Messy text]    9B same as 8B, CNBE no additional help
v5.6 (4B)   [All tasks]     Gemma 4B: CNBE > Unicode (+17.4pp)
v5.7 (2B)   [Qwen compare]  Qwen 2B Unicode comparison
v5.8 (4B)   [Qwen compare]  Qwen 4B cross-architecture comparison
v5.9 (20B)  [All models]    7-model full comparison, CN vs foreign
v6.0 (Skill) [Skill table]  8105 char table, 81.6KB, 100% correct
v6.1 (Qwen) [Long text]     Qwen family 4-model comparison
v6.2 (6 models) [Long text] CN vs foreign comparison
v6.3 (0.8B) [Numerical]     93% -> 87%, numerical features viable
v6.4 (0.8B) [Numerical]     C/B ratio 106.9%, result reproducible
v6.5 (0.8B) [Format F]      Bare numbers F best: 100% effective
v6.5.1 (Daodejing) [Format] Ancient text: Format F 100% effective
v6.5.2 (CNBE vs Unicode)    CNBE > Unicode on 0.8B and 2B
v6.5.3 (Hard tasks)         Rare/hard chars: CNBE > baselines
v6.6 (Multi-model)          5-model hard task comparison
```

## Key Discoveries

| Discovery | Evidence |
|-----------|----------|
| CNBE helps small models most | 0.8B: +81%, 8B+: 0% |
| Format A (per-char annotation) optimal | v3 confirmed |
| Numerical features work in raw form | v6.3-v6.5 confirmed |
| CNBE > Unicode on Gemma 4B | v6.6: +17.4pp |
| Skill table 100% correct | v6.0: 8105 chars verified |
| Spike integration complete | v7.0-v7.1.1 verified |

## Results Data

All raw experiment results are in the `results/` directory as Excel files
(cnbe_v*_results.xlsx). Each file contains per-question comparison data
between control and experimental groups.

## See Also

- `riscv/` directory: Hardware implementation results (v7 series)
- `docs/` directory: System architecture and design documents
- `hardware/` directory: Original Spike patches (v2)
- `experiments/` directory: Python experiment scripts
- `src/` directory: CNBE encoding tools
