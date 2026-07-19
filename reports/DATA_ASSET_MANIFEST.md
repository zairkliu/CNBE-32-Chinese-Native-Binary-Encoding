# CNBE Data Asset Manifest

## Purpose

This manifest classifies the current `data/` directory before any repository
reorganization, database reconstruction, or branch-specific promotion work.

It is read-only evidence. It does not move files, delete files, rewrite
databases, change encoding rows, create release tags, or publish packages.

The manifest supports the two-track governance model:

- `test/legacy-ai-encoding-baseline`: legacy AI-generated or AI-assisted test
  baseline.
- `release/standards-agent-baseline`: future standards-aligned release
  reconstruction baseline.

## Audit Method

The audit used local filesystem metadata, file type detection, SHA-256 hashes,
JSON parsing, SQLite table inspection, CSV header inspection, and XLSX workbook
dimension inspection through the XLSX zip/XML structure.

No spreadsheet dependency was installed. The XLSX dimensions were read from the
workbook XML files.

The current machine-readable companion is:

`reports/data_asset_manifest.json`

## Classification Vocabulary

| Class | Meaning |
|---|---|
| `legacy_test_baseline` | Historical CNBE data or report material retained for comparison and reconstruction |
| `runtime_package_data` | Data that may affect package behavior or install/runtime behavior |
| `standards_evidence_manifest` | Structured source or standards-side metadata used by audit tools |
| `generated_or_derived_artifact` | Derived export, compressed database, benchmark output, or generated report |
| `release_reconstruction_candidate` | Asset likely to inform future standards-aligned reconstruction |
| `external_reference_manifest` | Structured record pointing to external or local reference evidence |
| `invalid_or_placeholder_asset` | File that exists but does not contain a usable workbook or structured payload |

## Authority Boundary

Assets in `data/` are not automatically standards-aligned release data.

Legacy spreadsheets, JSON exports, and old databases remain test-version
material unless they pass the CNBE Agent release gates:

1. Unicode identity alignment.
2. Source-grade labeling.
3. 8105 or other national-standard baseline linkage where applicable.
4. Stroke, stroke-shape, stroke-order, component, radical, and structure
   evidence.
5. GF0017 scoring with source status.
6. Legacy-to-Agent structure localization.
7. Release reconstruction review.

Dictionary, encyclopedia, and historical reference sources may support review,
but they do not replace national-standard evidence for standard-required fields.

## Inventory Summary

The `data/` directory currently contains 22 tracked files.

Observed high-level groups:

- 4 legacy or generated `.xlsx` workbook paths;
- 5 `.docx` report or whitepaper assets;
- 4 small CSV lookup tables;
- 4 JSON files at `data/`;
- 3 structured source manifests under `data/sources/`;
- 1 SQLite database;
- 2 compressed catalog/database exports.

One workbook path is a 2-byte placeholder and is not a readable XLSX zip file.

## Runtime-Sensitive Assets

### `data/cnbe32.db`

Classification:

- `runtime_package_data`
- `legacy_test_baseline`
- `release_reconstruction_candidate`

Observed evidence:

- SQLite database.
- Table `cnbe32` has 20,902 rows.
- Size: 1,654,784 bytes.

Governance:

- Do not rewrite this database in a documentation or manifest round.
- Treat current rows as legacy baseline rows until release gates pass.
- Any future replacement must include database schema, row count, row-level
  audit summary, and rollback path.

### `data/cnbe32.json`

Classification:

- `legacy_test_baseline`
- `release_reconstruction_candidate`
- `generated_or_derived_artifact`

Observed evidence:

- JSON object with `metadata` and `characters`.
- Size: 4,160,527 bytes.

Governance:

- Preserve as a legacy snapshot for comparison.
- Do not treat as release data without row-level Agent audit.
- Use as one input to detect legacy row fields during reconstruction.

## Workbook Assets

### `data/CNBE_编码目录_修复版_v3.xlsx`

Classification:

- `legacy_test_baseline`
- `release_reconstruction_candidate`

Observed workbook dimensions:

- `CNBE完整编码表`: `A1:N97688`
- `GB 18030-2022标准对比`: `A1:F50`

Governance:

- Keep as a historical full-catalog input.
- Use only after schema extraction and row-level evidence gates.
- Do not cite as a release-quality database by itself.

### `data/CNBE_编码目录_修复版_v4.xlsx`

Classification:

- `legacy_test_baseline`
- `release_reconstruction_candidate`

Observed workbook dimensions:

- `CNBE完整编码表v4`: `A1:P97687`

Governance:

- Treat as a later legacy workbook candidate.
- Compare with v3 and v4 fixed before selecting reconstruction input.

### `data/CNBE_编码目录_修复版_v4_fixed.xlsx`

Classification:

- `legacy_test_baseline`
- `release_reconstruction_candidate`

Observed workbook dimensions:

- `CNBE完整编码表v4_fixed`: `A1:Q97687`

Governance:

- Treat as the likely latest legacy workbook candidate.
- Still requires Unicode, standards, GF0017, and Agent checks before release
  promotion.

### `data/CNBE_编码目录_修复完整版.xlsx`

Classification:

- `invalid_or_placeholder_asset`

Observed evidence:

- Size: 2 bytes.
- File command reports ASCII text with CRLF line terminators.
- XLSX parser reports that it is not a zip file.

Governance:

- Do not use as workbook evidence.
- Keep only as a tracked historical placeholder until a cleanup round decides
  whether to remove or replace it.

## Document Assets

The `.docx` files are treated as historical report assets, not as release data.

Files:

- `data/CNBE-32_v3_全量验证实验白皮书.docx`
- `data/CNBE-32_技术白皮书_发布版.docx`
- `data/CNBE_White_Paper_v3_fixed_GB.docx`
- `data/CNBE_大规模验证实验报告.docx`
- `data/CNBE_编码目录_修复版_v3_完整统计报告.docx`

Classification:

- `legacy_test_baseline`
- `generated_or_derived_artifact`

Governance:

- Preserve as historical context.
- Do not use as authority for release reconstruction fields.
- Any claims in historical documents must be reviewed under current claim
  policy before being cited in public docs.

## Compressed Catalog Assets

### `data/cnbe_catalog_fixed.csv.gz`

Classification:

- `legacy_test_baseline`
- `generated_or_derived_artifact`
- `release_reconstruction_candidate`

Observed evidence:

- Gzip archive originally named `cnbe_catalog_fixed.csv`.
- Original size modulo 2^32: 4,926,072 bytes.

Governance:

- Treat as a derived legacy catalog.
- Decompress only in a controlled build or review workspace.

### `data/cnbe_catalog_fixed.db.gz`

Classification:

- `legacy_test_baseline`
- `generated_or_derived_artifact`
- `release_reconstruction_candidate`

Observed evidence:

- Gzip archive originally named `cnbe_catalog_fixed.db`.
- Original size modulo 2^32: 5,349,376 bytes.

Governance:

- Treat as a derived legacy database.
- Do not replace runtime database without a release reconstruction round.

## Small Lookup Tables

Files:

- `data/ext_db.csv`
- `data/radix_table.csv`
- `data/stroke_db.csv`
- `data/struct_db.csv`

Classification:

- `legacy_test_baseline`
- `runtime_package_data`
- `release_reconstruction_candidate`

Observed evidence:

- `ext_db.csv`: 3 rows with `unicode`, `hanzi`, `ext_flags`, `sub_type`.
- `radix_table.csv`: 5 rows with `radix_id`, `unicode`, `hanzi`,
  `stroke_count`.
- `stroke_db.csv`: 7 rows with `unicode`, `hanzi`, `stroke_count`.
- `struct_db.csv`: 5 rows with `unicode`, `hanzi`, `struct_id`,
  `struct_name`.

Governance:

- Treat as legacy lookup examples or seed data.
- Rebuild from standards evidence before release use.
- Do not silently infer release radical or structure maps from these files.

## Source Manifests

Files:

- `data/sources/cnbe-research-local.json`
- `data/sources/hanzi-standard-learning.json`
- `data/sources/unihan-17.0.0.json`

Classification:

- `standards_evidence_manifest`
- `external_reference_manifest`

Observed evidence:

- `cnbe-research-local.json` records local research source roots and authority
  boundaries.
- `hanzi-standard-learning.json` records standard-learning terms, structures,
  standards, and gates.
- `unihan-17.0.0.json` records Unicode source metadata.

Governance:

- Keep as source and evidence manifests.
- These files point to or summarize evidence; they are not replacement
  standards.
- Use them to route audits and reproduce source decisions.

## Experiment Output Assets

Files:

- `data/benchmark_results.json`
- `data/v3_experiment_results.json`

Classification:

- `generated_or_derived_artifact`
- `legacy_test_baseline`

Observed evidence:

- `benchmark_results.json` has `lookup_speed_us` and `stroke_correlation`.
- `v3_experiment_results.json` has experiment result keys including `E1` and
  few-shot experiment entries.

Governance:

- Preserve as historical experiment outputs.
- Do not cite as release evidence without a current audit report.

## Release Reconstruction Candidate Set

Initial candidate assets for future release reconstruction:

- `data/CNBE_编码目录_修复版_v4_fixed.xlsx`
- `data/CNBE_编码目录_修复版_v4.xlsx`
- `data/CNBE_编码目录_修复版_v3.xlsx`
- `data/cnbe32.json`
- `data/cnbe32.db`
- `data/cnbe_catalog_fixed.csv.gz`
- `data/cnbe_catalog_fixed.db.gz`
- `data/sources/hanzi-standard-learning.json`
- `data/sources/cnbe-research-local.json`
- `data/sources/unihan-17.0.0.json`

These files are candidates only. They do not become release outputs until a
future reconstruction batch passes its gates.

## Required Next Gates

Before any file movement:

1. Confirm whether tracked `.docx` files should remain in `data/` or move to an
   archive path.
2. Confirm whether legacy workbook files remain tracked or become external
   release artifacts.
3. Decide whether `data/CNBE_编码目录_修复完整版.xlsx` is retained as a
   placeholder or removed in a dedicated cleanup PR.
4. Build schema extractors for v3, v4, and v4 fixed workbooks.
5. Compare workbook row counts and column schemas.
6. Confirm which file is the first reconstruction input.
7. Run Unicode-first row identity checks.
8. Run standards evidence and GF0017 gates.
9. Produce checkpointed reconstruction reports.

## Non-Goals

This manifest does not:

- change `data/`;
- change `src/cnbe32/data/cnbe32.db`;
- change package metadata;
- change branch contents outside documentation and format checks;
- publish a release;
- create a tag;
- publish to PyPI;
- declare legacy data ready for teaching;
- declare legacy data ready for research citation;
- promote Agent-standard output to national-standard output.

## Recommended Next Branch

Recommended next branch:

`data/asset-manifest`

Recommended commit scope:

- add this report;
- add `reports/data_asset_manifest.json`;
- add both files to format integrity checks.

## Acceptance Checklist

- format integrity passes;
- pytest passes;
- JSON manifest parses;
- remote raw line endings are LF;
- changed files are limited to manifest reports and format checks;
- no `data/` asset is modified;
- no release, tag, or PyPI action is performed.
