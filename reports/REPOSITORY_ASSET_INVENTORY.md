# CNBE-32 Repository Asset Inventory

## Purpose

This report records the repository asset inventory after the standards evidence
workflow and repository structure boundary work.

It is intentionally conservative. It does not move, delete, rewrite, compress,
or relabel any project asset.

The goal is to make the next cleanup round reproducible, auditable, and safe for
an open-source project whose research data, runtime package, experimental files,
and evidence records now coexist in one repository.

## Audit Scope

Repository: `zairkliu/CNBE-32-Chinese-Native-Binary-Encoding`

Main branch state used for remote verification: after PR #18.

Local checkout note: the local checkout may remain on an older branch because
GitHub HTTPS fetches were intermittently failing. Remote GitHub API and raw
checks are therefore treated as the authoritative publication surface for merged
changes in this audit round.

This report covers the repository layout visible in the current working tree and
the remote-main structure already documented by `docs/REPOSITORY_STRUCTURE.md`.

## Top-Level Asset Classes

### 1. Core Runtime Assets

Core runtime assets are files required to install, import, test, or use the
published Python package and its cross-language golden-vector checks.

Primary examples:

- `src/cnbe32/`
- `src/cnbe32/data/cnbe32.db`
- `spec/`
- `tests/`
- `c/golden_vectors/`
- `rust/golden_vectors/`
- `bindings/`
- `pyproject.toml`
- `MANIFEST.in`

Handling rule: do not move or rename these files without a package import test,
wheel build test, and release-artifact check.

### 2. Standards Evidence Assets

Standards evidence assets record the renewed 8105-centered, GF0017-scored,
Unicode-first research workflow.

Primary examples:

- `evidence/README.md`
- `evidence/8105/`
- `evidence/gf0017/`
- `evidence/agent-standard/`
- `evidence/validation/random-150/`
- `reports/CNBE_RESEARCH_EVIDENCE_WORKFLOW.md`
- `reports/ENCODING_WORK_PREP_READINESS.md`

Handling rule: keep these files versioned because they are review evidence, not
temporary build output.

### 3. Data Assets

Data assets include legacy spreadsheets, generated databases, compressed tables,
small source manifests, and older whitepaper source files.

Primary examples:

- `data/cnbe32.json`
- `data/cnbe32.db`
- `data/cnbe_catalog_fixed.csv.gz`
- `data/cnbe_catalog_fixed.db.gz`
- `data/sources/`
- `data/*.xlsx`
- `data/*.docx`

Handling rule: classify each file before moving it. Runtime data, source
evidence, generated data, and legacy document artifacts must not be mixed in a
single cleanup commit.

### 4. Historical Experiment Assets

Historical experiment assets preserve LLM and validation experiment history.

Primary examples:

- `llm_experiments/`
- `experiments/`
- `results/`
- `cnbe-llm training(demo)/`

Handling rule: keep them as historical archives unless a human authorizes an
archive move. Do not rewrite their claims while doing structural cleanup.

### 5. Hardware And System Assets

Hardware and system assets include RISC-V, Linux, Verilog, WASM, C headers, and
simulator material.

Primary examples:

- `hardware/`
- `riscv/`
- `linux_cnbe32_riscv/`
- `include/`
- `processor.cc.patch`

Handling rule: do not merge these assets into Python package directories. They
need their own future ownership review.

### 6. Generated Local Artifacts

Generated local artifacts are files produced by local builds, tests, packaging,
or review exports.

Observed examples:

- `.pytest_cache/`
- `.ruff_cache/`
- `build/`
- `dist/`
- `scripts/__pycache__/`
- `src/__pycache__/`
- `src/cnbe32/__pycache__/`
- `tests/__pycache__/`
- `src/cnbe32.egg-info/`
- `c/golden_vectors/cnbe32_golden_test`

Handling rule: these should remain ignored and should not be added to normal
feature commits.

## Large Tracked Assets

The repository contains large tracked evidence and data files. These are not
automatically defects, but they require explicit ownership.

Largest observed tracked evidence files include:

- `evidence/gf0017/cnbe8105_gf0017_normativity_scores.json`
- `evidence/agent-standard/cnbe20902_agent_preencoding_test.json`
- `evidence/8105/cnbe8105_encoding_comparison.json`
- `evidence/8105/cnbe8105_standard_baseline.json`
- `evidence/8105/cnbe8105_auto_fix_candidates.json`
- `evidence/8105/cnbe8105_dry_run_patch.json`

Largest observed tracked data files include:

- `data/CNBE_编码目录_修复版_v4.xlsx`
- `data/CNBE_编码目录_修复版_v4_fixed.xlsx`
- `data/CNBE_编码目录_修复版_v3.xlsx`
- `data/cnbe32.json`
- `data/cnbe32.db`
- `data/cnbe_catalog_fixed.db.gz`

Decision: keep the newly created `evidence/` assets in-repo for now because they
are required for reproducible review. Defer any LFS, release-asset, or external
artifact strategy to a separate human-authorized repository policy round.

## Current Ignore Coverage

The current `.gitignore` already covers many local generated artifacts:

- Python bytecode and `__pycache__/`
- editor swap files
- build directories
- distribution artifacts
- egg-info metadata
- local generated data files
- most `.db`, `.db.gz`, `.xlsx`, and `.docx` assets
- the C golden-vector executable

The ignore file includes a duplicated `c/golden_vectors/cnbe32_golden_test`
entry. This is harmless but should be cleaned in a small hygiene commit if the
next round edits `.gitignore`.

## Confirmed Non-Goals

This audit does not:

- delete tracked files
- move tracked files
- rewrite Git history
- change package metadata
- change the runtime CNBE table
- change the 8105 or GF0017 evidence content
- alter tag, release, or PyPI state
- convert evidence JSON into a different storage format
- claim that all historical experiments are scientifically valid

## Cleanup Priority

### Priority 1: Local Working Tree Hygiene

Before any new feature branch, remove ignored local artifacts from the working
tree or keep them ignored and untracked.

Candidate commands for a human-authorized local cleanup round:

- inspect ignored files with `git status --ignored --short`
- remove caches with `git clean -fdX`
- avoid `git clean -fdx` unless the exact untracked file list has been reviewed

### Priority 2: Data Asset Manifest

Create a committed manifest that classifies `data/` files into:

- runtime package source
- generated catalog export
- legacy spreadsheet source
- legacy whitepaper source
- source manifest
- compressed derived artifact

Do this before moving any file out of `data/`.

### Priority 3: Experiment Archive Policy

Create an archive policy for:

- `llm_experiments/`
- `results/`
- `experiments/`
- `cnbe-llm training(demo)/`
- `hardware/`
- `riscv/`
- `linux_cnbe32_riscv/`

The policy should distinguish historical record, active research workflow, and
deprecated generated output.

### Priority 4: Git Ignore Hygiene

Clean duplicate ignore entries and consider adding explicit comments for:

- local SQLite builds
- local review packet exports
- release distributions
- bytecode caches
- compiled C golden-vector binaries

This should remain a no-behavior-change commit.

### Priority 5: Repository Size Strategy

Only after the manifest and archive policy exist, decide whether large evidence
or data files should remain tracked, move to Git LFS, move to release assets, or
be regenerated by scripts.

## Required Review Gate Before Moving Files

Any future move or deletion proposal must include:

- exact source path
- exact target path
- current tracked size
- owner class
- whether the file is imported or packaged
- whether tests reference it
- whether release artifacts reference it
- whether raw GitHub review evidence depends on it
- rollback command

## Recommended Next Branch

Recommended branch name:

`chore/repository-asset-inventory`

Recommended commit scope:

- add this report
- add this report to format integrity checks
- do not change `.gitignore` yet
- do not clean tracked assets yet
- do not move `data/`, `evidence/`, `llm_experiments/`, `hardware/`, or `riscv/`

## Acceptance Checklist

- format integrity passes
- pytest passes
- `git diff --check` passes
- changed files are limited to this report and the format integrity script
- no generated cache files are tracked
- no release, tag, or PyPI action is performed
