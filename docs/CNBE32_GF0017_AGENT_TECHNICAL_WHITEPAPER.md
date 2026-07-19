# CNBE-32 GF0017 Agent Technical Whitepaper

## Status

This whitepaper records the current standards-aligned CNBE-32 engineering
workflow.

It supersedes historical exploratory claims for active engineering decisions.
It does not delete or rewrite older whitepapers, because those documents remain
useful audit artifacts for understanding how the project moved away from
AI-generated encoding claims.

## Authority Boundary

CNBE-32 is currently treated as a compact carrier for source-backed Hanzi
knowledge.

The carrier is not itself the authority.

Formal evidence must come from national language and writing standards, from
reproducible standard-derived extracts, or from explicitly marked Agent
standard mappings that are never described as national-standard claims.

The active distinction is:

```text
national_standard = direct 8105 / GF / GB / GG source evidence
agent_standard = project-level mapping aligned to 8105 and accepted by Agent gates
```

OCR, dictionary text, Wikipedia, Unihan, Kangxi, Cihai, Hanzi etymology, and
third-party decomposition sources can support review and scholarly context.
They cannot directly control CNBE32 bit fields without a source-grade gate.

## Current Role Of CNBE32

The 32-bit layout remains a useful engineering carrier:

```text
bits 31..24: radical or radical-code carrier
bits 23..19: stroke-count carrier
bits 18..15: structure-type carrier
bits 14..4 : group or catalog index carrier
bits 3..0  : extension flags
```

This layout is not sufficient by itself for research-grade or teaching-grade
encoding.

GF0017 requires language and writing normativity to be evaluated before a
formal encoding row is accepted.

## GF0017 Normativity Gate

The active normativity model uses the GF0017 50-point language-and-writing
portion:

| Item | Points |
|---|---:|
| character_set_coverage | 3 |
| stroke_shape | 3 |
| stroke_order | 3 |
| component_validity | 3 |
| component_name_validity | 8 |
| radical_validity | 3 |
| independent_character_rule | 7 |
| structure_first_decomposition | 20 |

A numeric score without source status is invalid.

`SOURCE_GAP`, `EVIDENCE_GAP`, `REVIEW_REQUIRED`, and `BLOCKER` must remain
visible in every report.

## Full-Catalog Preparation Gates

The full-catalog candidate workbook is:

```text
data/CNBE_编码目录_修复版_v4_fixed.xlsx
```

The workbook has passed these read-only gates:

1. data asset manifest;
2. workbook schema inspection;
3. fixed sample-row inspection;
4. full Unicode identity gate;
5. Agent runtime logic verification;
6. GF0017 preflight plan;
7. GF0017 source mapping;
8. GF0017 join schema;
9. GF0017 blocker reconciliation.
10. structured 8105 knowledge diff packet.

These gates support readiness for source-evidence mapping and blocker review.
They do not establish release readiness.

## Current Quantitative State

Current verified preparation counts:

| Item | Count |
|---|---:|
| v4_fixed data rows | 97,686 |
| v4_fixed workbook columns | 17 |
| GF0017 normativity items | 8 |
| GF0017 total points | 50 |
| join evidence tables | 5 |
| blocker rules | 6 |
| knowledge blockers | 3 |

The 20,902-row legacy CNBE Agent scan also passed Unicode identity, but it
preserved review signals:

| Signal | Count |
|---|---:|
| legacy structure labels requiring localization | 20,902 |
| CNBE32 bitfield review required | 12,864 |
| outside 8105 GF0017 scope | 13,073 |

This is a positive result because the Agent refuses to silently promote legacy
AI-generated rows into formal standard output.

## Current Blockers

Three knowledge asset blockers remain:

1. `Unihan.zip` failed ZIP integrity.
2. `structured/base_character_data.json` has an 8105 membership and Unicode
   label mismatch.
3. `structured/cnbe_character_knowledge.json` has an 8105 membership and
   Unicode label mismatch and
   depends on the base table reconciliation.

These blockers prevent batch GF0017 scoring and database reconstruction.

They do not invalidate the completed Unicode identity gate for `v4_fixed`.

## Decision Boundary

The project may continue automatically through read-only audit, planning,
schema design, report generation, and test creation.

The project must stop for human authorization before:

- deleting or replacing external archives;
- modifying `cnbe-research/knowledge` structured JSON files;
- changing CNBE encoded rows;
- rebuilding SQLite databases;
- running formal full-catalog batch GF0017 scoring;
- publishing release artifacts;
- creating tags or PyPI releases.

## Unified Evidence Index

The current full-catalog evidence layer has been materialized as a read-only
Unicode-keyed index.

Outputs:

- `reports/unified_hanzi_evidence_index.json`;
- `reports/UNIFIED_HANZI_EVIDENCE_INDEX.md`;
- `reports/unified_hanzi_evidence_index_audit.json`;
- `reports/UNIFIED_HANZI_EVIDENCE_INDEX_AUDIT.md`.

Audit result:

| Item | Result |
|---|---:|
| total rows | 97,686 |
| direct 8105 core rows | 8,105 |
| outside-8105 Agent candidates | 89,581 |
| GF0017 scores assigned | 0 |
| final structure labels emitted | 0 |
| CNBE row writes | 0 |
| database rebuilds | 0 |

The index uses schema-coded rows and top-level profiles for repeated evidence
statuses. Dictionary, Cihai, Kangxi/Zhonghua, origin, and Wiki material remains
review context unless a later gate validates a specific item as scoring
evidence.

This audit permits human review preparation. It does not permit formal scoring,
encoding repair, database rebuild, release claims, or publication.

## GF0017 Scoring Start

GF0017 scoring has been started from the existing unified index, without
regenerating the full Unicode catalog.

The scoring pass uses:

```text
reports/unified_hanzi_evidence_index.json
reports/unified_hanzi_evidence_index_audit.json
```

The pass writes:

```text
reports/unified_hanzi_gf0017_scoring_from_index.json
reports/UNIFIED_HANZI_GF0017_SCORING_FROM_INDEX.md
```

Result:

| Item | Count |
|---|---:|
| rows evaluated | 97,686 |
| rows with any assigned points | 8,105 |
| fully scored rows | 0 |
| rows not scorable from current index | 89,581 |
| total assigned points across rows | 24,315 |

The only assigned item in this pass is `character_set_coverage` for direct
`8105_core` rows. The remaining GF0017 items are preserved as not scorable
because the current index contains source gaps or pending evidence.

This means the project has begun standards-based scoring, but it has not yet
completed GF0017 scoring. The next engineering target is source-evidence repair
for stroke shape, stroke order, components, component names, radicals,
independent-character rules, and structure-first decomposition.

## Source-Evidence Repair Start

The first source-evidence repair plan was generated from the existing unified
index and scoring report.

The plan confirms that `structure_first_decomposition` is the highest priority
repair target:

| GF0017 item | Points | Blocked rows |
|---|---:|---:|
| structure_first_decomposition | 20 | 97,686 |
| component_name_validity | 8 | 97,686 |
| independent_character_rule | 7 | 97,686 |

The first repair package materialized structure/decomposition evidence status
for all rows, without assigning points:

| Status item | Count |
|---|---:|
| total rows | 97,686 |
| reviewable or partial rows | 4,580 |
| 8105 standard-join required rows | 8,105 |
| score values assigned | 0 |
| final structure labels emitted | 0 |

This converts a vague "structure evidence missing" blocker into explicit review
queues. It still does not authorize final structure labels, CNBE field repair,
database rebuild, or release claims.

## Bounded Review Packet

The structure/decomposition evidence repair was audited before packet export.
The packet strategy avoids repeating the 97,686-row source table:

| Artifact | Role |
|---|---|
| `reports/gf0017_structure_decomposition_evidence_repair_from_index.json` | source status report |
| `reports/structure_decomposition_evidence_repair_agent_audit.json` | Agent audit |
| `reports/structure_decomposition_review_packet_manifest.json` | packet manifest |
| `reports/structure_decomposition_review_packet.csv` | canonical bounded review CSV |
| `review_packets/structure_decomposition/structure_decomposition_review_packet_EDITABLE.csv` | editable review copy |

The review packet has 212 rows, selected deterministically from the evidence
status queues. It references the full source report by SHA-256 instead of
duplicating it.

Rules:

- do not regenerate the 97,686-row table for review;
- do not create a database for review;
- do not create a new XLSX unless a later human decision explicitly asks for
  one;
- edit only the file marked `EDITABLE`;
- do not treat editable notes as source evidence until a merge-and-audit gate.

## Agent Review Pass

The bounded structure/decomposition packet was reviewed by the Agent without
promoting review notes into evidence:

| Artifact | Role |
|---|---|
| `reports/structure_decomposition_agent_review_result.json` | Agent review summary |
| `reports/STRUCTURE_DECOMPOSITION_AGENT_REVIEW_RESULT.md` | human-readable review report |
| `review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_EDITABLE.csv` | reviewed editable copy |

The Agent review populated triage status, reviewer identity, source references,
and next-action notes for 212 rows. It left structure labels and decomposition
fields blank.

This preserves the project boundary: review notes can guide future human
decisions and merge planning, but they are not GF0017 scores, source evidence,
CNBE rows, or database records.

## ZDIC Snapshot References

The review packet now includes ZDIC online lookup references.

Artifacts:

| Artifact | Role |
|---|---|
| `reports/zdic_reference_snapshot_manifest.json` | ZDIC URL and snapshot manifest |
| `reports/zdic_snapshots/` | representative browser DOM snapshots and viewport PNGs |
| `reports/structure_decomposition_agent_review_zdic_enhancement.json` | enhancement audit |
| `reports/zdic_enhanced_agent_review_packet_validation.json` | ZDIC-enhanced packet boundary validation |
| `review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_ZDIC_EDITABLE.csv` | ZDIC-enriched editable copy |

The ZDIC layer covers the bounded 212-row packet and includes representative
snapshots for `鑫`, `焱`, `㐀`, `㑇`, and `𲎯`.

ZDIC is useful for online review navigation because pages often expose radical,
stroke count, Unicode, stroke order, structure, Kangxi dictionary, and
glyph-origin sections. The project still treats this as cross-reference
context only, not national-standard authority.

The validation gate records ZDIC field gaps explicitly. In the current
snapshot set, `𲎯` exposes core navigation fields but lacks Kangxi, origin, and
structure fields on the captured page. The gap is retained as review metadata
and does not authorize inference, scoring, final labels, CNBE writes, XLSX
generation, or database reconstruction.

## 8105 Core Rule Plan

The next planning gate freezes the 8,105-row 通用规范汉字表 as the
national-standard core for the encoding rewrite.

Artifacts:

| Artifact | Role |
|---|---|
| `reports/8105_core_rule_to_full_catalog_encoding_plan.json` | machine-readable 8105-to-full-catalog plan |
| `reports/8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN.md` | human-readable plan |
| `scripts/plan_8105_core_rule_to_full_catalog_encoding.py` | read-only plan generator |

The plan keeps the full 97,686-row catalog split into 8,105
`national_standard_core` rows and 89,581 outside-8105
`agent_standard_candidate_not_national_standard` rows. It defines three
evidence layers: `national_standard`, `standard_aligned`, and
`cross_reference_only`.

The only authorized next step is designing a bounded 300-character pilot:
100 8105 core controls, 100 outside-8105 rows with strong dictionary/origin
context, and 100 outside-8105 extension or gap rows. Full-catalog encoding,
formal full-row GF0017 scoring, CNBE row writes, database rebuilds, and XLSX
duplication remain blocked.

## 300-Character Pilot Plan

The bounded pilot plan has been generated as a review queue:

| Artifact | Role |
|---|---|
| `reports/300_character_8105_pilot_plan.json` | machine-readable pilot selection |
| `reports/300_CHARACTER_8105_PILOT_PLAN.md` | human-readable pilot plan |
| `review_packets/300_character_8105_pilot/300_character_8105_pilot_plan.csv` | review CSV with blank human fields |
| `scripts/plan_300_character_8105_pilot.py` | deterministic pilot planner |

The pilot contains exactly 300 rows:

- 100 `8105_core_control` rows;
- 100 `outside_8105_strong_dictionary_context` rows;
- 100 `outside_8105_extension_or_gap` rows.

The pilot revealed that the 8105 control rows still require
standard-derived structure/decomposition joins before scoring. This is expected
and useful: it indicates the next step is pilot evidence join, not full-catalog
encoding.

The pilot assigns zero GF0017 points, emits zero final structure labels, writes
zero CNBE rows, creates no database, and creates no XLSX workbook.

## 300-Character Pilot Evidence Join

The pilot evidence join has been generated as a human-review surface:

| Artifact | Role |
|---|---|
| `reports/300_character_pilot_evidence_join.json` | machine-readable joined evidence status |
| `reports/300_CHARACTER_PILOT_EVIDENCE_JOIN.md` | human-readable join report |
| `review_packets/300_character_8105_pilot/300_character_pilot_evidence_join.csv` | joined review CSV |
| `scripts/run_300_character_pilot_evidence_join.py` | read-only join runner |

The join keeps all 300 rows bounded and records context coverage:

- dictionary context rows: 190;
- Yuanliu context rows: 97;
- Cihai context rows: 59;
- Wiki context rows: 18;
- ZDIC URL rows: 300;
- ZDIC snapshot rows: 3.

The joined GF0017 status split is:

- 100 rows pending standard-derived item joins for 8105 controls;
- 102 rows with review context available but not scorable;
- 98 rows in the Agent-standard queue and not scorable.

This evidence join assigns zero GF0017 points, emits zero final structure
labels, writes zero CNBE rows, creates no database, and creates no XLSX
workbook.

## Current Source-Write Result

The structured 8105 knowledge repair was authorized and applied to the local
`cnbe-research` knowledge assets.

The patch created timestamped backups before changing source files:

- `base_character_data.json.bak.20260716T183315Z`
- `cnbe_character_knowledge.json.bak.20260716T183315Z`

The repaired source files now align with the repository 8105 baseline:

- missing baseline characters repaired: `㧐`, `栲`, and `𬺈`;
- extra non-baseline rows removed: space and private-use ``;
- Unicode labels normalized from padded forms such as `U+04E00` to canonical
  forms such as `U+4E00`;
- both structured files now contain 8,105 rows;
- the structured diff packet now reports zero missing rows, zero extra rows,
  and zero Unicode label issues.

The repository manifest was then synchronized to the new external asset
identity. The source audit reports 18 passing sources and no attention items.
The remaining source inventory blocker is the excluded invalid
`knowledge/Unihan.zip` archive. That archive is not treated as scoring
authority and does not justify formal GF0017 scoring by itself.

## Batch Evaluation Result

After the structured repair, the first full-catalog batch evaluation was run as
a source-join assessment, not as formal GF0017 scoring.

The batch contains 97,686 rows:

- 8,105 rows are joined to the repaired 8105 structured baseline and classified
  as `JOINED_8105_STANDARD_DERIVED_KNOWLEDGE`;
- 89,581 rows are outside the 8105 baseline and classified as
  `OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED`;
- row-level Unicode blockers are not present in this source-join pass;
- no numeric GF0017 score values were assigned.

This is the correct intermediate state. It shows the Agent can distinguish
direct 8105 baseline rows from rows that require Agent-standard mapping. It
does not establish that the outside-8105 rows are nationally standardized.

Formal scoring remains blocked because the GF0017 source map still contains:

- two `SOURCE_GAP` items: `character_set_coverage` and `stroke_shape`;
- six `SOURCE_EVIDENCE_REQUIRED` items that require row-level evidence joins
  before points can be assigned.

## Agent-Standard Mapping Plan Result

The read-only Agent-standard mapping plan has been generated for the 89,581
outside-8105 rows.

The plan keeps all outside-8105 rows outside national-standard claims and
classifies them only as Agent-standard mapping candidates.

The outside-8105 rows are stratified as:

- BMP rows: 19,675;
- supplementary-plane rows: 69,906;
- CJK Unified Ideographs: 13,160;
- CJK Unified Ideographs Extension A: 6,515;
- CJK Unified Ideographs Extension B: 42,684;
- CJK Unified Ideographs Extension C: 4,116;
- CJK Unified Ideographs Extension D: 214;
- CJK Unified Ideographs Extension E: 5,666;
- CJK Unified Ideographs Extension F: 7,473;
- CJK Unified Ideographs Extension G: 4,939;
- CJK Unified Ideographs Extension H: 4,192;
- CJK Unified Ideographs Extension I: 622.

The plan includes a deterministic 120-row review sample across Unicode blocks.
It still assigns zero GF0017 points and keeps formal scoring blocked.

The next safe implementation step is a read-only row-level evidence join design
for the six `SOURCE_EVIDENCE_REQUIRED` GF0017 items and the two `SOURCE_GAP`
items.

## Row-Level Evidence Join Result

The row-level evidence join runner has materialized evidence status records for
all 89,581 outside-8105 rows.

The output status is:

- `PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED`;
- zero GF0017 score values assigned;
- zero CNBE row writes;
- no database rebuild.

Every outside-8105 row currently remains in:

- `ROW_SOURCE_GAP_AND_EVIDENCE_JOIN_PENDING`: 89,581 rows.

GF0017 item status counts are:

- `character_set_coverage`: 89,581 rows remain
  `SOURCE_GAP_NOT_SCORABLE`;
- `stroke_shape`: 89,581 rows remain `SOURCE_GAP_NOT_SCORABLE`;
- `stroke_order`: 89,581 rows remain `ROW_LEVEL_EVIDENCE_JOIN_PENDING`;
- `component_validity`: 89,581 rows remain
  `ROW_LEVEL_EVIDENCE_JOIN_PENDING`;
- `component_name_validity`: 89,581 rows remain
  `ROW_LEVEL_EVIDENCE_JOIN_PENDING`;
- `radical_validity`: 89,581 rows remain
  `ROW_LEVEL_EVIDENCE_JOIN_PENDING`;
- `independent_character_rule`: 89,581 rows remain
  `ROW_LEVEL_EVIDENCE_JOIN_PENDING`;
- `structure_first_decomposition`: 89,581 rows remain
  `ROW_LEVEL_EVIDENCE_JOIN_PENDING`.

This result establishes the next engineering target: a source-resolution plan.
It does not authorize formal GF0017 scoring or database reconstruction.

## Source-Resolution Plan Result

The source-resolution plan has been generated.

The plan separates the eight blocked GF0017 items into three classes:

- `POLICY_DECISION_REQUIRED`: 1 item;
- `SOURCE_EXTRACTION_SPEC_REQUIRED`: 1 item;
- `ROW_LEVEL_EXTRACTION_REQUIRED`: 6 items.

The policy decision item is:

- `character_set_coverage`.

The seven items that may continue through read-only extraction-spec work are:

- `stroke_shape`;
- `stroke_order`;
- `component_validity`;
- `component_name_validity`;
- `radical_validity`;
- `independent_character_rule`;
- `structure_first_decomposition`.

All eight items still cover 89,581 blocked outside-8105 rows. The plan allows
row-level extraction-spec design, but it keeps formal GF0017 scoring, CNBE row
writes, and database reconstruction blocked.

The reproducible Agent model is now documented in
`docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md`.

## Row-Level Extraction Specs Result

The row-level extraction specifications have been generated for the seven
automatable GF0017 items:

- `stroke_shape`;
- `stroke_order`;
- `component_validity`;
- `component_name_validity`;
- `radical_validity`;
- `independent_character_rule`;
- `structure_first_decomposition`.

Each extraction spec defines:

- `unicode` as the join key;
- input source paths;
- output table;
- output fields;
- validation rules;
- failure codes;
- the next runner gate.

The extraction specs still assign zero GF0017 points. They allow a future
read-only evidence join runner, but they do not authorize formal scoring,
database reconstruction, or CNBE row writes.

## Row-Level Extraction Runner Result

The read-only row-level extraction runner has materialized extraction-status
records for the seven automatable GF0017 items.

The result is:

- `PASS_ROW_LEVEL_EXTRACTION_STATUS_MATERIALIZED`;
- 89,581 outside-8105 rows covered;
- seven extraction specs applied;
- zero missing source paths;
- zero GF0017 score values assigned;
- zero CNBE row writes;
- no database rebuild.

Every automatable item currently has 89,581 rows in:

- `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.

This means source paths and extraction specifications are available. It does
not mean the actual evidence values have been extracted, reviewed, or scored.

The next safe stage is an evidence-review plan that determines which concrete
parsers should be implemented first.

## Evidence-Review Plan Result

The evidence-review plan has been generated.

The plan prioritizes parser implementation planning in this order:

- `structure_first_decomposition`: 20 points;
- `component_name_validity`: 8 points;
- `independent_character_rule`: 7 points;
- `component_validity`: 3 points;
- `radical_validity`: 3 points;
- `stroke_order`: 3 points;
- `stroke_shape`: 3 points.

The policy decision item remains:

- `character_set_coverage`.

The review plan allows parser implementation planning. It does not assign
GF0017 scores, run formal scoring, rebuild databases, write CNBE rows, or make
outside-8105 national-standard claims.

## Parser Implementation Plan Result

The parser implementation plan has been generated.

The planned parser phases are:

- Phase 1: `structure_first_decomposition`;
- Phase 2: `component_name_validity`;
- Phase 3: `independent_character_rule`;
- Phase 4: `component_validity`;
- Phase 5: `radical_validity`;
- Phase 6: `stroke_order`;
- Phase 7: `stroke_shape`.

Phase 1 would implement a read-only structure/decomposition evidence parser
with a 300-row review sample. This is a decision point because parser
implementation moves from planning into executable extraction logic.

The plan still assigns zero GF0017 points and does not authorize source asset
writes, CNBE row writes, database reconstruction, or formal scoring.

## Phase 1 Structure/Decomposition Parser Result

The Phase 1 read-only parser has been implemented and run.

The parser reads the external `cnbe-research` evidence workspace through
`data/sources/cnbe-research-local.json` and joins by Unicode. It uses
decomposition dictionary evidence, component mappings, and CJK decomposition
cross-references to materialize structure/decomposition evidence statuses for
outside-8105 rows.

Current result:

- outside-8105 rows covered: `89,581`;
- `STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW`: `2,551`;
- `STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED`: `2,029`;
- `STRUCTURE_DECOMPOSITION_EVIDENCE_GAP`: `85,001`;
- score values assigned: `0`.

The failure profile is also evidence-bearing:

- `MISSING_STRUCTURE`: `84,936`;
- `MISSING_DECOMPOSITION_COMPONENTS`: `84,773`;
- `AMBIGUOUS_DECOMPOSITION`: `148`.

This means Phase 1 has not solved structure/decomposition for the full
catalog. It has made the next review surface explicit. The dominant issue is
that outside-8105 extension characters have sparse structure evidence in the
available candidate sources. That gap must remain visible and must not be
converted into GF0017 points or CNBE rows by inference.

The next safe stage is Phase 1 evidence review. Formal GF0017 scoring, source
asset edits, CNBE row writes, and database reconstruction remain blocked.

## Phase 1 Evidence Review Plan Result

The Phase 1 evidence review plan has been generated.

The review queues are:

- `human_review_ready`: `2,551` rows;
- `partial_evidence_review`: `2,029` rows;
- `source_gap_resolution_required`: `85,001` rows.

The dominant blocker is `MISSING_STRUCTURE`.

This confirms that the full-catalog path cannot move directly from parser
output to GF0017 scoring. The next useful engineering step is a source-gap
resolution plan for structure/decomposition evidence. The ready and partial
queues can provide review samples and parser calibration material, but they do
not authorize point assignment or CNBE row repair.

## Structure/Decomposition Source-Gap Resolution Result

The source-gap resolution plan has been generated for the `85,001`
structure/decomposition source-gap rows.

The source policy is now explicit:

- GF/GB/GG and 8105-derived evidence remain the national-standard layer;
- `汉字源流大典` / `yuanliu_chars` can provide character-origin,
  decomposition, etymology, radical, pinyin, and definition clues for review;
- `辞海` can provide dictionary meaning and usage contexts for review;
- offline Chinese Wikipedia can be used only as a lowest-tier cross-reference
  after standard and dictionary sources are insufficient;
- no dictionary, encyclopedia, OCR, or LLM memory source can directly assign
  GF0017 points or write CNBE rows.

Current source-hit result for the `85,001` gap rows:

- `hanzi_yuanliu_chars`: `32`;
- `cihai_search_index`: `32`;
- `definitions_index`: `0`;
- offline Wikipedia file: present, `2,393,692,848` bytes.

The dictionary gap extractor has also produced a review packet:

- `DICTIONARY_AND_YUANLIU_REVIEW_READY`: `2`;
- `YUANLIU_REVIEW_READY`: `30`;
- `DICTIONARY_CONTEXT_REVIEW_READY`: `30`;
- `NO_DICTIONARY_REVIEW_HIT`: `84,939`.

Because dictionary coverage is narrow, the workflow now includes an optional
offline-Wikipedia streaming index plan for the remaining `84,939` rows. This
plan is deliberately lowest-tier and read-only. It is meant for source
discovery and human review, not scoring, encoding, or national-standard claims.

## Offline Wiki Cross-Reference Index Result

The offline Chinese Wikipedia streaming index has been run in read-only mode.

Result:

- target rows: `84,939`;
- articles scanned: `1,489,790`;
- `WIKI_CROSS_REFERENCE_HIT`: `11,108`;
- `NO_WIKI_CROSS_REFERENCE_HIT`: `73,831`;
- elapsed seconds: `65.1`;
- score values assigned: `0`.

These hits are lowest-tier cross-references only. They can help human reviewers
find source-discovery leads, meanings, names, and usage contexts, but they do
not authorize GF0017 scoring, structure acceptance, national-standard claims,
CNBE row writes, or database rebuilds.

The remaining `73,831` rows are still unresolved source gaps and should be
handled by stronger source acquisition, extension-character decomposition
resources, or explicitly retained as non-scorable Agent-standard gaps.

## Remaining Source Acquisition And Agent-Standard Result

The remaining `73,831` rows were audited against local stronger-resource
candidates.

Result:

- stronger authoritative row-level IDS source available: `False`;
- GF/GG/GB sources remain direct standards for rules, but not row-level IDS
  coverage for these extension rows;
- `Unihan2.zip` covers the remaining rows as Unicode cross-reference, not
  structure authority;
- `Unihan.zip` is not a readable ZIP archive and is rejected;
- Kangxi exact dictionary entries hit `28,917` rows, but are dictionary context,
  not modern structure/IDS authority;
- `cjk-decomp` hits `89` rows, but is third-party IDS cross-reference;
- `decomp-data` hits `0` remaining rows.

Therefore the remaining rows have been routed to Agent-standard planning, not
national-standard output:

- `agent_standard_rule_learning_candidate`: `5,885` rows;
- `agent_standard_extension_review_candidate`: `67,946` rows.

This stage still assigns zero GF0017 points and does not write CNBE rows. The
next safe stage is Agent-standard rule-learning design, which may learn from
the audited 8105 baseline and available cross-references but must continue to
label outputs as `agent_standard_candidate_not_national_standard`.

## Agent-Standard Rule-Learning Design Result

The Agent-standard rule-learning design has been generated.

The design uses:

- Unicode identity from previous gates;
- the 13-label Agent structure set;
- the audited 8,105-row baseline as a rule-learning reference;
- GF0017 8105 issue distributions as risk priors;
- available cross-reference presence as review-priority input.

It explicitly does not emit final structure labels.

Result:

- rule-learning candidates: `5,885`;
- extension-review candidates: `67,946`;
- baseline 8105 rows: `8,105`;
- baseline structure distribution includes `左右=4,358`, `上下=1,626`,
  `UNRESOLVED=1,244`, and other approved labels;
- GF0017 8105 status distribution: `FAIL_FIXABLE=6,314`,
  `FAIL_REVIEW_REQUIRED=547`, `EVIDENCE_GAP=1,244`;
- score values assigned: `0`.

The next allowed stage is a read-only Agent-standard feature table runner. It
may emit review priors and confidence buckets, but still must not emit final
structures, formal GF0017 scores, CNBE32 fields, or database rows.

## Agent-Standard Feature Table Result

The Agent-standard feature table runner has been executed.

Result:

- feature rows: `73,831`;
- `agent_standard_rule_learning_candidate`: `5,885`;
- `agent_standard_extension_review_candidate`: `67,946`;
- `review_prior_medium`: `1,080`;
- `review_prior_low_medium`: `4,805`;
- `review_prior_low`: `67,946`;
- score values assigned: `0`;
- final structure labels emitted: `0`.

The feature table materializes identity fields, review queues, review priors,
feature flags, and source-gap failure codes only. It does not contain
`final_structure_label`, `gf0017_score`, or `cnbe32_fields`.

The next safe stage is a review-prior audit. It may verify queue boundaries and
sampling strategy, but it still must not assign formal scores or write CNBE
rows.

## Non-Claims

The current workflow must not claim:

- CNBE-32 has completed national-standard full-catalog encoding;
- CNBE-32 has release-ready coverage for 97,686 characters;
- the legacy workbook is a final database source;
- OCR, dictionary, Wikipedia, or generated CNBE fields are direct standard
  authority;
- Agent-standard mappings are national-standard outputs.

## Reproducible Commands

The current gate chain is reproducible with:

```bash
python3 scripts/verify_cnbe_agent_runtime_logic.py
python3 scripts/plan_full_catalog_gf0017_preflight.py
python3 scripts/map_full_catalog_gf0017_sources.py
python3 scripts/design_full_catalog_gf0017_join_schema.py
python3 scripts/reconcile_full_catalog_gf0017_blockers.py
python3 scripts/diff_structured_8105_knowledge.py
python3 scripts/evaluate_full_catalog_gf0017_batch_readiness.py
python3 scripts/run_full_catalog_gf0017_source_join_batch.py
python3 scripts/plan_full_catalog_agent_standard_mapping.py
python3 scripts/design_full_catalog_agent_mapping_evidence_join.py
python3 scripts/run_full_catalog_agent_mapping_evidence_join.py
python3 scripts/plan_full_catalog_source_resolution.py
python3 scripts/design_full_catalog_row_level_extraction_specs.py
python3 scripts/run_full_catalog_row_level_extraction_specs.py
python3 scripts/plan_full_catalog_evidence_review.py
python3 scripts/plan_full_catalog_parser_implementation.py
python3 scripts/run_structure_decomposition_evidence_parser.py
python3 scripts/plan_structure_decomposition_evidence_review.py
python3 scripts/plan_structure_decomposition_source_gap_resolution.py
python3 scripts/run_structure_decomposition_dictionary_gap_extractor.py
python3 scripts/plan_wikipedia_structure_cross_reference_index.py
python3 scripts/run_wikipedia_structure_cross_reference_index.py
python3 scripts/plan_remaining_structure_source_acquisition.py
python3 scripts/plan_remaining_structure_agent_standard.py
python3 scripts/design_remaining_structure_agent_standard_rule_learning.py
python3 scripts/run_remaining_structure_agent_standard_feature_table.py
python3 scripts/audit_remaining_structure_agent_standard_review_priors.py
python3 scripts/plan_remaining_structure_agent_standard_review_samples.py
python3 scripts/build_remaining_structure_agent_standard_human_review_packet.py
python3 scripts/evaluate_external_dictionary_source_candidates.py
python3 scripts/plan_external_dictionary_context_import.py
python3 scripts/build_external_dictionary_context_staging.py
python3 scripts/run_external_dictionary_context_review_join.py
python3 scripts/plan_dictionary_context_knowledge_merge.py
python3 scripts/merge_dictionary_context_into_cnbe_research_knowledge.py
python3 scripts/validate_format_integrity.py
```

The relevant tests are:

```bash
python3 -m pytest -q \
  tests/test_cnbe_agent_runtime_logic.py \
  tests/test_full_catalog_gf0017_preflight_plan.py \
  tests/test_full_catalog_gf0017_source_mapping.py \
  tests/test_full_catalog_gf0017_join_schema.py \
  tests/test_full_catalog_gf0017_blocker_reconciliation.py \
  tests/test_structured_8105_knowledge_diff_packet.py \
  tests/test_structured_8105_knowledge_patch.py \
  tests/test_full_catalog_gf0017_batch_readiness.py \
  tests/test_full_catalog_gf0017_source_join_batch.py \
  tests/test_full_catalog_agent_standard_mapping_plan.py \
  tests/test_full_catalog_agent_mapping_evidence_join_design.py \
  tests/test_full_catalog_agent_mapping_evidence_join.py \
  tests/test_full_catalog_source_resolution_plan.py \
  tests/test_full_catalog_row_level_extraction_specs.py \
  tests/test_full_catalog_row_level_extraction_results.py \
  tests/test_full_catalog_evidence_review_plan.py \
  tests/test_full_catalog_parser_implementation_plan.py \
  tests/test_structure_decomposition_evidence_parser.py \
  tests/test_structure_decomposition_evidence_review_plan.py \
  tests/test_structure_decomposition_source_gap_resolution_plan.py \
  tests/test_structure_decomposition_dictionary_gap_extractor.py \
  tests/test_wikipedia_structure_cross_reference_index_plan.py \
  tests/test_wikipedia_structure_cross_reference_index.py \
  tests/test_remaining_structure_source_acquisition_plan.py \
  tests/test_remaining_structure_agent_standard_plan.py \
  tests/test_remaining_structure_agent_standard_rule_learning_design.py \
  tests/test_remaining_structure_agent_standard_feature_table.py \
  tests/test_remaining_structure_agent_standard_review_prior_audit.py \
  tests/test_remaining_structure_agent_standard_review_samples.py \
  tests/test_remaining_structure_agent_standard_human_review_packet.py \
  tests/test_external_dictionary_source_candidate_evaluation.py \
  tests/test_external_dictionary_context_import_plan.py \
  tests/test_external_dictionary_context_staging.py \
  tests/test_external_dictionary_context_review_join.py \
  tests/test_dictionary_context_knowledge_merge_plan.py
```

## Current Review-Prior Audit Gate

The latest read-only Agent-standard gate audits the review queues and review
priorities produced for the 73,831 remaining structure rows.

The audit confirms:

- feature rows: 73,831;
- rule-learning queue: 5,885;
- extension-review queue: 67,946;
- review prior medium: 1,080;
- review prior low-medium: 4,805;
- review prior low: 67,946;
- prior mismatches: 0;
- forbidden final/scoring/CNBE fields: 0;
- point-assignment rows: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

This gate permits only a deterministic review-sample planning step. It does not
authorize formal GF0017 scoring, final structure labels, CNBE row writes,
database rebuilding, source-asset modification, tags, releases, or PyPI work.

## Current Review-Sample Plan Gate

The deterministic review-sample plan has also passed. It selects evenly spaced
samples from the audited review-prior buckets:

- total samples: 150;
- review prior medium: 50;
- review prior low-medium: 50;
- review prior low: 50;
- rule-learning queue samples: 100;
- extension-review queue samples: 50;
- duplicate sample keys: 0;
- forbidden final/scoring/CNBE field leaks: 0;
- point-assignment leaks: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

This sample plan is a review packet input only. It does not authorize formal
GF0017 scoring, final structure labels, CNBE row writes, database rebuilding,
source-asset modification, tags, releases, or PyPI work.

## Current Human Review Packet Gate

The human review packet has been generated from the deterministic 150-row
sample and exported to a coding-directory workbook for manual review.

The packet confirms:

- packet rows: 150;
- review prior medium: 50;
- review prior low-medium: 50;
- review prior low: 50;
- rule-learning queue rows: 100;
- extension-review queue rows: 50;
- duplicate keys: 0;
- forbidden final/scoring/CNBE field rows: 0;
- human structure/decomposition prefill rows: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

The workbook is an evidence collection surface only. Human notes entered into
the workbook must be merged and audited in a later gate before any formal
GF0017 score, final structure label, CNBE row write, database rebuild, release,
or PyPI operation is allowed.

## Current External Dictionary Context Gate

Human review found that many sampled characters have entries in Kangxi and
Zhonghua Dazidian resources. Three external repositories were evaluated:

- `leechenhwa2/nlp-han-dicts`: selected as primary structured dictionary
  context source because it provides BSD-2-Clause SQLite databases for Kangxi
  and Zhonghua Dazidian.
- `kanripo/KR1j0048`: retained as supporting Kangxi primary-text witness after
  parser and license review.
- `he426100/kangxi`: retained only as secondary comparison because the local
  snapshot has no license file and the README warns that one packaged database
  has data errors.

The selected staging database contains:

- staged rows: 68,395;
- unique chars: 49,085;
- Kangxi context rows: 48,708;
- Zhonghua Dazidian context rows: 19,687.

This database lives under `build/dictionary_context_staging/` and is not a
formal `cnbe-research/knowledge` import. Dictionary entries are cross-reference
context for human review and source-gap resolution, not national-standard
structure authority and not GF0017 scoring evidence by themselves.

## Current Dictionary Context Review Join Gate

The staged dictionary context has been joined to the human-review packet and
remaining Agent-standard rows:

- dictionary context unique chars: 49,085;
- human-review packet rows: 150;
- human-review dictionary hits: 104;
- human-review dual-source hits: 61;
- human-review single-source hits: 43;
- human-review dictionary gaps: 46;
- remaining Agent-standard rows: 73,831;
- remaining dictionary hits: 28,960;
- remaining dictionary gaps: 44,871.

The join output is an evidence-review aid only. It provides Kangxi and Zhonghua
Dazidian previews for reviewers, but it still does not write
`cnbe-research/knowledge`, assign GF0017 points, emit final structure labels,
or repair CNBE rows.

## Current Dictionary Context Knowledge Merge Plan

The official knowledge merge plan is ready but not executed. The selected
strategy is to create a separate structured index:

```text
/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json
```

This keeps dictionary context separate from the 8,105-row national-standard
core files:

- staging rows: 68,395;
- unique chars: 49,085;
- overlapping 8105 base chars: 7,321;
- outside-8105 chars: 41,764;
- `base_character_data.json`: unchanged by plan;
- `cnbe_character_knowledge.json`: unchanged by plan.

The plan requires explicit authorization before any write to
`cnbe-research/knowledge`. The future authorized merge must create backups and
update `references.json`; it still must not assign GF0017 scores, emit final
structure labels, repair CNBE rows, or rebuild databases.

## Current Dictionary Context Authorized Merge Script Gate

The authorized merge script exists and has passed dry-run. A normal invocation
prepares the 49,085-entry dictionary-context index and writes only report
artifacts. It does not create the real target index.

Official `cnbe-research/knowledge` writes require both `--execute` and an exact
authorization token. The permitted write set remains narrow:

- create `knowledge/structured/dictionary_context_index.json`;
- backup and update `knowledge/references.json`.

The script does not modify `base_character_data.json` or
`cnbe_character_knowledge.json`, and it does not assign GF0017 scores, emit
final structure labels, repair CNBE rows, or rebuild databases.

## Current Dictionary Context Knowledge Merge Audit

The dictionary-context knowledge merge has now executed under explicit
authorization and passed post-merge audit.

Audit result:

- status: `PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED`;
- target index entries: 49,085;
- references entries: 9;
- reference key: `reference_9`;
- backup: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/references.json.bak.20260717T031651Z`;
- `base_character_data.json` hash unchanged: true;
- `cnbe_character_knowledge.json` hash unchanged: true;
- score values assigned: 0;
- final structure labels emitted: 0;
- CNBE rows written: 0;
- database rebuilds: 0.

The new knowledge file is:

```text
/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json
```

It is a cross-reference dictionary context index. It does not alter the 8,105
national-standard core and does not authorize scoring, final labels, CNBE row
repair, database reconstruction, release, or publication.

## Current Post-Merge Source Revalidation

After the authorized dictionary-context knowledge merge, the local
`cnbe-research` source gates were rerun:

- knowledge inventory files: 226;
- JSON parse pass: 218 / 218;
- source audit pass: 18;
- source audit attention: 0;
- blocker count: 1;
- encoding generation gate: `NO_GO`;
- SQLite build gate: `NO_GO`.

The legacy `Unihan.zip` fails zip integrity, but the manifest-pinned canonical
`Unihan2.zip` passes size, hash, and zip checks. The legacy archive is now an
excluded warning rather than a blocker.

Current gates:

- knowledge inventory: `PASS_WITH_NOTES`;
- source audit: `PASS`;
- encoding generation: `REVIEW_REQUIRED`;
- SQLite build: still not allowed.

This opens the path for evidence-index design only. It does not open formal
GF0017 scoring, CNBE row writes, database reconstruction, release, or
publication.

## Current Unified Evidence Index Plan

The project now has a plan for a Unicode-keyed evidence graph:

- status: `PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY`;
- full catalog rows: 97,686;
- unique Unicode values: 97,686;
- 8105 national-standard core rows: 8,105;
- dictionary context entries: 49,085;
- Yuanliu index entries: 9,574;
- Cihai index entries: 5,423.

The graph is designed to connect evidence layers without mixing authority
levels. Dictionary, Yuanliu, Cihai, and Wiki data remain review and
cross-reference context unless a later gate explicitly promotes a specific
item-level source status. The plan permits only read-only evidence-index
materialization. It does not permit formal GF0017 scoring, final labels, CNBE
row writes, database reconstruction, release, or publication.

## Current Regression Maintenance Note

The source-asset blocker count is not a permanent constant. Earlier reports
preserved three blockers, but authorized structured-knowledge repair reduced
the current inventory blocker set to the remaining critical blocker
`Unihan.zip`. Regression tests now assert consistency with the live inventory
and preserve named critical blockers instead of hard-coding historical totals.

## Engineering Conclusion

The project has moved from historical AI-generated encoding experiments into a
standards-aligned Agent workflow.

The next engineering value is not a new encoding table. The next value is a
reviewable evidence join layer that can explain, for every character, what is
known from national standards, what is project-level Agent mapping, what is
only context, and what must stop the batch.

## 8105 Core Standard-Source Join Pilot

The current pilot adds a bounded 100-row `8105_core_control` standard-source
join. It reads the existing 300-character pilot evidence join and the local
structured 8105 baseline, then records which GF0017 inputs are already
available from standard-derived 8105 data.

Result:

- status: `PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY`;
- rows: 100;
- `base_character_data.json` coverage: 100 / 100;
- Unicode matches: 100 / 100;
- stroke count/order joined: 100 / 100;
- structure source extraction still required: 100 / 100;
- decomposition source extraction still required: 100 / 100;
- GF0017 points assigned: 0;
- final structure labels emitted: 0;
- CNBE rows written: 0.

This is a quality boundary. The 8105 baseline currently gives Unicode
identity, standard level/rank, stroke count, and stroke order. The local
`cnbe_character_knowledge.json` file adds dictionary context, but it does not
supply source-audited structure or decomposition fields for this pilot.
Therefore the next engineering step is a separate standards-source extraction
plan for structure and decomposition, not scoring or encoding.

## Dedicated Decomposition Skill

The Agent workflow now has a dedicated structure/decomposition skill:

```text
/Users/liuzhaoqi/.codex/skills/cnbe-hanzi-decomposition-standardizer
```

Its role is to sit between the total-control Agent and GF0017 scoring:

```text
Unicode identity
-> standard-source evidence join
-> cnbe-hanzi-decomposition-standardizer
-> cnbe-gf0017-batch-audit
-> later CNBE candidate generation
```

The dedicated skill owns:

- raw and normalized structure-label handling;
- decomposition tree status;
- character, non-character, and basic component categories;
- component-name status;
- single-component conflict checks;
- blocker and resume fields;
- no-score/no-write output schema.

This separation prevents the project from using dictionary definitions, ZDIC,
Wiki, visual memory, or historical AI-generated CNBE rows as substitutes for
standard-source structure/decomposition evidence.

## 8105 Core Structure/Decomposition Extraction Plan

The repository now has a bounded extraction plan for the 100-row
`8105_core_control` pilot:

- status: `PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY`;
- standard source files available: 8 / 8;
- handoff rows: 100;
- Unicode identity pass rows: 100;
- structure source-required rows: 100;
- decomposition source-required rows: 100;
- component-name source-required rows: 100;
- GF0017 points assigned: 0;
- final structure labels emitted: 0;
- CNBE rows written: 0.

The plan produces a standardizer handoff CSV rather than an encoding table:

```text
review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv
```

The next permitted engineering step is a bounded standardizer extraction run
that tries to attach standard-source evidence and blocker statuses. It is still
not formal GF0017 scoring and not a CNBE rewrite.

## 8105 Core Pilot Partial GF0017 Scoring

The project has now started bounded GF0017 scoring for the 100-row 8105 core
pilot. This is partial scoring, not a complete 50-point result:

- status: `PASS_8105_CORE_PILOT_GF0017_PARTIAL_SCORING_READY`;
- rows evaluated: 100;
- rows partially scored: 100;
- rows fully scored: 0;
- assigned max per row: 6 / 50;
- assigned items: `character_set_coverage`, `stroke_order`;
- blocked items: `stroke_shape`, `component_validity`,
  `component_name_validity`, `radical_validity`,
  `independent_character_rule`, `structure_first_decomposition`;
- final structure labels emitted: 0;
- CNBE rows written: 0.

The scoring rule is deliberately conservative: missing evidence is neither
scored as zero nor treated as a pass. The remaining 44 points per row require
bounded standardizer extraction and evidence audit before they can be scored.

## 8105 CNBE32 Runtime Promotion

The project later received explicit human authorization to promote the
force-approved 8105 CNBE32 runtime copy into the package runtime data.

The promotion is reproducible from the following chain:

```text
hanzi_decomp_v0.3 adapter
-> human-approved 8105 Agent structure packet
-> repository structure-model merge
-> CNBE32 dry-run patch
-> human force approval
-> copied-dataset write plan
-> runtime promotion
```

Runtime promotion outputs:

- status: `PASS_8105_CNBE32_RUNTIME_PROMOTED`;
- runtime source rows: 20,902;
- 8105 dry-run rows patched into runtime: 6,712;
- force-approved but not patched rows retained for later strategy: 1,393;
- rebuilt root database: `data/cnbe32.db`;
- rebuilt packaged database: `src/cnbe32/data/cnbe32.db`;
- release, tag, and PyPI publication: not performed.

Known promoted samples:

| Character | Radical | Strokes | Structure | Structure type |
|---|---|---:|---|---:|
| 家 | 宀 | 10 | 上下 | 1 |
| 侵 | 亻 | 9 | 左右 | 3 |
| 偶 | 亻 | 11 | 左右 | 3 |
| 孓 | 子 | 3 | 独体字 | 0 |

The `1393` retained rows are not silently invented. They remain categorized by
the preserved dry-run reasons: `964` missing approved radicals, `276` missing
current-model rows, and `153` non-conservative radical mappings.
