# Full Catalog Pre-GF0017 Handoff

## Purpose

This handoff freezes the completed full-catalog preparation gates before the
project enters source evidence and GF0017 preflight work.

It is a read-only handoff artifact. It does not modify `data/`, rewrite the
workbook, rebuild the SQLite database, reconstruct CNBE rows, create a release,
create a tag, or publish to PyPI.

## Current Decision

The project may proceed to a source evidence and GF0017 preflight plan.

The project must not start batch GF0017 scoring until the preflight plan maps
the v4_fixed workbook columns to the required scoring fields and source evidence
classes.

## Source Workbook

Primary candidate workbook:

`data/CNBE_编码目录_修复版_v4_fixed.xlsx`

Source role:

- legacy test baseline;
- release reconstruction candidate;
- not yet release data;
- not yet source-evidence-scored;
- not yet GF0017-scored;
- not yet a reconstructed CNBE database.

The workbook is suitable for the next preflight stage because it has passed the
schema, sample-row, and Unicode identity gates.

## Completed Gates

### Gate 1: Data Asset Manifest

Artifacts:

- `reports/DATA_ASSET_MANIFEST.md`
- `reports/data_asset_manifest.json`

Result:

- 22 tracked `data/` files classified.
- 4 workbook paths identified.
- 1 invalid or placeholder workbook path identified.
- `v4_fixed` classified as a likely latest legacy reconstruction candidate.

Boundary:

- Asset classification does not validate encoding rows.
- Asset classification does not promote legacy data into release data.

### Gate 2: Workbook Schema Inspection

Artifacts:

- `scripts/inspect_full_catalog_excel_schemas.py`
- `reports/full_catalog_excel_schema_comparison.json`
- `tests/test_full_catalog_excel_schema_inspection.py`

Result:

- v3 workbook: 97,688 worksheet rows and 14 columns.
- v4 workbook: 97,687 worksheet rows and 16 columns.
- v4_fixed workbook: 97,687 worksheet rows and 17 columns.
- All three valid workbooks expose character, Unicode, CNBE, radical, stroke,
  and structure field candidates.

Boundary:

- Schema validity is not row validity.
- Schema validity is not source evidence.
- Schema validity is not GF0017 scoring.

### Gate 3: v4_fixed Fixed Sample Rows

Artifacts:

- `scripts/inspect_v4_fixed_sample_rows.py`
- `reports/full_catalog_v4_fixed_sample_rows.json`
- `tests/test_v4_fixed_sample_rows.py`

Sample strategy:

- first five data rows;
- middle five data rows;
- final five data rows.

Sample worksheet rows:

- `2` through `6`;
- `48841` through `48845`;
- `97683` through `97687`.

Result:

- 15 sampled rows.
- 0 Unicode-to-character failures.
- 0 CNBE hex, decimal, and binary representation failures.
- 0 CNBE bitfield recomputation failures.

Boundary:

- Sample success is not full-row success.
- Sample success only permits the full Unicode identity gate.

### Gate 4: v4_fixed Full Unicode Identity Gate

Artifacts:

- `scripts/audit_v4_fixed_unicode_identity.py`
- `reports/full_catalog_v4_fixed_unicode_identity.json`
- `tests/test_v4_fixed_unicode_identity.py`

Result:

- data rows: 97,686;
- expected data rows: 97,686;
- unique Unicode values: 97,686;
- unique characters: 97,686;
- issue counts: none;
- sequence min: 0;
- sequence max: 97,685;
- sequence gap sample: none;
- status: PASS.

Boundary:

- Unicode identity success is not source evidence success.
- Unicode identity success is not GF0017 success.
- Unicode identity success is not Agent-standard mapping success.
- Unicode identity success does not authorize database reconstruction.

## Confirmed Field Headers

The v4_fixed primary worksheet exposes these columns:

- `序号`
- `汉字`
- `Unicode`
- `CNBE(Hex)`
- `CNBE(Dec)`
- `CNBE(Bin)`
- `部首区`
- `笔画数`
- `结构区(v4)`
- `结构名称(v4)`
- `字库索引`
- `扩展区`
- `是否现代`
- `Space_Label`
- `Category_Label`
- `Time_Label`
- `备注(v3原结构)`

These columns are legacy workbook fields. Their names and values must be mapped
to standards evidence fields before release reconstruction work begins.

## Required Preflight Before GF0017 Scoring

The next stage should create a source evidence and GF0017 preflight report.

The preflight must map v4_fixed columns to the fields required by the CNBE Agent
workflow:

- Unicode identity;
- target scope membership;
- national-standard source grade;
- stroke count;
- stroke shape;
- stroke order;
- component validity;
- component-name validity;
- radical validity;
- independent-character rule;
- structure-first decomposition;
- legacy-to-Agent structure localization;
- CNBE32 compact-field candidate;
- CNBE64 or CNBE128 extended archive fields;
- blocker class;
- checkpoint and resume position.

## Required Source Grade Handling

Every field entering the GF0017 preflight must declare a source grade:

- `direct_standard`
- `standard_derived`
- `cross_reference`
- `referenced_not_direct`
- `unresolved`

Rows with `unresolved` required fields must not proceed to scoring.

Rows with `referenced_not_direct` required fields must be marked as source gaps
unless a reviewed rule permits an Agent-standard mapping.

## GF0017 Score Model Entry Requirements

Before a row can receive a GF0017 score, the preflight must identify which
source or rule supports:

- character set coverage;
- stroke shape;
- stroke order;
- component validity;
- component-name validity;
- radical validity;
- independent-character rule;
- structure-first decomposition.

A numeric score without source status is not acceptable.

## Agent Standard Boundary

The Agent may produce project-level mappings after the required gates pass.

Agent-standard output must remain distinct from national-standard output.

The handoff distinction is:

- `national_standard`: direct GB, GF, GG, 8105, or related official standard
  evidence;
- `agent_standard`: project-level output aligned to the 8105 rule system and
  accepted by the Agent gates;
- `source_gap`: evidence exists but is not direct enough for release promotion;
- `unresolved`: the row must stop or remain outside the release batch.

## Stop Conditions For The Next Stage

The next stage must stop if:

- a required source column cannot be mapped;
- source grade is missing;
- source grade is unresolved for a required GF0017 field;
- a legacy structure label cannot be localized;
- a row conflicts with Unicode identity;
- an evidence file is missing;
- a scoring field would rely on LLM memory or visual intuition;
- database rewrite becomes necessary before explicit authorization.

## Resume Rule

If the next stage processes rows in batches, it must record:

- batch id;
- row offset;
- last verified row;
- first failed row;
- blocker reason;
- next resume offset.

Resume may only start at `last_verified_offset + 1` after the blocker is
resolved and the affected gate is rerun.

## Recommended Next Artifact

Recommended next report:

`reports/FULL_CATALOG_GF0017_PREFLIGHT_PLAN.md`

Recommended next script:

`scripts/plan_full_catalog_gf0017_preflight.py`

The script should be read-only and should not score all rows yet. It should map
fields, list source requirements, identify blockers, and produce a preflight
plan for human review.

## Validation State

The repository validation state at this handoff:

- format integrity passes;
- pytest passes;
- schema report parses;
- sample-row report parses;
- Unicode identity report parses;
- no `data/` file was modified;
- no workbook was rewritten;
- no database was rewritten.

## Non-Goals

This handoff does not:

- run GF0017 scoring;
- create Agent-standard mappings;
- repair legacy CNBE fields;
- rebuild `data/cnbe32.db`;
- rebuild `src/cnbe32/data/cnbe32.db`;
- modify any workbook;
- move any `data/` file;
- remove any historical experiment;
- create a release;
- create a tag;
- publish to PyPI.

## Final Handoff Decision

Proceed to source evidence and GF0017 preflight planning.

Do not proceed directly to batch scoring or database reconstruction.

