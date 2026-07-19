# CNBE 8105 Encoding Governance

## Purpose

This document fixes the current repository boundary for the CNBE encoding
rebuild. It is a governance and review document. Earlier pilot stages did not
rewrite the existing source catalog, packaged SQLite database, release tag, or
PyPI package. A later explicit human authorization promoted the approved 8105
CNBE32 runtime copy into `data/cnbe32.json` and rebuilt the packaged SQLite
databases.

The restart goal is broader than a documentation cleanup. CNBE is being rebuilt
as a standards-aligned, Agent-operated, human-reviewable, and research
reproducible Hanzi structure encoding project.

The four project obligations are:

1. encoding must be processed against national language and writing standards;
2. Agent workflows must enforce the same gates every time;
3. repository structure must separate runtime code, evidence, reports, and
   historical experiments;
4. every promoted result must be reproducible from committed scripts, evidence,
   review packets, and tests.

## Core Position

The 8105 common standardized Chinese character table is the national-standard core for the current CNBE standards restart.

All other catalog work must align around this core:

| Scope | Repository role | Public claim boundary |
|---|---|---|
| 8105 standardized characters | National-standard core | May be treated as the authoritative rebuild baseline after evidence gates pass |
| Existing Basic CJK runtime rows | Legacy/current package data | May be used for comparison and runtime compatibility, not as standards-aligned proof |
| 20,902 Agent pre-encoding rows | Agent-standard candidate pool | May be used as project candidate output, not as national-standard output |
| 97,686 full catalog target | Extended research target | Must not be described as complete, validated, or teaching-ready until audited |

## Current Evidence Snapshot

The current confirmed evidence snapshot is:

- 8105 baseline rows: `8105`
- current CNBE rows inside 8105 scope: `7829`
- missing current CNBE rows inside 8105 scope: `276`
- human-approved 8105 Agent structure baseline: `8105 / 8105`
- approved CNBE32 dry-run rows promoted into runtime copy: `6712`
- conservative standardized runtime repairs after promotion: `598`
- patched 8105 runtime rows after standardized repair: `7310`
- force-approved but not patched rows retained for later strategy: `795`
- production runtime source rows: `20902`
- rebuilt runtime databases: `data/cnbe32.db` and
  `src/cnbe32/data/cnbe32.db`
- release, tag, and PyPI publication: not performed

The main confirmation report is
[`reports/CNBE8105_CORE_CONFIRMATION.md`](../reports/CNBE8105_CORE_CONFIRMATION.md).

The runtime promotion report is
[`reports/8105_CNBE32_RUNTIME_PROMOTION.md`](../reports/8105_CNBE32_RUNTIME_PROMOTION.md).

The standardized runtime repair report is
[`reports/8105_STANDARDIZED_RUNTIME_REPAIR.md`](../reports/8105_STANDARDIZED_RUNTIME_REPAIR.md).

## Historical Test Baseline

The pre-restart CNBE catalog was useful as a test/runtime seed, but many of its
structure, radical, and stroke fields were AI-generated or otherwise not
aligned to the current GF/GB/GG standards workflow. Those rows are now
classified as a historical test baseline. They may be used for regression
localization, diff review, and compatibility analysis, but they must not be
used as evidence for teaching, research claims, or new release-track encoding
decisions.

## Encoding Rebuild Gate

Every future row-level rebuild must start with Unicode identity and then pass
through the following gates:

1. Unicode code point and normalized character identity are recorded.
2. Scope membership is recorded, with 8105 membership checked first.
3. National-standard evidence is joined where available.
4. Stroke count, stroke shape, and stroke order evidence are recorded.
5. Structure is limited to the project-approved standard structure set.
6. Decomposition records character components, non-character components, and
   basic components.
7. Radical and side-component evidence are separated.
8. Independent-character status is checked where applicable.
9. GF0017 normativity scoring is calculated with source status.
10. Rows are classified as `national_standard`, `standard_derived`,
    `agent_standard`, `source_gap`, or `unresolved`.
11. Batch processing stops on blockers and resumes only from a checkpoint.
12. Human review authorizes any source-table write.
13. SQLite rebuild is a separate authorized step.

## Agent Workflow Boundary

The Agent is not a free-form generator. It is a controlled executor for the
standards workflow.

The Agent must:

- read Unicode identity before structure or encoding work;
- prefer national-standard evidence for 8105 characters;
- completely discard legacy CNBE structure fields during candidate generation;
- use only the three-tier structure evidence path:
  `national_standard` -> `core_reference` -> `network_cross_reference`;
- use programmatic extraction for network references such as ZDIC before any
  model interpretation;
- record source level when direct standard evidence is unavailable;
- stop on Unicode ambiguity, structure ambiguity, decomposition gaps, or
  unsupported score promotion;
- emit review packets instead of silently rewriting source catalogs;
- preserve legacy CNBE values for comparison;
- write checkpoint and resume metadata for batch work;
- keep Agent-standard output separate from national-standard output.

The Agent must not:

- invent structure labels beyond the approved set;
- turn dictionary context into national-standard proof;
- infer missing ZDIC or dictionary fields from memory when parser output is a
  gap;
- import old generated CNBE structure labels into any candidate structure field;
- regenerate the full 97,686-row catalog when evaluating existing assets;
- modify runtime data unless a separate write authorization exists;
- treat CNBE32 bit pressure as a reason to weaken Hanzi evidence.

## Research Reproducibility Boundary

A result is not considered research-reproducible until it includes:

- fixed input asset paths or source manifests;
- Unicode identity checks;
- standards evidence joins;
- Agent rule version or skill version;
- generated review packet;
- GF0017 scoring summary where applicable;
- blocker and resume state;
- test coverage for the workflow;
- a no-release statement unless release work is explicitly authorized.

Dictionary and encyclopedia sources may improve explanation and gap triage, but
they must be recorded as cross-reference evidence unless they are being cited
for a non-national-standard field.

## Structure Boundary

The project uses the following structure labels for rebuild work:

- independent character
- top-bottom
- top-middle-bottom
- left-right
- left-middle-right
- upper-left enclosure
- upper-right enclosure
- left-three-side enclosure
- lower-left enclosure
- upper-three-side enclosure
- lower-three-side enclosure
- full enclosure
- embedded structure

No additional public structure label should be introduced without a standards
evidence note and a migration plan.

## CNBE32, CNBE64, And CNBE128

CNBE32 remains a compact runtime-oriented carrier. It must not force a weak
Hanzi analysis into a small bitfield.

CNBE64 and CNBE128 are reserved for richer evidence fields, including complete
stroke sequences, decomposition trees, source anchors, review state, and
metadata needed for reproducible research.

## Repository Write Rules

The following actions are not allowed from this governance document alone and
still require explicit authorization:

- publishing a tag, GitHub release, or PyPI package;
- claiming 97,686-row validation;
- promoting Agent-standard rows as national-standard rows.

The 8105 runtime promotion already performed the specifically authorized
source-table and SQLite database rebuild for the 20,902-row runtime package.
That authorization does not extend to release publishing, PyPI publishing, or
97,686-row validation claims.

Large generated artifacts should remain local or be packaged separately unless
they have been reviewed and intentionally committed.

## Next Safe Implementation Round

The next safe implementation round is blocked-queue resolution for the `795`
force-approved rows that remain unpatched after the standardized runtime
repair:

1. resolve `486` rows still missing a usable radical after approved-packet and
   cached cross-reference joins;
2. define insertion/index strategy for `276` rows missing from current runtime
   data;
3. resolve `32` rows with non-conservative radical mappings;
4. resolve `1` row with invalid or missing stroke-count evidence;
5. generate another copied dataset and dry-run report before any additional
   source-table write;
6. keep release, tag, and PyPI work separate.
