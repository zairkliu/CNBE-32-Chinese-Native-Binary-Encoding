# CNBE-32 Python SDK

## Status

The Python SDK is currently a research-prototype SDK.

Stable scope:

- CNBE-32 bitfield encode/decode
- Basic CJK database lookup when `cnbe32.db` is available
- Distance utilities

Current packaged database scope:

- 20,902 Basic CJK entries

Experimental / not guaranteed by the packaged SDK:

- 97,686 extended CJK coverage
- LLM / JEPA / RISC-V / OS / finance / biology / physics experiments

## Database loading

Database resolution order:

1. `CNBE32_DB_PATH`
2. packaged data: `cnbe32/data/cnbe32.db`
3. source checkout fallback: `data/cnbe32.db`

Example:

```bash
export CNBE32_DB_PATH=/path/to/cnbe32.db
```

## Distance functions

Use:

* `bit_hamming_distance(a, b)` for true bit-level Hamming distance.
* `field_weighted_distance(a, b)` for the legacy CNBE field-weighted distance.

Deprecated:

* `hamming_distance(a, b)`

`hamming_distance` is retained for compatibility but is not a true bit-level Hamming distance.
