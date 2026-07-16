# CNBE Agent Encoding Standard

## Standard Level

`8105` and cited GF/GB/GG files are the national-standard baseline.
This document defines the CNBE Agent standard: a project-level encoding standard aligned to 8105, not a national-standard document.

## Mandatory Order

| Step | Gate |
| --- | --- |
| 1 | Unicode identity |
| 2 | 8105 or extension scope classification |
| 3 | source-grade evidence |
| 4 | Hanzi knowledge schema |
| 5 | GF0017 50-point audit |
| 6 | Agent-standard mapping for out-of-scope rows |
| 7 | CNBE32 dry-run candidate |
| 8 | roundtrip and batch checkpoint audit |

## Allowed Agent Structures

| Agent structure | Agent struct_type |
| --- | --- |
| 独体字 | 0 |
| 上下 | 1 |
| 上中下 | 2 |
| 左右 | 3 |
| 左中右 | 4 |
| 左上包 | 5 |
| 右上包 | 6 |
| 左三包 | 7 |
| 左下包 | 8 |
| 上三包 | 9 |
| 下三包 | 10 |
| 全包围 | 11 |
| 镶嵌 | 12 |

## Legacy Localization

| Legacy label | Agent structure | Agent struct_type | Confidence |
| --- | --- | --- | --- |
| single | 独体字 | 0 | 1.0 |
| up-down | 上下 | 1 | 1.0 |
| up-mid-down | 上中下 | 2 | 1.0 |
| left-right | 左右 | 3 | 1.0 |
| left-mid-right | 左中右 | 4 | 1.0 |
| top-left-wrap | 左上包 | 5 | 0.85 |
| top-right-wrap | 右上包 | 6 | 0.85 |
| left-wrap | 左三包 | 7 | 0.75 |
| bottom-left-wrap | 左下包 | 8 | 0.75 |
| top-wrap | 上三包 | 9 | 0.75 |
| bottom-wrap | 下三包 | 10 | 0.75 |
| full-wrap | 全包围 | 11 | 1.0 |
| triangle | 镶嵌 | 12 | 0.65 |

## CNBE32 Carrier

- bits 31..24: radical code
- bits 23..19: stroke count
- bits 18..15: structure type
- bits 14..4: group index
- bits 3..0: extension flags

CNBE32 is a compact carrier. It is not the linguistic authority.

## Output Rule

`AGENT_STANDARD_MAPPING` may be used as this Agent's standard output after Unicode, evidence, Hanzi schema, GF0017, and batch gates pass.
It must be labeled as `agent_standard_aligned_to_8105_not_national_standard`.
