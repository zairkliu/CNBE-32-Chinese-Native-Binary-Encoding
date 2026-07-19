# 8105 Core Rule To Full Catalog Encoding Plan

## Result

- Overall status: `PASS_8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN_READY`
- Next workflow status: `READY_FOR_300_CHARACTER_PILOT_PLAN_NO_ENCODING_WRITES`
- Total catalog rows: 97686
- 8105 national-standard core rows: 8105
- Outside-8105 Agent-standard candidates: 89581
- May create 300-character pilot plan: `True`
- May start full-catalog encoding: `False`
- May write CNBE rows: `False`
- May rebuild database: `False`

## Core Rule

8105 is the controlling baseline for national-standard claims. Outside-8105 rows may align to 8105-derived project rules only as Agent-standard candidates.

## Evidence Layers

| Layer | Priority | Allowed Use | Forbidden Use |
|---|---:|---|---|
| `national_standard` | 1 | direct or standard-derived evidence after row-level validation | none; this is the only layer for national-standard claims |
| `standard_aligned` | 2 | project-level evidence support and human review after standard alignment | direct national-standard authority or automatic GF0017 scoring |
| `cross_reference_only` | 3 | review navigation, source discovery, semantic disambiguation | final labels, GF0017 points, CNBE row writes, database reconstruction |

## GF0017 Model

| Item | Points | Required Evidence |
|---|---:|---|
| `character_set_coverage` | 3 | 8105 scope decision |
| `stroke_shape` | 3 | GF/GB stroke-shape evidence |
| `stroke_order` | 3 | 通用规范汉字笔顺规范 evidence |
| `component_validity` | 3 | 现代常用字部件规范 evidence |
| `component_name_validity` | 8 | 部件及部件名称规范 evidence |
| `radical_validity` | 3 | 汉字部首表 evidence |
| `independent_character_rule` | 7 | 现代常用独体字规范 evidence |
| `structure_first_decomposition` | 20 | 结构类型 and decomposition evidence |

## Pilot Design

| Stratum | Rows | Purpose | Expected Output |
|---|---:|---|---|
| `8105_core_control` | 100 | prove national-standard core evidence and GF0017 item joins | evidence status and review packet, not rewritten CNBE rows |
| `outside_8105_strong_dictionary_context` | 100 | test 8105-aligned rule transfer with strong dictionary/origin support | Agent-standard candidates requiring human review |
| `outside_8105_extension_or_gap` | 100 | stress-test gaps, extension characters, ZDIC navigation, and stop gates | review queues and blockers, not filled values |

## Stop Gates

- do not generate final structure labels from visual intuition
- do not assign GF0017 scores from cross-reference-only evidence
- do not write CNBE rows before source-evidence merge and audit
- do not rebuild SQLite databases in this planning phase
- do not duplicate the 97,686-row catalog into another XLSX/database
- do not label outside-8105 rows as national-standard outputs

## Decision

The project is ready to plan a bounded 300-character pilot around the frozen 8105 core. It is not ready for full-catalog encoding writes or database reconstruction.
