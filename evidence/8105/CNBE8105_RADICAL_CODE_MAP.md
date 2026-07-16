# CNBE-32 8105 Radical Code Map

## Scope

This report validates whether proposed radical names in the 8105 auto-fix candidates can be assigned numeric radical codes.
It does not modify source CNBE data and does not recalculate 32-bit CNBE values.

## Source Gate

- Source declared count: 201
- Source actual count: 214
- Source count consistent: False

## Candidate Gate

- Candidate rows: 6314
- Unique candidate radicals: 244
- Direct radical names: 184
- Alias radical names: 53
- Blocked radical names: 7
- Ready candidate rows: 6184
- Blocked candidate rows: 130

## Alias Samples

| Variant | Canonical | Code | Candidate Rows |
| --- | --- | --- | --- |
| 氵 | 水 | 85 | 343 |
| 艹 | 艸 | 140 | 321 |
| 扌 | 手 | 64 | 248 |
| 钅 | 金 | 167 | 209 |
| 亻 | 人 | 9 | 201 |
| 讠 | 言 | 149 | 133 |
| ⺼ | 肉 | 130 | 131 |
| 纟 | 糸 | 120 | 131 |
| 忄 | 心 | 61 | 125 |
| ⺮ | 竹 | 118 | 107 |
| 辶 | 辵 | 162 | 96 |
| 鱼 | 魚 | 195 | 72 |
| 犭 | 犬 | 94 | 68 |
| 鸟 | 鳥 | 196 | 67 |
| 贝 | 貝 | 154 | 59 |
| 马 | 馬 | 187 | 51 |
| 刂 | 刀 | 18 | 50 |
| 衤 | 衣 | 145 | 49 |
| 车 | 車 | 159 | 49 |
| 门 | 門 | 169 | 44 |
| 饣 | 食 | 184 | 36 |
| 页 | 頁 | 181 | 35 |
| 礻 | 示 | 113 | 33 |
| 攵 | 攴 | 66 | 21 |
| 灬 | 火 | 86 | 19 |
| 罒 | 网 | 122 | 15 |
| 户 | 戶 | 63 | 13 |
| 见 | 見 | 147 | 13 |
| 齿 | 齒 | 211 | 12 |
| 风 | 風 | 182 | 8 |

## Blocked Radicals

| Radical | Candidate Rows | Reason |
| --- | --- | --- |
| 阝 | 116 | position-sensitive: left 阝 is 阜, right 阝 is 邑; source does not preserve side. |
| 丷 | 5 | component-like label; no conservative modern radical code assignment in this phase. |
| 乚 | 3 | stroke/component-like label; no conservative radical assignment in this phase. |
| 巳 | 2 | ambiguous against 己/已/巳 shape group in this evidence layer. |
| 民 | 2 | component-like label; not a Kangxi radical main-form in the mapping source. |
| 乛 | 1 | stroke/component-like label; no conservative radical assignment in this phase. |
| 兀 | 1 | component-like label; ambiguous against 儿 in this evidence layer. |

## Decision

The radical-code gate is not fully closed while blocked radicals remain.
A later dry-run patch may only use candidates whose proposed radical resolves as DIRECT or ALIAS.
