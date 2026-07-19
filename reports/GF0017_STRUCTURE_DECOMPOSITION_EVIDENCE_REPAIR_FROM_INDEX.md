# GF0017 Structure/Decomposition Evidence Repair From Existing Index

## Result

- Overall status: `PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED`
- Next workflow status: `STRUCTURE_DECOMPOSITION_REVIEW_REQUIRED_NO_SCORING`
- Total rows: 97686
- Reviewable or partial rows: 4580
- Source-gap rows: 40130
- 8105 standard-join required rows: 8105
- Score values assigned: 0
- Final structure labels emitted: 0

This report does not regenerate Unicode identity, assign GF0017 points,
emit final structure labels, write CNBE rows, or rebuild databases.

## Status Counts

| Status | Count |
|---|---:|
| `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | 8105 |
| `STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY` | 44871 |
| `STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED` | 2029 |
| `STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY` | 2551 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT` | 12 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT` | 40118 |

## Samples

### 𲎯 `U+323AF`

- Scope: `outside_8105_agent_candidate`
- Structure evidence status: `STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY`
- Source grade: `agent_standard_candidate_not_national_standard`
- Next action: `human_review_or_agent_rule_learning_design_only`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

### 㐀 `U+3400`

- Scope: `outside_8105_agent_candidate`
- Structure evidence status: `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT`
- Source grade: `cross_reference_context`
- Next action: `promote_or_reject_review_context_after_source_check`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

### 㐁 `U+3401`

- Scope: `outside_8105_agent_candidate`
- Structure evidence status: `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT`
- Source grade: `cross_reference_context`
- Next action: `promote_or_reject_review_context_after_source_check`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

### 一 `U+4E00`

- Scope: `8105_core`
- Structure evidence status: `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED`
- Source grade: `standard_derived_join_pending`
- Next action: `join_8105_structure_decomposition_sources`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

### 家 `U+5BB6`

- Scope: `8105_core`
- Structure evidence status: `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED`
- Source grade: `standard_derived_join_pending`
- Next action: `join_8105_structure_decomposition_sources`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

### 鑫 `U+946B`

- Scope: `8105_core`
- Structure evidence status: `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED`
- Source grade: `standard_derived_join_pending`
- Next action: `join_8105_structure_decomposition_sources`
- Score status: `NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY`

## Decision

Structure/decomposition evidence statuses have been materialized from existing reports. They support review queue planning but do not yet authorize scoring or final labels.

The next allowed step is review-packet planning for structure and
decomposition evidence. Scoring and encoding writes remain blocked.
