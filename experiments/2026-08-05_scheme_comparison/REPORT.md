# CNBE-32 vs IDS / Four-Corner / Cangjie: Objective Comparison (8105 scope)

Scope: 8105 characters from the national-standard 8105 table. All measured numbers are produced by `analyze_schemes.py`; see `results.json` for raw data.

## 1. Coverage and code statistics

| Scheme | Covered | Distinct codes | Unique ratio | Colliding code values | Avg length | Storage bytes |
|---|---:|---:|---:|---:|---:|---:|
| CNBE-32 | 8105 | 8101 | 0.9995 | 4 | 32-bit fixed (4 bytes) | 32420 |
| IDS | 7952 | 7949 | 0.9996 | 3 | 3.38 | 76940 |
| Four-Corner | 8105 | 4889 | 0.6032 | 1551 | 5.52 | 44746 |
| Cangjie | 7913 | 7718 | 0.9754 | 186 | 4.02 | 31813 |

| Scheme | Fixed width | Bit-level compute | Standard status | Primary use |
|---|---|---|---|---|
| CNBE-32 | Yes, 32-bit | Yes, direct field extraction | GF alignment in progress | Structural computing layer |
| IDS | No, variable | No, text parsing | Part of Unicode standard | Describing character composition |
| Four-Corner | Yes, 5 digits | No, lookup table | Unofficial | Input/retrieval |
| Cangjie | No, 1-5 letters | No, lookup table | Unofficial | Input method |
| Wubi | No, 1-4 letters | No, lookup table | Unofficial | Input method |

## 2. CNBE-32 field statistics

- Standard track rows in scope: 7602
- Legacy track rows in scope: 503
- Rows whose structure label is outside the 13 GF 0017 labels: 503
- Storage at 4 bytes per char: 32420 bytes for 8105 chars

## 3. Boundary statements

- IDS data is from cjkvi/cjkvi-ids; aggregate statistics only, no source file is shipped.
- Four-Corner and Cangjie are read from Unicode Unihan fields kFourCornerCode and kCangjie.
- Wubi is not measured because no authoritative machine-readable table is available here.

Wubi: code length is fixed by its rule (1-4 letters), but an authoritative machine-readable mapping for all 8105 chars is not bundled, so no measured collision or storage number is reported.
