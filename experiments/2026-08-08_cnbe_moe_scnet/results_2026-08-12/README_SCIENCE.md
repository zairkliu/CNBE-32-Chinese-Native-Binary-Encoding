# V1 Controlled Comparison of CNBE-MoE-128, CNBE-Dense, and Unicode-Dense

**Date**: 2026-08-12

**Hardware**: SCNet DCU BW x2 (2 x 63GB), 30 CPU cores, 118GB RAM,
Python 3.11.9, PyTorch 2.9.0, DTK 26.04.

**Timing**: MoE-128 approximately 64 minutes, Dense approximately 39 minutes,
Unicode approximately 20 minutes, evaluation approximately 10 minutes,
recorded from execution logs on 2026-08-11/12.

## Abstract

This report evaluates whether a structured Chinese character encoding (CNBE-32)
and a 128-expert Mixture-of-Experts (MoE) architecture provide measurable
advantages over a plain Transformer trained on Unicode codepoints. Using the
same v1 corpus, training schedule, and evaluation split, we compare four
conditions: CNBE-MoE-128, CNBE-Dense, CNBE-Dense with matched parameters, and
Unicode-Dense. The corrected v1 results show that CNBE-MoE-128 outperforms
the same-configuration dense baseline on next-code prediction and structural
field accuracy, and that CNBE-Dense substantially outperforms Unicode-Dense.
An equal-parameter dense control is required to fully attribute the gains to
the MoE architecture.

## 1. Introduction

CNBE-32 encodes Chinese characters into 32-bit structured fields:
radix (8 bit), strokes (5 bit), structure (4 bit), index (11 bit), and
extension bits. Unlike Unicode codepoints, CNBE carries explicit structural
information. This experiment tests whether the structure-aware encoding and
the expert architecture help sequence models learn Chinese structure.

## 2. Experimental Design

### 2.1 Hypotheses

- H1: CNBE-MoE-128 outperforms CNBE-Dense on next-code and structural fields.
- H2: CNBE encoding outperforms Unicode codepoints for next-token prediction.

### 2.2 Conditions

| Condition | Encoding | Model |
|---|---|---|
| MoE-128 | CNBE-32 | 128 experts, Top-2, hard structural routing |
| Dense same-config | CNBE-32 | Same Transformer, no MoE |
| Dense matched-params | CNBE-32 | Dense widened to approximate MoE parameter count |
| Unicode Dense | Unicode codepoint | Same Transformer, no MoE |

## 3. Data

- v1 corpus: 7 sources, 24,381,237 CNBE codes;
- train split: 24,000,000 tokens;
- eval split: 381,237 tokens (identical for all conditions);
- vocabulary: 10,991 CNBE codes; 11,163 Unicode codepoints;
- random seed: 42.

## 4. Models and Training

All conditions use the same transformer backbone:

| Parameter | Value |
|---|---:|
| d_model | 512 |
| d_ff | 2048 |
| layers | 8 |
| heads | 8 |
| seq_len | 128 |
| batch_size | 8 |
| grad_accum_steps | 1 |
| epochs | 2 |
| optimizer | AdamW |
| lr | 3e-4 |
| precision | bf16 |

MoE-128 adds 128 shared experts with top-2 hard routing on
(radix, structure, strokes). The matched dense condition increases d_ff to
32768 to approximate the MoE parameter count.

## 5. Results

| Metric | MoE-128 | Dense same-config | Dense matched-params | Unicode Dense |
|---|---:|---:|---:|---:|
| eval_loss | 4.543038 | 7.303338 | N/A | 7.793252 |
| next-code / next-token | 22.96% | 2.61% | N/A | 0.0010% |
| radix | 24.52% | 3.10% | N/A | N/A |
| struct | 43.05% | 38.41% | N/A | N/A |
| strokes | 30.13% | 13.87% | N/A | N/A |
| radix head | 22.15% | 0.03% | N/A | N/A |
| struct head | 45.81% | 0.64% | N/A | N/A |
| strokes head | 27.96% | 0.02% | N/A | N/A |
| expert_gini | 0.147240 | N/A | N/A | N/A |
| params | 289920031 | 37954591 | N/A | 38130891 |
| tokens_evaluated | 381184 | 381184 | N/A | 381184 |

## 6. Analysis

1. MoE-128 achieves substantially higher next-code accuracy and structural
   field accuracy than the same-configuration dense baseline.
2. CNBE-Dense clearly outperforms Unicode-Dense on next-token accuracy,
   supporting the structured-encoding hypothesis.
3. MoE field heads recover structural categories far better than dense heads,
   suggesting experts help structure-specific learning.
4. Expert Gini is low (0.1472), indicating balanced routing.

## 7. Limitations

- The same-configuration dense baseline has far fewer parameters
  (37.95M vs 289.9M); an equal-parameter control is required.
- The Unicode condition reports only next-token accuracy; structural metrics
  are not applicable to raw codepoints.
- Results are on the small v1 corpus and may not transfer to the 544M-token
  merged corpus.

## 8. Reproducibility

The package includes configs, metrics, mapping, vocab, code, and checkpoints.
Training and evaluation use `train_distributed.py` and `eval.py` from the
same code snapshot. The evaluation split is fixed at 381,237 tokens.

## 9. Conclusion and Next Steps

The corrected v1 experiment supports both the MoE and CNBE encoding
hypotheses. Before scaling, we should complete the equal-parameter dense
control, then run the same three-condition comparison on the 544M-token
corpus and evaluate structural downstream tasks.
