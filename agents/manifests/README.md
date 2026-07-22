# Agent Invocation Manifests

This directory contains reproducible invocation contracts for CNBE Agent runs.

The goal is to make each Agent task reviewable before it writes data, rebuilds
a database, or claims a standards-aligned result.

## Manifest Purpose

A manifest records the boundary of a run:

- who the operator is;
- which input rows or files are in scope;
- which authority order is allowed;
- which outputs may be produced;
- which outputs are forbidden;
- when the run must stop;
- which commands verify the result.

The manifest is not a result file. It is the contract that makes a result
auditable.

## Required Fields

Each CNBE Agent manifest should include:

- `run_id`
- `operator_role`
- `input_scope`
- `input_artifacts`
- `unicode_gate`
- `authority_order`
- `allowed_outputs`
- `forbidden_outputs`
- `stop_conditions`
- `verification_commands`
- `review_required_before`
- `resume_policy`

## Current Example

The current example is:

```text
agents/manifests/cnbe-hanzi-structure-encoding-agent.invocation.json
```

Use it as a template for 8105-aligned structure audits, GF0017 scoring runs,
and Agent-standard candidate workflows.

## Non-Destructive Rule

Manifests must not authorize hidden rewrites.

If a run needs to modify a source table, runtime JSON, SQLite database, release
note, tag, GitHub release, or PyPI package, the manifest must mark that action
as forbidden unless the human maintainer has issued explicit authorization for
that specific step.

## Resume Rule

Batch runs must be checkpointed.

If quality gates fail, stop the batch, keep the failed row and evidence packet,
and resume only from the recorded checkpoint after review. Do not silently skip
blocked rows.

## Authority Rule

Manifests must separate evidence grades:

- national language and writing standards;
- repository core reference files;
- reviewed local knowledge assets;
- dictionary and character-origin context;
- network lookup context;
- historical AI-generated CNBE fields.

Only the first category is national-standard authority. Other categories may
support review but must not be mislabeled.

