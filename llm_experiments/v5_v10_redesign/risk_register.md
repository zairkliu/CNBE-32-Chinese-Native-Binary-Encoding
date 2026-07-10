# v5-v10 Risk Register

Status: protocol draft

This document lists validity risks for redesigned v5-v10 experiments.

Each completed report must address relevant risks.

## R1 Prompt-Length Confounding

Risk:

CNBE annotations may improve output simply because they add tokens or structure.

Applies to:

- v5,
- v6,
- v10 LLM-based tasks.

Mitigation:

- same-length random annotation,
- shuffled-field annotation,
- token-overhead reporting,
- cost-adjusted metrics.

## R2 Model-Family Confounding

Risk:

A result may reflect one model family's training data or prompt style rather than CNBE.

Applies to:

- v5,
- v6,
- v10.7,
- v10.8.

Mitigation:

- fixed model matrix,
- per-family reporting,
- no universal claim from one model,
- model version recording.

## R3 Evaluation Leakage

Risk:

The judge or scoring process may see condition labels.

Applies to:

- v5,
- v6,
- v10 reasoning tasks.

Mitigation:

- blind sample IDs,
- hidden condition labels,
- frozen rubric,
- audit subset.

## R4 Temporal Leakage

Risk:

Predictive experiments may train or tune on future information.

Applies to:

- v9,
- v10 finance,
- v10 typhoon,
- v10 lifecycle.

Mitigation:

- time-based splits,
- frozen cutoffs,
- no random split across time,
- timestamp audit.

## R5 Domain Baseline Weakness

Risk:

CNBE treatment may appear strong only because baselines are weak.

Applies to:

- v9,
- v10.

Mitigation:

- native domain baselines,
- naive baselines,
- published benchmark references when available,
- ablation against non-CNBE representation.

## R6 Demo-to-Validation Overreach

Risk:

A working demo may be described as broad validation.

Applies to:

- v7,
- v8.

Mitigation:

- classify demos as smoke tests,
- define fixture coverage,
- require negative tests,
- require trace logs.

## R7 Toolchain Drift

Risk:

Compiler, emulator, model runtime, or API changes may alter results.

Applies to:

- all stages.

Mitigation:

- record versions,
- record commit SHA,
- archive command line,
- store output hashes,
- pin dependencies where practical.

## R8 Manual Output Editing

Risk:

Outputs may be cleaned manually before scoring.

Applies to:

- all stages.

Mitigation:

- retain raw outputs,
- use deterministic parsers,
- log exclusions,
- report invalid-output rate.

## R9 Cross-Domain Claim Inflation

Risk:

Positive results in one domain may be generalized to unrelated domains.

Applies to:

- v10.

Mitigation:

- per-domain reporting,
- domain-specific metrics,
- no aggregate headline without domain breakdown,
- explicit null-result reporting.

## R10 Hardware Readiness Overclaim

Risk:

Emulator or FPGA smoke tests may be described as production hardware readiness.

Applies to:

- v7,
- v8.

Mitigation:

- separate emulator, FPGA, and silicon evidence,
- require trace comparison,
- report unsupported instructions,
- avoid production-readiness claims.
