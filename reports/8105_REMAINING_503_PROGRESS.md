# 8105 Remaining Rows Progress Report

Date: 2026-08-05

## Current state

- 8105 scope: 8105 chars; runtime rows: 8105; missing: 0
- Standard-track rows: 7602
- Remaining legacy-track rows: 503

## Completion packet

- Path: `evidence/8105/8105_REMAINING_503_COMPLETION_PACKET.json`
- Actions: {'REVIEW_REQUIRED': 503}
- Unresolved radical names (no code in current radical map): 10
- Rows with cross-reference evidence (Unihan radical/strokes or cjk_decomp): 503
- Rows with cross-reference radical code: 503
- Rows with cross-reference total strokes: 503
- Rows with cjk_decomp: 503

## Policy

- This run is read-only. No release database row is written.
- `AUTO_CANDIDATE` rows carry a verified roundtrip (encode/decode) and still require governance approval before apply.
- `REVIEW_REQUIRED` rows need expert adjudication (decomposition ambiguity or missing standard evidence).

## Reproduce

```bash
PYTHONPATH=repo/src python3 scripts/advance_8105_remaining.py \
    --unihan-irg experiments/2026-08-05_scheme_comparison/build/Unihan_IRGSources.txt
```
