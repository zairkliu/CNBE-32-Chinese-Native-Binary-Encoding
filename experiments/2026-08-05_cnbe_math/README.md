# CNBE-32 Mathematical Foundation Experiments (2026-08-05)

**Status**: run on Ubuntu-26.04 WSL against `data/cnbe32.db` (21,178 rows).

This experiment pack validates five deepening directions proposed for the CNBE-32
mathematical model:

1. Metric-space axioms for `cnbe.cmp`
2. Lattice / poset structure and range queries
3. Information-theoretic entropy of the 8/5/4 field allocation
4. Hyperbolic-geometry distance as an alternative similarity
5. Lightweight algebraic specification and property tests

## Result summary

See [REPORT_2026-08-05.md](REPORT_2026-08-05.md) after running the scripts.

## How to run

```bash
python3 scripts/metric_space.py
python3 scripts/lattice_range.py
python3 scripts/information_theory.py
python3 scripts/hyperbolic.py
python3 scripts/algebra_spec.py
python3 scripts/deep_analysis.py
python3 scripts/consolidate.py
```

Formal specification draft: `spec/CNBE32_ALGEBRA.tla`.
