# Agent Templates

This directory contains reusable templates for CNBE Agent run records.

Templates are intentionally separate from source data. They help reviewers
understand what was done without giving an Agent permission to rewrite runtime
assets.

## Available Templates

| Path | Purpose |
|---|---|
| `agents/templates/cnbe-agent-run-report.md` | Human-readable report for one Agent run |

## Template Rules

Each report should record:

- the manifest used;
- the exact input scope;
- the Unicode identity gate result;
- the authority sources consulted;
- the output files produced;
- any skipped or blocked rows;
- verification commands and results;
- whether human review is required before the next step.

## Evidence Boundary

Templates must preserve the authority boundary:

- national standards are standards evidence;
- repository knowledge assets are project evidence;
- dictionaries and network sources are review context;
- legacy AI-generated rows are historical baseline data;
- runtime database writes are separate authorized actions.

## Batch Boundary

For batch work, the report must include checkpoint state.

If the batch stopped on a row-level blocker, the report must name the row,
record the reason, and prevent automatic continuation until the blocker is
reviewed.

## Release Boundary

Reports do not authorize release work.

Tag creation, GitHub release publication, and PyPI publication remain separate
human-authorized steps even when a report says all local checks passed.

