# CNBE-32: v10 Experiments — Cross-Domain Generalization

This directory contains all v10-phase experiments validating structured encoding across 9 domains.

## Sub-experiments

| Directory | Domain | Key Metric |
|-----------|--------|:----------:|
| Core (this level) | v10.0 A-share backtest | CNBE positive returns |
| v101_timescale/ | Multi-scale backtest | 5min/15min/daily validation |
| v102_six_month/ | 6-month cross-period | Positive returns both markets |
| v10_3_typhoon/ | Meteorology | Path error -19 percent |
| v10_4_protein/ | Bioinformatics | Q3 41.0 percent |
| v10_5_blackhole/ | Physics (Gaia BH1) | R-squared 0.60-0.77 |
| v10_6_decision_center/ | Sociology | Compared vs One-Hot |
| v10_7_pretrain_base/ | Pre-training | Frozen embedding close to learned |
| v10_8_math_reasoning/ | Mathematics | CNBE wins all tasks |
