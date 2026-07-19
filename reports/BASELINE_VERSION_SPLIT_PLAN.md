# Baseline Version Split Plan

## Purpose

This report records the first clean-baseline plan for splitting the repository
governance model into a legacy test version and a standards-aligned release
version.

It is a planning and audit artifact. It does not modify encoding rows,
databases, release tags, package metadata, or PyPI state.

## Current Baseline

The remote `main` branch is the authoritative baseline for this planning round.

At the time this plan was prepared, `main` had already received:

- repository structure boundary documentation;
- repository asset inventory documentation;
- evidence-layer documentation for 8105, GF0017, Agent standard, and random
  validation artifacts;
- format integrity checks that include the repository governance reports.

Local checkout state may lag behind remote `main` because network fetches have
been intermittent. Therefore remote GitHub API and raw GitHub checks are treated
as the publication surface for this round.

## Target Branches

Two remote branches should be used as governance anchors:

| Branch | Classification | Initial source |
|---|---|---|
| `test/legacy-ai-encoding-baseline` | Legacy test version | current remote `main` |
| `release/standards-agent-baseline` | Standards-aligned release preparation | current remote `main` |

Both branches can point to the same commit at creation time. Their difference is
their allowed future use.

## Test Version Definition

The test version represents the original project encoding material as a legacy
test baseline.

It should be understood as:

- historical AI-generated or AI-assisted encoding work;
- useful for comparison and reconstruction planning;
- not yet aligned row-by-row with national language standards;
- not yet accepted by the current skill and Agent workflow;
- not yet suitable as a research or teaching foundation;
- not a release candidate database.

This branch should preserve legacy data for auditability. It should not be used
to publish claims about national-standard alignment.

## Release Version Definition

The release version is the future reconstruction target.

It should be based on:

- Unicode-first identity;
- 8105 as the core national-standard baseline for the current scope;
- GB, GF, GG, and related official language standard evidence;
- GF0017 quality scoring and stop-on-blocker behavior;
- component, radical, stroke, stroke-shape, stroke-order, and structure evidence;
- CNBE Agent workflow coordination;
- clear separation of national-standard output and Agent-standard output;
- CNBE32 compact fields plus CNBE64 and CNBE128 evidence archives where needed.

The release branch should be used only after a reconstruction batch has a
reviewed plan, a checkpoint path, and acceptance gates.

## Required Evidence For Release Reconstruction

Each release reconstruction batch must record:

1. Unicode code point and normalization status.
2. Scope membership.
3. Source-grade labels.
4. Structure label from the allowed Agent structure set.
5. Stroke count.
6. Stroke-shape evidence.
7. Stroke-order evidence.
8. Component list.
9. Component-name evidence.
10. Character-component and non-character-component classification.
11. Basic component evidence.
12. Radical.
13. Side component when applicable.
14. Glyph-form and independent-character status.
15. GF0017 50-point score and status.
16. Legacy CNBE value snapshot.
17. Proposed release CNBE value.
18. CNBE64 or CNBE128 archive fields where CNBE32 cannot retain enough evidence.
19. Blocker or repair class.
20. Checkpoint and resume offset.

## Explicit Boundary For Reference Sources

National standards are the primary authority for standard-required fields.

Dictionary, encyclopedia, and historical reference sources may support
interpretation, explanation, or cross-checking. They do not replace official
standard evidence where such evidence is required.

The release workflow may use sources such as:

- Cihai;
- Kangxi Dictionary;
- Hanzi etymology references;
- Zhonghua dictionary references;
- offline Chinese Wikipedia extracts;
- other reviewed scholarly or reference sources.

These sources must be labeled by source grade.

## Version Relationship

The test version is not discarded. It becomes the comparison baseline.

The release version does not inherit a legacy row as authoritative merely
because it exists in the test version. Release reconstruction must either:

- confirm and preserve the row with evidence;
- repair the row with evidence;
- move extended details into CNBE64 or CNBE128 archives;
- isolate the row as a blocker;
- defer the row to human review.

## Branch Safety Rules

For `test/legacy-ai-encoding-baseline`:

- no release tags;
- no PyPI publishing;
- no release claims;
- no database promotion;
- no deletion of legacy evidence without review.

For `release/standards-agent-baseline`:

- no batch continuation after a blocker;
- no database rewrite without explicit authorization;
- no CNBE32 compression that hides required evidence;
- no Agent-standard output described as national-standard output;
- no release tag until release-specific checks are authorized.

For `main`:

- only reviewed work should merge;
- structure and governance docs may merge before data migration;
- release work remains separate from governance work.

## Clean Baseline Procedure

The clean baseline procedure is:

1. Resolve current remote `main` SHA.
2. Create or update `test/legacy-ai-encoding-baseline` at that SHA.
3. Create or update `release/standards-agent-baseline` at that SHA.
4. Add governance documentation through a review branch.
5. Validate format integrity.
6. Run tests.
7. Open a PR for the documentation only.
8. Do not merge until CI passes.
9. Do not tag, release, or publish.

## Acceptance Criteria

This planning round is accepted only if:

- both intended branch anchors exist or their creation failure is recorded;
- governance documentation is versioned;
- format integrity passes;
- pytest passes;
- changed files are limited to governance documents and format checks;
- remote raw files use LF line endings;
- no source database is changed;
- no runtime package behavior is changed.

## Next Work After Acceptance

The next work should be a data manifest round. It should classify existing data
assets into:

- legacy test baseline;
- runtime package data;
- standards evidence;
- generated local output;
- release reconstruction candidate;
- external reference manifest.

Only after that manifest is reviewed should the project start experimental
reconstruction of test-version content into the release-version workflow.
