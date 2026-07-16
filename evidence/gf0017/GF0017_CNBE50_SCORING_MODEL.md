# GF0017 50-Point Normativity Scoring Model for CNBE

Role: repository-admin workflow specification

This document maps GF 0017-2013 section 5.1 and Appendix A to the current CNBE
encoding remediation workflow. It is intended for human review before the next
implementation round.

## 1. Purpose

The CNBE encoding work should no longer be judged only by whether a value can
fit the current CNBE32 bit layout. The first professional gate is whether the
character evidence and decomposition process satisfies GF 0017-2013.

The 50-point normativity score becomes the first score for each character:

| GF0017 item | Points | CNBE priority |
|---|---:|---|
| 编码字符集 | 3 | Coverage gate |
| 笔形 | 3 | Stroke-shape evidence gate |
| 笔顺 | 3 | Stroke-order and stroke-count gate |
| 汉字部件 | 3 | Component validity gate |
| 部件名称 | 8 | Component-name evidence gate |
| 部首 | 3 | Radical validation gate |
| 独体字 | 7 | Independent-character split gate |
| 汉字拆分 | 20 | Structure-first decomposition gate |
| Total | 50 | Normativity score |

## 2. Required Character Review Order

Every character must be reviewed in this order:

1. Identify the character and Unicode code point.
2. Confirm character-set scope and rank.
3. Confirm whether the character is an independent character under GF0013.
4. Confirm the allowed structure class.
5. Confirm radical under GF0011.
6. Confirm stroke count, stroke order, and available stroke-shape evidence.
7. Confirm components, component names, and decomposition evidence under
   GF0014/GF3001.
8. Compare those standard fields to the current CNBE row.
9. Assign GF0017 itemized score, status, and repair class.
10. Only after the score is computed, decide whether CNBE32 can store the
    corrected field or whether the evidence must be archived for CNBE64/CNBE128.

## 3. Score Item Mapping

### 3.1 编码字符集: 3 Points

GF0017 requirement:

- The encoding character set should include characters from 现代汉语通用字表 and
  GB 2312-1980.

Current source status:

- GF0017 direct source exists.
- The local 8105 table exists and is useful for current CNBE scope.
- Standalone GB2312, 现代汉语通用字表, and 印刷通用汉字字形表 sources are not yet
  confirmed as independent local files.

CNBE fields:

- Standard side: `char`, `unicode`, `standard_rank`, `level`.
- Current side: `char`, `unicode`, `index`.
- Issue labels: `missing_from_current_cnbe`, `unicode_mismatch`, `out_of_scope`.

Workflow impact:

- A missing character cannot be repaired by changing stroke or structure fields.
- Missing-set errors become the first gate.
- Until direct older-set sources are confirmed, these cases can be marked
  `SOURCE_GAP` rather than final failure.

### 3.2 笔形: 3 Points

GF0017 requirement:

- Basic stroke-shape types, classification, and order follow 印刷通用汉字字形表
  and 现代汉语通用字表.

CNBE fields:

- Standard side: `stroke_order`, `stroke_order_str`, `stroke_count`.
- Current side: `strokes`.
- Issue labels: `stroke_count_mismatch`, `stroke_shape_source_gap`.

Workflow impact:

- CNBE32 can store stroke count, but not the complete stroke-shape evidence.
- Full stroke-shape classification should be archived for CNBE64/CNBE128.
- Do not claim a final stroke-shape score until direct or accepted derived
  evidence is available.

### 3.3 笔顺: 3 Points

GF0017 requirement:

- Stroke order follows GF3002-1999.

CNBE fields:

- Standard side: `stroke_order`, `stroke_order_str`, `stroke_count`.
- Current side: `strokes`.
- Issue labels: `stroke_count_mismatch`, `missing_standard_stroke_count`.

Workflow impact:

- CNBE32 repair may update `strokes`.
- Full stroke-order sequence is evidence and should be preserved even if CNBE32
  only stores the count.

### 3.4 汉字部件: 3 Points

GF0017 requirement:

- Components follow GF3001-1997 or GF0014-2009.

CNBE fields:

- Standard side: `components`, `decomposition`,
  `evidence_sources.component_db`.
- Current side: `struct_name`, `struct_type`.
- Issue labels: `missing_standard_components`, `invalid_component`,
  `ambiguous_decomposition`.

Workflow impact:

- Component validity is a repair gate.
- If components are unresolved, do not auto-rewrite structure or decomposition.

### 3.5 部件名称: 8 Points

GF0017 requirement:

- Component names follow GF0014-2009.

CNBE fields:

- Standard side: `components`, `component_names`.
- Current side: current compact fields plus report-level component names.
- Issue labels: `component_name_mismatch`, `unsupported_component_name`,
  `missing_component_name`.

Workflow impact:

- This item carries 8 points, so unsupported names must be reviewed carefully.
- CNBE32 does not need to store full names, but the report must retain names as
  evidence for the compact code.

### 3.6 部首: 3 Points

GF0017 requirement:

- Radicals follow GF0011-2009 汉字部首表.

CNBE fields:

- Standard side: `radical`, `radix`.
- Current side: `radix`, `radix_name`.
- Issue labels: `radical_mismatch`, `missing_standard_radical`.

Workflow impact:

- `radix_name` repair can be planned when standard radical evidence is direct.
- Numeric radical-code repair requires a separately validated radical-code map.

### 3.7 独体字: 7 Points

GF0017 requirement:

- Independent characters follow GF0013-2009.
- If an independent character is split, it may only be split into strokes.

CNBE fields:

- Standard side: `structure`, `decomposition`, `components`.
- Current side: `struct_type`, `struct_name`.
- Issue labels: `independent_character_non_stroke_split`,
  `structure_mismatch`, `invalid_current_structure`.

Workflow impact:

- A standard-confirmed independent character must not be converted into an
  arbitrary multi-component decomposition.
- Stroke-level archival evidence is allowed.

### 3.8 汉字拆分: 20 Points

GF0017 requirement:

- Decomposition starts from character structure and follows GF3001-1997 or
  GF0014-2009.

CNBE fields:

- Standard side: `structure`, `decomposition`, `components`,
  `decomposition_has_unknown`.
- Current side: `struct_type`, `struct_name`.
- Issue labels: `structure_mismatch`, `invalid_standard_structure`,
  `invalid_current_structure`, `missing_standard_structure`,
  `ambiguous_decomposition`.

Workflow impact:

- This is the largest score item and the main repair target.
- CNBE32 may repair structure type/name only when evidence is complete.
- Full decomposition trees should be kept in reports and extended encodings.

## 4. Character Status Classes

| Status | Meaning |
|---|---|
| PASS | Applicable direct-evidence items pass. |
| FAIL_FIXABLE | Direct-evidence mismatch can be repaired under the approved field policy. |
| FAIL_REVIEW_REQUIRED | There is a likely error, but human review is required. |
| SOURCE_GAP | GF0017 requires a source that has not yet been confirmed as a local direct asset. |
| EVIDENCE_GAP | The character lacks enough standard-side evidence for a final score. |
| OUT_OF_SCOPE | The row is not in the scored character scope. |

## 5. Repair Policy

Auto-fix can be considered only when:

- The mismatch is radical, stroke count, or structure type/name.
- The standard-side evidence is complete.
- The relevant source is direct or accepted as standard-derived.
- The change does not require inventing decomposition or component names.

Human review is mandatory for:

- Ambiguous decomposition.
- Missing standard structure.
- Missing standard radical.
- Component-name mismatch.
- Independent-character split violations.
- Any source-gap item.

Extended archive is mandatory for:

- Full stroke order.
- Stroke-shape classification.
- Complete decomposition tree.
- Component-name evidence.
- Source page/image anchors.

## 6. Implementation Deliverables

The next implementation round should create:

1. `scripts/score_cnbe8105_gf0017_normativity.py`
2. `evidence/gf0017/cnbe8105_gf0017_normativity_scores.json`
3. `evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md`
4. Tests for model totals, score item IDs, source-gap handling, and no-write
   behavior.

The script must be read-only. It may read current CNBE comparison reports and
cnbe-research knowledge assets, but it must not rewrite the CNBE database or
source tables.
