---
name: cnbe-hanzi-structure-encoding-agent
description: Orchestrate authoritative, professional, reproducible CNBE Hanzi structure encoding work by coordinating cnbe-standard-skill, cnbe-hanzi-knowledge-builder, and cnbe-gf0017-batch-audit. Use when designing, auditing, or generating CNBE32/CNBE64/CNBE128 Chinese character structure encoding rules, batch plans, repair candidates, Unicode alignment gates, evidence schemas, GF0017 scoring, checkpointed review workflows, or research-grade encoding reports.
---

# CNBE Hanzi Structure Encoding Agent

## Role

Act as the total-control agent for CNBE Hanzi structure encoding. Do not replace
the lower-level skills. Coordinate them in order so encoding work is based on
standard evidence, reproducible Hanzi knowledge, and GF0017 audit gates.

The encoding stack is:

```text
Unicode identity
-> authoritative source evidence
-> Hanzi knowledge schema
-> Hanzi structure/decomposition standardizer
-> GF0017 50-point audit
-> CNBE Agent encoding standard and legacy localization
-> 8105 rule-learning transfer when direct evidence is absent
-> CNBE32 candidate fields
-> CNBE64/CNBE128 extended archive
```

## Required Skill Chain

Use these skills as the conceptual pipeline:

1. `cnbe-standard-skill`
   - Location: `/Users/liuzhaoqi/Documents/cnbe-research/cnbe-standard-skill`
   - Purpose: authoritative source and evidence engineering.
   - Use for national standards, OCR/source status, source grades, dictionary
     and encyclopedia cross-references, and evidence boundaries.

2. `cnbe-hanzi-knowledge-builder`
   - Location: `/Users/liuzhaoqi/Documents/cnbe-research/cnbe-hanzi-knowledge-builder`
   - Purpose: Hanzi knowledge schema construction.
   - Use for strokes, stroke shapes, stroke order, components, component names,
     radicals, side components, glyph forms, independent characters, structure,
     and decomposition.

3. `cnbe-hanzi-decomposition-standardizer`
   - Location: `/Users/liuzhaoqi/.codex/skills/cnbe-hanzi-decomposition-standardizer`
   - Purpose: dedicated structure and decomposition evidence standardization.
   - Use for structure labels, decomposition trees, character components,
     non-character components, basic components, component names,
     single-component conflict checks, and no-score review packets.

4. `cnbe-gf0017-batch-audit`
   - Location: `/Users/liuzhaoqi/.codex/skills/cnbe-gf0017-batch-audit`
   - Purpose: batch quality gate and checkpoint discipline.
   - Use for Unicode-first batch auditing, GF0017 50-point scoring,
     stop-on-blocker behavior, and resume rules.

## Hard Rules

- Always start with Unicode alignment.
- Treat `v1.0.4` as the current published SDK checkpoint: it publishes the
  20,902-row runtime package and 8105 standards-restart runtime repair state,
  but it does not publish 97,686-row validation or outside-8105
  national-standard claims.
- Do not generate CNBE fields from visual intuition or LLM memory.
- Do not treat OCR, Wikipedia, dictionary text, or generated CNBE fields as
  direct standard authority.
- Completely discard legacy CNBE structure fields during structure generation.
  They may appear only in separated error-localization reports and must never
  become candidate structure evidence.
- Use only the three-tier evidence path for structure work:
  national standard -> core reference files -> network/dictionary
  cross-reference. Network/dictionary evidence is review context only.
- Use programmatic network-reference extraction before asking the model to
  analyze a glyph manually. For ZDIC pages, call
  `scripts/extract_zdic_structure_references.py` or an equivalent cached
  extractor and record parser gaps explicitly.
- Do not let CNBE32 bit pressure override Hanzi evidence.
- Treat 8105 as the national-standard baseline for this project.
- Treat 8105-learned mappings that pass the Agent gates as Agent standard
  outputs for CNBE project use. Do not present them as national-standard
  outputs.
- Do not continue a batch after a blocker.
- Do not rewrite CNBE databases or source encoding tables unless the user
  explicitly authorizes that implementation phase.
- For legacy full-catalog workbooks, proceed through the fixed gate order:
  asset manifest -> workbook schema inspection -> fixed sample rows -> full
  Unicode identity gate -> source evidence and GF0017 gates. Do not skip from a
  workbook directly to database reconstruction.
- In continuous repository-maintenance mode, proceed automatically through
  read-only plans, audits, schemas, reports, tests, skill updates, and
  whitepaper updates. Stop for human authorization before writing source
  encoding tables, modifying `cnbe-research/knowledge` assets, rebuilding
  databases, starting formal full-catalog batch scoring, pushing, tagging,
  releasing, or publishing to PyPI.

## Current Standard Artifacts

When working in the CNBE repository, load or regenerate these artifacts before
candidate generation:

```text
evidence/agent-standard/cnbe_agent_encoding_standard.json
evidence/agent-standard/CNBE_AGENT_ENCODING_STANDARD.md
evidence/agent-standard/cnbe_legacy_structure_localization.json
evidence/agent-standard/CNBE_LEGACY_STRUCTURE_LOCALIZATION.md
```

These define the Agent standard, not national standards. The 8105 and cited
GF/GB/GG files remain the national-standard baseline.

## Agent Workflow

### Stage 0: Manifest

Define:

- task type: single character, sample, 8105 batch, full CJK, repair pass, or
  research report
- target encoding: CNBE32, CNBE64, CNBE128, or evidence-only
- source files and expected row count
- output reports
- checkpoint path if batch work is involved

Every Agent run must also declare this invocation contract before reading or
writing batch outputs:

```text
run_id
operator_role
input_scope
input_artifacts
unicode_gate
authority_order
allowed_outputs
forbidden_outputs
stop_conditions
verification_commands
```

If the contract is absent, conflicts with repository governance, or fails to
separate read-only review work from source writes, database rebuilds, tags,
GitHub releases, or PyPI publication, stop and request a corrected contract.

### Stage 1: Unicode Identity Gate

For every character, record:

- `char`
- `unicode` as `U+XXXX` or wider
- integer `codepoint`
- normalization status
- variant/simplified/traditional note when relevant
- target-scope membership

Stop if identity is ambiguous.

For legacy workbook batches, Stage 1 must first be run as a read-only gate. The
gate may read every row, but it must not rewrite the workbook, database, or
encoding table. A passing identity gate should report row count, unique
Unicode count, unique character count, duplicate samples, sequence gaps, and a
per-row identity summary when the output size is acceptable.

The current full-catalog workflow has these read-only continuation stages after
Unicode identity:

```text
Agent runtime verification
-> GF0017 preflight plan
-> GF0017 source mapping
-> GF0017 join schema
-> GF0017 blocker reconciliation
-> structured 8105 knowledge diff packet
-> authorized structured 8105 knowledge patch when required
-> batch readiness evaluation
-> full-catalog source-join batch assessment
-> outside-8105 Agent-standard mapping plan
-> row-level evidence join design
-> row-level evidence status materialization
-> source-resolution plan
-> row-level extraction specs
-> row-level extraction runners
-> evidence-review plan
-> parser implementation plan
-> Phase 1 parser implementation decision
-> Phase 1 structure/decomposition parser
-> Phase 1 evidence-review decision
-> structure/decomposition source-gap resolution plan
-> dictionary/character-origin review packet
-> optional offline-Wikipedia lowest-tier cross-reference index plan
-> offline-Wikipedia lowest-tier cross-reference index
-> remaining structure source acquisition plan
-> remaining structure Agent-standard plan
-> Agent-standard rule-learning design
-> Agent-standard feature table runner
-> Agent-standard review-prior audit
-> Agent-standard deterministic review sample plan
-> Agent-standard human-review packet
-> external dictionary context source evaluation
-> external dictionary context staging
-> external dictionary context review join
-> dictionary context official knowledge merge plan
-> dictionary context authorized merge script dry-run
-> dictionary context official knowledge merge audit
```

These stages may be created and tested without human confirmation because they
do not modify source assets or score rows, except the structured knowledge patch
stage, which requires explicit human authorization before it writes
`cnbe-research/knowledge`. They must keep formal batch GF0017 scoring and
database reconstruction blocked until source evidence joins are complete. A
source-join batch may classify rows as 8105-derived or Agent-mapping-required,
but it must not assign GF0017 points. The Agent-standard mapping plan may
stratify outside-8105 rows by Unicode block, plane, and evidence status, but it
must keep those rows labeled as project Agent mappings rather than
national-standard outputs.
The row-level evidence join may materialize per-row item statuses, but if any
item remains `SOURCE_GAP_NOT_SCORABLE` or
`ROW_LEVEL_EVIDENCE_JOIN_PENDING`, the next stage is source resolution rather
than scoring.
The source-resolution plan may authorize read-only extraction-spec design for
automatable items, but policy items such as character-set coverage remain
human-decision gates before scoring.
Extraction specs define parsers, output fields, validation rules, and failure
codes for automatable items. They do not authorize point assignment.
Extraction runners may confirm that source paths and specifications are
available for each row and item, but they do not mean evidence values have been
extracted or reviewed. If runner outputs remain pending, route to an
evidence-review plan rather than scoring.
Evidence-review plans may prioritize concrete parser implementation work, but
they still do not authorize point assignment, database rebuilds, CNBE row
writes, or national-standard claims for outside-8105 rows.
Parser implementation plans may define phases and runner names. Moving from the
plan to Phase 1 parser execution is a decision point that should be surfaced to
the user before continuing.
When Phase 1 parser execution is authorized, it must remain read-only. It may
materialize structure/decomposition evidence statuses from `cnbe-research`
candidate sources, but it must not assign GF0017 points, modify source assets,
write CNBE rows, or rebuild databases. A dominant evidence gap is a valid
parser result and must be routed to evidence review rather than filled by
visual intuition or LLM memory.
Phase 1 evidence review may split parser output into human-review,
partial-review, and source-gap queues. If source-gap rows dominate, route to a
source-gap resolution plan. Do not use review queue membership as a score.
For source-gap resolution, use standards first. If standards are insufficient,
the Agent may add `汉字源流大典`/`yuanliu_chars` and `辞海` as review
context, and only then offline Chinese Wikipedia as a lowest-tier
cross-reference. These sources can support source discovery and human review,
but they must not become direct national-standard authority, GF0017 scores, or
CNBE row writes.
For 8105 gap auto-fill work, the default priority is:
existing 8105 standard-side fields -> `yuanliu_chars` -> local `辞海` search
index -> offline Chinese Wikipedia -> ZDIC only as a final optional network
reference. Do not let ZDIC outrank local dictionary and origin resources.
`辞海` and Wiki context may be attached to review packets, but they must not
assign structure labels. `yuanliu_chars` may propose a review candidate only
when its structure label is in the approved 13-label set and its IDS operator
maps back to the same structure. Otherwise keep the row in a review queue.
Offline Wiki index output must remain bounded review context. Rows still
without Wiki, dictionary, or source-derived clues should be routed to source
acquisition planning or retained as non-scorable gaps; do not fill them from
visual intuition.
If source acquisition finds no stronger authoritative row-level IDS resource,
route the remaining rows to Agent-standard planning. Unihan, Kangxi, cjk-decomp
and similar resources can support cross-reference or review queues, but they
must not be described as national-standard structure authority. Agent-standard
outputs remain `agent_standard_candidate_not_national_standard` until later
gates explicitly approve them as project-level outputs.
Agent-standard rule-learning design may define feature tables, priors,
confidence buckets, and review queues. It must not emit final structure labels,
GF0017 scores, CNBE32 fields, source-asset edits, or database rows.
Agent-standard feature table runners may materialize review queues and prior
buckets. They must keep final structure labels, GF0017 points, and CNBE fields
absent from row records. If the table passes, route to review-prior audit.
Agent-standard review-prior audits may verify feature-row coverage, queue
counts, prior bucket counts, mismatch counts, and forbidden-field absence. They
must keep formal scoring, final labels, source-asset edits, CNBE row writes, and
database rebuilds blocked. If the audit passes, route to deterministic review
sample planning rather than scoring.
Agent-standard deterministic review sample plans may select reproducible sample
rows from audited prior buckets. They must keep the packet evidence-only and
must not assign GF0017 points, emit final structure labels, write CNBE rows,
modify source assets, or rebuild databases.
Agent-standard human-review packets may export samples to JSON, CSV, Markdown,
or XLSX for manual evidence intake. They must keep all human structure,
decomposition, and evidence fields blank before review and must not convert
reviewer notes into scores or encoding rows without a later merge-and-audit
gate.
External dictionary context source evaluations may compare Kangxi and Zhonghua
Dazidian resources for human-review support. Prefer licensed structured sources
for staging; keep unlicensed or quality-flagged sources as comparison only.
Dictionary context remains cross-reference evidence, not national-standard
structure authority, GF0017 points, final labels, or CNBE row writes.
External dictionary context review joins may attach Kangxi and Zhonghua
Dazidian previews to human-review packets and count coverage for remaining
Agent-standard rows. They must keep previews as review context and must not
promote them to scores, final structures, CNBE rows, or official knowledge
imports.
Dictionary context official knowledge merge plans may define how to create a
separate `dictionary_context_index.json` and update references. They must not
write `cnbe-research/knowledge` until explicit authorization, and they must keep
the 8105 core files separate from dictionary cross-reference context.
Dictionary context authorized merge scripts may be generated and dry-run before
authorization. The dry-run must build the planned index in memory, prove that
the real target index was not written, and require both an execute flag and an
exact authorization token before any official `cnbe-research/knowledge` write.
Dictionary context official knowledge merge audits may verify an authorized
write after it occurs. The audit must prove that only the separate dictionary
context index and references file changed, that 8105 core files stayed
unchanged, and that dictionary context remains cross-reference-only evidence.
Legacy source artifacts may be downgraded from blockers to warnings only when a
canonical replacement source passes identity and integrity checks. A
`REVIEW_REQUIRED` gate allows evidence-index design, but it still does not
authorize formal GF0017 scoring, CNBE row writes, or database reconstruction.
Unified Hanzi evidence index plans may define a Unicode-keyed evidence graph
that links national-standard core data, dictionary context, origin context,
Wiki context, legacy CNBE rows, and Agent-standard context. The plan authorizes
only read-only index materialization, not scores, final labels, CNBE row writes,
or database reconstruction.
Unified Hanzi evidence index builders should store the full 97,686-row index in
a schema-coded representation with top-level profiles for repeated statuses.
Do not emit repeated nested evidence objects that make the report too large for
repository review. The index audit may verify counts, profile references,
sample details, and stop-gate flags. A passing audit authorizes human review
preparation only; it still does not authorize formal GF0017 scoring, final
structure labels, CNBE row writes, or database reconstruction.
When formal GF0017 scoring is explicitly authorized after the unified index
audit, score from the existing unified index rather than regenerating the full
Unicode catalog. Assign points only for items supported by the current index
evidence. Preserve `NOT_SCORABLE_SOURCE_GAP` and
`NOT_SCORABLE_EVIDENCE_REQUIRED`; do not convert missing source evidence into a
numeric zero, a pass, or a final structure label. The first current scoring pass
assigns only `character_set_coverage` for `8105_core` rows and routes all other
items to source-evidence repair.
For bounded pilot scoring, partial scores may be assigned only to source-backed
items. The current 100-row 8105 core pilot may assign 3 points for
`character_set_coverage` and 3 points for `stroke_order`. It must keep the
remaining 44 points unscored until bounded standardizer extraction joins
structure, decomposition, component, radical, stroke-shape, and
single-component evidence.
GF0017 source-evidence repair plans should prioritize
`structure_first_decomposition` because it carries 20 points and unlocks
component and independent-character review. Structure/decomposition evidence
repair may materialize row-level evidence statuses from existing index,
Phase-1 parser, dictionary, Wiki, and Agent-standard feature reports. It must
not emit final structure labels or assign points. A passing repair report routes
to review-packet planning, not scoring.
Structure/decomposition review packets must be bounded review surfaces. Do not
duplicate the 97,686-row evidence table, regenerate an XLSX workbook, or build a
database for review. Reference the existing full report by path and SHA-256,
export only deterministic review samples or queue manifests, and create a
separate file clearly marked `EDITABLE` when human or Agent notes are needed.
The editable copy is not source evidence until a later merge-and-audit gate.
Agent review of a bounded packet may populate triage status, source-reference
notes, reviewer identity, and next-action notes in a separate
`AGENT_REVIEWED_EDITABLE` copy. It must leave final structure labels and
decomposition fields blank. Agent review notes are not GF0017 points, source
evidence, final labels, CNBE rows, or database records until a later human
decision and merge-and-audit gate.
Online ZDIC lookup may be used to add review URLs and representative browser
snapshots for bounded packets. Use it as cross-reference context only. Do not
query or duplicate the full 97,686-row table, do not build a database, and do
not promote ZDIC output to national-standard evidence. ZDIC-enriched copies must
remain explicitly marked editable/review-only and cannot produce scores or
final labels without a later standards validation and merge-audit gate.
ZDIC validation must record field gaps rather than infer missing data. Some
extension characters may expose Unicode, radical, stroke count, and stroke
order while lacking structure, Kangxi, or origin fields. Those gaps are
acceptable for review navigation only and must remain non-scorable until
validated against project standards.
For structure work, ZDIC should be parsed by program rather than interpreted
freehand. Extract fields such as `字形结构`, `字形分析`, `部首`, `总笔画`, `统一码`,
and `笔顺` into cache records. Missing pages, network timeouts, and missing
fields are blockers or review gaps, not reasons to guess.
After ZDIC and bounded review validation, freeze the 8105 national-standard
core before any encoding rewrite. A valid 8105-to-full-catalog plan must keep
8105 as the only national-standard core, classify all outside-8105 rows as
Agent-standard candidates, define the three evidence layers
`national_standard`, `standard_aligned`, and `cross_reference_only`, and route
the next action to a bounded 300-character pilot plan rather than full-catalog
encoding writes.
For full 8105 work, use the existing 8,105-row standard-side evidence and
no-legacy workflow rather than sampling or regenerating the 97,686-row catalog.
The full 8105 workflow may emit standardizer packets, ZDIC/source gap queues,
and GF0017 structure-item scoring for complete rows only. It must keep
unresolved rows in a gap queue, preserve ZDIC as cross-reference context, and
block CNBE source-table writes and SQLite rebuilds.
After priority candidates pass, an initial auto-filled review packet may be
materialized as a separate artifact. It may apply only audited candidates,
record the fill rule and source priority, and keep every row marked for human
review. It must not overwrite the original standardizer packet, write CNBE
source tables, edit `cnbe-research/knowledge`, or rebuild databases.
User-supplied decomposition tools such as `hanzi_decomp_v0.3.zip` may be
adapted only as read-only Agent candidate layers. If a package contains
hardcoded local paths, starts a server, opens a browser, or otherwise mixes UI
runtime with data extraction, do not import it directly. Read stable data
assets from the package with an adapter, normalize structures to the approved
13-label set, separate conflicts from gap-fill candidates, and apply only
blank-gap fills to a separate candidate packet. Such packets may emit
`agent_struct_type` review candidates, but they must not write CNBE32 fields,
overwrite current structures, edit source assets, rebuild databases, or be
presented as national-standard output.
When the human reviewer explicitly accepts a user-supplied candidate layer,
materialize a separate human-approved Agent packet rather than editing source
tables. The current accepted decision is
`HUMAN_REVIEW_2026_07_19_V03_ACCEPTED_JUE_DUTIZI`: `hanzi_decomp_v0.3` is the
approved Agent candidate reference for rows where it has structure data, and
`孓` (`U+5B53`) is `独体字` with `agent_struct_type = 0`. This approval makes an
8105 Agent candidate baseline only. It still does not authorize national
standard claims, CNBE32 writes, SQLite rebuilds, release work, or PyPI work.
After a human-approved 8105 Agent packet passes, merge it with the repository
structure model as evidence before any source-table rewrite. The merge output
should compare approved Agent structure/type against legacy `data/cnbe32.json`
fields, classify rows as confirmed, repair candidates, or missing, and preserve
old `struct_name`/`struct_type` only as current-model evidence. A passing merge
model authorizes CNBE32 dry-run patch design, not source-table writes or
database rebuilds.
CNBE32 dry-run patch design may use the approved 8105 Agent structure model,
approved stroke counts, conservatively resolved radicals, and the current model
index/extension bits. It must block rows that are missing from the current
model, lack an approved radical, have non-conservative radical resolution, or
fail bitfield roundtrip. A passing dry-run can contain blocked rows when every
blocked row has a reason and no writes occur. It authorizes review of proposed
CNBE32 field values only, not `data/cnbe32.json` edits or SQLite rebuilds.
If the human reviewer force-approves an existing dry-run, record a separate
human force-approval artifact. Preserve the original ready/blocked counts and
block reasons, and mark rows for next-step implementation planning. This
approval may authorize copied-dataset write-plan design, but it still must not
invent missing numeric fields, edit `data/cnbe32.json`, rebuild SQLite, tag,
release, or publish.
Copied-dataset write-plan design may materialize an explicitly marked copy
under evidence paths only. It may apply dry-run-ready rows to the copy and
preserve force-approved blocked rows as a separate queue. The production
`data/cnbe32.json` file, SQLite database, generated headers, package metadata,
tags, releases, and PyPI artifacts remain unchanged until a later explicit
source-write authorization.
After explicit source-write authorization, runtime promotion may replace
`data/cnbe32.json` with the approved copied dataset and rebuild both
`data/cnbe32.db` and `src/cnbe32/data/cnbe32.db`. The promotion must be
scripted, must verify SQLite integrity and known samples, must write a report,
and must still keep tag, release, and PyPI publication separate.
After a later authorized standardized runtime repair, continue from
`reports/8105_standardized_runtime_repair.json` and
`review_packets/8105_full/8105_standardized_runtime_repair_remaining_blockers.csv`.
The current release-track runtime has 7,310 patched 8105 rows and 795 remaining
force-approved blockers. Do not restart from the older 6,712/1,393 runtime
promotion counts except when reproducing the historical promotion stage.
The standardized repair may use cached ZDIC records only as
`network_cross_reference` context, must preserve current runtime index/ext bits,
must not insert missing-current-model rows such as `㑇`, and must keep tag,
release, GitHub release, and PyPI publication separate.
Old AI-generated catalog fields are a historical test baseline only. They may
support regression localization but must never become structure, radical,
stroke, GF0017, teaching, or research authority.
The 300-character pilot plan may select review rows and create a CSV review
surface only when it keeps human structure/decomposition fields blank, assigns
zero GF0017 points, emits zero final labels, writes zero CNBE rows, and creates
no database or XLSX artifact. Its next action is pilot evidence join, not
full-catalog encoding.
The pilot evidence join may merge the 300 pilot rows with existing index,
structure repair, dictionary, Yuanliu, Cihai, Wiki, and ZDIC navigation
context. It must keep all GF0017 items unscored, all final labels blank, all
CNBE writes disabled, and all outside-8105 rows outside national-standard
claims.
The 8105 core standard-source join pilot may join the 100 core control rows to
`base_character_data.json` for Unicode identity, standard level/rank, stroke
count, and stroke order. It must keep structure and decomposition pending when
the local 8105 knowledge files contain only dictionary context or generated
candidate fields. The next work is a standards-source extraction plan, not
formal scoring.
When structure or decomposition work begins, call
`cnbe-hanzi-decomposition-standardizer` before `cnbe-gf0017-batch-audit`. The
standardizer owns the call contract for raw/normalized structure labels,
decomposition trees, component categories, component-name status,
single-component status, blocker values, and no-score/no-write result fields.
The GF0017 batch audit consumes those statuses later; it must not be used to
invent missing decomposition evidence.

### Stage 2: Source Evidence Gate

Use `cnbe-standard-skill` source grading:

- `direct_standard`
- `standard_derived`
- `cross_reference`
- `referenced_not_direct`
- `unresolved`

Stop on `unresolved` for required scoring fields. Preserve
`referenced_not_direct` as `SOURCE_GAP`, not success.

### Stage 3: Hanzi Knowledge Schema

Use `cnbe-hanzi-knowledge-builder` to create or audit:

- stroke count
- stroke shape
- stroke order
- Hanzi components
- character components
- non-character components
- basic components
- radical
- side component
- glyph form
- independent-character status
- structure type
- decomposition method

Allowed structure labels:

```text
独体字
上下
上中下
左右
左中右
左上包
右上包
左三包
左下包
上三包
下三包
全包围
镶嵌
```

No other final structure label is allowed. If source text uses a non-final
label, preserve it as raw evidence and normalize only with documented rules.

### Stage 4: GF0017 Audit Gate

Use `cnbe-gf0017-batch-audit` and the 50-point model:

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

Store both score and status. A numeric score without source status is
insufficient.

### Stage 5: Agent Encoding Standard Gate

Apply the CNBE Agent encoding standard:

- `national_standard`: direct 8105/GF/GB/GG source evidence.
- `agent_standard`: project-level output aligned to 8105 and accepted by this
  Agent.
- legacy English structure labels must be localized through
  `cnbe_legacy_structure_localization.json`.
- final Agent structure labels must be Chinese labels from the 13-label set.
- old `struct_type` values are raw legacy evidence unless they match the Agent
  standard type.

If a row uses a legacy structure label, preserve both:

```text
legacy_struct_name
legacy_struct_type
agent_structure
agent_struct_type
standard_level
confidence
```

### Stage 6: Candidate Encoding

Only after Stages 1-4 pass or are explicitly classified:

- CNBE32 may carry compact fields: radical code, stroke count, structure type,
  group index, and extension flags.
- CNBE64/CNBE128 should preserve extended evidence: full stroke sequence,
  stroke-shape classification, decomposition tree, component names, source
  anchors, and review status.

Do not recompute numeric radical codes unless the radical-code map has passed
its own gate.

### Stage 7: 8105 Rule-Learning Transfer

Use this stage only for characters that are outside the current direct coding
rules or lack direct standard-side evidence.

Learn from the audited 8105 baseline:

- Unicode identity and row ordering patterns;
- allowed structure labels and structure normalization;
- radical-name to radical-code mapping after the radical-code gate passes;
- stroke-count ranges and CNBE32 bit boundaries;
- safe repair classes from GF0017 scoring;
- cases that must remain human-review-only.

Output only:

- `AGENT_STANDARD_MAPPING`;
- confidence and support count;
- source examples from 8105;
- fields proposed for CNBE32;
- extended archive fields for CNBE64/CNBE128;
- blocker or review reason.

An `AGENT_STANDARD_MAPPING` is valid as this Agent's standard output after the
Unicode, evidence, Hanzi-schema, GF0017, and batch gates pass. It is not a
national-standard output. Reports must preserve the distinction:

```text
national_standard = direct 8105 / GF / GB / GG source evidence
agent_standard = project mapping aligned to 8105 rules and passed by this Agent
```

### Stage 8: Report And Resume

Every batch report must include:

- Unicode alignment summary
- source grade summary
- GF0017 score summary
- Agent standard / national standard distinction
- legacy localization summary if legacy rows are present
- 8105 learned-rule support summary when learning transfer is used
- blockers
- checkpoint
- next resume offset
- no-write statement

Resume only from `last_verified_offset + 1` after blocker resolution and
revalidation.

## Existing CNBE Repo Commands

When operating in the CNBE repository, prefer:

```bash
python3 scripts/inspect_full_catalog_excel_schemas.py
python3 scripts/inspect_v4_fixed_sample_rows.py
python3 scripts/audit_v4_fixed_unicode_identity.py
python3 scripts/audit_cnbe8105_encoding_comparison.py
python3 scripts/score_cnbe8105_gf0017_normativity.py
python3 scripts/build_cnbe_agent_encoding_standard.py
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
python3 scripts/plan_unified_hanzi_evidence_index.py
python3 scripts/build_unified_hanzi_evidence_index.py
python3 scripts/audit_unified_hanzi_evidence_index.py
python3 scripts/score_unified_hanzi_gf0017_from_index.py
python3 scripts/plan_gf0017_source_evidence_repair_from_index.py
python3 scripts/repair_structure_decomposition_evidence_from_index.py
python3 scripts/audit_structure_decomposition_evidence_repair_from_index.py
python3 scripts/build_structure_decomposition_review_packet_from_index.py
python3 scripts/run_structure_decomposition_agent_review_packet.py
python3 scripts/build_zdic_reference_snapshot_manifest.py
python3 scripts/apply_zdic_references_to_agent_review_packet.py
python3 scripts/validate_zdic_enhanced_agent_review_packet.py
python3 scripts/plan_8105_core_rule_to_full_catalog_encoding.py
python3 scripts/plan_300_character_8105_pilot.py
python3 scripts/run_300_character_pilot_evidence_join.py
python3 scripts/plan_8105_core_standard_source_join_for_pilot.py
python3 scripts/plan_8105_core_structure_decomposition_source_extraction.py
python3 scripts/score_8105_core_pilot_gf0017_partial.py
python3 scripts/run_8105_full_no_legacy_workflow.py
python3 scripts/apply_8105_gap_auto_fill_candidates.py
python3 scripts/build_8105_gap_priority_reference_candidates.py
python3 scripts/materialize_8105_initial_auto_filled_packet.py
python3 scripts/run_hanzi_decomp_v03_8105_adapter.py
python3 scripts/materialize_hanzi_decomp_v03_8105_candidate_packet.py
python3 scripts/approve_hanzi_decomp_v03_8105_structure_packet.py
python3 scripts/build_8105_approved_structure_model_merge.py
python3 scripts/build_8105_approved_cnbe32_dry_run_patch.py
python3 scripts/force_approve_8105_cnbe32_dry_run_review.py
python3 scripts/build_8105_cnbe32_copied_dataset_write_plan.py
python3 scripts/promote_8105_cnbe32_copy_to_runtime.py
python3 scripts/validate_format_integrity.py
python3 -m pytest tests/test_cnbe8105_encoding_comparison.py tests/test_cnbe8105_gf0017_normativity.py
python3 -m pytest tests/test_8105_full_no_legacy_workflow.py
```

## References

Read [orchestration.md](references/orchestration.md) when designing a new
batch runner, encoding candidate workflow, or research-grade report.
