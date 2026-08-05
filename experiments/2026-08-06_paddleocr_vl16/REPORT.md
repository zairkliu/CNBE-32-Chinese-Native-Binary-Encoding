# V1 Rerun: PaddleOCR-VL-1.6 Cloud API on Yongle 37 Pages

Date: 2026-08-06

## Baseline (sequence-level character accuracy)

- PaddleOCR-VL-1.6: 0.9091 (14657/16123)
- Previous: best-per-page 0.3764, DeepSeek v1 0.3871, local Paddle 0.1188

## CNBE oracle on real substitutions

- Substitutions: 603
- Error breakdown: OCR char in standard track 148, truth char in standard track 315, both in standard track 65
- Confusing-group errors (all): 16
- Both chars in CNBE standard track: 65
- Truth in CNBE top-K: {'1': 4, '3': 6, '5': 9, '10': 10, '20': 17}
- Confusing-group errors: 10, group top-1: 10 (1.0)

## Group verifier applied to OCR output

- Baseline: 0.9091
- After group verifier: 0.9085
- Changes: 16, correct changes: 0

## Notes

- API jobs and raw JSON are kept in jobs.json and raw/; markdown in pages/.
- Token is read from PADDLEOCR_VL_TOKEN and is not stored in the repository.
- Reproduce OCR: `PADDLEOCR_VL_TOKEN=<token> python3 run_paddleocr_vl16.py --images-dir <dir> --pages 3-39`.
- Reproduce eval: `python3 eval_paddleocr_vl16.py`.

## Conclusion

The cloud OCR resolves the local compute bottleneck: PaddleOCR-VL-1.6 reaches 0.9091 sequence-level character accuracy, versus 0.3871 for the best previous local engine. The remaining 603 substitutions are dominated by traditional/variant forms and rare characters outside the CNBE standard track, not by clean shape-confusable errors. CNBE still ranks every standard-track confusing-group error top-1, but a context-free group verifier remains neutral on the full page. The next bottleneck is variant normalization and CNBE coverage expansion, then OCR top-N candidate reranking.
