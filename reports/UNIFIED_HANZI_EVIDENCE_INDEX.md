# Unified Hanzi Evidence Index

## Result

- Overall status: `PASS_UNIFIED_EVIDENCE_INDEX_BUILT`
- Next workflow status: `UNIFIED_EVIDENCE_INDEX_AUDIT_REQUIRED_FORMAL_SCORING_BLOCKED`
- Total entries: 97686
- 8105 core entries: 8105
- Outside-8105 Agent candidates: 89581
- Entries with dictionary context: 49085
- Entries with origin context: 9565
- Entries with Cihai context: 5423
- Entries with Wiki context: 11108
- Entries with evidence gaps: 97686

## Boundary

- This index is Unicode-keyed and read-only.
- Dictionary, Cihai, Kangxi/Zhonghua, origin, and Wiki material is review context unless a later gate upgrades a specific item with evidence.
- It does not assign GF0017 scores, emit final structure labels, write CNBE rows, or rebuild SQLite databases.

## Decisions

- May audit unified evidence index: `True`
- May start formal GF0017 scoring: `False`
- May write CNBE rows: `False`
- May rebuild database: `False`

## Review Status Counts

| Status | Count |
|---|---:|
| `OUTSIDE_8105_REVIEW_CONTEXT_AVAILABLE` | 44307 |
| `OUTSIDE_8105_SOURCE_GAP_REVIEW_REQUIRED` | 45274 |
| `READY_FOR_8105_CORE_ITEM_LEVEL_REVIEW` | 8105 |

## Samples

### 一 `U+4E00`

- Scope: `8105_core`
- Review status: `READY_FOR_8105_CORE_ITEM_LEVEL_REVIEW`
- Dictionary context: `True`
- Origin context: `True`
- Wiki hits: 0
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`

### 㐀 `U+3400`

- Scope: `outside_8105_agent_candidate`
- Review status: `OUTSIDE_8105_REVIEW_CONTEXT_AVAILABLE`
- Dictionary context: `True`
- Origin context: `False`
- Wiki hits: 2
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`

### 㐁 `U+3401`

- Scope: `outside_8105_agent_candidate`
- Review status: `OUTSIDE_8105_REVIEW_CONTEXT_AVAILABLE`
- Dictionary context: `True`
- Origin context: `False`
- Wiki hits: 0
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`

### 家 `U+5BB6`

- Scope: `8105_core`
- Review status: `READY_FOR_8105_CORE_ITEM_LEVEL_REVIEW`
- Dictionary context: `True`
- Origin context: `True`
- Wiki hits: 0
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`

### 鑫 `U+946B`

- Scope: `8105_core`
- Review status: `READY_FOR_8105_CORE_ITEM_LEVEL_REVIEW`
- Dictionary context: `True`
- Origin context: `True`
- Wiki hits: 0
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`

### 𲎯 `U+323AF`

- Scope: `outside_8105_agent_candidate`
- Review status: `OUTSIDE_8105_SOURCE_GAP_REVIEW_REQUIRED`
- Dictionary context: `False`
- Origin context: `False`
- Wiki hits: 0
- Score status: `NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY`
