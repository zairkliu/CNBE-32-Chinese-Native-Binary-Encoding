# Remaining Structure Agent-Standard Rule-Learning Design

## Purpose

This report designs read-only Agent-standard rule learning for remaining
structure/decomposition candidates. It uses the audited 8105 baseline as
a learning reference while preserving all remaining rows as project-level
Agent-standard candidates, not national-standard outputs.

It does not assign GF0017 scores, emit final structure labels, modify
source assets, write CNBE rows, rebuild databases, create tags, publish
releases, or upload to PyPI.

## Result

- Overall status: `PASS_AGENT_STANDARD_RULE_LEARNING_DESIGN_READY`
- Next workflow status: `AGENT_STANDARD_FEATURE_TABLE_RUNNER_ALLOWED_FORMAL_SCORING_BLOCKED`
- Rule-learning candidates: `5885`
- Extension-review candidates: `67946`
- Standard level: `agent_standard_candidate_not_national_standard`
- Score values assigned: `0`

## Design Phases

- Phase 1 `feature_table_design`: 5885 rows; output `read_only_agent_standard_feature_table_schema`
- Phase 2 `8105_rule_prior_design`: 5885 rows; output `review_prior_rules_with_support_counts`
- Phase 3 `candidate_bucket_design`: 5885 rows; output `candidate_buckets_no_final_structure`
- Phase 4 `extension_review_holding_design`: 67946 rows; output `extension_review_holding_queue`

## Review Policy

- `candidate_output_level`: agent_standard_candidate_not_national_standard
- `may_emit_final_structure_label`: False
- `may_emit_review_prior`: True
- `may_emit_confidence_bucket`: True
- `may_assign_gf0017_score`: False
- `may_write_cnbe32_fields`: False
- `required_human_review_before_acceptance`: True

## Decision

Agent-standard rule-learning design is ready. The next runner may build read-only feature tables and review priors, but must not emit final structures, scores, or CNBE rows.
