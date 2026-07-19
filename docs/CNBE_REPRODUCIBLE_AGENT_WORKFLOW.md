# CNBE Reproducible Agent Workflow

## Purpose

This workflow defines how CNBE encoding work should be performed after the
standards restart. It turns national language and writing standards into a
repeatable Agent process with audit checkpoints.

The workflow is mandatory for future CNBE32, CNBE64, and CNBE128 rebuild work.

## Authority Order

The Agent must read sources in this order:

1. Unicode identity and code point compatibility.
2. 8105 common standardized Chinese character table for core scope.
3. National language and writing standards for stroke, stroke shape, stroke
   order, component, component name, radical, structure, and decomposition.
4. Core reference files under `evidence/` and `cnbe-research/knowledge`.
5. Dictionary and network reference context for explanation, gap triage, and
   non-standard cross-reference fields.

When sources conflict, national-standard evidence controls the release-track
field. Cross-reference sources must not override it.

Legacy CNBE structure fields are fully discarded for structure generation. They
may be inspected only in separate error-localization reports and must never be
used as candidate structure evidence.

Network references should be parsed by code before model interpretation. For
ZDIC pages, use the local extractor to cache `部首`, `总笔画`, `统一码`, `笔顺`,
`字形结构`, and `字形分析`. Missing pages or network failures must be recorded as
gaps, not filled by visual memory.

## Batch Lifecycle

Every batch must follow the same lifecycle:

1. **Preflight**
   - confirm input file and row count;
   - confirm the batch is not regenerating the full 97,686-row catalog without
     explicit authorization;
   - confirm output paths are review packets or copied work tables.
2. **Unicode Gate**
   - record character, code point, normalized identity, and scope membership;
   - stop on ambiguity.
3. **8105 Core Gate**
   - if the character belongs to 8105, mark it as core scope;
   - if not, classify it as Agent-standard candidate scope.
4. **Standard Evidence Join**
   - join stroke, stroke shape, stroke order, component, radical, independent
     character, structure, and decomposition evidence where available.
5. **Decomposition Standardizer**
   - classify structure with the approved structure set;
   - record character components, non-character components, and basic
     components;
   - record unresolved evidence instead of guessing.
6. **GF0017 Audit**
   - calculate the 50-point normativity model only for supported fields;
   - mark blocked fields separately;
   - stop the batch when blocker thresholds are hit.
7. **Review Packet**
   - emit CSV/XLSX/JSON review packets for human review;
   - keep legacy CNBE values and proposed values side by side;
   - never overwrite source catalogs in this step.
8. **Human Review Gate**
   - accept, reject, or request repairs;
   - record reviewer decision and blocker class.
9. **Controlled Write Round**
   - write only to a copied work table first;
   - promote to source catalog only after explicit authorization;
   - rebuild SQLite only in a separate authorized round.
10. **Runtime Blocker Resolution**
    - classify retained force-approved rows by missing field or policy blocker;
    - do not treat force approval as a substitute for missing radix, stroke,
      index, or bitfield values;
    - resolve blank radical/stroke joins, position-sensitive radical rules,
      component-like radical policy, and missing runtime indices as separate
      queues.
11. **Reproducibility Report**
    - write source manifests, script names, tests, score summaries, and
      generated artifact paths.

## Stop Conditions

The Agent must stop and report instead of continuing when any of these occur:

- Unicode identity is ambiguous;
- 8105 scope cannot be determined for an 8105-targeted batch;
- structure label falls outside the approved set;
- component or radical evidence is missing for a release-track promotion;
- force-approved rows still lack numeric CNBE32 fields, radical/stroke joins,
  or runtime index allocation policy;
- GF0017 scoring attempts to award unsupported points;
- output would overwrite runtime data without authorization;
- generated artifact size indicates accidental full-catalog regeneration;
- dictionary context is being promoted as national-standard evidence.

## Standard Output Fields

Each row-level review packet should include at least:

- `character`
- `unicode_codepoint`
- `scope`
- `source_level`
- `proposed_cnbe32`
- `structure_label`
- `decomposition`
- `basic_components`
- `radical`
- `stroke_count`
- `stroke_order_status`
- `gf0017_score`
- `blocked_items`
- `evidence_sources`
- `review_status`

CNBE64 and CNBE128 packets may add richer source anchors, full stroke sequence,
decomposition tree, review metadata, and provenance fields.

## Repository Outputs

Use these paths consistently:

| Path | Use |
|---|---|
| `evidence/8105/` | 8105 core comparisons, repair candidates, and standard evidence snapshots |
| `evidence/gf0017/` | GF0017 score models and batch scoring evidence |
| `evidence/agent-standard/` | Agent-standard candidate outputs and comparison evidence |
| `review_packets/` | Human review CSV/XLSX/JSON packets |
| `reports/` | Compact Markdown and JSON summaries |
| `docs/` | Stable governance, workflow, and reproducibility rules |

Large full-catalog intermediate files should not be committed by default.

## Required Verification

Before a batch can be proposed for review, run:

```bash
python3 scripts/confirm_cnbe8105_core.py
python3 -m pytest tests/test_confirm_cnbe8105_core.py
git diff --check
```

Batch-specific scripts must add their own tests before source-table writes are
considered.

For post-runtime 8105 blocker planning, run:

```bash
python3 scripts/plan_8105_runtime_blocker_resolution.py
python3 -m pytest tests/test_8105_runtime_blocker_resolution_plan.py
```

The blocker-resolution outputs are review artifacts only. They must not rebuild
SQLite databases or modify `data/cnbe32.json`.

For the authorized standardized runtime repair round, run:

```bash
python3 scripts/apply_8105_standardized_runtime_repair.py
python3 -m pytest tests/test_8105_standardized_runtime_repair.py
```

This repair may update `data/cnbe32.json` and rebuild the two packaged SQLite
databases only after source-write authorization. It must preserve current
runtime index/ext bits, keep missing-current-model rows out of the runtime
table, keep ZDIC/cache data labeled as cross-reference context, and keep tag,
release, and PyPI publication blocked.

After this repair, continue from the remaining queue rather than regenerating
the full catalog:

- `486` rows still need stronger radical evidence or a conservative mapping;
- `276` rows need an insertion/index policy because they are absent from the
  current 20,902-row runtime table;
- `32` rows need radical policy review;
- `1` row needs stroke-count evidence repair.

Use these committed artifacts as the restart point:

```text
reports/8105_standardized_runtime_repair.json
review_packets/8105_full/8105_standardized_runtime_repair_remaining_blockers.csv
```
