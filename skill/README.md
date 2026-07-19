# CNBE Repository Skills

This directory contains reusable Codex skill material that belongs to the
repository.

## Current Operational Agent

The current standards-aligned Hanzi encoding Agent is:

```text
skill/cnbe-hanzi-structure-encoding-agent/SKILL.md
```

It is also listed for Agent discovery at:

```text
skill/agents/cnbe-hanzi-structure-encoding-agent.yaml
```

It is exposed to GitHub's repository Agents page at:

```text
.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md
```

Use it for CNBE32/CNBE64/CNBE128 structure encoding planning, 8105 alignment,
GF0017 gates, source-evidence workflow design, review packets, and batch
quality control.

This Agent is the repository-published entry point for the post-`v1.0.4`
standards restart. It preserves these boundaries:

- Unicode identity is always first.
- 8105 is the national-standard core.
- Outside-8105 rows remain Agent-standard candidates until later evidence
  gates approve a project-level mapping.
- Dictionary, Wikipedia, ZDIC, OCR, and old generated CNBE fields are not
  direct national-standard authority.
- CNBE32 is a compact carrier layer, not the authority.
- Database rebuilds, source-table writes, tags, GitHub releases, and PyPI
  publication require separate authorization.

## Historical Experiment Skill

The legacy file below remains for historical experiment reproduction only:

```text
skill/SKILL.md
```

Its legacy Agent entry is:

```text
skill/agents/openai.yaml
```

It predates the standards restart and must not be used as authority for
structure, radical, stroke, teaching, research, or release-track encoding
claims.
