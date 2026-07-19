# Changelog

All notable changes to CNBE-32 will be documented in this file.

## [Unreleased]

## [1.0.4] - 2026-07-19

### Added

- Standardized 8105 runtime repair workflow for the post-promotion blocker queue.
- Runtime repair reports and review packets for applied repairs and remaining blockers.
- Historical baseline boundary for legacy AI-generated catalog fields.
- Tests covering standardized runtime repair counts, known samples, database integrity, and release boundary.

### Changed

- Python package version prepared as `1.0.4`.
- Runtime CNBE32 data now records `7310` patched 8105 rows after conservative standardized repair.
- Runtime SQLite databases were rebuilt from the updated 20,902-row runtime source.
- Documentation now separates legacy AI-generated test data from the standards-aligned release track.

### Fixed

- Repaired `598` additional 8105 runtime rows that had enough conservative evidence to preserve runtime index/ext bits and pass CNBE32 bitfield roundtrip.
- Corrected known runtime samples including `队` to `阜 / 4 / 左右 / 3` and `玕` to `王 / 7 / 左右 / 3`.
- Preserved `795` unresolved force-approved rows as explicit blockers rather than inventing missing numeric fields.

### Notes

This release remains a research-prototype SDK checkpoint. It does not claim 97,686-row validation, teaching-ready full-catalog data, production readiness, or outside-8105 national-standard output.

## [1.0.3] - 2026-07-10

### Added

- SDK hardening tests for invalid CNBE-32 decode inputs.
- Ordered database batch lookup coverage with duplicate preservation.
- Format integrity coverage for all packaged Python modules in `src/cnbe32`.
- Strict release artifact filename and count validation.

### Changed

- Python package version prepared as `1.0.3`.
- `batch()` now preserves input order and repeated characters.
- Release artifact verification now requires exactly one `1.0.3` wheel and one `1.0.3` source distribution.

### Fixed

- `decode_cnbe()` and direct `CNBE32(...)` construction now reject invalid code values instead of silently truncating or masking them.
- Removed UTF-8 BOM from the packaged experimental encoder module.
- Release verification now checks the packaged encoder module in wheel and source distributions.

### Notes

This release remains a research-prototype SDK checkpoint. It does not claim full CJK coverage, zero-collision behavior, production readiness, or validated model / hardware performance.

## [1.0.2] - 2026-07-10

### Added

- Release preparation notes for v1.0.2.
- Release artifact verification script.
- CI release artifact verification step.
- Remote format-integrity validation requirement before release.

### Changed

- Python package version prepared as `1.0.2`.
- Release process now requires validating source format integrity before tagging.
- Release checklist now explicitly verifies Python, C, and Rust golden vector consistency.

### Fixed

- Repository-wide format integrity was restored before this release preparation.
- Added safeguards against single-line compressed source, TOML, YAML, Markdown, C, Makefile, and Rust files.

### Notes

This release remains a research-prototype SDK checkpoint. It does not claim full CJK coverage, zero-collision behavior, production readiness, or validated model / hardware performance.

## [1.0.1] - 2026-07-10

### Added

- Release readiness documentation.
- Contribution guidelines.
- Security policy.
- GitHub issue templates.
- Installation smoke tests.
- Hardened Python SDK baseline.
- Strict CNBE-32 bitfield validation.
- True bit-level `bit_hamming_distance`.
- Legacy `field_weighted_distance`.
- Deprecated compatibility wrapper for `hamming_distance`.
- Robust database path resolution using `CNBE32_DB_PATH`, packaged data, and source checkout fallback.
- Explicit `SkillTable.empty()` and `SkillTable.from_file()` construction.
- Machine-readable golden vectors in `spec/golden_vectors.json`.
- Golden vector documentation in `spec/GOLDEN_VECTORS.md`.
- Python golden vector tests.
- Minimal C golden vector consistency test.
- Minimal Rust golden vector consistency test.
- Multilingual README files with scoped research-prototype positioning.

### Changed

- README now separates stable Python SDK scope from experimental research scope.
- 97,686 CJK is documented as an experimental target, not current packaged SDK coverage.
- CI validates Python build, wheel install, pytest, ruff, C consistency tests, and Rust consistency tests.

### Fixed

- Python packaging baseline.
- Single-line file formatting issues.
- `encode_cnbe` now rejects invalid `index` and `ext` values.
- `batch("")` and `batch([])` now return an empty list.
- `SkillTable()` no longer silently creates an all-zero table.

### Notes

This release remains a research-prototype SDK. It does not claim full CJK coverage, zero-collision behavior, production readiness, or validated model/hardware performance.
