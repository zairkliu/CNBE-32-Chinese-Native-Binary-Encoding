---
name: cnbe-ebook-corpus-builder-v3
description: 编写“电子书 -> AI 高质量语义语料”批量转换程序 v3.0 MVP 的 Codex 规则。当用户要求实现 azw3/mobi/epub 批量转 TXT、去出版信息、去非中文干扰、CNBE 编码、语料打包，或提到 v3.0 MVP、5516 本电子书时使用。
tags: [Ebook, Corpus, CNBE-32, Pipeline, Python, Calibre, Pandoc]
---

# E-book -> AI 高质量语义语料 v3.0 MVP

## 目标

把 `.azw3 / .epub / .mobi` 电子书批量转换成适合 AI 训练的高质量中文纯文本：

- 每本一个扁平 UTF-8 `.txt`
- 可选 CNBE-32 `.cnbe` 码流
- `manifest.json`、`quality_report.json`、`all_publications.txt`

## 架构

```text
input/*.azw3|.mobi|.epub
  -> Calibre 转 epub（epub 直接跳过）
  -> Pandoc 转 markdown
  -> clean_to_txt() 清洗
  -> 可选 encode_cnbe() -> .cnbe
  -> 质量门槛 -> manifest/quality_report
```

## 依赖

- Python 3.11+
- Calibre `ebook-convert`
- Pandoc
- numpy
- 可选 `cnbe32.db`

## CLI

```bash
python main.py --input <dir> --output <dir> --db cnbe32.db --jobs 4 --merge
```

## 清洗规则

1. 删除 YAML frontmatter；
2. 删除版权页、CIP、ISBN、书号、出版社、电子版制作信息；
3. 删除“总目录”整块、书名/作者/译者/编者/主编；
4. 删除通讯地址、邮编、电话、邮箱、开本、印张、定价；
5. 删除理想国译丛序、丛书总序、出版说明、编辑推荐、内容提要、
   作者简介等前页整块；
6. 删除图片、目录链接、脚注、HTML/CSS、页码、`[TABLE]`；
7. 书名页标题后出现著/译/出版社/ISBN/版权时跳过；
8. Markdown 标题与引用符转为纯文本。

## 质量门槛

- 单书 ≥1000 字符；
- 核心中文占比 ≥70%，技术 30%-70%，其余排除；
- CJK-only CNBE 覆盖率 ≥99.9%；
- minhash 去重阈值 0.7；
- 每类抽样 5 本复核。

## 实现复用

- `clean_publication_markdown.py`：清洗规则；
- `batch_encode_publications.py`：CNBE 编码；
- `dedup_corpus_minhash.py`：去重；
- v2 `azw3-corpus-pipeline/convert.py`：Calibre/Pandoc 编排。

## 非目标

- 不做 GUI（本期）；
- 不处理 DRM；
- 不做 OCR；
- 不做模型训练。

## 验收

- azw3/mobi/epub 各 1 本跑通；
- 输出不含版权/ISBN/CIP/总目录；
- 单本失败不中断；
- 二次运行跳过相同 SHA-256；
- CNBE CJK-only 覆盖率报告正常。
