# Data Reproducibility Contract

This document records the release-track data contract for CNBE-32 after the
`v1.0.4` standards restart. It closes the ambiguity between runtime databases,
text source catalogs, review evidence, and local research assets.

## Current Committed Runtime Chain

The current package runtime is not a standalone binary-only artifact. The
release-track chain is:

1. `data/cnbe32.json`
2. `data/cnbe32.db`
3. `src/cnbe32/data/cnbe32.db`
4. `reports/8105_CNBE32_RUNTIME_PROMOTION.md`
5. `reports/8105_STANDARDIZED_RUNTIME_REPAIR.md`

The JSON source, root SQLite database, and packaged SQLite database are tracked
repository files. The package database is the file installed in the wheel. The
root database is kept as the source-checkout runtime copy used by local tests
and reproduction scripts.

## Authorized Builders

Runtime database writes must go through scripts that declare their evidence
inputs and rebuild both SQLite copies deterministically:

- `scripts/promote_8105_cnbe32_copy_to_runtime.py`
- `scripts/apply_8105_standardized_runtime_repair.py`

These scripts write `data/cnbe32.json`, rebuild `data/cnbe32.db`, rebuild
`src/cnbe32/data/cnbe32.db`, and emit compact reports. They must not be replaced
by ad hoc SQLite edits.

## Review Boundary

Reports, review packets, and Agent-standard outputs do not automatically modify
runtime data. A source-table write or database rebuild is a separate authorized
implementation round. The minimum review packet for such a round is:

- Unicode identity gate result;
- evidence source list;
- changed row count;
- unchanged row count;
- rejected or blocked row count;
- generated JSON report;
- generated Markdown report;
- SQLite integrity result for both database copies;
- test output for the relevant runtime and governance tests.

## Runtime Structure Guardrail

`spec/struct_types.json` records the structure labels accepted by the current
runtime database and the national-standard review target. This is a compatibility
guardrail, not a claim that all legacy rows are already nationally standardized.

Future structure migrations must update the spec, the runtime JSON, both SQLite
databases, and the related tests in the same pull request.

## Non-Goals

This contract does not:

- claim validated 97,686-row coverage;
- promote outside-8105 Agent-standard candidates to national-standard rows;
- remove human review from source-table writes;
- authorize PyPI publication, tags, or GitHub releases;
- require private local `cnbe-research` files for ordinary package tests.

## Verification Commands

Before merging a data-contract or runtime-data pull request, run:

```bash
python scripts/validate_format_integrity.py
python scripts/validate_doc_version.py
python -m pytest tests/test_doc_version.py tests/test_struct_types_spec.py tests/test_8105_cnbe32_runtime_promotion.py
git diff --check
```

If the local `cnbe-research` workspace is unavailable, ordinary package and
repository tests must still pass. Integration tests that require private local
knowledge sources should skip cleanly.
