# CNBE-32 Encoding Work Preparation Readiness

## Status

This report prepares the repository for a future encoding correction round.

It does not authorize a mapping replacement, SDK database replacement, SQLite build, GitHub Release, or PyPI
publication. It records what must be true before CNBE-32 encoding work resumes after the earlier AI-code,
encoding-error, and character-composition concerns.

The current preparation focus is evidence construction around CNBE-32's weak fields, not a narrow pursuit of one
standard-list row count. Character-scope reconciliation remains useful, but it must not delay work on radical,
component, single-component, stroke-order, stroke-shape, character-order, etymology, dictionary, and semantic evidence
domains.

## Repository Baseline

- Current repository branch inspected: `data/basic-cjk-scope-gap`.
- Current reference branch: `reference/full-catalog-audit-semantic-sample`.
- Current SDK compatibility scope: 20,902 rows.
- Current experimental full-catalog artifact: 97,686 rows.
- Current canonical mapping gate: `NO_GO`.
- Current full-catalog SQLite build gate: `NO_GO`.
- Current semantic authority status: `INSUFFICIENT`.
- Current semantic review validation status: `TEMPLATE_INCOMPLETE`.

The packaged SDK mapping remains an implementation compatibility contract. It is reproducible, but its radical,
stroke, structure, and index fields are generated from deterministic heuristics rather than reviewed linguistic
sources.

## External Research Folder Reviewed

Local folder reviewed:

```text
/Users/liuzhaoqi/Documents/cnbe-research/
```

The folder is a research workspace, not a ready-to-import data release. It contains structured knowledge, OCR outputs,
third-party decomposition datasets, source-document conversions, temporary scripts, and local working artifacts.

## Research Assets Found

| Asset | Observed Status | Use Before Encoding |
|---|---:|---|
| `knowledge/structured/base_character_data.json` | 8,104 character records | Candidate source for 8,105-list preflight after one missing-row audit |
| `knowledge/structured/cnbe_character_knowledge.json` | 8,104 enriched records | Candidate review index, not direct encoding authority |
| `knowledge/component_db.json` | 9,521 char mappings, 1,810 component mappings | Candidate component evidence after source and license audit |
| `knowledge/decomp_rules.json` | 6 rules, 1,047 chars needing rules | Useful gap map for structure review |
| `knowledge/kangxi_radicals.json` | 9,574 records | Candidate radical cross-check, source must be pinned |
| `decomp-data/dictionary.json` | 9,574 IDS records | Candidate decomposition evidence, license/schema must be pinned |
| `cjk-decomp/cjk-decomp.txt` | Large graphical decomposition data | Secondary evidence only; upstream README says it is unmaintained |
| `knowledge/Unihan2.zip` | 8,518,517 bytes, SHA-256 matches pinned Unihan 17.0.0 | Strong source identity candidate |
| `knowledge/Unihan.zip` | 8,454,996 bytes, invalid ZIP | Reject as source input |
| `knowledge/alignment_report.json` | Reports 79 missing CNBE chars and stroke-scheme mismatch note | Useful diagnostic, not final evidence |
| `knowledge/alignment_report_v2.json` | 3/4 steps complete; OCR gap remains | Useful progress marker, not a pass gate |
| `source/` converted standards | Many JSON/Markdown/image outputs | Useful only after per-document provenance and OCR QA |
| `knowledge/ocr/` | OCR batches across standards and Cihai | Review aid, not direct authority without confidence checks |

## Immediate Findings

The research workspace strengthens the evidence base but also confirms that the next encoding round cannot be a direct
"regenerate and replace" operation.

Key issues:

- `base_character_data.json` contains 8,104 records, while the target standard list is described as 8,105.
- `cnbe_character_knowledge.json` uses Unicode labels such as `U+04E00`; labels need canonical normalization before
  repository use.
- `knowledge/Unihan.zip` is not a valid ZIP and must be excluded.
- `build_knowledge.py`, `parse_stroke_order.py`, `remap_struct.py`, and `ocr_pipeline.py` contain local Windows paths
  and exploratory logic; they are not portable repository scripts.
- `remap_struct.py` rewrites structure fields by heuristic rules. It must not be used to update canonical CNBE codes.
- `cjk-decomp` explicitly says the data is unmaintained and recommends `cjkvi-ids`; use it only as secondary evidence.
- OCR outputs require confidence, page, and source-image checks before any row can be treated as reviewed evidence.
- Cihai and dictionary-derived definitions can support human review but should not define CNBE bit fields.

## Knowledge Asset Inventory

The repository now has a read-only inventory report for the local knowledge folder:

```text
reports/cnbe_research_knowledge_inventory.json
```

Inventory scope:

- local root: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge`;
- total files: 221;
- total size: 186,085,161 bytes;
- JSON files: 216, all parse successfully;
- ZIP files: 2, one passes Python ZIP integrity and one fails;
- Markdown files: 2;
- text files: 1.

Asset classification:

| Class | Count | Use Decision |
|---|---:|---|
| Primary candidate | 2 | Blocked until 8,105-row reconciliation passes |
| Canonical external archive | 1 | Candidate identity source after manifest pinning |
| Excluded archive | 1 | Reject unless replaced by a valid archive |
| OCR Cihai review aids | 139 | Human navigation aid only |
| OCR standard review aids | 31 | Human navigation aid only |
| OCR general review aids | 20 | Human navigation aid only |
| Reference indexes | 4 | Cross-check evidence only |
| Structured references | 1 | Cross-check evidence only |
| JSON references | 18 | Case-by-case review required |
| Documentation/reference notes | 3 | Context only |
| Diagnostic output | 1 | Not an encoding authority |

Current asset-confirmation blockers:

1. `knowledge/Unihan.zip` fails Python ZIP integrity and remains excluded.
2. `knowledge/structured/base_character_data.json` has 8,104 records, not the required 8,105.
3. `knowledge/structured/cnbe_character_knowledge.json` has 8,104 records, not the required 8,105.

Additional non-blocking observations:

- `knowledge/Unihan_RadicalStrokeCounts.txt` is empty.
- Several external research files contain CRLF or UTF-8 BOM; these are recorded as source hygiene issues and are not
  auto-normalized by this repository.
- OCR confidence is low for multiple general OCR batches, so OCR outputs remain review navigation aids only.

Result:

- asset confirmation status: `ACTION_REQUIRED`;
- encoding generation gate: `NO_GO`;
- SQLite build gate: `NO_GO`;
- SDK replacement allowed: `false`;
- external assets imported into this repository: `false`.

The 8,104/8,105 count mismatch is therefore treated as a source-scope reconciliation issue, not as the main project
objective. The next allowed stage is to design and validate an evidence schema for CNBE weak fields while keeping code
generation and SQLite construction closed.

## Evidence Domain Mapping

The repository now has a read-only evidence-domain audit:

```text
reports/cnbe_research_evidence_domains.json
```

This audit maps local `cnbe-research` assets to the actual CNBE weak points:

- standard character scope;
- radical classification;
- component inventory;
- single-component and structure evidence;
- stroke count, stroke order, and stroke shape;
- stroke-based ordering;
- etymology, dictionary, and semantic context;
- encoding and interchange standards.

Current result:

- 8 evidence domains inspected;
- 7 domains are `READY_FOR_SCHEMA_DESIGN`;
- 1 domain is `ACTION_REQUIRED` because invalid or empty Unihan-related artifacts must be excluded or replaced;
- encoding generation gate remains `NO_GO`;
- SQLite build gate remains `NO_GO`.

The companion workflow document is:

```text
reports/CNBE_RESEARCH_EVIDENCE_WORKFLOW.md
```

That workflow defines the next construction stage as a character evidence schema with source path, source hash,
extraction method, page or record reference, confidence, and review status columns. It explicitly forbids using OCR,
dictionary summaries, or generated CNBE outputs as direct bit-field authority.

## Evidence Tiers

### Tier 0: Identity and Integrity Inputs

These may be used to verify source identity:

- Pinned Unihan 17.0.0 archive with SHA-256 `f7a48b2b545acfaa77b2d607ae28747404ce02baefee16396c5d2d7a8ef34b5e`.
- CNBE full catalog workbook SHA-256 already recorded in the repository audit reports.
- Existing Git historical blobs already referenced by mapping provenance reports.

Tier 0 data can support reproducibility checks. It does not by itself support semantic correctness claims.

### Tier 1: Standard-Derived Review Inputs

These may be used after per-file provenance, schema, and count checks:

- `knowledge/structured/base_character_data.json`
- `knowledge/structured/cnbe_character_knowledge.json`
- `source/01-通用规范汉字表/`
- `source/02-汉字部首表/`
- `source/03-部件及部件名称规范/`
- `source/04-独体字规范/`
- `source/05-笔顺规范/`
- `source/06-汉字部件规范/`

Tier 1 data can support review tasks only after each source document is pinned, normalized, and checked against expected
counts.

### Tier 2: Third-Party Decomposition Inputs

These may be used only as cross-check signals:

- `decomp-data/dictionary.json`
- `decomp-data/dictionary.db`
- `cjk-decomp/cjk-decomp.txt`
- `knowledge/component_db.json`
- `knowledge/kangxi_radicals.json`

Tier 2 data must not override standard-derived evidence without documented manual review.

### Tier 3: Excluded or Diagnostic Inputs

These must not be used as direct encoding authority:

- Invalid `knowledge/Unihan.zip`.
- Windows-path exploratory scripts.
- OCR output without confidence and page validation.
- Cihai/definition summaries as bit-field authority.
- Any AI-generated decomposition, radical, or structure assignment without source-backed review.

## Pre-Encoding Gate

Before any new encoding values are generated, every item below must pass:

1. Source manifest exists for every accepted external source.
2. Source files have SHA-256, size, license, and local path recorded.
3. Every imported text file is UTF-8 LF with no BOM.
4. The 8,105-character standard list reconciles to exactly 8,105 rows or records a justified exclusion.
5. Unicode labels are canonicalized to `U+XXXX` or `U+XXXXX` without extra padding.
6. Radical evidence separates Unicode/Kangxi radical data from CNBE radical-index fields.
7. Stroke evidence separates actual stroke counts from CNBE clamped or encoded stroke fields.
8. Structure evidence separates character-level decomposition from radical-level heuristics.
9. Component evidence records source, decomposition syntax, and uncertainty.
10. Existing SDK codes are protected by a compatibility gate.
11. Full-catalog codes remain experimental until semantic review passes.
12. Human review packets are completed by Reviewer A and Reviewer B.
13. Disagreements are adjudicated before any decision report.
14. No generated database, XLSX, ZIP, OCR image, or large binary is committed.

If any gate fails, the encoding round must stop before code generation.

## Proposed Preparation Workflow

### Stage 0: Freeze Current Baseline

Record:

- current branch and commit;
- `origin/main` commit;
- current SDK database SHA-256;
- current full-catalog workbook SHA-256;
- current Unihan manifest SHA-256.

No mapping changes are allowed in this stage.

### Stage 1: Create Research Source Manifest

Create a repository-side manifest that references accepted sources under `/Users/liuzhaoqi/Documents/cnbe-research/`
without copying large files.

For each source, record:

- source type;
- local path;
- SHA-256;
- size;
- expected row count;
- license or source note;
- acceptance status.

### Stage 2: Build Read-Only Research Audit

Add a read-only audit script that inspects the external research folder and writes a report.

The script should check:

- `base_character_data.json` count and missing character;
- Unicode label canonicalization problems;
- Unihan archive identity;
- invalid archive rejection;
- decomposition dictionary count;
- component mapping count;
- OCR batch count and confidence availability;
- forbidden direct-use scripts.

The script must not modify `cnbe-research` or CNBE-32 data.

### Stage 3: Build Evidence Join Plan

Define a join schema by character:

- Unicode code point;
- character;
- standard list rank and level;
- actual stroke count;
- stroke order;
- radical source;
- component decomposition source;
- structure label source;
- confidence and review status.

This join schema is a preparation artifact, not a new encoding table.

### Stage 4: Produce Diff-Only Candidate Review

Generate a candidate issue list, not candidate codes.

The issue list should include:

- CNBE stroke field differs from standard stroke count;
- CNBE structure label differs from decomposition-derived structure;
- missing characters from the 8,105 standard list;
- characters present in CNBE but not in the standard list;
- OCR-only fields needing manual confirmation.

### Stage 5: Human Review

Use the existing reviewer packet pattern:

- Reviewer A checks radical, stroke, and structure evidence.
- Reviewer B independently checks the same fields.
- Adjudication resolves conflicts.

No code generation occurs during this stage.

### Stage 6: Decision Report

Only after strict review validation passes, produce a decision report with one of these outcomes:

- `NO_GO`: evidence is insufficient.
- `REFERENCE_ONLY`: keep as research reference.
- `EXPERIMENTAL_MAPPING_CANDIDATE`: build an isolated candidate mapping.
- `SDK_COMPATIBILITY_PROPOSAL`: propose versioned SDK migration, not direct replacement.

## Proposed Repository Branch

Use a new local branch:

```bash
git checkout -b prep/encoding-evidence-gates
```

This branch should contain only manifests, audit scripts, reports, and tests. It must not contain changed CNBE mapping
values.

## Files That May Be Added Next

Recommended first implementation set:

```text
data/sources/cnbe-research-local.json
scripts/audit_cnbe_research_sources.py
reports/cnbe_research_source_audit.json
reports/ENCODING_WORK_PREP_READINESS.md
tests/test_cnbe_research_source_audit.py
```

The manifest should reference external source files by path and hash. It should not import the external data payloads
into this repository.

## Files That Must Not Be Added

Do not add:

- `knowledge/Unihan.zip`
- `knowledge/Unihan2.zip`
- XLSX files
- MDX dictionaries
- SQLite dictionaries
- OCR image directories
- PaddleOCR checkout
- OpenCC checkout
- copied `source/*_images`
- generated full-catalog SQLite databases

## Claim Boundary

Allowed wording:

- "source-backed review input";
- "candidate evidence";
- "read-only audit";
- "semantic authority insufficient until reviewed";
- "experimental full catalog".

Avoid wording that implies:

- deployment readiness;
- full semantic authority;
- every error has been corrected;
- national-standard conformance for the whole mapping;
- complete validated coverage;
- direct SDK replacement.

## Current Recommendation

Proceed with Stage 1 and Stage 2 only.

The next safe task is to create a source manifest and read-only audit script for `/Users/liuzhaoqi/Documents/cnbe-research/`.
Do not generate or change CNBE codes until the source audit and human review gates pass.
