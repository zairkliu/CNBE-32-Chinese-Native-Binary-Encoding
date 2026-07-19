# ZDIC Structure Reference Extraction

- Overall status: `PASS_ZDIC_STRUCTURE_REFERENCE_EXTRACTION_READY`
- Requested characters: 5
- Parsed with normalized structure: 5
- Records with any fields: 5
- Online fetch enabled: `True`
- GF0017 points assigned: 0
- CNBE rows written: 0

ZDIC is machine-extracted as `network_cross_reference` only. It is not
national-standard authority and does not directly assign scores.

## Extracted Rows

| Char | Unicode | Status | Structure | Radical | Strokes | URL |
|---|---|---|---|---|---:|---|
| 丁 | `U+4E01` | `PARSED_WITH_STRUCTURE` | `单一结构` | `一` | `2` | https://www.zdic.net/hans/%E4%B8%81 |
| 已 | `U+5DF2` | `PARSED_WITH_STRUCTURE` | `单一结构` | `己` | `3` | https://www.zdic.net/hans/%E5%B7%B2 |
| 亡 | `U+4EA1` | `PARSED_WITH_STRUCTURE` | `单一结构` | `亠` | `3` | https://www.zdic.net/hans/%E4%BA%A1 |
| 与 | `U+4E0E` | `PARSED_WITH_STRUCTURE` | `单一结构` | `一` | `3` | https://www.zdic.net/hans/%E4%B8%8E |
| 焱 | `U+7131` | `PARSED_WITH_STRUCTURE` | `上下结构` | `火` | `12` | https://www.zdic.net/hans/%E7%84%B1 |

## Decision

ZDIC fields are now machine-extracted as network cross-reference evidence. They can reduce manual lookup work but still require standards-aware review before scoring or encoding changes.
