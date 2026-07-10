# CNBE-32 v1-v4 Confirmatory LLM Protocol

Status: protocol draft

This document defines the confirmatory protocol for redesigned v1-v4 large language model experiments.

It is a design document only. It does not report completed results.

## 1. Research Questions

RQ1: Do CNBE fields provide measurable incremental signal over Unicode and radical-only baselines for single-character tasks?

RQ2: Do CNBE annotations improve sentence comprehension after controlling for annotation length and prompt format?

RQ3: Which CNBE injection format provides the best tradeoff among score gain, distraction, and token cost?

RQ4: Does CNBE remain useful under long-context pressure, or does annotation overhead dominate?

RQ5: Are observed effects stable across Qwen-family and DeepSeek-family models?

## 2. Hypotheses

H1: CNBE full fields will outperform radical-only and Unicode-only conditions on stratified single-character semantic tasks.

H2: CNBE full annotations will improve key-point recall on low-frequency and classical sentence subsets more than on ordinary modern text.

H3: Selective annotation will provide a better cost-adjusted gain than annotating every character.

H4: Shuffled CNBE and random annotation controls will not match valid CNBE if the improvement comes from structured fields.

H5: Effects will vary by model family and model size; a single model result is not enough for a general claim.

## 3. Experimental Principles

The protocol uses paired inputs wherever possible.

Every sample appears in every relevant condition.

Condition order is randomized per model run.

The evaluator is blind to the condition label.

Prompts are fixed before execution.

Data splits are fixed before execution.

Sampling seeds are recorded.

Raw model outputs are retained.

Scoring scripts must be deterministic.

Human scoring guidelines must be frozen before scoring.

## 4. Model Matrix

The model matrix should include:

- Qwen small size band,
- Qwen medium size band,
- DeepSeek small size band,
- DeepSeek medium size band.

Optional extensions:

- an API-hosted frontier model,
- a local open-weight model from another family,
- one smaller stress-test model.

Each row in the model manifest must include:

- model name,
- provider or runtime,
- exact version or digest,
- context window,
- decoding parameters,
- date of run,
- hardware or API region when relevant.

## 5. Control Groups

The protocol requires these controls when the task permits them:

- character or text only,
- Unicode code point only,
- radical-only,
- CNBE full fields,
- shuffled CNBE fields,
- random CNBE-like fields,
- random annotation with matched token length,
- no-answer calibration prompts.

The random and shuffled controls are used to detect prompt-length and formatting effects.

## 6. Randomization and Seeds

Each experiment must define:

- dataset sampling seed,
- condition-order seed,
- prompt-example seed when few-shot examples are used,
- bootstrap seed for confidence intervals.

Recommended default:

- sampling seed: 20260710,
- condition seed: 20260711,
- bootstrap seed: 20260712.

The same seed values should be reused across model families for direct comparison.

## 7. Evaluation Plan

Evaluation uses both automatic and human-reviewed metrics.

Automatic metrics include:

- validity rate,
- refusal rate,
- distraction rate,
- key-point recall,
- lexical overlap for diagnostic use only,
- token overhead,
- cost-adjusted gain.

Human or judge-assisted metrics include:

- semantic correctness,
- factual consistency,
- hallucination,
- evidence grounding,
- answer usefulness.

LLM judging may be used only as an assistive evaluator.

At least a sample of outputs must be human-audited.

## 8. Statistical Testing Plan

Binary paired outcomes use McNemar tests where conditions share the same samples.

Numeric paired outcomes use paired bootstrap confidence intervals.

When score distributions are non-normal, use bootstrap intervals rather than relying only on parametric tests.

Every reported gain must include:

- sample count,
- baseline score,
- treatment score,
- delta,
- confidence interval,
- test used,
- p-value when applicable,
- correction for multiple comparisons when many conditions are compared.

## 9. Failure Criteria

An experiment fails protocol quality if:

- condition labels leak into judge prompts,
- answers are judged without blind IDs,
- random and shuffled controls are omitted,
- model versions are not recorded,
- prompts are changed mid-run,
- data split changes after seeing results,
- only response length is measured,
- outputs are manually filtered without an audit log.

## 10. Reporting Rules

Reports must distinguish:

- protocol,
- run manifest,
- raw results,
- scored results,
- interpretation.

Reports may state measured effects only within the tested setup.

Reports must not generalize from one model family to all models.

Reports must describe negative and null findings.

Reports must include known limitations.

Reports must cite exact prompt templates and dataset versions.

## 11. Non-Goals

This protocol does not:

- claim universal LLM benefit,
- claim deployment readiness,
- claim complete CJK validation,
- modify CNBE-32 bit layout,
- replace Unicode,
- validate hardware behavior,
- publish a new package release,
- define training or fine-tuning as part of v1-v4.

Fine-tuning, LoRA, or SFT should be treated as a later study after zero-shot and prompt-only experiments are complete.
