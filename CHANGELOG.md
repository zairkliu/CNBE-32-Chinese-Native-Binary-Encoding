# Changelog

All notable changes to CNBE-32 will be documented in this file.

## [Unreleased]

### Added

- Release readiness documentation.
- Contribution guidelines.
- Security policy.
- GitHub issue templates.
- Installation smoke tests.

## [1.0.1] - 2026-07-10

### Added

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

This release remains a research-prototype SDK. It does not claim full CJK coverage, 0% collision rate, production readiness, or validated model/hardware performance.
