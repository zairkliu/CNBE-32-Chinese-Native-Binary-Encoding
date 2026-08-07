# GF0011/GF0012 权威标准补位来源盘点

日期：2026-08-07

## 结论

1. **PaddleOCR-VL-1.6 对 GF0011 的失败不是算力问题**，而是国家标准 PDF 本身以扫描件发布。已实测 GF0011、GF0012、GF0013、GF0014、GF2001 官方 PDF 均无文本层；因此 OCR 结果只能作为 `DRAFT / NOT_AUTHORITATIVE`，不能作为正式锚定证据。
2. **可直接补位的机器可读来源是 Unicode 与开源构形层**：Unihan `kRSUnicode` / `kTotalStrokes`（Unicode 权威）、CHISE/cjkvi-ids（IDS 结构权威）、8105 转录库、汉典/康熙等词典上下文。
3. **GF0012-2009《GB13000.1字符集汉字部首归部规范》的 20902 字逐字归部表是最大缺口**。官方附件已确认存在，但为 236 页扫描件；当前未发现公开机器可读版本，只能通过“官方扫描件 + 双引擎 OCR + 人工复核”重建。

## 一、官方标准层（权威，但扫描件为主）

| 标准 | 范围 | 官方来源 | 机器可读 | 本地状态 |
|---|---|---|---|---|
| GF 0011-2009 汉字部首表 | 201 主部首 / 附形部首 | 用户提供完整版 docx（含官方 PDF 9 页图像与文字层） | docx 文字层可解析，官方 PDF 为扫描件 | `data/gf0011_201_radicals_full.json`（完整版入库） |
| GF 0011-2022 汉字部首表（修订） | 201 主部首 / 约 100 附形部首 + 国际编码 | [gov.cn 公告](http://www.gov.cn/xinwen/2022-11/24/content_5728500.htm)、[moe.gov.cn 公告](https://hudong.moe.gov.cn/jyb_xwfb/gzdt_gzdt/s5987/202211/t20221118_995332.html) | 否 | 仅有公告文本，未见官方公开电子表 |
| GF 0012-2009 GB13000.1字符集汉字部首归部规范 | 20902 字逐字归部 | [moe.gov.cn](https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/200901/t20090102_186104.html)，附件 [15hanzibushou.zip](http://video.moe.gov.cn/yuxinsi/15hanzibushou.zip) | 否 | 已下载 236 页扫描件，零文本层 |
| GF 0013-2009 现代常用独体字规范 | 256 独体字 | [moe.gov.cn](https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75697.html) | 否 | 已下载 7 页扫描件，零文本层 |
| GF 0014-2009 现代常用字部件及部件名称规范 | 441 组 514 部件 | [moe.gov.cn](https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75696.html) | 否 | 已下载 41 页扫描件，零文本层 |
| GF 2001-2001 GB13000.1字符集汉字折笔规范 | 折笔笔形表 | [moe.gov.cn](https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75688.html) | 否 | 已下载 11 页扫描件，零文本层 |
| GF 3002-1999 GB13000.1字符集汉字笔顺规范 | 20902 字序号式笔顺 | [moe.gov.cn](http://www.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75619.html) | 否 | 附件下载被站点反爬拦截，未完成 |
| GF 0031-2026 通用规范汉字笔顺规范 | 通用规范汉字笔顺 | [duan.gov.cn](http://www.duan.gov.cn/ztzl/yywzflfgxc/t10786988.shtml) | 未核验 | 待抓取 |
| GB 18030-2022 信息技术 中文编码字符集 | 88115 汉字/部首编码 | [国家标准全文公开系统](https://openstd.samr.gov.cn/bzgk/std/nd?no=1783) | 全文需系统查阅 | 题录已确认 |
| 通用规范汉字表（国发〔2013〕23号） | 8105 字 | [gov.cn PDF](http://www.gov.cn/gzdt/att/att/site1/20130819/tygfhzb.pdf) | 否（95MB 扫描件） | 仓库已有 8105 基线 |

> 标准号说明：公开渠道存在 GF0013/GF0014 编号互置的转载。按语文出版社《语言文字规范（GF 0013-2009）：现代常用独体字规范》与《语言文字规范（GF 0014-2009）：现代常用字部件及部件名称规范》，以及教育部发布新闻的正文描述，本项目采用 **GF0013=独体字、GF0014=部件规范**；最终以印刷件封面为准。

## 二、本地仓库已有补充项目

仓库内已经具备一套可复现的三层交叉验证基础设施，可直接复用：

| 资产 | 作用 | 证据等级 |
|---|---|---|
| `data/gf0011_201_radicals_full.json` | GF0011 201 主部首/附形部首/笔画分组/附形条目 | 完整版 docx + ichara + 维基模板交叉，2026-08-07 入库 |
| `results/GF0011_201_MAIN_ATTACHED_VERIFICATION.xlsx` | 201 主部首 + 84 表内附形逐条核对 | docx/ichara/维基三方来源，84+15=99（2009 后期口径），2022 修订为 100 |
| `data/sources/unihan-17.0.0.json` | Unihan 17.0.0 来源登记与 SHA-256 | Unicode 权威 |
| `data/sources/hanzi-standard-learning.json` | 国标术语/来源映射（GF0013/14、GF3002、GF0031） | 来源清单 |
| `data/sources/cnbe-research-local.json` | 本地研究知识库 18 项来源审计 | 研究输入 |
| `data/sources/ihandian-dictionary-web.json` | 汉典籍网逐字参考 | 交叉参考 |
| `data/stroke_db.csv` | 笔画候选库 | 交叉参考 |
| `third_party/README.md` | cjkvi-ids、Unihan、8105 scope 的复现命令 | 交叉参考 |
| `reports/8105_CROSS_VALIDATION.md` | 8105 范围结构 94.7%、部首 90.4%、笔画 93.5% | 交叉验证 |
| `evidence/8105/pending276/zdic/` | 276 个 8105 缺字汉典原始页 | 词典上下文 |
| `reports/zdic_8105_gap_cache/` | 8105 全量缺口汉典 JSON 缓存 | 词典上下文 |
| `evidence/8105/pending276/radical_name_to_kangxi.json` | 部首名到康熙 214 映射 | 交叉参考 |
| `experiments/2026-08-06_variant_normalization/GF0011_0013_ANCHORING_REPORT.md` | 812 条 provisional 的 GF0011 锚定与 7 条待 GF0012 复核项 | 中间结论 |
| `reports/external_dictionary_source_candidate_evaluation.json` | Kanripo、康熙、nlp-han-dicts 候选评估 | 外部来源评估 |

### 工作区补充项目（主仓库之外）

| 项目 | 作用 | 状态 |
|---|---|---|
| `work/roadmap/gf201_audit/` | `audit_gf201_mapping.py` + `radix_inventory.csv` + `GF201_GAP_REPORT.md`，审计当前 radix 口径 | 当前 distinct radix=212、最大 id=214，GF0011 期望 201；结论 `NOT_ANCHORED` |
| `work/roadmap/ROADMAP_EXECUTION.md` | GF0011 锚定、分栏 OCR、形近字抽检、WS-4 路线 | “拿到 GF0011 权威映射表后迁移 radix 字段并冻结” |

## 三、GitHub 外部补充项目

| 项目 | 许可证 | 作用 | 本项目判定 |
|---|---|---|---|
| [cjkvi/cjkvi-ids](https://github.com/cjkvi/cjkvi-ids) | 上游 GPLv2 | CJK IDS 结构分解 | 已纳入 `third_party`，交叉参考 |
| [Transfusion/cjkvi-ids-unicode](https://github.com/Transfusion/cjkvi-ids-unicode) | GPL-2.0 | Unicode-only CJKV IDS | 结构分解候选 |
| [shengdoushi/common-standard-chinese-characters-table](https://github.com/shengdoushi/common-standard-chinese-characters-table) | 未声明 | 8105 字表转录 | 8105 范围补位 |
| [max32002/chinese_dictionary](https://github.com/max32002/chinese_dictionary) | 未声明 | 81,052 字 部首/笔画/異體字/文字組件 JSON | 仅交叉参考，需质量抽查 |
| [howl-anderson/hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi) | Apache-2.0 | 汉字拆字/偏旁部首 | 部件与结构候选 |
| [hanziku/hanziyin](https://github.com/hanziku/hanziyin) | MPL-2.0 | IDS 拆分与搜索 | 结构候选 |
| [skishore/makemeahanzi](https://github.com/skishore/makemeahanzi) | NOASSERTION | 9000+ 字笔顺/分解/部首数据 | 字形与笔顺候选 |
| [cihai/unihan-etl](https://github.com/cihai/unihan-etl) | MIT | Unihan 导出 CSV/JSON/YAML | Unihan 管道工具 |
| [yawnoc/unihan-radical-strokes-readable](https://github.com/yawnoc/unihan-radical-strokes-readable) | 未声明 | Unihan 部首笔画可读版 | Unihan 派生 |
| [JuliaCJK/IDSGraphs.jl](https://github.com/JuliaCJK/IDSGraphs.jl) | MIT | IDS 图处理 | 结构实验候选 |
| [leechenhwa2/nlp-han-dicts](https://github.com/leechenhwa2/nlp-han-dicts) | BSD-2-Clause | 康熙/中华大字典 SQLite | 已 staging，交叉参考 |
| [kanripo/KR1j0048](https://github.com/kanripo/KR1j0048) | 未声明 | 御定康熙字典全文 | 已评估，文本见证 |
| [he426100/kangxi](https://github.com/he426100/kangxi) | 未声明 | 康熙字典 SQLite | 许可证/质量阻塞，暂缓 |
| [Radically/radically](https://github.com/Radically/radically) | GPL-2.0 | 部件检索 | 结构候选 |
| [mreichhoff/kanji-linear-algebra](https://github.com/mreichhoff/kanji-linear-algebra) | 未声明 | 基于 cjkvi-ids 的线性代数 | 方法参考 |
| [fighting41love/funNLP](https://github.com/fighting41love/funNLP) | 未声明 | 拆字词典等 NLP 数据合集 | 交叉参考候选 |

## 四、补位映射与缺口

| CNBE 字段 | 目标权威 | 当前可用 | 缺口 |
|---|---|---|---|
| 部首 | GF0011-2009/2022 | 201 主部首表（公开转载）、GF0012 逐字归部（扫描件） | 2022 修订国际编码未公开；GF0012 逐字表未电子化 |
| 部首逐字归部 | GF0012-2009 | 无机器可读正式表 | 20902 字表需扫描 + OCR + 人工复核 |
| 笔画 | GF0013/GF3002/GF0031 | Unihan `kTotalStrokes`、`stroke_db.csv` | 国标逐字笔画表未电子化；Unihan 不能冒充国标 |
| 笔顺 | GF3002/GF0031 | makemeahanzi 等开源数据 | 国标笔顺表未完成下载/电子化 |
| 结构/部件 | GF0014 | cjkvi-ids、hanzi_chaizi、hanziyin | GF0014 扫描件未电子化；开源 IDS 是交叉参考 |
| 编码 | GB 18030-2022 / Unicode | CNBE64 对齐实验已归档 | 全量编码表仍需标准全文系统核验 |
| 字表范围 | 通用规范汉字表 8105 | 官方 PDF（扫描）+ GitHub 转录 | 转录需人工核验 |

## 五、建议

1. **建立三层证据模型**：`NATIONAL_STANDARD_SCAN`（官方扫描件）→ `OCR_AND_HUMAN_REVIEW`（机器转录 + 专家核验）→ `CROSS_REFERENCE`（Unihan/IDS/词典）。任何未过第二层的数据标记 `REQUIRES_OFFICIAL_SOURCE`。
2. **GF0012 重建**：以官方 236 页扫描件为底，先只做 8105 范围内的逐字归部，双引擎 OCR + 人工复核后形成 `gf0012_8105_verified.json`；全量 20902 字随后推进。
3. **GF0011-2022 追踪**：继续盯教育部官方 PDF；拿到后优先抽取“部首名称 + 信息处理国际编码”，直接服务 CNBE64/GB18030 对齐。
4. **禁止混用体系**：Unihan `kRSUnicode` 是康熙 214 体系，不是 GF0011/GF0012；报告与代码中必须保留体系标签。
5. **外部仓库只作交叉参考**：尤其 `max32002/chinese_dictionary` 与 `he426100/kangxi` 许可证/质量未解决，不得作为正式锚定源。

## 产物

- `authoritative_sources/`：官方 PDF/HTML 下载与探测报告（大文件不入库，见 `.gitignore`）
- `authoritative_sources/supplement_catalog.json`：机器可读来源清单
- `../data/gf0011_201_radicals_full.json`：GF0011 完整版入库表（201 主部首 + 笔画分组 + 附形条目）
- `results/gf0011_docx_parsed.json`：完整版 docx 文字层解析
- `results/gf0011_wiki_template_parsed.json`：维基模板解析
- `results/gf0011_docx_vs_current.json`：docx 与现有表逐字段差异
- `fetch_official_sources.py` / `fetch_official_pdfs.py` / `fetch_remaining_standard_pdfs.py`：官方来源抓取与文本层探测
- `search_github_supplement_projects.py` / `fetch_github_candidate_metadata.py`：GitHub 补充项目检索
- `parse_gf0011_docx.py` / `parse_wiki_gf0011.py` / `ingest_gf0011_full.py`：GF0011 完整版解析与入库
