# P1 外部评审 · 评审人邀约信模板（中英文）

> 使用说明：复制对应语言版本，替换 `<...>` 占位符后发送。发送前请确认评审包 CSV 的获取方式（邮件附件 / 仓库路径）已写明。**请勿在邀约信中透露任何内部结论、标签或预期结果——这是盲审。**

---

## 中文版

**邮件主题：【评审邀请】汉字结构编码研究项目 CNBE-32 — 600 行盲审（约 3–5 小时）**

`<评审人姓名/称呼>` 老师，您好：

我是 CNBE-32（中文原生二进制编码）研究项目的维护者 `<你的名字>`。该项目尝试把汉字的部首、笔画、结构等形态信息编码进 32 位二进制值，全部数据以对齐国家语言文字规范（8105 通用规范汉字表、GF 0017-2013 等）为目标重建。项目主页：
https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding

目前项目进入**外部独立评审（P1）**阶段。这是论文/发布前的关键质量门禁：我们需要**未参与本项目**的独立评审人，对 600 条"汉字关系声明"逐行做盲审核验。想邀请您担任评审人（编号 `<REV_X>`）。

**评审内容**：600 行 CSV，三类各 200 行——部首归属、字形结构、笔画数。每行给出两个汉字和一条声明（如"两字同属部首一""候选字为左右结构""两字均为 10 画"），您只需依据我们指定的来源文件判断声明是否成立，勾选 positive / negative / exclude 并填 5 列。

**预计工作量**：每行约 20–40 秒，全卷 3–5 小时；**可分批提交**，单批行数不限。

**盲审纪律**：请不要查找项目内部的既有结论，也不要用项目编码反推答案；拿不准的行填 `exclude` 即可，排除本身就是有价值的审计信号。

**操作手册**：随附《P1 外部独立评审执行包》（[docs/review/P1_EXTERNAL_REVIEW_EXECUTION_KIT.md](./P1_EXTERNAL_REVIEW_EXECUTION_KIT.md)），内含填表规则、提交命名方式和常见问题。

如果您愿意参与，请回复确认，我会为您分配评审人编号并发送评审文件。若您时间有限，也欢迎只审 200 行（一个类别）或与他人合审。如蒙应允，项目将在公开报告与致谢中列明您的贡献（或按您意愿匿名）。

此致
敬礼

`<你的名字>` · CNBE-32 项目
`<日期>` · `<联系方式>`

---

## English version

**Subject: [Review Invitation] CNBE-32 Hanzi Structure Encoding — 600-row blinded review (~3–5 hrs)**

Dear `<Reviewer Name>`,

I am `<Your Name>`, maintainer of CNBE-32 (Chinese Native Binary Encoding), a research project that encodes Hanzi morphology — radical, stroke count, and structure type — into a compact 32-bit value, rebuilt around Chinese national language standards (the 8105 common standardized character table, GF 0017-2013, etc.). Project page:
https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding

The project has reached its **external independent review (P1)** gate — a quality checkpoint required before any benchmark publication. We are looking for reviewers **not involved in the project** to blindly verify 600 rows of Hanzi relation claims, and I would like to invite you as reviewer `<REV_X>`.

**The task**: a 600-row CSV with three claim types (200 rows each): shared radical, structure label, and stroke count. Each row gives two characters and one claim (e.g. "both characters belong to radical 一", "the candidate is left-right structured", "both have 10 strokes"). You check each claim against the cited source document and fill 5 columns (positive / negative / exclude plus confirmation and notes).

**Estimated effort**: 20–40 seconds per row, 3–5 hours total. **Partial submissions are welcome** — any batch size counts.

**Blinding**: please do not look up the project's internal conclusions or reverse-engineer answers from the encoding. When uncertain, mark `exclude`; exclusions are themselves valuable audit signals.

**Instructions**: see the *P1 External Review Execution Kit* ([docs/review/P1_EXTERNAL_REVIEW_EXECUTION_KIT.md](./P1_EXTERNAL_REVIEW_EXECUTION_KIT.md)) for fill-in rules, file naming, and FAQs.

If you are willing to help, just reply and I will assign your reviewer ID and send the packet. Reviewing a single 200-row category, or co-reviewing with a colleague, is equally welcome. Your contribution will be acknowledged in the public report (or anonymized if you prefer).

Best regards,

`<Your Name>` · CNBE-32 Project
`<Date>` · `<Contact>`
