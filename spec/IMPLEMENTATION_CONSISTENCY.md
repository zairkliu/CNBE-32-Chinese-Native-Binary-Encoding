# CNBE-32 Implementation Consistency

## Goal

Keep independent implementations consistent with the same 32-bit bitfield layout.

Current consistency targets:

- Python SDK tests
- Minimal C golden vector test
- Minimal Rust golden vector test

## Canonical vectors

The canonical vector file is:

```text
spec/golden_vectors.json
```

Each implementation should verify:

- fields → code
- code → fields
- boundary values
- invalid field rejection

## Scope

These tests only validate bitfield encode/decode consistency.

They do not claim:

- full CJK coverage,
- character mapping coverage,
- collision rate,
- model performance,
- hardware correctness,
- or production readiness.

## Running tests

### Python

```bash
pytest tests/test_golden_vectors.py
```

### C

```bash
make -C c/golden_vectors test
```

### Rust

```bash
cargo test --manifest-path rust/golden_vectors/Cargo.toml
```
