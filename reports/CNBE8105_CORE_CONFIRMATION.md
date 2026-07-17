# CNBE 8105 Core Confirmation

Overall status: `PASS_CNBE8105_CORE_CONFIRMATION_READY_TO_PUSH`
Next workflow status: `READY_FOR_REMOTE_REVIEW_OF_8105_CORE_CONFIRMATION`

## Scope

- Core: 8105 通用规范汉字表
- Core status: national-standard core
- Outside-8105 status: Agent-standard candidate, not national-standard output

## Confirmed Counts

- Baseline rows: 8105
- Baseline complete rows: 6569
- Baseline review-required rows: 1536
- Current CNBE rows in 8105 scope: 7829
- Missing from current CNBE: 276
- GF0017 average score: 44.4524
- GF0017 min/max score: 33 / 49
- Agent preencoding rows: 20902

## Boundary

- CNBE32 writes are not allowed by this confirmation.
- SQLite database rebuild is not allowed.
- Release and PyPI actions are not allowed.
- Missing evidence is not treated as a pass.
- Full GF0017 scoring remains incomplete until source gaps are resolved.

## Checks

- baseline_row_count_is_8105: `True`
- baseline_row_count_matches_expected: `True`
- comparison_standard_rows_are_8105: `True`
- gf0017_score_rows_are_8105: `True`
- agent_preencoding_is_read_only: `True`
- agent_preencoding_has_no_first_blocker: `True`
- current_cnbe_not_claimed_complete: `True`
- full_gf0017_not_claimed_complete: `True`
