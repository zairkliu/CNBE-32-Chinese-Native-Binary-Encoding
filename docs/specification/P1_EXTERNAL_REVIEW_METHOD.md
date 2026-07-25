# CNBE P1 Self-Validation and External Independent Review Method

**Chinese version:** [CNBE P1 自验证与外部独立审阅方法](P1_EXTERNAL_REVIEW_METHOD_ZH.md)

## Purpose

External review is the entry point for P1 independence. Internal self-validation checks artifact completeness, consistency, reproducibility, and leakage boundaries; it cannot establish that a Hanzi relation or its source is correct. External reviewers must independently check every source locator and relation claim without reading prior approval decisions.

## Artifact Order

1. Internal positive-relation ledger: `P1_INDEPENDENT_RELATION_LEDGER_HUMAN_APPROVED.csv`.
2. Self-validation report: `P1_SELF_VALIDATION_AND_EXTERNAL_REVIEW_PACKAGE.md`.
3. Redacted external-review packet: [P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv](../../experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv).
4. After external review, create a separate reconciliation-audit input; never overwrite the source ledger or external packet.

## External Review Rules

- Verify query/candidate characters and Unicode identity first.
- Verify `relation_claim_to_verify` solely from `source_document` and `source_locator`.
- `external_relation_label` may be only `positive`, `negative`, or `exclude`.
- `external_source_confirmation` may be only `confirmed`, `unclear`, or `conflict`.
- Record `exclude` for an unavailable locator, source conflict, or uncertain Unicode; do not infer.
- Do not read internal labels, family IDs, splits, or mathematical scores; do not use CNBE runtime fields to confirm the relation.

## Reconciliation and Stop Conditions

After external review, a reconciliation audit must count row-level agreement, conflict, exclusion, and missing input. Any conflict, missing source confirmation, missing independently reviewed hard negatives, or missing candidate pools keeps P1 metrics blocked.

Only an audit passing source grade, labels, family splits, target-field masking, negative-source provenance, and frozen pools may create P1 metric input. Source grades, including `standard_derived`, must remain separately reported.

## Reproduction

```bash
python3 experiments/morphology_computing/scripts/build_p1_self_validation_and_external_review_package.py
python3 -m pytest tests/test_morphology_computing_p1_self_validation_external_review.py -q
```

The builder script and tests run in the morphology-computing experiment package and land with the experiment-track merge; items 1 and 2 above are staged in the same package. The external-review packet (item 3) is available in this repository at the link above.
