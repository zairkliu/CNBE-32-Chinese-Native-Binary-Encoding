# GG 0011-2009 汉字部首表 API 分析报告（2026-08-07）

## 来源

- 官方 PDF：`GG 0011-2009 汉字部首表.pdf`（9 页扫描件，无文本层）
- OCR 引擎：PaddleOCR-VL-1.6 云端 API（job 提交/轮询，9 页 + 1 张内嵌表格图）
- 交叉参考：仓库内 `data/gf0011_201_radicals.json`（公开转载表）

## OCR 覆盖

| 项目 | 数量 |
|---|---:|
| 主部首（GF0011 表） | 201 |
| OCR 识别到主部首 | 180 |
| OCR 缺失主部首 | 21 |
| OCR 识别到附形部首条目 | 79 |
| 附形部首（GF 公开表回退） | 84 个字符 |
| 主部首 OCR 与公开表不一致 | 16 |
| 附形 OCR 与公开表不一致 | 27 |

OCR 缺失的主部首：122、167-187，集中在七画至九画区间，页面 007 的 OCR 输出不完整。

## 关系结果

`results/gg0011_main_attached_relation.json` 已保存 201 个主部首的完整关系：

- `main`：主部首（GF0011 公开表回退）
- `attached_forms`：附形部首（公开表回退）
- `ocr_main` / `ocr_attached_forms`：PaddleOCR-VL 原始识别
- `status`：MATCH / OCR_MAIN_MISMATCH / OCR_ATTACHED_MISMATCH / OCR_MISSING_MAIN

## 典型差异

- 编号 5：官方 PDF 前言称“序号为5的‘一’部”，公开转载表写为“乛”，两者存在编号/字形差异，需人工核对；
- 50 彐：OCR 输出“彐(丩互)”，公开表为“彐(彑)”；
- 64 木：OCR 输出“木(木)”，公开表为“木(朩)”；
- 126 覀：OCR 输出“酉(西西)”，公开表为“覀(襾西)”。

## 结论

PaddleOCR-VL-1.6 能稳定提取主部首与括注附形部首，覆盖约 89.6% 主部首；正式关系表以官方 PDF 为准仍需对 OCR 差异和缺失页人工复核。当前交付物为“OCR 原始 + 公开表回退”的关系候选，不宣称已完成国标逐项校对。

## 产物

- `results/gg0011_api_raw_entries.json`：OCR 原始条目
- `results/gg0011_main_attached_relation.json`：201 主部首 + 附形关系
- `results/GG0011_201_100_relation.xlsx` / `.csv`：可读表格
- `ocr_cloud/pages/`：9 页 Markdown
- `ocr_cloud/raw/`：API 原始 JSON
