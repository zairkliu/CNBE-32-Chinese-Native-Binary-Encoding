# CNBE-32 Full Catalog Database Workflow

## Status

The full catalog database is an experimental, separately built data artifact.
It is not the database bundled with the Python SDK.

The current source workbook contains 97,686 auditable catalog rows. The
packaged SDK database contains 20,902 rows and keeps its existing compatibility
contract. The full catalog must remain separate until the Basic CJK scope
difference and public API behavior have been reviewed.

## Release Boundary

This workflow does not:

- replace `data/cnbe32.db`;
- replace `src/cnbe32/data/cnbe32.db`;
- alter the `cnbe32` Python package API;
- change the project version;
- create a Git tag or GitHub Release;
- upload an artifact to PyPI;
- claim external semantic correctness for every catalog assignment.

The audit establishes internal consistency with the documented CNBE-32
bitfield formula. It does not independently establish the linguistic authority
or provenance of every radical, stroke, or structure assignment.

## Inputs

The workflow requires:

1. The source `.xlsx` catalog.
2. The repository checkout containing the audit and build scripts.
3. Python 3.10 or newer with the standard library.

The scripts do not require `openpyxl`. They read the workbook package and sheet
XML directly, which keeps the build dependency surface small.

The source workbook is intentionally not tracked in Git. Record its SHA-256 in
the feasibility report and build manifest before accepting an artifact.

## Stage 1: Audit

Run the read-only audit from the repository root:

```bash
python scripts/audit_full_catalog_xlsx.py \
  /path/to/CNBE_编码目录_修复版_v3.xlsx \
  --output reports/full_catalog_feasibility.json
```

The audit must return `FULL CATALOG AUDIT PASS` and exit with status zero.

The audit checks:

- required worksheet and column presence;
- exactly 97,686 data rows;
- required-value completeness;
- row parseability and sequence continuity;
- character and Unicode agreement;
- character, Unicode, and CNBE uniqueness;
- Hex, Dec, and Bin representation agreement;
- 32-bit CNBE bitfield recomputation;
- field limits;
- structure code/name consistency;
- Unicode-block and structure distributions;
- source file SHA-256;
- the scope difference from the packaged SDK database.

Do not run the builder if `summary.status` is not `PASS` or
`summary.sqlite_build_gate` is not `GO`.

## Stage 2: Build

Build the isolated database:

```bash
python scripts/build_full_catalog_db.py \
  /path/to/CNBE_编码目录_修复版_v3.xlsx
```

Default outputs:

- `build/full_catalog/cnbe32_full.db`
- `reports/full_catalog_build.json`

The `build/` directory and database binaries are ignored by Git. The JSON
manifest is suitable for review and source control.

The builder verifies that the source SHA-256 still matches the PASS audit
report. It writes to a temporary SQLite file, uses one transaction, verifies
the completed database, and atomically replaces the output only after all
checks pass.

## Database Schema

The `metadata` table stores:

- schema version;
- catalog scope;
- source SHA-256;
- audit report schema version;
- expected row count;
- CNBE bitfield formula.

The `cnbe32_full` table stores:

- Unicode code point;
- character;
- CNBE integer;
- radical field;
- stroke field;
- structure code and name;
- index field;
- extension field;
- Unicode block;
- source sequence.

Unicode, character, CNBE, and source sequence are independently unique. Field
ranges are protected with SQLite `CHECK` constraints. Indexes support CNBE,
character, radical, stroke, structure, and Unicode-block lookup patterns.

## Stage 3: Verify

The build manifest must report PASS for:

- SQLite `integrity_check`;
- row count;
- Unicode uniqueness;
- character uniqueness;
- CNBE uniqueness;
- source-sequence uniqueness and bounds;
- bitfield recomputation;
- Unicode-block reconciliation;
- structure-distribution reconciliation.

For reproducibility, build twice with the same source and environment and
compare the database SHA-256 values. Regenerating a PASS audit report for the
same source must not change the database hash. The manifest separately records
the accepted database hash and the exact audit report hash used by that run.

## Stage 4: Query

The query tool always opens SQLite in read-only mode.

Query by character:

```bash
python scripts/query_full_catalog_db.py --char 一
```

Query by Unicode code point:

```bash
python scripts/query_full_catalog_db.py --unicode U+20000
```

Query by CNBE value:

```bash
python scripts/query_full_catalog_db.py --cnbe 0x01080000
```

Inspect metadata, integrity, and distributions:

```bash
python scripts/query_full_catalog_db.py --stats
```

Use `--db /path/to/cnbe32_full.db` when the artifact is not at the default
build path. A missing record exits with status 1. Invalid input or an invalid
database exits with status 2.

## Distribution Recommendation

The recommended first distribution channel is a versioned GitHub Release
asset accompanied by:

- the SQLite database;
- `full_catalog_build.json`;
- checksums;
- the source-workbook identity and provenance statement;
- the schema version and compatibility notes.

Do not bundle the full database into the wheel in the first release. Keeping it
separate avoids silently increasing every Python installation, preserves the
existing SDK behavior, and allows the data artifact to follow its own review
and update cadence.

PyPI packaging should be reconsidered only after:

- the 20,992 versus 20,902 Basic CJK difference is resolved;
- license and redistribution rights for the source catalog are documented;
- update and deprecation policies are defined;
- download size and installation impact are accepted;
- public lookup API behavior is specified and tested;
- an external validation sample has been reviewed.

## CI Policy

Normal CI runs unit tests against a small temporary SQLite fixture. It does not
require the untracked source workbook or full database artifact.

A future release-artifact job may download an approved source file from a
controlled location, rerun the audit and builder, compare checksums, and upload
the resulting database. That job must use pinned inputs and must not run for
untrusted pull requests with release credentials.

## Current Decision

The project may continue developing and reviewing the experimental full
catalog database tooling. Publishing, SDK integration, and replacement of the
packaged database remain separate decisions requiring explicit authorization.
