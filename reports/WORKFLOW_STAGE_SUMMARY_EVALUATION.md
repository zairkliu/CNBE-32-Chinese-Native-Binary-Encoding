# CNBE Workflow Stage Summary Evaluation

## Purpose

This report evaluates whether the current CNBE preparation workflow should be
summarized before moving from Unicode identity work into standards evidence and
GF0017 scoring.

The answer is yes. The project has crossed from repository governance into
full-catalog workbook gates, and the next phase will be more expensive and more
authority-sensitive.

## Current Stage

The current stage is:

`legacy full-catalog preparation before source evidence and GF0017 gates`

The project is still in a read-only preparation phase. The current outputs do
not reconstruct CNBE rows, rewrite databases, or promote legacy data into a
release version.

## Completed Workflow Layers

### 1. Repository Governance

Completed:

- repository structure boundaries;
- repository asset inventory;
- test-version and release-version governance;
- baseline split into legacy test and standards-aligned release tracks.

Purpose:

- separate legacy AI-generated or AI-assisted test data from future release
  reconstruction;
- prevent historical experiments from being mistaken for standards-aligned
  outputs.

### 2. Data Asset Manifest

Completed:

- `reports/DATA_ASSET_MANIFEST.md`;
- `reports/data_asset_manifest.json`.

Purpose:

- classify `data/` files before movement or reconstruction;
- identify `v4_fixed` as a likely first reconstruction input candidate;
- preserve runtime database and legacy workbook boundaries.

### 3. Workbook Schema Inspection

Completed:

- `scripts/inspect_full_catalog_excel_schemas.py`;
- `reports/full_catalog_excel_schema_comparison.json`.

Purpose:

- compare v3, v4, and v4_fixed workbook shapes;
- confirm core field candidates exist;
- avoid jumping from workbook presence to release reconstruction.

Observed:

- v3 has 97,688 worksheet rows and 14 columns;
- v4 has 97,687 worksheet rows and 16 columns;
- v4_fixed has 97,687 worksheet rows and 17 columns.

### 4. v4_fixed Fixed Sample Rows

Completed:

- `scripts/inspect_v4_fixed_sample_rows.py`;
- `reports/full_catalog_v4_fixed_sample_rows.json`.

Purpose:

- inspect first, middle, and tail row windows;
- confirm field interpretation before full traversal.

Observed:

- 15 sampled rows;
- 0 Unicode-to-character failures;
- 0 CNBE representation failures;
- 0 CNBE bitfield recomputation failures.

### 5. v4_fixed Full Unicode Identity Gate

Completed:

- `scripts/audit_v4_fixed_unicode_identity.py`;
- `reports/full_catalog_v4_fixed_unicode_identity.json`.

Purpose:

- traverse all v4_fixed data rows;
- verify `汉字` and `Unicode` identity;
- detect duplicate Unicode values, duplicate characters, sequence gaps, invalid
  CNBE representations, and CNBE bitfield recomputation failures.

Observed:

- 97,686 data rows;
- 97,686 unique Unicode values;
- 97,686 unique characters;
- 0 issue counts;
- sequence min 0 and sequence max 97,685;
- no sequence gap sample.

## Skill Updates

The CNBE Hanzi Structure Encoding Agent skill was updated to encode the
workbook preparation sequence:

1. asset manifest;
2. workbook schema inspection;
3. fixed sample-row inspection;
4. full Unicode identity gate;
5. source evidence and GF0017 gates.

The skill now states that schema or sample success is not release readiness.

## Why A Stage Summary Is Needed

A stage summary is needed because the project now has enough completed gates to
create a reliable handoff boundary.

Without a summary, future work may confuse:

- legacy test data with release data;
- workbook schema validity with row-level authority;
- Unicode identity success with GF0017 success;
- Agent-standard output with national-standard evidence;
- CNBE32 compact-field consistency with full Hanzi knowledge evidence.

The next stage should be documented before batch scoring starts.

## Recommended Summary Artifact

Recommended next artifact:

`reports/FULL_CATALOG_PRE_GF0017_HANDOFF.md`

It should include:

- source workbook and SHA-256;
- completed gate list;
- row count and identity summary;
- field mapping;
- known boundaries;
- next stage entry criteria;
- explicit non-goals;
- resume and blocker rules.

## Next Stage Recommendation

The next stage should be:

`source evidence and GF0017 preflight`

Do not start full GF0017 scoring immediately. First build a preflight plan that
maps each v4_fixed column to the fields required by:

- Unicode identity;
- 8105 scope;
- stroke count;
- stroke shape;
- stroke order;
- component validity;
- component-name validity;
- radical validity;
- independent-character rule;
- structure-first decomposition;
- legacy-to-Agent structure localization.

## Non-Goals

This report does not:

- modify `data/`;
- rewrite the workbook;
- rewrite the SQLite database;
- change encoding rows;
- certify source evidence;
- run GF0017 scoring;
- create a release;
- create a tag;
- publish to PyPI.

## Decision

Proceed with a workflow summary before entering source evidence and GF0017
preflight.

