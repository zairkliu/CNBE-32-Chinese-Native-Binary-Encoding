# CNBE Version Governance

## Purpose

This document defines the project governance boundary between the legacy test
version and the standards-aligned release version of CNBE encoding work.

It is a repository policy document. It does not change the current database,
encoding table, package behavior, release tag, or PyPI state.

## Governance Summary

CNBE now uses a two-track version model:

| Track | Intended branch | Role |
|---|---|---|
| Test version | `test/legacy-ai-encoding-baseline` | Historical and experimental baseline for legacy AI-generated encoding assets |
| Release version | `release/standards-agent-baseline` | Standards-aligned baseline for future CNBE32, CNBE64, and CNBE128 work |

Both tracks may start from the same repository commit. The distinction is a
governance distinction until future authorized implementation work changes data,
code, reports, or generated assets.

## Test Version

The test version is the project-controlled home for legacy encoding material.

It includes the original CNBE encoding data and historical experiment material
as a test baseline. These assets are useful for comparison, regression checks,
error localization, and reconstruction planning.

The test version must be treated as non-authoritative for research and teaching
until the relevant rows pass the standards-aligned workflow.

### Test Version Classification

For project governance, the legacy test version is classified as:

- AI-generated or AI-assisted historical encoding material;
- not yet aligned row-by-row to GB, GF, GG, and related national language
  standards;
- not yet passed through the project skill audit gates;
- not yet validated against the full standards evidence database;
- not yet validated through the current GF0017 scoring workflow;
- not yet cross-checked through the current authoritative reference strategy;
- not a basis for public research claims;
- not a basis for teaching materials;
- not a release-quality encoding database.

This classification is deliberately conservative. It is used to prevent old
experimental rows from being mistaken for the renewed standards-aligned output.

### Allowed Test Version Uses

The test version may be used for:

- legacy behavior comparison;
- error class discovery;
- field distribution analysis;
- replaying older experiments under clearer labels;
- building migration candidate lists;
- measuring how much work remains before standards alignment;
- documenting historical project context.

### Disallowed Test Version Uses

The test version must not be used to:

- claim national-standard alignment;
- claim teaching readiness;
- claim research-grade validity;
- publish a new runtime database;
- create a release tag;
- publish to PyPI;
- overwrite the release-version database;
- silently promote a legacy row into the release track.

## Release Version

The release version is the future standards-aligned CNBE baseline.

It uses the CNBE32, CNBE64, and CNBE128 encoding ideas together with the project
skills and Agent workflow. The release version is not merely a copy of the old
database. It is a controlled reconstruction path.

### Release Version Foundations

The release version must be based on:

- Unicode identity alignment as the first gate;
- the 8105 common standardized Chinese character table as the core national
  baseline for the current project scope;
- GB, GF, GG, and related national language standard evidence where applicable;
- GF0017 keyboard Hanzi glyph input system evaluation rules as a quality model;
- GF0013 independent-character evidence where applicable;
- GF0014 common component and component-name evidence where applicable;
- stroke, stroke shape, stroke order, component, radical, side-component,
  glyph-form, structure, and decomposition evidence;
- the project `cnbe-hanzi-structure-encoding-agent` workflow;
- the project `cnbe-gf0017-batch-audit` stop-on-blocker behavior;
- evidence snapshots committed under `evidence/`;
- reproducible scripts and tests committed under `scripts/` and `tests/`.

### Release Version Reference Strategy

The release track may use multiple reference classes, but their authority must
not be mixed.

National-standard sources include GB, GF, GG, and related official language
standard material.

Cross-reference sources may include dictionaries, encyclopedia material, and
other scholarly or reference works, including sources such as Cihai, Kangxi
Dictionary, Hanzi etymology references, Zhonghua dictionaries, and offline
Chinese Wikipedia extracts.

Cross-reference sources may support review and explanation, but they do not
replace national-standard evidence when a national-standard field is required.

### Release Version Output Levels

Every future release-version row must declare its level:

| Level | Meaning |
|---|---|
| `national_standard` | Directly supported by national-standard evidence |
| `standard_derived` | Derived from direct standards through documented rules |
| `agent_standard` | Accepted by the CNBE Agent after alignment and audit gates |
| `source_gap` | Relevant evidence exists but is not direct enough for release promotion |
| `unresolved` | The row must stop the batch or remain out of release output |

Agent standard output is valid for CNBE project use after gates pass. It must not
be described as national-standard output unless direct evidence exists.

## CNBE32, CNBE64, And CNBE128 Roles

CNBE32 remains the compact runtime-oriented candidate format.

CNBE64 and CNBE128 are reserved for richer archival or research-grade evidence
fields, including full stroke sequences, decomposition trees, source anchors,
component-name evidence, review state, and reconstruction metadata.

CNBE32 bit pressure must not override Hanzi evidence. When evidence does not fit
cleanly into CNBE32, the overflow belongs in CNBE64 or CNBE128 design records.

## Promotion Gate From Test To Release

A row can move from test classification into release consideration only after it
passes all required gates:

1. Unicode identity is recorded and unambiguous.
2. Scope membership is recorded.
3. Structure label is normalized to the allowed Agent structure labels.
4. Component and component-name evidence is recorded.
5. Radical and side-component evidence is recorded.
6. Stroke count, stroke shape, and stroke order evidence is recorded.
7. Independent-character status is checked where applicable.
8. GF0017 scoring is calculated with source status.
9. National-standard and Agent-standard levels are separated.
10. Legacy CNBE fields are preserved for comparison.
11. Repair class and blocker class are recorded.
12. Batch checkpoint is updated.
13. Format integrity and tests pass.
14. Human review authorizes the migration phase.

## Branch Governance

### `main`

`main` remains the public integration branch. It should contain only reviewed
changes.

### `test/legacy-ai-encoding-baseline`

This branch anchors the legacy test baseline. It should not receive release
claims, package releases, or PyPI publishing work.

### `release/standards-agent-baseline`

This branch anchors the standards-aligned release preparation baseline. It is
the intended target for future reconstruction work after plans and review gates
are accepted.

## Required Reporting For Future Work

Every future encoding reconstruction PR must include:

- source branch and target branch;
- affected character count;
- Unicode alignment summary;
- source-grade summary;
- GF0017 score summary;
- national-standard versus Agent-standard distinction;
- blocker and resume summary;
- generated artifact list;
- no-release statement unless a release task is explicitly authorized.

## Non-Goals

This document does not:

- rewrite the existing database;
- move files between branches;
- delete legacy experiments;
- validate all historical rows;
- create a release;
- create a tag;
- publish to PyPI;
- rename the project;
- change the package API.

## Next Implementation Round

The next implementation round should create a data manifest that classifies
runtime data, legacy test data, evidence snapshots, generated assets, and release
candidates.

After the manifest exists, the project can plan controlled reconstruction of
test-version rows into the release-version workflow.
