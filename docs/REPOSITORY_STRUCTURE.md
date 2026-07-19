# Repository Structure

This document describes the intended repository layout after the CNBE standards
restart. It separates runtime package assets, standards evidence, historical
experiments, and maintenance outputs.

## Core Runtime Layer

| Path | Purpose |
|---|---|
| `src/` | Python package implementation |
| `src/cnbe32/data/cnbe32.db` | Packaged runtime database |
| `spec/` | Golden vectors and implementation consistency specs |
| `c/`, `rust/`, `bindings/` | Cross-language golden vector and binding work |
| `tests/` | Runtime, reproducibility, and audit tests |

Runtime-layer changes must preserve package build behavior and pass CI.

## Standards Evidence Layer

| Path | Purpose |
|---|---|
| `evidence/8105/` | 8105 baseline, comparison, repair-candidate, radical-code, and dry-run evidence |
| `evidence/gf0017/` | GF0017 scoring model and normativity score evidence |
| `evidence/agent-standard/` | CNBE Agent standard and legacy structure localization evidence |
| `evidence/validation/` | Human-facing validation attachments |

Evidence files are research and review assets. They are not runtime package
data, and they must not be described as automatic CNBE database changes.

The 8105 layer is the current national-standard core. The Agent-standard and
full-catalog layers must align to it, but they must not be presented as
national-standard output unless direct standards evidence has been joined and
reviewed. See `docs/CNBE8105_ENCODING_GOVERNANCE.md`.

## General Report Layer

| Path | Purpose |
|---|---|
| `reports/` | Audit summaries, reviewer instructions, feasibility reports, and maintenance reports |

Use `reports/` for compact audit summaries and review packets. Use `evidence/`
when the output is a complete reproducibility snapshot.

## Documentation Layer

| Path | Purpose |
|---|---|
| `README.md`, `README_EN.md`, `README_ZH.md` | Public project overview |
| `docs/` | Public documentation and repository structure docs |
| `docs/releases/` | Release documentation |
| `CHANGELOG.md`, `RELEASE.md` | Release process and current release notes |

Documentation must keep the boundary clear between national standards, CNBE
Agent standards, research evidence, and runtime encoding data.

Documentation is part of the reproducibility surface. Public docs must explain
which layer is runtime behavior, which layer is standards evidence, which layer
is Agent workflow, and which layer is historical experiment context.

The operational Agent workflow is defined in
`docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`.

## Skill Layer

| Path | Purpose |
|---|---|
| `skill/README.md` | Skill directory index and authority boundary |
| `skill/cnbe-hanzi-structure-encoding-agent/SKILL.md` | Repository-published total-control Agent for standards-aligned Hanzi encoding |
| `skill/SKILL.md` | Historical experiment-reproduction skill, not release-track authority |

The repository-published Agent skill is the portable entry point for the
post-`v1.0.4` standards restart. It must stay aligned with
`docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md` and
`docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`.

## Historical Experiment Layer

| Path | Purpose |
|---|---|
| `llm_experiments/` | Historical LLM experiment reports and workbooks |
| `results/` | Historical experiment outputs and duplicate report exports |
| `experiments/` | Early experiment scripts and notes |

These directories are historical context. They should not be cited as
standards-backed CNBE encoding authority unless a later evidence workflow
explicitly upgrades a result.

## Hardware And System Experiment Layer

| Path | Purpose |
|---|---|
| `hardware/` | Simulator, Verilog, WASM, and hardware-oriented prototypes |
| `riscv/` | RISC-V experiment files |
| `linux_cnbe32_riscv/` | Linux/RISC-V system experiment tree |
| `tools/` | Supporting tools |

Hardware and operating-system experiments should be documented separately from
the Python package runtime.

## Data Layer

| Path | Purpose |
|---|---|
| `data/` | CNBE source catalogs, databases, spreadsheets, and structured source snapshots |
| `data/sources/` | Small structured source records used by audit tools |

The `data/` directory needs a separate asset inventory before any files are
moved. Do not move or delete data files without a migration report.

Source catalog rewrites and SQLite database rebuilds are separate authorized
implementation rounds. Governance reports and pilot scoring reports do not, by
themselves, authorize editing runtime package data.

## Generated Local Artifacts

These should remain ignored unless explicitly reviewed:

- `build/`
- `dist/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `*.pyc`
- temporary local workbooks outside `evidence/validation/`

## Cleanup Policy

Repository organization should proceed in small, reviewable steps:

1. Document ownership and boundaries.
2. Add inventory reports.
3. Strengthen ignore rules and format checks.
4. Move archive-only materials only after human approval.
5. Keep release, tag, and PyPI work in separate PRs.
