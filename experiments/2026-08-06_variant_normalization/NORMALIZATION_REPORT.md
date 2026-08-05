# Direction-Aware Variant Normalization

Date: 2026-08-06

- Rules: 50 (min count 2 in 37-page VL-1.6 residual pairs)
- Baseline accuracy: 0.9091
- Normalized accuracy: 0.9264
- Changes: 359
- Correct changes (position-approx): 9

Rules are directional (OCR form -> target form) and must not be applied in reverse. Naive canonical normalization is intentionally not used.
