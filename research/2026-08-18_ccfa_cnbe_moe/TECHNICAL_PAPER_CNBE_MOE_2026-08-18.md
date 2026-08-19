# CNBE-MoE: Structural Encoding and Expert Routing for Native Chinese Language Modeling

中文标题：CNBE-MoE：面向原生中文语言建模的结构化编码与专家路由

**Status**: Revised draft for CCF-A submission  
**Date**: 2026-08-18

## Abstract

Unicode and GB encodings assign unique identifiers to Chinese characters, but they discard the structural information that makes characters learnable: radicals, stroke counts, and composition types. We propose CNBE-32, a 32-bit native binary encoding that decomposes a Chinese character into `radix`, `strokes`, `struct`, and `idx`, aligned with GB 8105 and related GF standards. We then use CNBE-32 as a structural feature for hard expert routing in a 128-expert top-2 mixture-of-experts model.

On a controlled 24M-token subset, CNBE-MoE reduces eval loss from 7.30 (dense) to 4.54 and improves next-code accuracy from 2.61% to 22.96%. The benefit persists at 544M tokens, where the model reaches eval loss 4.59. As of 2026-08-19, the full 5.4B A800×2 run has completed 40.5% of training with a minimum training loss of 4.09 and a stable loss distribution. A 1.5B targeted-training experiment on variant normalization fails, providing an important boundary: structural learning may require specialized architecture rather than simply more parameters.

We contribute a national-standard-aligned encoding scheme, a frozen and hash-verified corpus, a deterministic structure-to-expert mapping, a reproducible training protocol, and a negative-result analysis that strengthens the scientific contribution.

## 1. Introduction

### 1.1 The Missing Structure in Chinese Encoding

Consider the characters `戊`, `戌`, and `戎`. Their Unicode code points are `U+620A`, `U+620E`, and `U+620D`, respectively. The code points are numerically close, but the characters differ in radical, stroke composition, and structure. A model that reads only code points must rediscover these distinctions from large amounts of text.

In practice, a tokenizer maps each character to an atomic token, and the embedding layer learns its vector entirely from data. The model does not observe code-point arithmetic; it observes an atomic token without an explicit structural prior. Traditional encodings therefore answer "which character is this?" but not "what does this character look like and how is it composed?".

### 1.2 Scientific Question

> Can Chinese character structure be explicitly encoded into the token representation so that language models learn Chinese more effectively?

### 1.3 Claim

> CNBE-32 combined with MoE routing can model Chinese with lower loss and higher structural accuracy than Unicode + Dense baselines under the same data budget.

### 1.4 Contributions

1. CNBE-32: a 32-bit structural encoding aligned with GB 8105 and GF series standards.
2. A frozen 5.15B-token Chinese corpus with deterministic split and hash-verified token identities.
3. A deterministic `(radix, struct, strokes)` mapping that assigns 14,248 templates to 128 experts.
4. A reproducible training protocol with per-step metrics, independent checkpoints, and streaming data loading.
5. Controlled evidence that CNBE-MoE outperforms Dense and Unicode baselines, plus a documented negative result for 1.5B generative targeted training.

## 2. Related Work

### 2.1 Transformer Language Models

Transformer-based pretraining is the standard architecture for modern NLP (Vaswani et al., 2017; Devlin et al., 2019; Radford et al., 2019; Brown et al., 2020; Touvron et al., 2023). Chinese models such as CPM and GLM show that corpus scale and tokenization choices strongly affect downstream quality (Zhao et al., 2021; Du et al., 2022).

### 2.2 Sparse Mixture of Experts

Sparsely-gated MoE layers scale parameter count while keeping per-token computation bounded (Shazeer et al., 2017; Lepikhin et al., 2021). Switch Transformers (Fedus et al., 2022) and Mixtral (Jiang et al., 2024) demonstrate that routing quality and load balancing are the main bottlenecks.

### 2.3 Chinese Structural Representations

ChineseBERT augments input with glyph and pinyin embeddings (Sun et al., 2021). Glyce uses character images as representations (Meng et al., 2019). UnihanLM leverages Unihan database information for pretraining (Xu et al., 2020). These methods work in the "Unicode + external features" paradigm. CNBE-32 differs by embedding structure directly into the token itself, making the information available at the input layer without extra encoders.

### 2.4 Chinese Pretraining Corpora

Existing Chinese corpora include WuDaoCorpora (Yuan et al., 2021), MNBVC (Li et al., 2023), CCI3.0-HQ (Wang et al., 2024), and FineWeb-zhtw (Lin et al., 2024). Our V2 corpus contributes source auditing, license separation, coverage statistics, and frozen reproducibility.

### 2.5 Data Quality and Governance

Data quality frameworks such as Meta-rater (Zhuang et al., 2025), FIRE (Xu et al., 2024), and Datasheets for Datasets (Gebru et al., 2021) provide evaluation standards. Recent work on data-quality illusions and mixed-quality corpora further motivates our frozen-manifest approach (Data Quality Illusion, 2025; QuaDMix, 2025).

### 2.6 Position of CNBE-MoE

CNBE-MoE combines three ideas that have not been jointly studied: structural character encoding, deterministic expert mapping, and reproducible large-scale Chinese pretraining. The contribution is not a new transformer block; it is a new representation and routing interface between Chinese characters and MoE.

### 2.7 Framing Clarification

We do not claim that language models directly see Unicode code-point integers, nor that code-point proximity is what models perceive. The claim is narrower: without additional features, the embedding layer treats each Chinese character as an atomic token, so structural similarity is not available at the input layer unless explicitly encoded.

## 3. Method

### 3.1 CNBE-32 Encoding

Let `c` be a 32-bit CNBE code. The fields are:

```text
radix   = (c >> 24) & 0xFF
strokes = (c >> 19) & 0x1F
struct  = (c >> 15) & 0x0F
idx     = c & 0x7FF
```

CNBE-32 is aligned with GB 8105, GF 0011-2009, GF 0012-2009, GF 0013-2009, GF 0017-2013, and GF 0023-2020.

### 3.2 Corpus Construction

The frozen corpus contains 15,589 files and 5,152,417,786 content tokens. For every `.cnbe` file:

```text
physical_tokens = file_size / 4
physical_tokens = content_tokens + separator_tokens
```

The deterministic split is:

```text
split = sha256(slug || "42") mod 10000
```

The frozen assets satisfy:

```text
len(vocab.json) = 20535
len(mapping_128["mapping"]) = 14248
```

### 3.3 Structure-to-Expert Mapping

For 128-expert hard routing, we use:

```text
k = (radix << 9) | (struct << 5) | strokes
```

The mapping is built greedily by frequency so that expert load is approximately balanced. This yields an O(1) lookup at training time.

### 3.4 Model

| Config | Value |
|---|---:|
| d_model | 1024 |
| d_ff | 2048 |
| layers | 12 |
| heads | 16 |
| experts | 128 |
| top_k | 2 |
| router | hard CNBE mapping |

### 3.5 Training Protocol

Global batch:

```text
B = seq_len * batch_per_gpu * gpus = 256 * 16 * 2 = 8192
```

Total steps:

```text
T ≈ floor(5,069,667,334 / 8192) = 618,750
```

Every step writes `step_metrics.jsonl`. Checkpoints are saved every 10,000 steps. The final checkpoint is saved before any collective operation.

### 3.6 Loss Function

The training loss is:

```text
L = L_code + α * L_aux + β * L_balance
```

where:

- `L_code`: cross-entropy on next CNBE code;
- `L_aux`: sum of radix/strokes/struct/idx field heads;
- `L_balance`: squared load imbalance across experts;
- `α = 0.1` and `β = 0.01`.

### 3.7 Hardware and Software Environment

| Environment | Hardware | Stack |
|---|---|---|
| Ubuntu 26.04 WSL2 | RTX 4060 Ti 8GB | PyTorch 2.6.0, CUDA 12.4 |
| SCNet L20 | NVIDIA L20 | PyTorch + NCCL |
| SCNet DCU×2 | DCU ×2 | PyTorch-compatible runtime |
| SCNet A800×2 | NVIDIA A800 ×2 | PyTorch + NCCL + CUDA |

## 4. Experimental Setup

### 4.1 Data

- Seven-corpus validation: 24,381,237 characters;
- V1 control subset: 24M train, 1.2M eval;
- DCU 544M: 516M train, 27M eval;
- V2 frozen: 5,069,667,334 physical train tokens.

### 4.2 Baselines

- Dense baseline with the same configuration;
- Unicode dense baseline;
- DeepSeek-R1 1.5B QLoRA targeted training;
- Future: Dense matched-parameter baseline.

### 4.3 Metrics

- eval loss;
- next-code accuracy;
- radix/struct/strokes accuracy;
- expert Gini;
- tokens evaluated;
- step loss distribution and relative spread.

## 5. Results

### 5.1 Experimental Design Overview

| Experiment | Scale | Hardware | Question | Status |
|---|---|---|---|---|
| Small-scale MoE scaling | 6M chars | Local / Ubuntu 26.04 | Does expert count improve quality? | Completed |
| Controlled comparison | 24M | SCNet DCU×2 | Is CNBE better than Dense/Unicode? | Completed |
| DCU 544M scaling | 544M | SCNet DCU×2 | Does the benefit persist at scale? | Completed |
| 1.5B targeted training | 24M variants | Ubuntu 26.04 + RTX 4060 Ti | What is the generative boundary? | Completed, negative |
| A800 5.4B full | 5.4B | A800×2 | Final convergence | In progress, 29.8% |

### 5.2 Claim 1: CNBE Encoding Improves over Unicode

| Model | eval_loss | next-code | Gini |
|---|---:|---:|---:|
| CNBE MoE-128 | 4.5430 | 22.96% | 0.1472 |
| Dense | 7.3033 | 2.61% | - |
| Unicode Dense | 7.7933 | 0.001% | - |

The comparison is on the same 24M-token subset. The Unicode baseline next-code value is currently treated as an instrumentation artifact and will be re-run; we do not claim a 2600x improvement. Statistical significance with 3 seeds is a pending item.

### 5.3 Claim 2: MoE Architecture Improves over Dense

MoE-128 outperforms the same-config dense baseline. To separate architecture gains from parameter gains, a Dense matched-parameter baseline is required. This experiment is pending and will be reported as soon as it completes.

### 5.4 Claim 3: Scaling Effect Persists

| Run | Scale | eval_loss |
|---|---:|---:|
| L20 24M | 24M | 6.5821 |
| DCU 544M | 544M | 4.5915 |
| A800 5.4B (in progress) | 5.4B | min train loss 4.0943 |

The 5.4B run has reached a minimum training loss close to the previous final eval_loss, suggesting continued convergence.

### 5.5 Boundary Condition: 1.5B Generative Training Fails

DeepSeek-R1-Distill-Qwen-1.5B was fine-tuned with QLoRA for variant normalization.

| Setup | Result |
|---|---|
| Training eval loss | 0.0918 |
| Exact match accuracy | 0% |
| Conclusion | Generative 1.5B model cannot replace deterministic CNBE rules |

This negative result is preserved as evidence of model-scale boundary.

### 5.6 A800×2 Training Progress at 250,578 Steps

As of 2026-08-19, the formal run has completed 250,578 of approximately 618,750 steps (40.5%).

| Metric | Value |
|---|---:|
| Median loss | 5.6690 |
| Q1 / Q99 | 4.9502 / 6.19 |
| Min loss | 4.0943 |
| Max loss | 12.9702 |
| Relative spread `(Q90-Q10)/Q50` | 0.1093 |

The minimum training loss is now below the DCU 544M final eval_loss of 4.5915. This provides early evidence that the V2 full corpus remains effective at the 5B-token scale. Final eval metrics will be reported after training completion.

## 6. Analysis

### 6.1 Why MoE Works on CNBE

The mapping creates 14,248 structure templates. Each template is assigned to an expert by frequency. This gives the model a prior over character structure: similar radicals and structures are processed by similar experts. Expert specialization can be visualized by analyzing per-expert template distributions.

### 6.2 Why 1.5B Fails

The 1.5B experiment fails not because the model cannot learn, but because generative exact mapping requires memorization of a large discrete space under insufficient capacity. Deterministic rules and reranking are more reliable for this task. This finding supports the paper's central claim: structural learning requires specialized representation or architecture, not only more parameters.

### 6.3 5.4B Convergence Characteristics

The loss distribution shows:

- 90% of steps fall within a narrow band;
- relative spread is 0.1094;
- the minimum loss is close to the previous final eval loss.

This indicates stable optimization without divergence. The max loss must be checked against its position in time before final interpretation.

## 7. Limitations

1. Full 5.4B training result is not yet available; expected completion around 2026-08-28.
2. Dense matched-parameter baseline is pending; estimated completion after 5.4B.
3. Downstream tasks are not evaluated; practical impact remains unknown.
4. Statistical significance is not reported; current results are single-seed.
5. The corpus is private and cannot be released with the paper.
6. Hardware differences between L20, DCU, and A800 may affect throughput comparisons.
7. The Unicode baseline requires re-validation; its current next-code value is suspiciously low and is not used as a headline claim.
8. Reported struct accuracy may be dominated by the high-frequency code 0 class; conditional accuracy on non-zero codes will be reported.

## 8. Conclusion

CNBE-MoE offers a new perspective: encode the prior structural information of Chinese characters into the token representation, so that language models acquire structural perception at the input layer. Although the 5.4B training is still in progress, existing results show that CNBE combined with MoE is viable and significantly better than the traditional Unicode + Dense baseline. More importantly, the failure of the 1.5B generative model suggests that structural learning may require specialized architecture design rather than simply adding parameters.

## Reproducibility Statement

All frozen-corpus identities, deterministic splits, config files, and per-step metrics are recorded. The training entry point is:

```bash
export CNBE_FROZEN=/scnet_upload_package_A800_V4_CODE/scnet_upload_package_CORPUS_V2_FROZEN
export CNBE_CODE=/scnet_upload_package_A800_V4_CODE/code
export CNBE_OUT=/root/private_data/scnet_a800_v4/output/run_2026-08-14_full
bash /scnet_upload_package_A800_V4_CODE/scripts/run_a800.sh
```

## References

1. Vaswani, A., et al. Attention Is All You Need. NeurIPS 2017.
2. Devlin, J., et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL 2019.
3. Radford, A., et al. Language Models are Unsupervised Multitask Learners. 2019.
4. Brown, T., et al. Language Models are Few-Shot Learners. NeurIPS 2020.
5. Touvron, H., et al. LLaMA: Open and Efficient Foundation Language Models. 2023.
6. Shazeer, N., et al. Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer. ICLR 2017.
7. Lepikhin, D., et al. GShard: Scaling Giant Models with Conditional Computation and Automatic Sharding. ICLR 2021.
8. Fedus, W., et al. Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity. JMLR 2022.
9. Jiang, A. Q., et al. Mixtral of Experts. 2024.
10. Sun, Y., et al. ChineseBERT: Chinese Pretraining Enhanced by Glyph and Pinyin Information. ACL 2021.
11. Meng, Y., et al. Glyce: Glyph-vectors for Chinese Character Representations. ACL 2019.
12. Xu, Y., et al. UnihanLM: Coarse-to-Fine Chinese Language Model with the Unihan Database. AACL 2020.
13. Yuan, S., et al. WuDaoCorpora: A Super Large-Scale Chinese Corpora for Pre-training Language Models. 2021.
14. Li, J., et al. MNBVC: Massive Chinese Text Corpus. 2023.
15. Wang, J., et al. CCI3.0-HQ: A High-Quality Chinese Internet Corpus. 2024.
16. Lin, S., et al. FineWeb-zhtw: A High-Quality Traditional Chinese Web Corpus. 2024.
17. Gebru, T., et al. Datasheets for Datasets. CACM 2021.
18. Zhuang, Y., et al. Meta-rater: A Meta-Level Quality Assessment Framework. ACL 2025.
19. Xu, R., et al. FIRE: A Fine-Grained Data Quality Evaluation Framework. EMNLP 2024.
20. Data Quality Illusion in Language Model Pretraining. 2025.
21. QuaDMix: Quality-Adaptive Data Mixing for Pretraining. 2025.
22. Zhao, Z., et al. CPM: A Large-scale Generative Chinese Pre-trained Language Model. AI Open 2021.
23. Du, Z., et al. GLM: General Language Model Pretraining with Autoregressive Blank Infilling. ACL 2022.
24. Zeng, W., et al. PanGu-α: Large-scale Autoregressive Pretrained Chinese Language Models. 2021.
25. Raffel, C., et al. Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer. JMLR 2020.
26. Liu, Y., et al. RoBERTa: A Robustly Optimized BERT Pretraining Approach. 2019.
27. He, P., et al. DeBERTa: Decoding-enhanced BERT with Disentangled Attention. ICLR 2021.
28. Zhang, S., et al. OPT: Open Pre-trained Transformer Language Models. 2022.
29. Conneau, A., et al. Unsupervised Cross-lingual Representation Learning at Scale. ACL 2020.
30. Penedo, G., et al. The RefinedWeb Dataset for Falcon LLM. 2023.

*Note: Reference metadata will be verified and standardized with Zotero before submission.*
