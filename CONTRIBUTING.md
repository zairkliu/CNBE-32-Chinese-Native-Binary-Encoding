# Contributing to CNBE-32

CNBE-32 is a research-prototype project exploring 32-bit structural encoding for CJK characters.

## Project scope

**Stable baseline:** Python SDK bitfield encode/decode, strict field validation, distance utilities, Basic CJK database lookup, golden vector consistency tests.

**Experimental:** Extended CJK coverage, LLM/JEPA experiments, RISC-V/hardware prototypes, OS/kernel prototypes, finance/biology/physics experiments.

Please keep stable claims separate from experimental claims.

## Development setup

```bash
python -m pip install -U pip build pytest ruff
python -m pip install -e .
```

Run checks:

```bash
python -m compileall src tests
python -m build
python -m pip install --force-reinstall dist/*.whl
pytest
ruff check src tests
make -C c/golden_vectors test
cargo test --manifest-path rust/golden_vectors/Cargo.toml
```

## Golden vectors

Implementation changes must preserve compatibility with `spec/golden_vectors.json`. If a change modifies bitfield behavior, update the spec, Python tests, C tests, Rust tests, and documentation together.

## Documentation claims

Avoid unsupported claims: full coverage verified, 0% collision, proves, production-ready, validated on 90,000+.

Preferred wording: explores, experiments with, preliminary evidence, research target, stable baseline, implementation consistency.

## Pull requests

A good PR includes: clear summary, scope boundaries, tests or documentation updates, local verification results, and no unrelated formatting churn. Do not mix large research experiments with SDK maintenance changes.
