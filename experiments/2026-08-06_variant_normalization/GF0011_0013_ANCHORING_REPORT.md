# GF0011/GF0013 锚定说明（2026-08-06）

## 结论摘要

对 2026-08-06 人工复核批准的 812 条 provisional 候选，执行 GF0011/GF0013 正式锚定尝试：

| 项目 | 数量 | 状态 |
|---|---:|---|
| 批准候选总数 | 812 | - |
| GF0011 部首名称/附形匹配 | 805 | MAPPED |
| 需 GF0012 归部复核 | 7 | REQUIRES_GF0012_REVIEW |
| GF0013 笔画候选（Unihan 交叉参考） | 812 | REQUIRES_OFFICIAL_STROKE_TABLE |

## GF0011 锚定边界

- 依据 GF0011-2009《汉字部首表》公开转载版（主部首 201 个、附形部首 99 个），来源：
  https://www.ichara.cn/web/account/view_article.php?art_id=110
- 锚定方式：以人工复核的部首名为键，匹配 GF0011 主部首或附形部首名称。
- 本次匹配是“名称/附形匹配”，不是逐字归部。逐字归部以 GF0012-2009 为准，本包不冒充权威归部。

## 7 条待 GF0012 复核项

以下人工复核部首名不在 GF0011 201 主部首或附形部首名称表中，不能直接声称已锚定：

| 汉字 | 人工复核部首名 | GF0013 笔画候选 |
|---|---|---:|
| 也 | 乙 | 3 |
| 亂 | 乚 | 13 |
| 黃 | 黃 | 12 |
| 區 | 匸 | 11 |
| 亞 | 二 | 8 |
| 夐 | 夊 | 14 |
| 黈 | 黃 | 16 |

## GF0013 边界

- 仓库内没有 GF0013-2009 权威逐字笔画表的机器可读版本。
- 数据包中的 `gf0013_strokes_candidate` 仅取自 Unihan `kTotalStrokes`，属交叉参考，不作为国标笔画锚定结论。
- 正式锚定需补充权威逐字笔画表后重跑。

## 产物

- `data/gf0011_201_radicals.json`：GF0011 201 部首表（编号/主部首/附形）。
- `experiments/2026-08-06_variant_normalization/gf0011_0013_anchoring_packet.json`：812 条逐字锚定状态。

## 复现

```bash
python3 experiments/2026-08-06_variant_normalization/build_gf_anchoring.py
```
