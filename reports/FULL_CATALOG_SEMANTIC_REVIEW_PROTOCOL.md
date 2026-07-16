# CNBE-32 Full Catalog Semantic Review Protocol

## Status

This protocol is a review plan, not evidence that the 97,686-row catalog is semantically authoritative.

The current evidence establishes artifact identity and historical algorithm reproducibility. It does not establish that the
radical-level structure classifier is linguistically correct for every character. The next step is therefore an
independent semantic sample review before any stronger public claim, SDK replacement, or production database release.

## Scope

The review covers the experimental full catalog derived from `CNBE_编码目录_修复版_v3.xlsx`.

The review does not change `data/cnbe32.db`, does not create a new public canonical mapping, does not publish to PyPI,
and does not create a GitHub Release.

## Sampling Frame

Use a deterministic seed and record it in the final review report.

The sample should include 400 to 600 characters. It must cover:

- All observed structure classes.
- At least 30 rows per structure class where available.
- Basic CJK and CJK Extensions A through H, plus Extension I if present in the workbook.
- All 19 special radical overrides from the recovered classifier.
- High-stroke characters, including rows affected by the 31-stroke clamp.
- Large groups where the `idx` field approaches its maximum observed value.

## Reviewer Requirements

Use two independent reviewers for the semantic sample.

Each reviewer records judgments without seeing the other reviewer's decisions. Disagreements are preserved in the
report and resolved only by a documented adjudication pass.

## Fields To Review

Reviewers should classify each sampled row by field:

- `radical`: agrees with cited radical source, disagrees, or unclear.
- `strokes`: agrees with cited stroke source, disagrees, or unclear.
- `struct_type`: plausible under the CNBE radical-level heuristic, implausible, or unclear.
- `struct_name`: matches `struct_type`, mismatches, or unclear.
- `idx`: deterministic grouping index only; not a linguistic field.
- `cnbe`: bitfield recomputation only; not a semantic field.

## Evidence Sources

The primary machine-readable source for radical and stroke review is the pinned Unicode 17.0.0 Unihan archive.

Human reviewers may use additional dictionaries or glyph references, but every additional source must be named in the
review output. Additional sources may support a judgment; they do not silently replace the pinned Unihan baseline.

## Acceptance Criteria

The sample review may support cautious experimental wording only if:

- Both reviewers complete the full sample.
- Radical and stroke disagreements are itemized.
- Structure disagreements are separated from radical/stroke disagreements.
- Every special radical override is represented.
- The report states that structure labels are heuristic unless a stronger decomposition method is later added.

## Decision Outcomes

The final review must choose one of these outcomes:

- `ACCEPT_EXPERIMENTAL`: Keep the full catalog as an experimental artifact with cautious claims.
- `REVISE_RULES`: Keep the catalog blocked and update the classifier or documentation.
- `INSUFFICIENT_EVIDENCE`: Do not proceed toward a generated SQLite database or stronger claims.

No outcome authorizes SDK replacement, release tagging, GitHub Release publication, or PyPI publication by itself.
