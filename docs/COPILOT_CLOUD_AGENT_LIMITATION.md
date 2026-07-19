# GitHub Copilot Cloud Agent Status

This repository includes GitHub-facing Agent configuration, but it does not
require GitHub Copilot cloud agent access for open-source reproducibility.

## Current Decision

GitHub Copilot cloud agent is treated as an optional paid integration, not as a
required CNBE project dependency.

The CNBE standards-restart workflow remains reproducible through repository
files, local tools, ordinary GitHub Actions, review packets, and the
repository-published Agent skill:

```text
skill/cnbe-hanzi-structure-encoding-agent/SKILL.md
```

## What Was Configured

The repository keeps these files so maintainers who already have Copilot cloud
agent access can use the same CNBE rules:

```text
.github/agents/cnbe-hanzi-structure-encoding-agent.agent.md
.github/copilot-instructions.md
.github/workflows/copilot-setup-steps.yml
```

These files define the Agent prompt surface, repository-wide Copilot
instructions, and a cloud setup workflow for validation tooling.

## Access Check Result

The repository administrator performed a browser-level smoke test on
2026-07-19:

- The repository `/agents?q=is:open+author:@me` page was available.
- The page showed the Copilot cloud agent task-session list.
- No open task sessions were present.
- A smoke-test issue was created as issue `#35`.
- Assigning the issue to `copilot` through the API did not add an assignee.
- Searching for `copilot` in the issue assignee picker returned no assignable
  Copilot actor.
- The repository settings page displayed `No Copilot cloud agent access`.
- The settings page stated that Copilot Pro, Copilot Pro+, Copilot Business,
  or Copilot Enterprise is required to assign tasks to Copilot.

Therefore, a runnable Copilot cloud agent session was blocked by account or
license access, not by missing repository files.

## Open-Source Reproducibility Boundary

CNBE must remain reproducible without a paid GitHub Copilot cloud agent
license. Required project workflows must therefore be expressible as:

- committed documentation,
- committed tests,
- local scripts,
- review packets,
- GitHub Actions workflows that do not require cloud-agent assignment,
- and human review gates.

Paid Copilot cloud agent features may be used by maintainers as convenience
automation only. They must not become the sole way to run, audit, reproduce, or
release CNBE work.

## Recommended Workflow

Use this order for future Agent work:

1. Read the repository-published Agent skill.
2. Declare the CNBE invocation contract.
3. Run Unicode-first evidence gates.
4. Generate bounded reports or review packets.
5. Run local tests and ordinary CI.
6. Submit changes through normal branches and pull requests.

If a maintainer later enables Copilot cloud agent access, issue `#35` can be
used as a smoke-test template. Until then, `#35` documents the paid-access
blocker and should not be treated as a project failure.

## Non-Goals

This status note does not authorize:

- changing repository security settings,
- disabling firewall or approval policies,
- adding secrets,
- changing version numbers,
- tagging or releasing,
- publishing to PyPI,
- rebuilding CNBE databases,
- or promoting unreviewed Agent-standard rows.
