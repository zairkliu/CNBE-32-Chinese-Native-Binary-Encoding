# CNBE-32 Algebraic Specification Draft

This is the formal counterpart of the passing property tests.

- `CNBE32_ALGEBRA.tla`: lightweight TLA+ draft with `Map / Extract / Cmp / Skill`.
- It is not yet TLC-checkable; the next step is to bind it to the actual 21,178-row table and run TLC.
- After TLA+ stabilizes, the same axioms can be encoded in Coq, and C/Verilog implementations can be checked with CBMC / SymbiYosys.

Current property-test baseline (see `results/`):

| Axiom | Checks | Passed |
|---|---|---:|
| extract(map(U),field)=field(U) | 105,890 | 105,890 |
| cmp nonneg/symmetric | 500,000 | 500,000 |
| cmp triangle | 500,000 | 500,000 |
| skill(map(U)) first-match | 21,178 | 21,178 |
| hash reverse = linear reverse | 10,000 | 10,000 |
