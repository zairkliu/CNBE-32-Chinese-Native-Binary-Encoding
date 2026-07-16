# CNBE-32 8105 Dry-Run Patch

## Scope

This report previews the field-level patch for radix-ready 8105 candidates.
It does not write to `cnbe32_updated.json`, does not update SDK databases, and does not change golden vectors.

## Gate

- Dry-run ready rows: 6184
- Radix blocked rows: 130
- All roundtrips pass: True
- Write gate: NO_WRITE_DRY_RUN_ONLY

## Changed Field Counts

| Field | Rows |
| --- | --- |
| cnbe | 6184 |
| radix | 6158 |
| radix_name | 6171 |
| strokes | 5995 |
| struct_name | 4327 |
| struct_type | 4327 |

## Known Ready Samples

| Char | Current CNBE | Proposed CNBE | Current Radical | Proposed Radical | Current Strokes | Proposed Strokes | Current Structure | Proposed Structure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 家 | 0x5741DB60 | 0x2850DB60 | 爪 | 宀 | 8 | 10 | 左右 | 上下 |
| 遛 | 0x52F8A5B0 | 0xA26C25B0 | 毛 | 辶 | 31 | 13 | 上下 | 左下包 |
| 涡 | 0xB43DFA10 | 0x5551FA10 | 音 | 氵 | 7 | 10 | 全包围 | 左右 |
| 焱 | 0x16A03310 | 0x5660B310 | 匚 | 火 | 20 | 12 | 独体字 | 上下 |
| 衍 | 0xA078A4D0 | 0x904E24D0 | 辛 | 行 | 15 | 9 | 上下 | 镶嵌 |

## First Blocked Samples

| Char | Unicode | Radical | Reason |
| --- | --- | --- | --- |
| 卫 | U+536B | 乛 | stroke/component-like label; no conservative radical assignment in this phase. |
| 队 | U+961F | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 邓 | U+9093 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 兰 | U+5170 | 丷 | component-like label; no conservative modern radical code assignment in this phase. |
| 民 | U+6C11 | 民 | component-like label; not a Kangxi radical main-form in the mapping source. |
| 邦 | U+90A6 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 邪 | U+90AA | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 关 | U+5173 | 丷 | component-like label; no conservative modern radical code assignment in this phase. |
| 阵 | U+9635 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 阳 | U+9633 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 阶 | U+9636 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 阴 | U+9634 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 防 | U+9632 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 邮 | U+90AE | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 乱 | U+4E71 | 乚 | stroke/component-like label; no conservative radical assignment in this phase. |
| 邻 | U+90BB | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 际 | U+9645 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 陆 | U+9646 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 阿 | U+963F | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 陈 | U+9648 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 阻 | U+963B | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 附 | U+9644 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 郁 | U+90C1 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 乳 | U+4E73 | 乚 | stroke/component-like label; no conservative radical assignment in this phase. |
| 郊 | U+90CA | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 氓 | U+6C13 | 民 | component-like label; not a Kangxi radical main-form in the mapping source. |
| 郑 | U+90D1 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 郎 | U+90CE | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 陌 | U+964C | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 陕 | U+9655 | 阝 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |

## Decision

This dry-run is suitable for review only. A write patch requires explicit authorization and must operate on a copied dataset first.
