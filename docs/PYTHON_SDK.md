# CNBE-32 Python SDK

## Current Status

The Python SDK is a **stable core** that covers:

- 32-bit bitfield encode/decode with strict boundary validation
- SQLite-backed CJK character lookup (20,902 Basic CJK characters)
- Weighted and bit-level distance functions
- A zero-overhead SkillTable for in-memory char-to-code mapping

## Installation

```bash
pip install cnbe32
```

For editable install from source:

```bash
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding
cd CNBE-32-Chinese-Native-Binary-Encoding
pip install -e .
```

## Database Loading

The `cnbe32.db` (SQLite, ~1.5 MB, 20,902 entries) ships inside the wheel.
The SDK resolves the database path in this priority order:

1. `CNBE32_DB_PATH` environment variable
2. `importlib.resources` from the installed package
3. `data/cnbe32.db` relative to the repository root (source installs)

If the database cannot be found, a clear `FileNotFoundError` is raised with
instructions.  To use a custom database:

```bash
export CNBE32_DB_PATH=/path/to/cnbe32.db
```

## Coverage

- **Stable**: Python bitfield encoder/decoder and Basic CJK lookup (20,902
  characters in the U+4E00–U+9FFF range), depending on available database.
- **Experimental**: LLM, JEPA, RISC-V, OS, finance, biology, and physics
  prototypes.

The 97,686 CJK figure quoted elsewhere in the project refers to the
theoretical encoding space (including Extension A–F), not the current
database population.

## Core API

### encode_cnbe

```python
>>> from cnbe32 import encode_cnbe
>>> code = encode_cnbe(radix=72, stroke=8, struct=1, index=42, ext=0)
>>> hex(code)
'0x48402a01'
```

| Parameter | Type | Range   | Description       |
|-----------|------|---------|-------------------|
| radix     | int  | 0–255   | Kangxi radical ID |
| stroke    | int  | 0–31    | Stroke count      |
| struct    | int  | 0–15    | Structure type    |
| index     | int  | 0–2047  | Glyph index       |
| ext       | int  | 0–15    | Extension flags   |

All parameters are strictly validated.  Out-of-range values raise
`CNBEValueError` with the field name and legal range — no silent masking.

### decode_cnbe

```python
>>> from cnbe32 import decode_cnbe
>>> d = decode_cnbe(0x48402a01)
>>> d
{'radix': 72, 'stroke': 8, 'structure': 1, 'index': 42, 'extension': 0,
 'struct_name': 'left-right'}
```

### Distance Functions

```python
from cnbe32 import bit_hamming_distance, field_weighted_distance

a = encode_cnbe(1, 1, 0)
b = encode_cnbe(2, 1, 0)

# True bit-level Hamming distance (popcount of XOR)
bit_hamming_distance(a, b)  # → varies by bit pattern

# Field-weighted distance: |Δradix|*8 + |Δstroke|*5 + |Δstruct|*4
field_weighted_distance(a, b)  # → 8
```

**`hamming_distance` is deprecated.**  It produces the same result as
`field_weighted_distance`, but the name was misleading (it is not a
bit-level Hamming distance).  Use `bit_hamming_distance` or
`field_weighted_distance` in new code.

### SkillTable

```python
from cnbe32 import SkillTable

# Zero-filled table (safe for testing)
st = SkillTable.empty()

# Load from disk
st = SkillTable.from_file("skill_table.bin")  # .bin or .npy

# Lookup
st.lookup(0x6C49)  # → CNBE-32 code for 汉
st["汉"]           # same as above
```

Calling `SkillTable()` directly creates an empty table (same as
`SkillTable.empty()`).  This avoids the previous behavior of silently
returning 0 for every character when a real table was expected.

### Database Queries

```python
from cnbe32.db import lookup, search, batch, by_radix, count, stats

lookup("明")           # → dict or None
search(0x48400801)     # → dict or None
batch(["明", "汉"])    # → list[dict]
batch("")              # → []  (safe for empty input)
batch([])              # → []  (safe for empty input)
by_radix(72)           # → all chars sharing radical 72 (日)
count()                # → total entries in db
stats()                # → {total, strokes, radices, structures}
```

## Testing

```bash
# Unit tests (no database required)
pytest tests/test_cnbe32_full.py -m "not integration"

# All tests (including database-dependent)
pytest tests/test_cnbe32_full.py
```

Database-dependent tests are marked with `@pytest.mark.integration` and
will be skipped automatically when `cnbe32.db` is unavailable.

## Known Limitations

- The current database covers 20,902 Basic CJK characters only, not the
  full 97,686 CJK Unified Ideographs across all extensions.
- The module-level database connection in `db.py` is shared across all
  callers.  Call `close()` to release it explicitly.
- No async / threaded support for database access.
