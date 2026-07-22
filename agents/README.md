# CNBE Agent Directory

This directory is the public top-level entry point for CNBE Agent work.

It is intentionally a non-destructive structure bridge. It makes the current
Agent workflow visible at repository root while preserving the existing
`skill/`, `.github/agents/`, documentation, evidence, and script paths.

## Purpose

CNBE now treats Agent-driven structure encoding as a core project method, not
as an auxiliary tool hidden under implementation scripts.

The top-level `agents/` directory gives contributors one stable place to find:

- the current standards-aligned Agent entry point;
- the difference between portable skills and GitHub-native profiles;
- reproducible invocation contracts;
- run report templates;
- the non-goals that prevent accidental database, release, or PyPI changes.

## Source Of Truth

The full operational skill remains:

```text
skill/cnbe-hanzi-structure-encoding-agent/SKILL.md
```

The GitHub-native profile remains:

```text
.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md
```

The historical skill remains:

```text
skill/SKILL.md
```

That historical skill is retained for experiment reproduction only. It must
not be used as authority for current structure, radical, stroke, teaching, or
release-track encoding claims.

## Directory Map

| Path | Role |
|---|---|
| `agents/README.md` | Human-facing index for Agent-driven CNBE work |
| `agents/skills/README.md` | Pointer map for portable skills and GitHub profiles |
| `agents/manifests/README.md` | Invocation contract rules for reproducible runs |
| `agents/manifests/cnbe-hanzi-structure-encoding-agent.invocation.json` | Example manifest for the current Agent |
| `agents/templates/README.md` | Template index for review and run reports |
| `agents/templates/cnbe-agent-run-report.md` | Human-readable run report template |
| `skill/` | Existing portable Codex skill store |
| `.github/agents/` | GitHub-native Agent profile adapter |

## Authority Boundary

Every Agent run must preserve these boundaries:

- Unicode identity is checked before decomposition or scoring.
- 8105 is the national-standard release-track core.
- Outside-8105 rows are Agent-standard candidates until evidence gates approve
  project-level mappings.
- GF, GB, and GG language-writing standards control structure work.
- Dictionaries, ZDIC, Wikipedia, OCR text, and older CNBE rows are review
  context unless explicitly promoted by a governed evidence workflow.
- CNBE32 is a compact runtime carrier, not the authority source.
- CNBE64 and CNBE128 may preserve evidence that does not fit inside CNBE32.

## Non-Destructive Structure Policy

This directory does not delete, move, or rewrite existing content.

Future cleanup may migrate files into a stricter layout, but that requires a
separate migration report, path compatibility plan, and explicit human review.
Until then, `agents/` is the visible index layer and existing paths remain
valid.

## Required Run Contract

Before batch work, an Agent run must declare:

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

Runs that cannot declare this contract are planning drafts, not authoritative
CNBE encoding or audit work.

## Stop Gates

Stop immediately if:

- Unicode identity is ambiguous;
- a structure label falls outside the approved structure set;
- 8105 and non-8105 authority levels are mixed;
- dictionary or network context is treated as direct national-standard output;
- batch quality fails GF0017-style normativity gates;
- a run would rewrite databases, source tables, tags, releases, or PyPI
  artifacts without explicit authorization.
- a database rebuild is requested without a separate human-approved runtime
  data round.

## Related Documents

- `docs/REPOSITORY_STRUCTURE.md`
- `docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`
- `docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md`
- `docs/CNBE8105_ENCODING_GOVERNANCE.md`
- `docs/DATA_REPRODUCIBILITY_CONTRACT.md`
- `docs/COPILOT_CLOUD_AGENT_LIMITATION.md`
