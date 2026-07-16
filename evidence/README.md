# CNBE Evidence Layer

This directory stores reproducible research evidence for the CNBE standards
restart workflow. It is intentionally separated from `data/`, `src/`, and
package assets.

The files here document how current CNBE fields are audited against Unicode
identity, national-language standards, GF0017 normativity scoring, 8105-aligned
rule transfer, and the CNBE Agent project standard.

## Boundary

The evidence layer is not a runtime database.

It must not be imported as direct package data, used as a PyPI release payload,
or treated as an automatic replacement for `data/cnbe32.json` or
`src/cnbe32/data/cnbe32.db`.

The evidence layer may support future repair work only after a separate human
authorization step.

## Authority Levels

Use these labels consistently:

- `national_standard`: direct evidence from 8105, GF, GB, or GG standards.
- `standard_derived`: structured data derived from local standard assets.
- `agent_standard`: CNBE project output aligned to 8105 and accepted by the
  Agent gates.
- `cross_reference`: useful context from dictionaries, encyclopedia sources,
  OCR, or other supporting material.
- `unresolved`: missing or insufficient evidence.

Agent-standard mappings are valid CNBE project evidence. They are not national
standards and must not be described as national-standard output.

## Directory Layout

```text
evidence/
  8105/
    8105 baseline, comparison, repair-candidate, radical-code, and dry-run
    patch evidence.

  gf0017/
    GF0017 50-point scoring model, source map, and 8105 normativity scores.

  agent-standard/
    CNBE Agent encoding standard, legacy structure localization, 20,902-row
    pre-encoding pressure test, and rule-learning transfer workflow.

  validation/
    Human-facing validation attachments and previews.
```

## Required Workflow

Every encoding audit must begin with Unicode identity:

1. Confirm `char`, `unicode`, `codepoint`, normalization status, and scope.
2. Attach source-grade labels for every required field.
3. Build the Hanzi knowledge schema.
4. Score GF0017 normativity.
5. Apply the CNBE Agent standard only after earlier gates pass.
6. Keep CNBE32 as a carrier layer, not an authority layer.
7. Preserve CNBE64 and CNBE128 archive fields when CNBE32 is too compact.
8. Stop on blockers and resume only from the saved checkpoint.

## Non-Goals

This directory does not claim:

- CNBE32 has completed national-standard formal encoding.
- CNBE32 has full coverage for all Chinese characters.
- Agent-standard output is national-standard output.
- dry-run repair candidates are approved database changes.
- evidence JSON files are package runtime assets.

## Reproduction Commands

Run these commands from the repository root:

```bash
python3 scripts/audit_cnbe8105_encoding_comparison.py
python3 scripts/build_cnbe8105_auto_fix_candidates.py
python3 scripts/build_cnbe8105_radical_code_map.py
python3 scripts/build_cnbe8105_dry_run_patch.py
python3 scripts/score_cnbe8105_gf0017_normativity.py
python3 scripts/build_cnbe_agent_encoding_standard.py
python3 scripts/run_cnbe20902_agent_preencoding_test.py
python3 scripts/validate_format_integrity.py
python3 -m pytest \
  tests/test_cnbe8105_encoding_comparison.py \
  tests/test_cnbe8105_auto_fix_candidates.py \
  tests/test_cnbe8105_radical_code_map.py \
  tests/test_cnbe8105_dry_run_patch.py \
  tests/test_cnbe8105_gf0017_normativity.py \
  tests/test_cnbe_agent_encoding_standard.py \
  tests/test_cnbe20902_agent_preencoding.py
```

## Review Rule

Evidence can be submitted in full for open-source reproducibility, but any
future source-table rewrite must be a separate reviewed implementation step.
