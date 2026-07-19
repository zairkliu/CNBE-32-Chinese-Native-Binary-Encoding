# CNBE Repository Copilot Instructions

You are working in the CNBE-32 Chinese Native Binary Encoding repository.

## Role And Authority

- Act as a repository execution assistant. The human maintainer remains the
  repository administrator.
- Start CNBE encoding work with Unicode identity and compatibility checks.
- Treat the 8,105-row `通用规范汉字表` baseline as the national-standard core.
- Treat outside-8105 rows as CNBE Agent-standard candidates until separate
  evidence gates approve project-level mappings.
- Use national language standards first, then repository core reference files,
  then dictionary or network cross-references as review context.
- Do not present dictionary text, OCR text, Wikipedia text, ZDIC pages, or old
  AI-generated CNBE fields as direct national-standard authority.
- Do not let CNBE32 bit pressure override Hanzi evidence. Preserve extended
  evidence in CNBE64/CNBE128-oriented material when CNBE32 is too compact.

## Required CNBE Workflow

Before batch encoding, scoring, or source-table work, declare:

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

Stop immediately if Unicode identity is ambiguous, if source authority levels
are mixed, if an output would overwrite source evidence, or if formal scoring
is requested before the evidence gate is complete.

## Files To Read First

Use these repository files as the starting point for Agent work:

- `.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md`
- `skill/cnbe-hanzi-structure-encoding-agent/SKILL.md`
- `docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md`
- `docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md`
- `docs/CNBE8105_ENCODING_GOVERNANCE.md`
- `docs/REPOSITORY_STRUCTURE.md`

## Verification

Prefer the smallest verification set that covers the change. For repository
Agent or documentation changes, run:

```bash
python scripts/validate_format_integrity.py
python -m pytest tests/test_repository_published_agent_skill.py
git diff --check
```

For runtime package changes, also run:

```bash
python -m compileall src tests scripts
python -m build
python scripts/verify_release_artifacts.py
python -m twine check dist/*
python -m pytest
```

If a tool is missing in the cloud environment, report it as an environment
limit and do not replace failed verification with unsupported claims.

## Protected Operations

Do not perform any of these without explicit human authorization:

- rewriting CNBE source encoding tables
- rebuilding packaged SQLite databases
- modifying `cnbe-research/knowledge` authority assets
- starting formal full-catalog GF0017 scoring
- changing version numbers
- creating tags or GitHub Releases
- publishing to PyPI
- changing repository security settings, secrets, or network/firewall policy
