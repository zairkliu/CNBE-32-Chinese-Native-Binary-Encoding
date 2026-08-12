# Codex 规则：E-book -> AI 高质量语义语料 v3.0 MVP

用途：在一个新对话中，依据本规则实现一个批量转换程序。
输入：`.azw3 / .epub / .mobi` 电子书（现有 5,516 个文件）。
输出：去出版信息、去非中文干扰的 AI 训练纯文本，可选 CNBE 码流。

## 一、目标

把 v2 的“AZW3 -> EPUB -> Markdown”升级为：

```text
mobi/azw3/epub -> 统一中间态 -> 干净 TXT -> 可选 CNBE -> 质量报告
```

每一本书只产出一个扁平 UTF-8 `.txt`，并生成：

```text
manifest.json
quality_report.json
all_publications.txt
conversion.log
```

## 二、架构

```text
input/
├── a.azw3
├── b.mobi
└── c.epub
        │
        ▼
convert_book()
  ├─ azw3/mobi -> Calibre ebook-convert -> epub
  ├─ epub -> Pandoc -> markdown
  └─ clean_to_txt(markdown) -> txt
        │
        ▼
optional: encode_cnbe(txt) -> .cnbe
        │
        ▼
quality gates -> manifest/quality_report/merged txt
```

## 三、依赖

- Python 3.11+
- Calibre（`ebook-convert`）
- Pandoc
- numpy
- 可选：`cnbe32.db`（CNBE-32 编码表）

找不到工具时支持 CLI 参数显式指定路径。

## 四、CLI 规范

```bash
python main.py \
  --input <ebooks_dir> \
  --output <out_dir> \
  --db <cnbe32.db> \
  --jobs 4 \
  --keep-epub \
  --force \
  --merge
```

输出目录：

```text
out/
├── txt/<slug>.txt
├── cnbe/<slug>.cnbe        # 可选
├── all_publications.txt
├── manifest.json
├── quality_report.json
└── conversion.log
```

## 五、格式处理

| 格式 | 处理 |
|---|---|
| epub | 直接交给 Pandoc 转 Markdown |
| azw3 | Calibre 转 epub，再转 Markdown |
| mobi | Calibre 转 epub，再转 Markdown |

- 单书失败不中断批次；
- 临时 epub 默认删除，`--keep-epub` 保留；
- 相同源文件 SHA-256 且已成功时跳过，`--force` 强制重转。

## 六、v3 清洗规则

从 v2 继承并强化：

### 1. 转换层

- 删除 EPUB 内 raw HTML/script/style；
- 删除图片与媒体引用；
- 按 OPF spine 保持正文顺序。

### 2. 出版信息

- 删除 YAML frontmatter；
- 删除版权页、版权声明、CIP、ISBN、书号、出版社、电子版制作信息；
- 删除“总目录”整块与书名/作者/译者/编者/主编行；
- 删除通讯地址、邮编、电话、邮箱、开本、印张、定价；
- 删除理想国译丛序、丛书总序、出版说明、编辑推荐、内容提要、
  作者简介等前页整块；
- 书名页标题后出现著/译/出版社/ISBN/版权时，跳过该标题继续找章节。

### 3. 非中文干扰

- 删除图片、目录链接、脚注、HTML/CSS、页码、`[TABLE]`；
- Markdown 标题、引用符转为纯文本；
- 保留中文标点；西文、数字、未知字符保留在原文中但计入 code 0；
- 核心子集要求中文占比 ≥70%，技术子集 30%-70%，其余排除。

## 七、质量门槛

| 指标 | 要求 |
|---|---|
| 单书输出 | ≥1000 字符 |
| 中文占比 | 核心 ≥70%；技术 30%-70% |
| CJK-only CNBE 覆盖率 | ≥99.9% |
| minhash 去重 | 阈值 0.7，报告重复组 |
| 抽样复核 | 每类至少 5 本 |
| 出版信息抽查 | 不应出现版权页/CIP/总目录 |

`quality_report.json` 必须包含：

```json
{
  "files": 5516,
  "ok": 0,
  "failed": 0,
  "core": 0,
  "technical": 0,
  "excluded": 0,
  "cjk_coverage": 0.0,
  "duplicate_groups": 0,
  "warnings": []
}
```

## 八、CNBE 编码（可选但推荐）

- 使用 CNBE-32 lookup table，`code 0` 表示未知；
- 输出大端 4 字节/字 `.cnbe`；
- 记录每本覆盖率与 CJK-only 覆盖率。

## 九、MVP 范围

本期只做：

- 命令行工具；
- 批量转换 + 清洗 + 质量报告；
- 可选 CNBE 编码；
- 可选合并 `all_publications.txt`。

本期不做：

- GUI；
- DRM 去除；
- OCR；
- 模型训练；
- 云上传自动化。

## 十、验收测试

1. 分别用 1 本 azw3、1 本 mobi、1 本 epub 跑通；
2. 输出 TXT 不含“版权/ISBN/CIP/总目录”等出版信息；
3. manifest 每本书有 status；
4. 单本损坏不影响其他书；
5. 同一书二次运行跳过；
6. CNBE 编码后 CJK-only 覆盖率报告正常。

## 十一、打包

- PyInstaller 打包 CLI 或窗口版；
- 内置 `filters/`、`cnbe32.db`（可选）、字体（可选）；
- 复用 v2 的 `azw3-corpus-pipeline` 作为转换骨架，替换清洗模块。

## 十二、实现建议

直接复用已有模块：

- `clean_publication_markdown.py`：清洗规则；
- `batch_encode_publications.py`：CNBE 批量编码；
- `dedup_corpus_minhash.py`：内容级去重；
- v2 `convert.py`：Calibre/Pandoc 编排与 manifest。

新增：

- `discover_books()`：支持 azw3/mobi/epub；
- `clean_to_txt()`：v3 清洗；
- `quality_gates()`：子集与覆盖率；
- `merge_all()`：合并输出。
