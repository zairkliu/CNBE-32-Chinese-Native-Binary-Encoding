# GF 0017 Normative Scoring Source Map

Role: repository-admin review note

This report records how GF 0017-2013 section 5 should be used to improve
CNBE encoding assessment before any full-scale recoding work. It is a source
map and workflow definition only; it does not modify encoded character data.

## 1. GF 0017 Section 5: Normative Requirements

GF 0017 section 5.1 defines the normative requirements for a literacy-oriented
common-keyboard Chinese character shape input system. For CNBE, these
requirements should become the first-layer scoring gate.

| GF 0017 item | Requirement | Score in Appendix A | CNBE audit meaning |
|---|---|---:|---|
| 5.1.1 编码字符集 | Must include 现代汉语通用字表 and GB 2312 basic-set characters | 3 | The target set must be explicit and missing characters must be counted. |
| 5.1.2 笔形 | Basic stroke-shape types, classification, and order must follow 印刷通用汉字字形表 and 现代汉语通用字表 | 3 | Stroke-shape evidence must be traceable, not inferred by model output. |
| 5.1.3 笔顺 | Must follow GF 3002-1999 GB 13000.1 character stroke-order standard | 3 | Stroke order should be checked against a standard table. |
| 5.1.4 汉字部件 | Components must follow GF 3001-1997 or GF 0014-2009 | 3 | Component existence and component category must be validated. |
| 5.1.5 部件名称 | Component names must follow GF 0014-2009 | 8 | Component naming has a large score weight and must not be hallucinated. |
| 5.1.6 部首 | Radicals must follow GF 0011-2009 | 3 | Radical and radical class should be checked independently. |
| 5.1.7 独体字 | Independent characters must follow GF 0013-2009; if split, they may only split into strokes | 7 | Non-stroke component splits for independent characters are hard errors. |
| 5.1.8 汉字拆分 | Decomposition must start from character structure and follow GF 3001-1997 or GF 0014-2009 | 20 | This is the largest normative score item and should dominate repair priority. |

Appendix A allocates 50 points to language/writing-system normativity, 25 to
code elements and mapping rules, 20 to system functions, and 5 to technical
documentation. The current CNBE remediation should focus first on the 50-point
normativity section.

## 2. Local Knowledge Source Status

The following direct assets exist in the local cnbe-research project and are
usable as authoritative or standard-derived sources:

| Source requirement | Local status | Evidence path |
|---|---|---|
| GF 0017-2013 evaluation rule | Direct source exists | `/Users/liuzhaoqi/Documents/cnbe-research/source/11-评测与分类/GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则.json` |
| GF 3002-1999 stroke order | Direct source exists | `/Users/liuzhaoqi/Documents/cnbe-research/source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.json` |
| GF 0014-2009 components and names | Direct source exists | `/Users/liuzhaoqi/Documents/cnbe-research/source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.json` |
| GF 0013-2009 independent characters | Direct source exists | `/Users/liuzhaoqi/Documents/cnbe-research/source/04-独体字规范/GF 0013-2009 现代常用独体字规范.json` |
| GF 0011-2009 radicals | Direct source exists | `/Users/liuzhaoqi/Documents/cnbe-research/source/02-汉字部首表/GG 0011-2009 汉字部首表.json` |
| GF 3001-1997 / GB 13000.1 components | Direct source exists by title | `/Users/liuzhaoqi/Documents/cnbe-research/source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.json` |
| 通用规范汉字表 8105 | Direct source exists, useful for modern target scope | `/Users/liuzhaoqi/Documents/cnbe-research/source/01-通用规范汉字表/通用规范汉字表(8105).json` |
| GF 0031-2026 stroke order | Direct source exists, useful as newer stroke-order extension | `/Users/liuzhaoqi/Documents/cnbe-research/source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.json` |

The following GF 0017 references are currently not confirmed as standalone
source files in the local project:

| GF 0017 referenced source | Current finding | How to use now |
|---|---|---|
| GB 2312-1980 信息交换用汉字编码字符集·基本集 | Mentioned in GF 0017 OCR and related OCR files; no standalone source file found in this pass | Mark as `referenced_not_direct`; use only for coverage gate after extracting or adding a verified GB2312 table. |
| 现代汉语通用字表 | Mentioned in GF 0017/OCR/Ci Hai/Wikipedia files; no standalone standard file found in this pass | Mark as `referenced_not_direct`; do not claim direct scoring evidence until sourced. |
| 印刷通用汉字字形表 | Mentioned in GF 0017/OCR/Ci Hai/Wikipedia files; no standalone standard file found in this pass | Mark as `referenced_not_direct`; use GF 0031/GF 3002/fold-stroke assets only as support, not replacement. |

## 3. Required Scoring Model

The next CNBE scoring model should separate three layers:

1. Normative evidence layer: Unicode identity, target set membership, stroke
   count, stroke order, stroke shape, component list, component name, radical,
   independent-character status, structure class, and decomposition path.
2. CNBE mapping layer: how the verified normative evidence is encoded into
   CNBE32. Fields that do not fit CNBE32 should be retained as CNBE64/CNBE128
   candidate evidence instead of being forced into the 32-bit layout.
3. Reproducibility layer: every score item must include source file, source
   standard, confidence level, and whether it is direct, derived, or unresolved.

The normativity score should be computed as:

| Score field | Max |
|---|---:|
| character_set_coverage | 3 |
| stroke_shape | 3 |
| stroke_order | 3 |
| component_validity | 3 |
| component_name_validity | 8 |
| radical_validity | 3 |
| independent_character_rule | 7 |
| structure_first_decomposition | 20 |
| total_normativity_score | 50 |

## 4. Current CNBE Weakness Mapping

The previous AI-generated CNBE data should not be judged only by whether it
fits the current 32-bit integer. It must be judged by GF 0017 requirements.

Known weakness classes:

- Wrong or unsupported decomposition directly damages the 20-point
  `structure_first_decomposition` score.
- Wrong component names damage the 8-point `component_name_validity` score.
- Treating independent characters as arbitrary components violates GF 0013 and
  damages the 7-point `independent_character_rule` score.
- Radical mismatch damages the 3-point `radical_validity` score.
- Stroke-count and stroke-order errors damage the 3-point `stroke_order` and
  3-point `stroke_shape` items.
- CNBE32 bit-layout pressure should not override normative evidence. Extra
  evidence should be archived for CNBE64/CNBE128.

## 5. Next Implementation Workflow

Stage 1: Build a `gf0017_source_map` JSON table.

- Record each GF 0017 item.
- Attach direct local source files where present.
- Mark GB2312, 现代汉语通用字表, and 印刷通用汉字字形表 as unresolved direct-source gaps unless standalone verified files are added.

Stage 2: Build a per-character normative baseline for the 8105 scope.

- Unicode code point.
- 8105 rank and level.
- stroke count/order from standard data.
- radical from GF 0011-derived data.
- independent-character status from GF 0013.
- component/decomposition evidence from GF 0014/GF 3001-derived data.

Stage 3: Score existing CNBE records against the GF 0017 50-point section.

- Output per-character itemized deductions.
- Output aggregate score distribution.
- Separate `direct_fail`, `source_gap`, and `needs_human_review`.

Stage 4: Generate repair candidates.

- Only repair fields with direct standard evidence.
- Keep unresolved or conflicting cases in a human-review queue.
- Do not force extended evidence into CNBE32 when CNBE64/CNBE128 is the better archive.

Stage 5: Update skills/workflow.

- Add GF 0017 score vocabulary.
- Add mandatory source-grade labels.
- Require full evidence report for each tested character and each batch audit.
