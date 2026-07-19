# Legacy AI-Generated Test Baseline

This directory records the historical status of the pre-restart CNBE catalog.
It does not duplicate the large runtime JSON file because Git already preserves
the exact historical objects.

## Boundary

The pre-restart catalog is treated as a historical test/runtime baseline. It
may be used for:

- regression localization;
- compatibility comparison;
- old experiment reproduction;
- diff review against standards-aligned repairs.

It must not be used as:

- national-standard Hanzi evidence;
- GF0017 scoring authority;
- teaching-ready data;
- research-ready structure, radical, stroke, or decomposition ground truth;
- a source for future CNBE32/CNBE64/CNBE128 release-track fields.

## Current Release-Track Rule

Release-track encoding work starts from Unicode identity and then aligns to the
8105 national-standard core, GF/GB/GG standards, approved Agent review packets,
and explicitly graded cross-reference context.

The current runtime repair path is documented in:

- `reports/8105_CNBE32_RUNTIME_PROMOTION.md`
- `reports/8105_STANDARDIZED_RUNTIME_REPAIR.md`
- `docs/CNBE8105_ENCODING_GOVERNANCE.md`
- `docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`

## Historical Retrieval

Use the manifest in this directory to retrieve exact historical objects from
Git when old experiment reproduction is required.
