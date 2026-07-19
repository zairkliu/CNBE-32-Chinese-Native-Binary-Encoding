# CNBE Hanzi Structure Agent Model

## Purpose

This document defines the reproducible Agent model for CNBE Hanzi structure
encoding work.

The model is designed for auditability. It separates Unicode identity,
standard-side evidence, Agent-standard mapping, GF0017 scoring gates, and CNBE
carrier fields.

It does not define a release claim. It does not state that the full catalog is
ready for teaching, research, release, database rebuild, or PyPI publication.

## Authority Boundary

The Agent keeps three authority levels separate:

- `national_standard`: direct GF, GB, GG, or 8105 source evidence.
- `standard_derived`: structured data derived from a standard source and
  traceable back to the source.
- `agent_standard`: project-level output aligned to the 8105 baseline and
  accepted by the Agent gates.

Outside-8105 rows may become Agent-standard candidates after evidence gates,
but they are not national-standard outputs.

## Non-Goals

The Agent must not:

- modify the legacy Excel workbook during planning or audit stages;
- write CNBE rows without explicit authorization;
- rebuild SQLite databases without explicit authorization;
- assign formal GF0017 scores while source gaps remain;
- describe OCR, dictionary, Wikipedia, or generated CNBE fields as direct
  national-standard authority;
- turn `SOURCE_GAP` or `ROW_LEVEL_EVIDENCE_JOIN_PENDING` into success;
- publish tags, releases, or PyPI artifacts.

## State Machine

The Agent runs the following states in order.

| State | Output | Automatic | Stop Condition |
|---|---|---:|---|
| asset_manifest | data asset manifest | yes | missing source file |
| workbook_schema | workbook schema report | yes | unknown workbook schema |
| sample_identity | fixed sample report | yes | Unicode or CNBE form mismatch |
| full_unicode_identity | full identity report | yes | duplicate or mismatched identity |
| runtime_verification | Agent runtime report | yes | missing Agent standard artifact |
| gf0017_preflight | scoring preflight plan | yes | malformed score model |
| source_mapping | source mapping report | yes | unresolved controlling source |
| join_schema | row-level join schema | yes | missing required join key |
| blocker_reconciliation | blocker report | yes | source write needed |
| structured_8105_diff | diff packet | yes | knowledge write needed |
| structured_8105_patch | patched knowledge source | no | requires authorization |
| batch_readiness | readiness report | yes | row or source blocker |
| source_join_batch | full source-join report | yes | row source-join blocker |
| agent_mapping_plan | outside-8105 mapping plan | yes | Unicode gap |
| evidence_join_design | join design report | yes | missing source path |
| evidence_status_join | row evidence status report | yes | row representation gap |
| source_resolution | source resolution plan | yes | scoring policy needed |
| extraction_specs | row-level extraction specifications | yes | source parser ambiguity |
| evidence_join_runners | row-level evidence tables | yes | unresolved row evidence |
| unified_evidence_index | schema-coded 97,686-row evidence index | yes | profile or count mismatch |
| unified_evidence_index_audit | index consistency audit | yes | scoring/write gate violation |
| formal_scoring | GF0017 score records | no | requires authorization |
| cnbe_candidate_generation | CNBE candidate rows | no | requires authorization |
| database_rebuild | SQLite database | no | requires authorization |

## Core Invariants

Every Agent state must preserve these invariants:

- Unicode identity is the first key.
- One input row maps to one intended Unicode scalar value.
- `national_standard` and `agent_standard` are not conflated.
- Source gaps remain visible.
- Pending evidence is not a score.
- CNBE32 is a carrier layer, not the authority.
- CNBE64 and CNBE128 are evidence archive paths when CNBE32 is too compact.
- Reports are machine-readable and human-readable.
- Tests cover every new runner.
- `scripts/validate_format_integrity.py` passes before handoff.

## Current Full-Catalog Status

The current full-catalog path has reached `source_resolution`.
The read-only extraction-spec stage has also been generated for automatable
items.
The read-only extraction runner has materialized source-availability statuses
for those automatable items.
The evidence-review plan now prioritizes parser implementation planning.
The parser implementation plan has been generated and identifies Phase 1 as a
decision point.

Known counts:

- Full catalog rows: 97,686.
- Direct 8105 baseline rows: 8,105.
- Outside-8105 Agent-standard mapping candidates: 89,581.
- Outside-8105 BMP rows: 19,675.
- Outside-8105 supplementary-plane rows: 69,906.

Current item statuses:

- `character_set_coverage`: policy decision required.
- `stroke_shape`: source extraction specification required.
- `stroke_order`: row-level extraction required.
- `component_validity`: row-level extraction required.
- `component_name_validity`: row-level extraction required.
- `radical_validity`: row-level extraction required.
- `independent_character_rule`: row-level extraction required.
- `structure_first_decomposition`: row-level extraction required.

Formal scoring remains blocked.

Current extraction-spec outputs:

- `stroke_shape`: `extract_stroke_shape_evidence_v1`;
- `stroke_order`: `extract_stroke_order_evidence_v1`;
- `component_validity`: `extract_component_inventory_v1`;
- `component_name_validity`: `extract_component_name_validation_v1`;
- `radical_validity`: `extract_radical_evidence_v1`;
- `independent_character_rule`: `extract_independent_character_status_v1`;
- `structure_first_decomposition`: `extract_structure_decomposition_v1`.

Current extraction-result status:

- Outside-8105 rows materialized: 89,581.
- Row status: `ROW_EXTRACTION_SOURCES_AVAILABLE_PENDING` for 89,581 rows.
- Missing source paths: zero.
- `stroke_shape`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `stroke_order`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `component_validity`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `component_name_validity`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `radical_validity`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `independent_character_rule`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.
- `structure_first_decomposition`: 89,581 rows
  `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`.

These statuses mean source paths and extraction specifications are available.
They do not mean evidence values have been extracted, reviewed, or scored.

Current evidence-review priority:

- priority 1: `structure_first_decomposition`, 20 points;
- priority 2: `component_name_validity`, 8 points;
- priority 3: `independent_character_rule`, 7 points;
- priority 4: `component_validity`, 3 points;
- priority 5: `radical_validity`, 3 points;
- priority 6: `stroke_order`, 3 points;
- priority 7: `stroke_shape`, 3 points.

The review plan authorizes parser implementation planning only. It does not
authorize parser execution that writes source assets, point assignment, CNBE row
writes, or database rebuilds.

Current parser implementation plan:

- Phase 1: `structure_first_decomposition` using
  `run_structure_decomposition_evidence_parser`;
- Phase 2: `component_name_validity` using
  `run_component_name_evidence_parser`;
- Phase 3: `independent_character_rule` using
  `run_independent_character_evidence_parser`;
- Phase 4: `component_validity` using
  `run_component_inventory_evidence_parser`;
- Phase 5: `radical_validity` using `run_radical_evidence_parser`;
- Phase 6: `stroke_order` using `run_stroke_order_evidence_parser`;
- Phase 7: `stroke_shape` using `run_stroke_shape_evidence_parser`.

Phase 1 implementation is the next decision point.

## Unified Evidence Index Result

The Agent has built and audited a read-only unified Hanzi evidence index:

- index report: `reports/unified_hanzi_evidence_index.json`;
- audit report: `reports/unified_hanzi_evidence_index_audit.json`;
- rows: 97,686;
- direct 8105 core rows: 8,105;
- outside-8105 Agent candidates: 89,581;
- formal GF0017 scores assigned: 0;
- final structure labels emitted: 0;
- CNBE row writes: disabled;
- database rebuild: disabled.

The index uses a schema-coded row array plus top-level profiles for repeated
statuses. This keeps the full-catalog report reviewable and avoids a repeated
nested JSON artifact that is too large for repository handling.

The passing audit allows human review preparation only. It does not authorize
formal GF0017 scoring, final structure labels, CNBE row repair, SQLite rebuild,
release work, or publishing.

## GF0017 Scoring From Existing Index

After explicit authorization, the Agent started GF0017 scoring from the
existing unified evidence index. This pass did not regenerate the full Unicode
catalog and did not read the Excel workbook.

Outputs:

- `reports/unified_hanzi_gf0017_scoring_from_index.json`;
- `reports/UNIFIED_HANZI_GF0017_SCORING_FROM_INDEX.md`.

Current result:

- rows evaluated: 97,686;
- rows with any assigned points: 8,105;
- fully scored rows: 0;
- rows not scorable from the current index: 89,581;
- assigned item: `character_set_coverage` for `8105_core` rows only;
- structure/decomposition item status: `NOT_SCORABLE_EVIDENCE_REQUIRED` for
  97,686 rows.

This is a scoring start, not a full scoring completion. The next required work
is source-evidence repair and materialization for the remaining GF0017 items.
No CNBE rows or databases may be written from this partial scoring result.

## Source Evidence Repair

The Agent generated a GF0017 source-evidence repair plan from the existing
index:

- `reports/gf0017_source_evidence_repair_plan_from_index.json`;
- `reports/GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_FROM_INDEX.md`.

The plan prioritizes `structure_first_decomposition` because it carries 20
points and currently blocks all 97,686 rows from complete GF0017 scoring.

The first repair package materialized structure/decomposition evidence status:

- `reports/gf0017_structure_decomposition_evidence_repair_from_index.json`;
- `reports/GF0017_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_FROM_INDEX.md`.

Result:

- total rows: 97,686;
- reviewable or partial structure/decomposition rows: 4,580;
- 8105 core rows requiring structure standard join: 8,105;
- score values assigned: 0;
- final structure labels emitted: 0;
- CNBE/database writes: 0.

The next allowed step is structure/decomposition review-packet planning. It is
not a scoring step and must not emit final structure labels.

## Structure Review Packet

The Agent audit for structure/decomposition evidence repair passed:

- `reports/structure_decomposition_evidence_repair_agent_audit.json`;
- `reports/STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_AGENT_AUDIT.md`.

A bounded review packet was then created:

- manifest: `reports/structure_decomposition_review_packet_manifest.json`;
- markdown: `reports/STRUCTURE_DECOMPOSITION_REVIEW_PACKET.md`;
- canonical CSV: `reports/structure_decomposition_review_packet.csv`;
- editable copy:
  `review_packets/structure_decomposition/structure_decomposition_review_packet_EDITABLE.csv`.

The packet contains 212 deterministic review rows and references the existing
97,686-row source report by path and SHA-256. It does not duplicate the full
table, create XLSX files, create databases, assign GF0017 points, or emit final
structure labels.

If review edits are required, only the `EDITABLE` copy may be modified. Review
notes in that copy remain evidence intake, not formal source evidence, until a
later merge-and-audit gate.

The Agent review pass created a separate reviewed copy:

- `reports/structure_decomposition_agent_review_result.json`;
- `reports/STRUCTURE_DECOMPOSITION_AGENT_REVIEW_RESULT.md`;
- `review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_EDITABLE.csv`.

The Agent reviewed 212 rows and populated triage notes only. It did not fill
final structure labels, did not fill decomposition fields, did not assign
GF0017 points, and did not modify the source report or original editable copy.

The next decision is whether to design a merge plan for reviewed notes or keep
the packet for human review. A merge plan would still be read-only until a later
authorization gate.

## ZDIC Online Cross-Reference

ZDIC was added as an online lookup and snapshot reference for the bounded
structure/decomposition packet:

- `reports/zdic_reference_snapshot_manifest.json`;
- `reports/ZDIC_REFERENCE_SNAPSHOT_MANIFEST.md`;
- `reports/zdic_snapshots/`;
- `reports/structure_decomposition_agent_review_zdic_enhancement.json`;
- `reports/STRUCTURE_DECOMPOSITION_AGENT_REVIEW_ZDIC_ENHANCEMENT.md`;
- `reports/zdic_enhanced_agent_review_packet_validation.json`;
- `reports/ZDIC_ENHANCED_AGENT_REVIEW_PACKET_VALIDATION.md`;
- `review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_ZDIC_EDITABLE.csv`.

The ZDIC manifest covers the 212-row packet and includes 5 representative
browser snapshots. It does not query or duplicate the full 97,686-row table.

ZDIC is online cross-reference context only. It can help reviewers navigate
部首、总笔画、统一码、笔顺、字形结构、康熙字典、字源字形 fields, but it is not
promoted to national-standard evidence and does not produce GF0017 points or
final labels.

The enhanced packet validation gate requires core navigation fields to be
present and records supplemental field gaps separately. A missing Kangxi,
structure, or 字源字形 field in ZDIC is not filled by inference and remains
non-scorable until checked against the standards workflow.

## 8105 Core To Full Catalog Plan

The Agent now has a fixed transition gate from review-navigation work to
encoding rewrite planning:

- `reports/8105_core_rule_to_full_catalog_encoding_plan.json`;
- `reports/8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN.md`;
- `scripts/plan_8105_core_rule_to_full_catalog_encoding.py`.

This gate asserts that 8105 is the controlling national-standard core and that
all 89,581 outside-8105 rows remain Agent-standard candidates until later
evidence and GF0017 gates approve project-level outputs. It also fixes the
next action as a 300-character pilot plan, not full-catalog encoding.

## 300-Character Pilot Queue

The Agent now has a bounded pilot queue:

- `reports/300_character_8105_pilot_plan.json`;
- `reports/300_CHARACTER_8105_PILOT_PLAN.md`;
- `review_packets/300_character_8105_pilot/300_character_8105_pilot_plan.csv`;
- `scripts/plan_300_character_8105_pilot.py`.

The queue has 100 8105 core controls, 100 outside-8105 strong
dictionary/origin rows, and 100 outside-8105 extension or gap rows. It is an
evidence-join test surface only. The Agent must not treat it as an encoding
table, GF0017 scoring output, final structure label source, CNBE row source, or
database seed.

## Pilot Evidence Join

The Agent can now join the 300-row pilot with existing review evidence:

- `reports/300_character_pilot_evidence_join.json`;
- `reports/300_CHARACTER_PILOT_EVIDENCE_JOIN.md`;
- `review_packets/300_character_8105_pilot/300_character_pilot_evidence_join.csv`;
- `scripts/run_300_character_pilot_evidence_join.py`.

The join records Unicode identity, authority layer, structure evidence status,
dictionary context, Yuanliu context, Cihai context, Wiki hit count, and ZDIC
navigation. It keeps all GF0017 items unscored and all final structure labels
blank. The next action is human review or a standards-source join plan, not
full-catalog encoding.

## Required Output Shape

Every runner should output JSON with:

```json
{
  "report_schema_version": "1.0",
  "mode": "read_only_stage_name",
  "overall_status": "PASS_OR_BLOCKED",
  "next_workflow_status": "NEXT_GATE",
  "authority_boundary": {
    "does_not_assign_gf0017_scores": true,
    "does_not_modify_workbook": true,
    "does_not_modify_cnbe_rows": true,
    "does_not_rebuild_database": true,
    "does_not_publish_release": true
  },
  "summary": {},
  "decision": {
    "may_start_formal_gf0017_scoring": false,
    "may_rebuild_database": false,
    "may_modify_cnbe_rows": false,
    "reason": "reader-facing explanation"
  },
  "next_artifacts": []
}
```

Every runner should also output a Markdown report with:

- purpose;
- no-write and no-score boundary;
- result;
- blockers;
- next artifact list;
- decision statement.

## Reproducible Command Chain

Run the current chain with:

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
python3 scripts/validate_format_integrity.py
```

Run the current focused tests with:

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
  tests/test_full_catalog_parser_implementation_plan.py
```

## Stop Rules

The Agent must stop before:

- modifying `cnbe-research/knowledge` source assets;
- assigning formal GF0017 scores;
- writing CNBE rows;
- rebuilding databases;
- changing version tags or release artifacts;
- pushing, creating PRs, or publishing packages.

The Agent may continue automatically through:

- read-only inventory;
- schema inspection;
- source mapping;
- blocker reconciliation;
- report generation;
- test generation;
- skill and whitepaper updates;
- source-resolution planning;
- extraction-spec design.

## Next Model Step

The previous decision step has now been executed as a read-only parser:

```text
run_structure_decomposition_evidence_parser
```

The parser covers all 89,581 outside-8105 rows and produces only evidence
statuses. It does not assign points, modify source assets, write CNBE rows, or
rebuild databases.

The current Phase 1 result is:

- ready for review: 2,551 rows;
- partial review required: 2,029 rows;
- evidence gap: 85,001 rows;
- score values assigned: 0.

## Next Model Step

The Phase 1 evidence review plan has also been generated. Its queues are:

- human review ready: 2,551 rows;
- partial evidence review: 2,029 rows;
- source-gap resolution required: 85,001 rows.

The dominant blocker is `MISSING_STRUCTURE`.

## Next Model Step

The source-gap resolution plan and dictionary review extractor have now been
run. The plan confirms:

- source-gap rows: 85,001;
- yuanliu hits: 32;
- cihai hits: 32;
- dictionary/character-origin review packet rows with hits: 62 status rows;
- rows without dictionary review hit: 84,939.

The offline Wikipedia corpus exists and has a read-only index plan, but it is
lowest-tier cross-reference only.

The read-only Wiki streaming index has now run over the full offline corpus:

- target rows: 84,939;
- articles scanned: 1,489,790;
- Wiki cross-reference hits: 11,108;
- rows still without Wiki cross-reference: 73,831;
- score values assigned: 0.

These hits are review aids, not scoring evidence.

The remaining-source audit found no stronger local authoritative row-level IDS
source for the `73,831` unresolved rows. Local resources are useful but bounded:

- Unihan2: Unicode cross-reference, not structure authority;
- Kangxi: dictionary context;
- cjk-decomp: third-party IDS cross-reference for only 89 remaining rows;
- decomp-data: no remaining-row hit;
- GF/GG/GB: rule authority, not remaining-row IDS coverage.

The rows have therefore been routed to Agent-standard planning:

- rule-learning candidates: 5,885;
- extension-review candidates: 67,946.

The Agent-standard rule-learning design is now complete. It permits only:

- read-only feature tables;
- review priors;
- confidence buckets;
- human-review queues.

It forbids:

- final structure labels;
- formal GF0017 points;
- CNBE32 fields;
- database writes.

The read-only feature table runner is now complete:

- feature rows: 73,831;
- rule-learning queue: 5,885;
- extension-review queue: 67,946;
- review prior medium: 1,080;
- review prior low-medium: 4,805;
- review prior low: 67,946;
- final structure labels emitted: 0;
- score values assigned: 0.

## Next Model Step

The next automatic planning step is:

```text
audit_remaining_structure_agent_standard_review_priors
```

That step may audit queue boundaries, prior buckets, and sampling strategy. It
must not claim national-standard status, assign GF0017 points, emit final
structure labels, write CNBE rows, modify source assets, or rebuild databases.

## Review-Prior Audit Result

The review-prior audit has passed:

- audited feature rows: 73,831;
- rule-learning queue: 5,885;
- extension-review queue: 67,946;
- review prior medium: 1,080;
- review prior low-medium: 4,805;
- review prior low: 67,946;
- prior mismatches: 0;
- forbidden field rows: 0;
- point assignment rows: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

The next automatic step is:

```text
plan_remaining_structure_agent_standard_review_samples
```

That step may create deterministic review samples from the audited queues. It
must still keep formal GF0017 scoring, final structure labels, CNBE row writes,
source-asset edits, and database rebuilds blocked.

## Review-Sample Plan Result

The deterministic review-sample plan has passed:

- total samples: 150;
- review prior medium: 50;
- review prior low-medium: 50;
- review prior low: 50;
- rule-learning queue samples: 100;
- extension-review queue samples: 50;
- duplicate sample keys: 0;
- forbidden field leaks: 0;
- point assignment leaks: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

The next automatic step may construct a human-review packet from these samples.
That packet must remain evidence-only and must not emit final structures, assign
GF0017 points, repair CNBE rows, modify source assets, or rebuild databases.

## Human Review Packet Result

The human-review packet and coding-directory workbook are ready:

- packet rows: 150;
- review prior medium: 50;
- review prior low-medium: 50;
- review prior low: 50;
- rule-learning queue rows: 100;
- extension-review queue rows: 50;
- duplicate keys: 0;
- forbidden field rows: 0;
- human structure/decomposition prefill rows: 0;
- score values assigned: 0;
- final structure labels emitted: 0.

The workbook is a manual evidence intake surface. It is not a scoring result,
not a final structure table, and not a CNBE row repair table.

## External Dictionary Context Result

The post-review dictionary-source evaluation selected:

- primary structured source: `leechenhwa2/nlp-han-dicts`;
- supporting text witness: `kanripo/KR1j0048`;
- secondary comparison only: `he426100/kangxi`.

The staging database was built at:

```text
build/dictionary_context_staging/dictionary_context_entries.sqlite
```

It contains 68,395 staged dictionary context rows and 49,085 unique characters.
The staging data may support human review and source-gap resolution. It must
not be treated as national-standard structure authority, formal GF0017 scoring,
final structure labels, or CNBE row repairs.

## Dictionary Context Review Join Result

The staged dictionary context has been joined to the current review targets:

- human-review packet rows: 150;
- human-review dictionary hits: 104;
- human-review dual-source hits: 61;
- human-review single-source hits: 43;
- human-review dictionary gaps: 46;
- remaining Agent-standard rows: 73,831;
- remaining dictionary hits: 28,960;
- remaining dictionary gaps: 44,871.

This join is a reviewer-facing evidence aid. It does not convert dictionary
definitions into national-standard structure evidence, formal GF0017 scores,
final structure labels, or CNBE row repairs.

## Knowledge Merge Plan Result

The dictionary-context official knowledge merge plan is ready but not executed.
The plan deliberately avoids modifying the 8,105 core files and recommends a
separate index:

```text
knowledge/structured/dictionary_context_index.json
```

Rationale:

- dictionary context covers 49,085 unique characters;
- 41,764 of those are outside the 8,105 national-standard base;
- mixing them into `base_character_data.json` or
  `cnbe_character_knowledge.json` would blur the national-standard versus
  cross-reference boundary.

The merge requires explicit authorization and backup creation before writing
`cnbe-research/knowledge`.

## Knowledge Merge Script Dry Run Result

The authorized merge script now exists and has been dry-run. Default execution
does not write `cnbe-research/knowledge`; it builds the planned index in memory
and writes only reports:

```text
reports/dictionary_context_knowledge_merge_report.json
reports/DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_REPORT.md
```

Dry-run result:

- status: `PASS_DRY_RUN_READY`;
- index entries prepared: 49,085;
- authorized write: false;
- real target index exists after dry-run: false;
- GF0017 score values assigned: 0;
- final structure labels emitted: 0;
- CNBE rows written: 0;
- database rebuilds: 0.

The script refuses official writes unless both `--execute` and the exact
authorization token are supplied. Even authorized execution is limited to
creating `dictionary_context_index.json` and updating `references.json` with
backups; it does not modify the 8,105 core files.

## Knowledge Merge Audit Result

The authorized dictionary-context knowledge merge has executed and passed
post-merge audit:

- status: `PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED`;
- target index entries: 49,085;
- references entries: 9;
- reference key: `reference_9`;
- backup: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/references.json.bak.20260717T031651Z`;
- `base_character_data.json` hash unchanged: true;
- `cnbe_character_knowledge.json` hash unchanged: true;
- GF0017 score values assigned: 0;
- final structure labels emitted: 0;
- CNBE rows written: 0;
- database rebuilds: 0.

The official knowledge layer now contains dictionary context as a separate
cross-reference index. This is useful for review and source-gap triage, but it
is still not national-standard structure authority and still cannot be used as
formal GF0017 scoring evidence by itself.

## Post-Merge Revalidation Result

After the knowledge merge, the source and knowledge audit gates were rerun:

- knowledge inventory files: 226;
- JSON parse pass: 218 / 218;
- source audit pass: 18;
- source audit attention: 0;
- blocker count: 1;
- encoding generation gate: `NO_GO`;
- SQLite build gate: `NO_GO`.

The legacy `Unihan.zip` file fails zip integrity, but the manifest-pinned
canonical `Unihan2.zip` passes size, hash, and zip checks. The legacy archive is
therefore treated as an excluded warning rather than a blocker.

Current gates:

- knowledge inventory: `PASS_WITH_NOTES`;
- source audit: `PASS`;
- encoding generation: `REVIEW_REQUIRED`;
- SQLite build: still not allowed.

This means evidence-index design may continue. It still does not authorize
formal GF0017 scoring, CNBE row writes, or database reconstruction.

## Unified Evidence Index Plan Result

The next integration layer is a Unicode-keyed evidence graph, not a coding
table. The plan passed with:

- status: `PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY`;
- full catalog rows: 97,686;
- unique Unicode values: 97,686;
- 8105 national-standard core rows: 8,105;
- dictionary context entries: 49,085;
- Yuanliu index entries: 9,574;
- Cihai index entries: 5,423;
- source gate: `REVIEW_REQUIRED`;
- scoring allowed: false;
- CNBE row writes allowed: false;
- database rebuild allowed: false.

The planned index will keep these layers separate:

- national-standard core;
- dictionary cross-reference context;
- character-origin context;
- lowest-tier Wiki context;
- legacy CNBE context;
- Agent-standard context.

The index may be built read-only, then audited before any scoring or encoding
work starts.

## Pilot Standard-Source Join Behavior

For the first 100 8105 core pilot rows, the Agent now uses
`base_character_data.json` as the standard-derived baseline for these fields:

- Unicode identity;
- 8105 level;
- 8105 standard rank;
- stroke count;
- stroke order sequence.

The Agent must not infer structure or decomposition from dictionary
definitions, ZDIC pages, Wiki summaries, or visual memory. If the structured
knowledge file lacks source-audited structure/decomposition fields, every row
must remain in:

```text
STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED
DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED
```

This rule keeps the model reproducible: evidence may be joined and reviewed,
but formal GF0017 scoring, final labels, CNBE rows, and database rebuilds stay
blocked until the standards-source extraction plan passes.

## Decomposition Standardizer Call Layer

The Agent now calls a separate decomposition layer before GF0017 batch audit:

```text
skill: cnbe-hanzi-decomposition-standardizer
mode: evidence_only_no_score
required_input: char, unicode, row_id, scope_status, authority_layer
forbidden_output: gf0017_points, cnbe_rows, database, full_catalog_copy
```

Required result fields include:

```text
unicode_identity_status
structure_join_status
decomposition_join_status
component_name_status
single_component_status
source_grade
blocker
next_required_action
gf0017_points_assigned
cnbe_write_status
database_rebuild_status
```

The total-control Agent should use this call layer for single characters,
bounded batches, and review packets whenever structure or decomposition is in
scope. GF0017 scoring consumes these statuses later; it must not fill missing
structure evidence by itself.

## Current 8105 Pilot Handoff

The current handoff packet is:

```text
review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv
```

It contains 100 `8105_core_control` rows and has this status boundary:

```text
unicode_identity_status = PASS_UNICODE_IDENTITY
structure_join_status = STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED
decomposition_join_status = DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED
gf0017_points_assigned = 0
cnbe_write_status = NO_CNBE_WRITE
database_rebuild_status = NO_DATABASE_REBUILD
```

The packet is ready for a bounded extraction runner. It is not a source merge,
not a score sheet, and not an encoding table.

## Current Partial Scoring Boundary

The current pilot scoring artifact is:

```text
reports/8105_core_pilot_gf0017_partial_scoring.json
```

It starts scoring without allowing the Agent to fill evidence gaps:

```text
assigned_score = 6
formal_total_max = 50
scored_items = character_set_coverage, stroke_order
row_score_status = PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE
```

No later Agent may treat this as a complete GF0017 score. The next step is
bounded standardizer extraction for the missing 44 points per row.
