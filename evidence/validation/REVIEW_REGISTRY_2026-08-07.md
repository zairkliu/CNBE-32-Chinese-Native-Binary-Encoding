# CNBE 项目审核登记 2026-08-07

| 日期 | 审核项 | 范围 | 结论 | 审核人 | 依据 | 验证 |
|---|---|---|---|---|---|---|
| 2026-08-07 | 8105 legacy 预填人工审核 | 491 行 | 436 批准 + 55 修正，方法有效 | zairkliu | [CNBE8105_LEGACY_PREFILL_2026-08-07.xlsx](C:/Users/zairk/OneDrive/桌面/CNBE8105_LEGACY_PREFILL_2026-08-07.xlsx) | legacy491_reviewed_packet.json，490/491 往返通过 |
| 2026-08-07 | GF0011 完整版 docx 入库与附形核对 | 201 主部首 + 84 表内附形 + 15 未列出附形 | 201/201 主部首解析；3 处校正（80 手→扌龵、123 老→耂、170 雨→⻗）；2 处待复核（50 彐、61 王）；附形口径 84+15=99（2009 后期），2022 修订为 100 | zairkliu | WorkBuddy 完整版 docx + ichara 公开转载 + 维基模板 | gf0011_201_radicals_full.json + GF0011_201_MAIN_ATTACHED_VERIFICATION.xlsx，201 主部首 / 84 附形全量列出 |

## 归档位置

- 审核后候选包：`experiments/2026-08-07_api_pipeline/results/legacy491_reviewed_packet.json`
- 审核报告：`reports/LEGACY491_REVIEW_SUMMARY_2026-08-07.md`
- 摄入脚本：`experiments/2026-08-07_api_pipeline/ingest_legacy_review.py`
- GF0011 完整表：`data/gf0011_201_radicals_full.json`
- GF0011 全量核对包：`experiments/2026-08-07_gg0011_pdf/results/GF0011_201_MAIN_ATTACHED_VERIFICATION.xlsx` / `.csv` / `.md`
- GF0011 解析脚本：`experiments/2026-08-07_gg0011_pdf/parse_gf0011_docx.py`、`parse_wiki_gf0011.py`、`ingest_gf0011_full.py`
