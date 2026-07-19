# CNBE Research Position Statement

This document is the short research-position entry point for CNBE-32 after the
standards restart.

## One-Sentence Position

CNBE studies whether audited Hanzi structure evidence can be carried as compact
binary features alongside Unicode identity, without replacing Unicode and
without weakening national language and writing standards.

## Problem

Unicode identifies a character. It does not try to encode the internal Hanzi
evidence that matters for structure-aware processing:

- stroke count and stroke order;
- stroke shapes;
- components and component names;
- radicals and side components;
- independent-character status;
- glyph structure and decomposition;
- review provenance and source authority.

CNBE asks whether part of that evidence can become a stable, low-level feature
surface for CJK-aware software, machine-learning experiments, lookup systems,
and hardware-oriented prototypes.

## Current Time Point

The current published checkpoint is:

```text
v1.0.4 / cnbe32==1.0.4
```

At this checkpoint:

- the packaged runtime scope is 20,902 Basic CJK rows;
- the 8105 common standardized Chinese character table is the release-track
  national-standard core;
- 7,310 8105 runtime rows have been patched after the approved runtime
  promotion and standardized repair rounds;
- 795 force-approved rows remain intentionally blocked for later radical,
  stroke, insertion, or index policy work;
- the 97,686-row full catalog remains an extended research target, not a
  validated release claim.

## What Has Been Demonstrated

The repository currently demonstrates:

- a working 32-bit CNBE bitfield carrier with encode/decode validation;
- a packaged Python SDK and SQLite lookup surface;
- a 20,902-row runtime database shipped with the package;
- a standards-restart governance model using 8105 as the core;
- a reproducible Agent workflow with Unicode-first gates;
- separation between `national_standard`, `standard_derived`, and
  `agent_standard` evidence levels;
- audit reports for 8105 comparison, runtime promotion, and standardized
  runtime repair;
- tests that verify the runtime data, database rebuild, Agent profile, and
  documentation boundaries.

These results support CNBE as a reproducible research prototype and runtime
experiment surface.

## What Has Not Been Demonstrated

The repository does not yet demonstrate:

- validated 97,686-row coverage;
- teaching-ready full-catalog Hanzi structure data;
- national-standard status for outside-8105 Agent-standard rows;
- complete GF0017 scoring for the full catalog;
- final CNBE64 or CNBE128 carrier formats;
- proof that CNBE improves all downstream language models or tasks;
- a standards-backed resolution for every remaining 8105 runtime blocker.

These are future research and engineering tasks, not current release claims.

## Why 8105 Is The Core

The 8105 common standardized Chinese character table is the current
release-track national-standard core because it gives the rebuild a bounded,
reviewable, standards-facing baseline.

In this project, 8105 is used to:

- anchor the first standards-aligned repair round;
- prevent the old AI-generated catalog from becoming authority by accident;
- separate release-track claims from exploratory full-catalog work;
- provide a stable comparison target for radical, stroke, structure, and
  decomposition repair;
- define the first scope where human review and runtime promotion can be
  audited.

Rows outside 8105 may become project Agent-standard candidates, but they must
not be called national-standard output without direct evidence and review.

## Why 97,686 Is Not A Release Claim

The 97,686-row full catalog is important as a research target because it tests
whether the CNBE workflow can scale beyond the 8105 core. However, scale alone
does not establish authority.

The full-catalog path remains bounded by these rules:

- do not regenerate or duplicate the full table unless explicitly authorized;
- do not assign formal GF0017 points while source gaps remain;
- do not turn dictionary, OCR, Wikipedia, ZDIC, or legacy CNBE fields into
  national-standard evidence;
- do not rebuild runtime databases from full-catalog candidates without a
  separate write authorization;
- keep outside-8105 rows labeled as Agent-standard candidates until evidence
  gates approve project-level outputs.

This boundary keeps the project honest: 97,686 is a scale target and audit
surface, not current validated coverage.

## CNBE32, CNBE64, And CNBE128

CNBE32 is the compact runtime carrier. It is useful for:

- stable bitfield experiments;
- lookup tables;
- Basic CJK runtime packaging;
- low-level distance and feature tests;
- hardware-oriented prototypes where fixed-width fields matter.

CNBE64 and CNBE128 are reserved for richer evidence paths. They may carry:

- fuller stroke sequences;
- decomposition trees;
- source anchors;
- review state;
- provenance metadata;
- evidence-level distinctions that do not fit cleanly in 32 bits.

The rule is simple: CNBE32 must not force weak Hanzi analysis into a small
carrier. If the evidence does not fit, preserve it for CNBE64, CNBE128, or a
review archive.

## Reproducibility Path

The open-source reproducibility path starts from committed repository files,
not from a paid cloud Agent service.

Recommended entry points:

```text
README.md
docs/CNBE8105_ENCODING_GOVERNANCE.md
docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md
docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md
skill/cnbe-hanzi-structure-encoding-agent/SKILL.md
docs/COPILOT_CLOUD_AGENT_LIMITATION.md
```

Recommended checks:

```bash
python3 scripts/validate_format_integrity.py
python3 -m pytest tests/test_repository_published_agent_skill.py
python3 -m pytest tests/test_8105_cnbe32_runtime_promotion.py
python3 -m pytest tests/test_8105_standardized_runtime_repair.py
python3 -m pytest tests/test_cnbe8105_encoding_comparison.py
```

Paid GitHub Copilot cloud agent execution is optional convenience automation.
It is not required for reproducing, auditing, or reviewing CNBE work.

## Technical Feasibility

The project is technically feasible at the current prototype level because the
runtime layer is already operational:

- Python package metadata and imports are valid;
- CNBE32 encode/decode logic is testable;
- runtime JSON and SQLite databases are present;
- package data includes the SQLite runtime database;
- tests verify representative runtime samples and database lookup behavior;
- governance and Agent tests prevent key claim boundaries from drifting.

The harder technical problem is not whether a 32-bit carrier can exist. It is
whether each promoted Hanzi field can be sourced, audited, scored, and kept
compatible with the carrier without losing evidence.

## Scientific Value

CNBE's scientific value is in the reproducible workflow, not in a large table
alone.

The project is valuable if it can help researchers study:

- how Unicode identity and Hanzi structural evidence can coexist;
- whether structure-aware features improve CJK retrieval, embeddings, or
  model inputs;
- how national-language standards can be converted into auditable data
  pipelines;
- how compact carriers compare with richer evidence archives;
- how AI-generated linguistic tables can be repaired through standards,
  evidence, and human review.

The current repository is therefore best described as a standards-aligned
research prototype with a working CNBE32 runtime layer and a documented path
toward CNBE64/CNBE128 evidence expansion.

## Next Research Questions

The next useful research questions are:

1. Can the remaining 795 8105 blockers be resolved without weakening evidence
   rules?
2. Which fields require CNBE64 or CNBE128 rather than CNBE32?
3. Which downstream tasks benefit from CNBE features after strict baselines and
   fixed datasets are introduced?
4. How should outside-8105 Agent-standard candidates be reviewed and promoted
   without claiming national-standard authority?
5. Which reports and review packets are sufficient for external replication?
