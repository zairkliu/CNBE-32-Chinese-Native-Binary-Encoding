# Remaining Structure Agent-Standard Feature Table

## Purpose

This report materializes read-only feature rows for remaining
Agent-standard structure candidates. It emits review queues and review
priors only.

It does not assign GF0017 scores, emit final structure labels, modify
source assets, write CNBE rows, rebuild databases, create tags, publish
releases, or upload to PyPI.

## Result

- Overall status: `PASS_AGENT_STANDARD_FEATURE_TABLE_READY`
- Next workflow status: `AGENT_STANDARD_REVIEW_PRIOR_AUDIT_ALLOWED_FORMAL_SCORING_BLOCKED`
- Feature rows: `73831`
- Standard level: `agent_standard_candidate_not_national_standard`
- Score values assigned: `0`
- Final structure labels emitted: `0`

## Review Queue Counts

- `agent_standard_extension_review_candidate`: 67946
- `agent_standard_rule_learning_candidate`: 5885

## Review Prior Counts

- `review_prior_low`: 67946
- `review_prior_low_medium`: 4805
- `review_prior_medium`: 1080

## Decision

Read-only Agent-standard feature rows are materialized. The next step may audit review priors, but final structures, GF0017 points, and CNBE rows remain blocked.
