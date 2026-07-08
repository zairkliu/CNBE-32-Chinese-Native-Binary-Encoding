# CNBE-32: v9 Experiments — JEPA Semantic Prediction

All v9-phase experiments for CNBE-32, focused on JEPA prediction.

## Sub-experiments

| Directory | Focus | Key Metric |
|-----------|-------|:----------:|
| Core (this level) | v9.0 Tree growth JEPA | Error 0.0899 to 0.000001 |
| v91_lifecycle/ | Typhoon lifecycle prediction | Error reduced 4 orders |
| v92_financial/ | 2008 financial crisis | CNBE 99% better than baselines |
| v93_tick_ablation/ | Ablation + S&P500 tick data | Component analysis |
| v94_monthly/ | Cross-period robustness | 168 experiments |

## Core Files
- fix_cnbe.py, run_experiments.py, test_cnbe.py - v9.0 entry points
- src/ - tree encoder, JEPA model, environment
