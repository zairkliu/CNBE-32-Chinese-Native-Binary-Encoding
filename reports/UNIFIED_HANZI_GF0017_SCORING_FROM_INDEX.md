# GF0017 Scoring From Existing Unified Index

## Result

- Overall status: `PASS_GF0017_SCORING_FROM_EXISTING_INDEX_WITH_SOURCE_GAPS`
- Next workflow status: `GF0017_SOURCE_EVIDENCE_REPAIR_REQUIRED_BEFORE_FULL_SCORING`
- Rows evaluated: 97686
- Rows with any assigned points: 8105
- Fully scored rows: 0
- Rows not scorable from current index: 89581

This run did not regenerate the full Unicode catalog. It used the
existing schema-coded unified evidence index only.

## Boundary

- CNBE rows were not written.
- SQLite databases were not rebuilt.
- Final structure labels were not emitted.
- Missing source evidence was not converted into a numeric zero or pass.

## Row Score Status Counts

| Status | Count |
|---|---:|
| `NOT_SCORABLE_FROM_CURRENT_INDEX` | 89581 |
| `PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE` | 8105 |

## Item Status Counts

### `character_set_coverage`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_SOURCE_GAP` | 89581 |
| `PASS_8105_CORE_COVERAGE` | 8105 |

### `stroke_shape`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_SOURCE_GAP` | 97686 |

### `stroke_order`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |

### `component_validity`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |

### `component_name_validity`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |

### `radical_validity`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |

### `independent_character_rule`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |

### `structure_first_decomposition`

| Status | Count |
|---|---:|
| `NOT_SCORABLE_EVIDENCE_REQUIRED` | 97686 |
