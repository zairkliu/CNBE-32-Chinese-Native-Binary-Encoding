# CNBE-32 Golden Vectors

## Purpose

A small set of CNBE-32 golden vectors for implementation consistency tests.

These vectors ensure that independent implementations (Python, C, Rust, hardware prototypes) encode and decode the same bitfield values in the same way.

These vectors are **not** a coverage claim for the full CJK dataset. They are only normative examples for the 32-bit CNBE-32 bitfield layout.

## Bitfield layout

```text
31              24 23        19 18     15 14                 4 3        0
┌────────────────┬────────────┬─────────┬─────────────────────┬──────────┐
│ Radical/Radix  │  Stroke    │ Struct  │     Glyph Index     │   Ext    │
│     8 bits     │  5 bits    │ 4 bits  │       11 bits       │  4 bits  │
└────────────────┴────────────┴─────────┴─────────────────────┴──────────┘
```

| Field  | Bits | Shift | Min |  Max |
| ------ | ---: | ----: | --: | ---: |
| radix  |    8 |    24 |   0 |  255 |
| stroke |    5 |    19 |   0 |   31 |
| struct |    4 |    15 |   0 |   15 |
| index  |   11 |     4 |   0 | 2047 |
| ext    |    4 |     0 |   0 |   15 |

## Encoding formula

```text
code = (radix << 24) | (stroke << 19) | (struct << 15) | (index << 4) | ext
```

All fields must be validated before encoding. Invalid values must not be silently truncated.

## Vector file

The canonical machine-readable file is:

```text
spec/golden_vectors.json
```

Implementations should use that file for automated tests.

## Notes

* These vectors test bitfield consistency only.
* They do not define character-to-radical mappings.
* They do not claim full CJK coverage.
* They do not validate experiment results.
* Samples named `sample_*` are illustrative field samples, not normative character mappings.
