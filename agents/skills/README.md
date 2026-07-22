# Agent Skills Index

This directory explains how the top-level `agents/` entry point connects to
the repository's existing skill and GitHub Agent files.

It does not replace those files. It gives readers a stable map.

## Current Operational Skill

Use this file as the current portable rulebook:

```text
skill/cnbe-hanzi-structure-encoding-agent/SKILL.md
```

It defines the standards-aligned CNBE Hanzi Structure Encoding Agent.

Use it for:

- Unicode-first identity checks;
- 8105 national-standard core alignment;
- Hanzi structure and decomposition review;
- GF0017-style normativity gates;
- batch stop conditions;
- review packet design;
- reproducible Agent run planning.

## Discovery Metadata

The short metadata entry is:

```text
skill/agents/cnbe-hanzi-structure-encoding-agent.yaml
```

That file is a compact discovery record. It should stay aligned with the full
skill, but it is not the full operating rulebook.

## GitHub Profile

The GitHub-native profile is:

```text
.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md
```

That file exposes the current Agent to GitHub-compatible Agent discovery.
GitHub's repository `/agents` page may also show paid cloud Agent task sessions.
An empty cloud task page does not invalidate the committed Agent profile.

## Historical Skill

The older experiment skill is:

```text
skill/SKILL.md
```

It is preserved for historical reproduction. It predates the standards restart
and must not be used as authority for release-track CNBE encoding claims.

## Maintenance Rule

When the Agent workflow changes, update these files together:

- `agents/README.md`
- `agents/skills/README.md`
- `agents/manifests/cnbe-hanzi-structure-encoding-agent.invocation.json`
- `skill/cnbe-hanzi-structure-encoding-agent/SKILL.md`
- `skill/agents/cnbe-hanzi-structure-encoding-agent.yaml`
- `.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md`
- `docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`
- `docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md`

Do not silently diverge the public index, the portable skill, and the GitHub
profile.

## Review Rule

Any Agent change must make the authority boundary clear:

- 8105 is national-standard core.
- Agent-standard output is project-standard output.
- Dictionary and network evidence are context unless promoted by review.
- CNBE32 compact fields cannot override Hanzi evidence.
- Release and PyPI work require separate authorization.

