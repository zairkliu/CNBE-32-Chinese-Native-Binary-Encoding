# CNBE 8105 Rule-Learning Transfer Workflow

Role: repository-admin workflow specification

This document defines how the CNBE Hanzi structure encoding agent may learn
from audited 8105 rows and propose mappings for characters that are not yet
covered by direct encoding rules.

## Goal

Use the existing 8105 audit products as a controlled training/reference set so
the agent can align out-of-scope characters to the 8105 rule system and produce
project-level Agent standard mappings without claiming they are national
standards.

This is not direct source rewriting. It is Agent-standard output generation
after gates pass.

## Required Inputs

- `evidence/8105/cnbe8105_standard_baseline.json`
- `evidence/gf0017/cnbe8105_gf0017_normativity_scores.json`
- `evidence/8105/cnbe8105_radical_code_map.json`
- `evidence/agent-standard/cnbe20902_agent_preencoding_test.json`
- `data/cnbe32.json`
- cnbe-research standard and knowledge assets

## Learning Boundary

8105 is the national-standard baseline. The agent may learn:

- structure label normalization patterns;
- safe CNBE32 bit-field limits;
- radical-name mapping patterns after radical-code validation;
- stroke-count compatibility checks;
- which mismatch classes are repairable;
- which issue classes must be blocked or routed to human review.

The agent may not claim as national standard:

- Unicode identity;
- official standard text;
- component names absent from GF0014/GF3001-derived evidence;
- decomposition trees for ambiguous rows;
- independent-character status without source evidence;
- final CNBE values without a dry-run and audit gate.

## Candidate Statuses

| Status | Meaning |
|---|---|
| `AGENT_STANDARD_MAPPING` | Project standard output generated from 8105-aligned pattern after Agent gates |
| `DIRECT_EVIDENCE_CANDIDATE` | Candidate backed by direct or standard-derived evidence |
| `SOURCE_GAP` | Required standard source is not confirmed |
| `EVIDENCE_GAP` | Standard-side evidence is incomplete |
| `HUMAN_REVIEW_REQUIRED` | Evidence is ambiguous or conflict-prone |
| `BLOCKER` | Batch must stop before continuing |

## Candidate Schema

```json
{
  "char": "例",
  "unicode": "U+4F8B",
  "status": "AGENT_STANDARD_MAPPING",
  "standard_level": "agent_standard_not_national_standard",
  "confidence": 0.0,
  "support_count": 0,
  "support_examples": [],
  "source_grade": "learned_from_8105",
  "proposed_cnbe32_fields": {
    "radix_name": null,
    "strokes": null,
    "structure": null,
    "struct_type": null
  },
  "extended_archive_fields": {
    "stroke_order": null,
    "decomposition": null,
    "component_names": [],
    "source_anchors": []
  },
  "required_next_gate": "GF0017_BATCH_AUDIT"
}
```

## Implementation Plan

Stage 1: Extract learnable 8105 patterns.

- Build `evidence/agent-standard/cnbe8105_learned_rule_patterns.json`.
- Include structure label mappings, radical-name support counts, stroke-count
  ranges, repair-class distributions, and examples.
- Exclude rows with `EVIDENCE_GAP`, `HUMAN_REVIEW_REQUIRED`, or ambiguous
  decomposition from training support.

Stage 2: Generate out-of-scope candidates.

- Use `evidence/agent-standard/cnbe20902_agent_preencoding_test.json`.
- Target rows with `outside_8105_gf0017_score_scope`.
- Apply only deterministic, source-compatible pattern rules.
- Mark accepted output as `AGENT_STANDARD_MAPPING`, not `national_standard`.

Stage 3: Audit candidates.

- Run Unicode alignment.
- Run source-grade checks.
- Run GF0017-compatible scoring where fields exist.
- Stop on blockers.

Stage 4: Human review packet.

- Export small samples for review.
- Include support examples from 8105.
- Include no-write statement.

## Workflow Problems To Fix First

Current 20,902 pre-encoding pressure test exposed:

- 20,902 rows use legacy English structure labels and require formal
  localization.
- 13,073 rows are outside the current 8105 GF0017 score scope.
- 12,864 rows have CNBE32 structure type/name mismatch after normalization.
- Bit-range validity does not imply professional encoding validity.

## Acceptance Criteria

The rule-learning transfer is acceptable only when:

- no candidate lacks Unicode identity;
- every candidate has source grade;
- every Agent standard mapping has 8105 support examples;
- every Agent standard mapping is clearly labeled as not national standard;
- no source database is modified;
- reports and tests reproduce deterministically.
