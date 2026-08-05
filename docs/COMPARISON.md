# CNBE-32: Comparison with Existing Approaches

## 2026-08-05 客观量化对比（现行）

- 报告与原始数据：[experiments/2026-08-05_scheme_comparison/REPORT.md](../experiments/2026-08-05_scheme_comparison/REPORT.md) / [results.json](../experiments/2026-08-05_scheme_comparison/results.json)
- 范围：8105 通用规范汉字；数据源：CNBE 运行时库、cjkvi-ids、Unihan 17.0.0（kFourCornerCode / kCangjie）
- 关键结果：CNBE 唯一率 0.9995（4 个重码）、IDS 0.9996（3 个重码）、仓颉 0.9754（186 个重码）、四角 0.6032（1551 个重码）；五笔因缺少权威机器可读表暂作定性说明。

---

## 历史：算法/数据/硬件分层比较（legacy）

## Algorithm Layer

- ChineseBERT (ACL 2021): Renders characters as images for glyph features -- software only
- Glyph2Vec / Radical Embedding: Used in font conversion, OCR -- data level only

## Data Layer

- Unicode IDS: Describes structure with text symbols -- CPU does not compute
- CHISE (Japan): Large character structure database -- for lookup only
- Cangjie/Wubi: Input methods -- human-to-machine mapping

## Hardware Layer

**CNBE-32 is the only known project** that integrates Chinese character structure into CPU instruction sets, OS kernels, and machine encoding at the binary level.

## Similar Efforts

- FuXi-128: Uses Chinese characters as CPU instruction mnemonics -- conceptual/educational only
