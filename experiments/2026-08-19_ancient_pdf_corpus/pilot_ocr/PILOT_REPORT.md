# 古籍 PDF OCR Pilot

日期：2026-08-19  
PDF：永乐大典卷913-914（前 2 页）

## 结果

| 页 | 汉字数 | 唯一字 | CNBE DB 覆盖率 | 标准轨覆盖率 |
|---|---:|---:|---:|---:|
| page-001 | 0 | 0 | - | - |
| page-002 | 3696 | 31 | 100% | 100% |

说明：

- 第 1 页为封面，无汉字；
- 第 2 页识别正常，且全部汉字都能在 CNBE DB 和标准轨命中；
- 使用 `pdftoppm 60dpi` + Ollama `deepseek-ocr`；
- 提示词必须为 `OCR the image`，长指令会导致模型复读。

## 复现

```bash
python experiments/2026-08-19_ancient_pdf_corpus/pilot_ocr/pilot_ocr.py \
  --first 1 --last 2
```

## 下一步

- 用已有真值库对 981 卷 70 页做端到端校对；
- 加入行级去重；
- 扩展到更多 PDF。
