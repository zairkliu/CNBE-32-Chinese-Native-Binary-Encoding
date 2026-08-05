# P0: Variant Pairs and CNBE Coverage Gaps (VL-1.6 Residual Errors)

Date: 2026-08-06

## 1. Residual substitution classification

- Total substitutions: 603
- Label counts: {'variant': 354, 'other': 81, 'truth_not_in_standard': 121, 'shape_confusable': 27, 'truth_not_in_db': 11, 'ocr_not_in_db': 9}
- Unihan variant pairs: 354

## 2. CNBE coverage gaps

- Unique truth chars not in CNBE standard track: 812
- Unique truth chars not in CNBE DB at all: 6

## 3. Experiments

- Baseline accuracy: 0.9091
- Oracle variant fix: +354 chars -> 0.9310
- Corpus-learned direction map: 0.9264 (353 changes; alignment-based accuracy)
- Naive canonical map: 0.6524 (4940 changes; destructive without direction awareness)

### Top variant pairs (count)

| OCR form | Truth form | Count |
|---|---:|---:|
| 為 | 爲 | 41 |
| 盖 | 蓋 | 34 |
| 黃 | 黄 | 20 |
| 髙 | 高 | 14 |
| 說 | 説 | 11 |
| 詠 | 咏 | 11 |
| 宮 | 宫 | 10 |
| 別 | 别 | 9 |
| 竒 | 奇 | 9 |
| 橫 | 横 | 8 |
| 瑤 | 瑶 | 7 |
| 湏 | 須 | 7 |
| 鴈 | 雁 | 6 |
| 顏 | 顔 | 6 |
| 虛 | 虚 | 6 |

## 4. Notes

- Variant relation comes from Unihan kSemanticVariant / kSimplifiedVariant / kTraditionalVariant / kZVariant / kCompatibilityVariant / kSpoofingVariant.
- The learned-direction map is corpus-derived and in-sample; it is a data construction artifact, not a deployed model.
- Repro: `python3 analyze_variants.py`.

## 5. Conclusion

- Variant normalization is the largest residual lever: 354/603 substitutions are Unihan variant relations.
- Oracle variant fix ceiling: 0.9310 (+0.0219).
- Corpus-learned direction map: 0.9264 (+0.0173), close to the ceiling without using ground truth at decision time.
- Naive canonical normalization is destructive (0.6524) and must not be applied without direction awareness.
- Coverage: 812 unique truth chars are outside the CNBE standard track, 6 are missing from the DB entirely.
- The remaining non-variant errors need OCR top-N candidate reranking, not a static variant map.
