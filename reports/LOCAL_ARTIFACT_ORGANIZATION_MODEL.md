# Local Artifact Organization Model

## Purpose

This model records how the repository separates committed research artifacts
from local generated assets before pushing the current CNBE 8105 restart work.
It is a push-readiness companion to the runtime promotion, governance workflow,
and reproducible Agent evidence commits.

## Repository State

- Branch: `data/basic-cjk-scope-gap`
- Push state before this model: local branch ahead of
  `origin/data/basic-cjk-scope-gap`
- Runtime core: committed
- Governance workflow: committed
- Reproducible Agent evidence workflows: committed
- Tag, release, PyPI publish: not performed
- 97,686-row full-catalog validation claim: not made

## Commit Model

The local work is organized into four commit groups:

| Group | Commit purpose | Repository role |
|---|---|---|
| Runtime promotion | Promote the human-approved 8105 CNBE32 runtime copy | Runtime data and SQLite package baseline |
| Governance workflow | Codify 8105 governance, README boundaries, SDK notes, and format checks | Public project boundary |
| Reproducible evidence workflows | Add scripts, reports, tests, ZDIC snapshots, and review packets | Research reproducibility trail |
| Local artifact organization | Record committed-vs-local artifact policy | Push-readiness and repository hygiene |

## Committed Asset Classes

The following asset classes are intended to be committed:

- source code under `src/`, `scripts/`, and `tests/`;
- runtime database files explicitly allowed by `.gitignore`;
- bounded evidence reports and reproducible JSON summaries;
- review-packet CSV files;
- small ZDIC text snapshots and representative viewport images;
- governance and technical documentation;
- source manifests needed to reconnect repository work to local knowledge
  assets.

## Local-Only Asset Classes

The following asset classes are intentionally local-only:

- `outputs/`: rendered workbooks, screenshots, previews, and inspection dumps;
- `build/`: cloned external dictionaries, generated SQLite staging databases,
  and temporary extraction products;
- Python, pytest, ruff, and package build caches;
- generated Excel workbooks outside a committed evidence exception;
- full intermediate reports that exceed GitHub single-file limits.

## Explicitly Excluded Large Intermediates

Two generated full-catalog intermediates are not committed because they are
large local build products and can exceed GitHub upload constraints:

| Path | Role | Policy |
|---|---|---|
| `reports/full_catalog_row_level_extraction_results.json` | Full row-level extraction materialization | Regenerate from script; do not commit |
| `reports/full_catalog_agent_mapping_evidence_join.json` | Full Agent mapping evidence join materialization | Regenerate from script; do not commit |

Their companion Markdown summaries, schemas, scripts, and tests are committed
so reviewers can reproduce or audit the workflow without storing the largest
intermediate files in Git.

## Push Gate

Before push, the repository should satisfy:

- `git status --short --branch` shows only intentional ahead commits;
- no tracked file exceeds GitHub's 100 MB single-file limit;
- `PYTHONPATH=src python3 -m pytest` passes;
- `python3 scripts/validate_format_integrity.py` passes;
- `git diff --check` is clean;
- ignored local artifacts remain ignored.

## Boundary

This model does not authorize release work. Pushing this branch is still
separate from creating a PR, tagging, releasing, or publishing to PyPI.
