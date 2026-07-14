# CNBE Research Evidence Workflow

## Role

This workflow replaces a single-count gate with a source-backed evidence program.

The next CNBE-32 preparation stage is not to regenerate codes. It is to build a reviewable evidence layer around the
known weak points of the current encoding: radical classification, components, single-component status, structural
layout, stroke count, stroke order, stroke shape, character ordering, etymology, dictionary meaning, and interoperability
standards.

## Current Rule

Do not modify CNBE mapping values, SDK databases, golden vectors, release files, or PyPI artifacts in this stage.

The local `cnbe-research` folder is treated as an external research workspace. Repository scripts may read it and write
small audit reports, but they must not import large PDFs, image slices, OCR batches, or dictionary databases into this
repository.

## Evidence Domains

### 1. Standard Character Scope

Purpose:

- identify whether a character belongs to a reviewed scope;
- preserve level and source-list context;
- avoid circular validation against previously generated CNBE outputs.

Accepted source family:

- `通用规范汉字表`;
- OCR output for page-level review;
- alignment reports only as diagnostics.

Use boundary:

- supports source-scope review;
- does not authorize automatic CNBE replacement.

### 2. Radical Classification

Purpose:

- separate modern official radical tables from Kangxi radicals and Unicode radical-stroke indexes;
- prevent CNBE radix fields from mixing incompatible radical systems.

Accepted source family:

- `汉字部首表`;
- OCR standard pages;
- Kangxi and Unicode radical-stroke indexes as cross-checks only.

Use boundary:

- official modern radical table is primary;
- Kangxi and Unicode are reference systems, not silent substitutes.

### 3. Component Inventory

Purpose:

- correct AI-generated or heuristic component errors;
- map component names, component variants, and decompositions to source evidence.

Accepted source family:

- `现代常用字部件及部件名称规范`;
- `信息处理用 GB 13000.1 字符集汉字部件规范`;
- OCR standard pages;
- third-party decomposition dictionaries as disagreement discovery.

Use boundary:

- standards define accepted component terminology;
- third-party data cannot override standard-derived evidence without review.

### 4. Single-Component And Structure

Purpose:

- distinguish 独体字 from decomposable characters;
- avoid assigning structure labels purely by visual heuristics.

Accepted source family:

- `现代常用独体字规范`;
- component databases;
- decomposition rules;
- enriched character knowledge as review index.

Use boundary:

- use as a review gate before any structure-bit proposal;
- do not infer structure bits until conflicts are adjudicated.

### 5. Stroke Count, Stroke Order, And Stroke Shape

Purpose:

- separate actual stroke count, stroke order sequence, and folded-stroke categories;
- prevent compact CNBE stroke fields from being treated as complete paleographic facts.

Accepted source family:

- `通用规范汉字笔顺规范`;
- `GB13000.1 字符集汉字笔顺规范`;
- `GB13000.1 字符集汉字折笔规范`;
- cleaned stroke-order indexes.

Use boundary:

- source fields must remain separate columns;
- CNBE compact fields are downstream interpretations.

### 6. Stroke-Based Ordering

Purpose:

- preserve formal stroke-order sorting evidence;
- distinguish source ordering from Unicode, workbook, or generated CNBE ordering.

Accepted source family:

- `GB13000.1 字符集汉字字序（笔画序）规范`;
- OCR order extracts.

Use boundary:

- supports audit ordering and review packets;
- not a semantic bit-field by itself.

### 7. Etymology, Dictionary, And Semantic Context

Purpose:

- build academic defensibility and reviewer context;
- document why a character's structure or semantic grouping may be disputed.

Accepted source family:

- `汉字源流大典`;
- `辞海` OCR/search index;
- `康熙字典`;
- `中华大字典`;
- offline Chinese Wikipedia references.

Use boundary:

- supports scholarly notes and adjudication;
- does not directly assign CNBE bit fields.

### 8. Encoding And Interchange Standards

Purpose:

- separate CNBE compatibility from Unicode, GB 18030, Unihan, and SDK database compatibility;
- keep implementation constraints distinct from linguistic evidence.

Accepted source family:

- `GB 18030-2022`;
- Unicode radical-stroke index;
- pinned Unihan archive.

Use boundary:

- supports interoperability and external identity checks;
- invalid or empty artifacts are excluded.

## Next Implementation Stage

The next code stage should create a character evidence schema, not a CNBE code table.

Minimum schema columns:

- `char`;
- `unicode_codepoint`;
- `evidence_domain`;
- `field_name`;
- `candidate_value`;
- `source_path`;
- `source_sha256`;
- `source_type`;
- `extraction_method`;
- `page_or_record_ref`;
- `confidence`;
- `review_status`;
- `reviewer_note`;

Allowed review statuses:

- `source_identified`;
- `machine_extracted`;
- `ocr_review_needed`;
- `cross_checked`;
- `conflict_detected`;
- `human_verified`;
- `excluded`.

## Stage Plan

### Stage A: Evidence Domain Mapping

Run:

```bash
python3 scripts/audit_cnbe_research_evidence_domains.py
```

Expected output:

```text
reports/cnbe_research_evidence_domains.json
```

This confirms which source families exist and whether each evidence domain is ready for schema design.

### Stage B: Character Evidence Schema

Create a small schema file and validator for evidence rows.

No full database should be built yet.

### Stage C: Pilot Evidence Extraction

Extract a small representative sample across weak fields:

- radicals;
- component names;
- single-component status;
- stroke count and order;
- stroke-based ordering;
- etymology and dictionary notes.

The pilot should include source paths and hashes for every row.

### Stage D: Conflict Model

Build a conflict report that separates:

- official standard conflict;
- OCR uncertainty;
- dictionary disagreement;
- third-party decomposition disagreement;
- CNBE current value disagreement.

### Stage E: Review Packet

Export reviewer packets for human validation.

No encoding replacement occurs until review packets pass.

## Stop Conditions

Stop the workflow if any of these occur:

- a source path is missing;
- an accepted source cannot be parsed;
- OCR is the only evidence for a formal standard field;
- a field lacks source hash or page/record reference;
- a generated CNBE value is used as evidence for itself;
- a script attempts to change current SDK mappings or release artifacts.
