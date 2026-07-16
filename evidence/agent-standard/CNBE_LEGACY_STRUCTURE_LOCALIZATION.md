# CNBE Legacy Structure Localization

## Scope

This report maps the legacy 20,902-row English structure labels into the Agent standard Chinese structure labels.
It is read-only and does not modify `data/cnbe32.json` or any database.

## Summary

- Rows scanned: 20902
- Legacy labels: 13
- All legacy labels mapped: True
- Missing label rows: 0
- Struct type mismatch after Agent mapping: 12864

## Mapping

| Legacy label | Legacy type | Agent structure | Agent type | Rows | Confidence | Standard level |
| --- | --- | --- | --- | --- | --- | --- |
| single | 0 | 独体字 | 0 | 1608 | 1.0 | agent_standard_mapping_not_national_standard |
| up-down | 3 | 上下 | 1 | 1608 | 1.0 | agent_standard_mapping_not_national_standard |
| up-mid-down | 4 | 上中下 | 2 | 1608 | 1.0 | agent_standard_mapping_not_national_standard |
| left-right | 1 | 左右 | 3 | 1608 | 1.0 | agent_standard_mapping_not_national_standard |
| left-mid-right | 2 | 左中右 | 4 | 1608 | 1.0 | agent_standard_mapping_not_national_standard |
| top-left-wrap | 5 | 左上包 | 5 | 1608 | 0.85 | agent_standard_mapping_not_national_standard |
| top-right-wrap | 6 | 右上包 | 6 | 1608 | 0.85 | agent_standard_mapping_not_national_standard |
| left-wrap | 10 | 左三包 | 7 | 1608 | 0.75 | agent_standard_mapping_not_national_standard |
| bottom-left-wrap | 7 | 左下包 | 8 | 1608 | 0.75 | agent_standard_mapping_not_national_standard |
| top-wrap | 8 | 上三包 | 9 | 1608 | 0.75 | agent_standard_mapping_not_national_standard |
| bottom-wrap | 9 | 下三包 | 10 | 1608 | 0.75 | agent_standard_mapping_not_national_standard |
| full-wrap | 11 | 全包围 | 11 | 1607 | 1.0 | agent_standard_mapping_not_national_standard |
| triangle | 12 | 镶嵌 | 12 | 1607 | 0.65 | agent_standard_mapping_not_national_standard |

## Interpretation

The legacy `struct_type` ordering is not the same as the Agent standard ordering.
The localized Chinese structure name is suitable as Agent standard output after gates pass, but must not be described as a national-standard output.

## Review Rules

- Use the localized Chinese label as the Agent standard structure label.
- Preserve the legacy English label as raw evidence.
- Preserve the legacy `struct_type` when reporting old rows.
- Use the Agent `struct_type` only in dry-run or approved repair candidates.
- Do not claim this localization table is a national standard.
- Do not overwrite CNBE source data from this report alone.

## Next Gate

After localization, every row still needs Unicode alignment, source-grade evidence, GF0017-compatible scoring, and batch checkpoint review.
Rows with low-confidence localization, source gaps, or evidence gaps must remain reviewable before any source table change.
