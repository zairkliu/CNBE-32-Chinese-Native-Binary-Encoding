# V1: Ancient OCR + CNBE Character-Level Verification (Yongle 37 pages)

Date: 2026-08-05

## 1. OCR baselines (sequence-level character accuracy)

| Source | Pages | Truth chars | Matched | Accuracy | Substitutions |
|---|---:|---:|---:|---:|---:|
| best | 37 | 16123 | 6068 | 0.3764 | 5243 |
| paddle | 37 | 16123 | 1916 | 0.1188 | 9620 |
| v1 | 37 | 16123 | 6242 | 0.3871 | 4896 |

## 2. CNBE oracle on real substitutions

- Substitutions: 5243
- Both chars in CNBE standard track: 2797
- Truth in CNBE top-K: {'1': 10, '3': 21, '5': 29, '10': 38, '20': 65}
- Confusing-group errors: 17
- Group top-1 (CNBE field distance): 17 (1.0000)

Interpretation: most real OCR errors are layout/order corruption, not clean shape-confusable substitutions. CNBE top-K recall on real substitutions is low, but every confusing-group error in the real data is ranked top-1 by CNBE fields.

## 3. Synthetic confusable-corruption benchmark

Corrupt ground truth with confusing-group or CNBE-neighbor substitutions, then run a CNBE verifier (field distance + corpus frequency).

| Corruption rate | Corrupted | Truth | Baseline acc | Group verifier | Neighbor verifier |
|---|---:|---:|---:|---:|---:|
| 0.01 | 105 | 16123 | 0.9935 | 0.9926 | 0.8026 |
| 0.02 | 255 | 16123 | 0.9842 | 0.9833 | 0.7998 |
| 0.05 | 609 | 16123 | 0.9622 | 0.9619 | 0.7924 |
| 0.1 | 1164 | 16123 | 0.9278 | 0.9279 | 0.7819 |

## 2b. Group verifier applied to real best OCR

- Baseline accuracy: 0.3764
- After group verifier: 0.3761
- Changes: 9, correct changes: 0

## 3b. Group-only synthetic corruption

Only characters belonging to known confusing groups are corrupted, isolating the CNBE group-disambiguation capability.

| Group corruption rate | Group positions | Corrupted | Baseline acc | Group verifier | Neighbor verifier | Oracle upper bound |
|---|---:|---:|---:|---:|---:|---:|
| 0.5 | 1004 | 450 | 0.5518 | 0.6155 | 0.5608 | 1.0000 |
| 1.0 | 1004 | 911 | 0.0926 | 0.2410 | 0.1972 | 1.0000 |

## 4. Boundaries

- No OCR candidate lists were available; real OCR is dominated by reading-order corruption.
- The synthetic benchmark isolates the CNBE verifier on clean shape-confusable errors.
- Corpus frequency prior comes from the seven-corpus data set (24.38M chars).
- Reproduce: `python3 run_v1_experiment.py`.

## 5. Conclusion for V1 gate

The +5% overall accuracy gate is **not met** on the current 37-page OCR corpus: real OCR errors are dominated by reading-order and garbage substitutions, not by clean shape-confusable character errors. CNBE top-K recall on real substitutions is low (truth in top-20 for 65/2797 in-standard pairs). The CNBE character-level verifier is validated only on its target slice: all 17 real confusing-group errors are ranked top-1 by CNBE field distance (100%), and on group-only synthetic corruption it recovers +6.4pp at 50% corruption and +14.8pp at 100% corruption on group positions. A general context-free neighbor verifier without OCR candidate lists is destructive and should not be used.

Next step: obtain OCR top-N candidates (Paddle/vision-model candidate lists), then apply the CNBE verifier as a reranker only on candidate sets, with page context.
