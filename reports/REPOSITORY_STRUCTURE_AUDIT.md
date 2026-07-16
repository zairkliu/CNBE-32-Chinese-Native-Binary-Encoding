# Repository Structure Audit

This audit records the repository state after the CNBE standards evidence
workflow was merged. It is a planning artifact for repository organization. It
does not authorize moving source data, rewriting history, creating releases, or
publishing packages.

## Current Role

The repository now contains several distinct layers:

- Python package and SDK runtime.
- CNBE source data and packaged database.
- Standards evidence and reproducibility artifacts.
- Release and documentation files.
- Historical LLM experiments.
- Hardware, RISC-V, and simulator experiments.
- Review reports and generated audit outputs.

The next organization task is to make those layers explicit so contributors can
understand which files are runtime assets, which files are research evidence,
and which files are historical experiments.

## Current Root-Level Observations

The root directory has grown into a mixed workspace. The important directories
are:

| Directory | Current Role | Organization Status |
|---|---|---|
| `src/` | Python package source | Keep as runtime package layer |
| `data/` | Source catalog files, databases, spreadsheets, and legacy documents | Needs separation between runtime data and archived source material |
| `evidence/` | Reproducible standards evidence | Keep as research evidence layer |
| `reports/` | General audit reports and reviewer packets | Keep, but distinguish from evidence snapshots |
| `scripts/` | Reproduction, audit, and maintenance scripts | Keep, but group by workflow in docs |
| `tests/` | Unit, audit, and reproducibility tests | Keep |
| `docs/` | Public documentation and release docs | Keep |
| `llm_experiments/` | Historical LLM experiment reports and workbooks | Candidate for archive policy |
| `results/` | Historical experiment outputs and duplicated reports | Candidate for archive policy |
| `hardware/`, `riscv/`, `linux_cnbe32_riscv/` | Hardware and RISC-V experiments | Candidate for separate domain documentation |
| `build/`, `dist/`, `.pytest_cache/`, `.ruff_cache/` | Local generated artifacts | Must stay ignored and untracked |

## Tracked Binary And Data Artifacts

The repository intentionally tracks some non-source artifacts. These need clear
policy rather than silent deletion:

| Pattern | Current Examples | Recommendation |
|---|---|---|
| Runtime DB | `src/cnbe32/data/cnbe32.db` | Keep packaged runtime DB |
| Legacy DB/source DB | `data/cnbe32.db`, `data/cnbe_catalog_fixed.db.gz` | Review whether these belong in `data/archive/` or release assets |
| Source spreadsheets | `data/*.xlsx`, `llm_experiments/**/*.xlsx` | Archive or document as legacy experiment inputs |
| Word documents | `data/*.docx` | Archive or replace with Markdown summaries |
| Evidence validation workbook | `evidence/validation/random-150/*.xlsx` | Keep as explicit evidence attachment |

No tracked `build/`, `dist/`, `__pycache__`, `.pyc`, or cache directories were
found in the intended submission set.

## Packaging Boundary

The Python package configuration currently includes:

- top-level metadata and README files;
- `docs/releases/*.md`;
- `scripts/*.py`;
- `spec/*.json` and `spec/*.md`;
- package code under `src/`;
- runtime package data: `src/cnbe32/data/cnbe32.db`.

The `evidence/` directory is intentionally not included in wheel or sdist
payloads. That boundary should be preserved.

## Main Risks

1. `data/` mixes runtime-ish artifacts, source catalog spreadsheets, Word
   reports, compressed databases, and small structured sources.
2. `reports/` and `evidence/` are now both audit-oriented, but only `evidence/`
   is intended as complete reproducibility evidence.
3. `llm_experiments/` and `results/` contain historical AI experiment outputs
   that should not be confused with standards-backed evidence.
4. Hardware/RISC-V material is useful but lacks a concise root-level ownership
   map.
5. Root-level documentation does not yet explain the post-standards-restart
   repository layout.

## Recommended Non-Destructive Cleanup Order

1. Add repository structure documentation.
2. Add an archive policy for historical LLM and hardware experiments.
3. Add a data asset inventory before moving any `data/` file.
4. Add checks that prevent generated caches, build output, and accidental
   package artifacts from being tracked.
5. Only after human approval, move legacy spreadsheets/documents into an
   `archive/` or `data/archive/` layout.

## Non-Goals For The Next Commit

- Do not rewrite Git history.
- Do not delete historical experiment files.
- Do not move packaged runtime database files.
- Do not change `pyproject.toml` package metadata without a separate review.
- Do not tag, release, or publish PyPI artifacts.
- Do not modify CNBE source encoding tables.
