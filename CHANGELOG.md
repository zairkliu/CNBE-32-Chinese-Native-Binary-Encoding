# Changelog

All notable changes to CNBE-32 will be documented in this file.

## [Unreleased]

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
