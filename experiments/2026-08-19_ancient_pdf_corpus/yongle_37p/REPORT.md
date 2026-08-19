# 永乐大典 37 页端到端评估

日期：2026-08-19  
数据：37 页人工真值库 + VL-1.6 OCR 页面

## 结果

| 指标 | 值 |
|---|---:|
| 页面数 | 37 |
| 真值汉字数 | 16,123 |
| 基线准确率 | 90.91% |
| Unihan variant map 修正后 | 92.64% |
| 提升 | +1.74pp |

## 说明

- 基线：VL-1.6 OCR 原始输出；
- 修正：只使用 `variant_rules.json`，不依赖真值；
- 提升来自 354 个异体字替换对；
- CNBE 覆盖率在 OCR pilot 中达到 100%。

## 文件

- `evaluate_yongle_37p.py`
- `yongle_37p_results.json`

## 下一步

- 把 GBDT/MLP re-ranker 接入端到端修正；
- 对 70 页完整卷981补充真值；
- 扩展到更多 PDF。
