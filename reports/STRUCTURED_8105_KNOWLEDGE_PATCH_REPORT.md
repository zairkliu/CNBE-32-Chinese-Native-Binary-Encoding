# Structured 8105 Knowledge Patch Report

## Purpose

This report records the authorized repair of structured 8105 knowledge
files under `cnbe-research/knowledge/structured`.

It does not modify CNBE encoding tables, score rows, rebuild databases,
create tags, publish releases, or upload to PyPI.

## Result

- Mode: `apply_patch`
- Overall status: `PASS`
- Source write applied: `True`
- Baseline rows: `8105`
- Batch scoring allowed by this patch: `False`

## Dataset Repairs

| Dataset | Missing before | Extra before | Unicode repairs | Rows after |
|---|---:|---:|---:|---:|
| `base_character_data` | 3 | 2 | 7907 | 8105 |
| `cnbe_character_knowledge` | 3 | 2 | 7907 | 8105 |

## Backups

- `base_character_data`: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/base_character_data.json.bak.20260716T183315Z`
- `cnbe_character_knowledge`: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cnbe_character_knowledge.json.bak.20260716T183315Z`

## Next Steps

- rerun structured 8105 diff packet
- rerun cnbe-research source audit
- rerun knowledge inventory
- rerun GF0017 readiness gates
- then evaluate whether batch scoring can start
