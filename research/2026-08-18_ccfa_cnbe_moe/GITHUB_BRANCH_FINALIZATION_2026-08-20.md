# GitHub Branch Finalization

Date: 2026-08-20

## Result

- Remaining remote branches: 0 (only `main`)
- Main head: `b47ab4a3459fcb43d79439b005e879fa3aec84de`
- Merged into main: 3 branches
- Archived / deleted: 25 branches

## Merged

```text
docs/readme-evidence-boundary-20260728
docs/strict-evidence-correction-20260819
data/basic-cjk-scope-gap
```

## Archived / Deleted

```text
chore/repository-structure-hardening
chore/post-v1.0.3-release-hardening
data/full-catalog-builder
data/v4-fixed-sample-inspector
docs/add-research-position-statement
docs/document-copilot-agent-limitation
docs/enable-copilot-agent-readiness-api
docs/fix-github-agent-filename
docs/harden-experiment-claims-and-format-guards
docs/normalize-historical-claims
docs/readme-geek-polish
docs/readme-runtime-21178
docs/redesign-v1-v4-llm-experiments
docs/redesign-v5-v10-experiment-protocols
docs/register-github-agent-profile
docs/research-origin-readme
docs/sync-multilingual-readmes
docs/sync-v10-archived-claims
feat/penc276-authorized-encoding
fix/p0-python-sdk-hardening-clean
impl/c-rust-golden-vector-consistency
release/prepare-v1.0.3-sdk-hardening
release/readiness-baseline
spec/add-golden-vectors
test/legacy-ai-encoding-baseline
```

## Notes

- Merges were performed via git and pushed directly to `main`; PRs #57 and #58 now have their content in main but remain open in the GitHub UI and should be closed manually.
- PR #38 was archived because it conflicted with main; its branch is deleted and the PR should be closed in the GitHub UI.
- Full branch backups are stored locally under `work/github-branch-backup-2026-08-20.bundle` and `work/github-branch-backup-2026-08-20-v2.bundle`.
