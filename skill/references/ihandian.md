# 汉典籍网（ihandian）网页字典交叉参考

## 定位

`https://www.ihandian.com/` 是 CNBE 的网络字典交叉参考来源。它与辞书、ZDIC
和其他网络资料处于同一**审核辅助**层：可用于人工审核导航、字段比对和缺口发现，
不能作为国家标准、GF0017 直接计分依据、CNBE 自动编码来源或人工审核的替代品。

## 页面概述字段

以 `https://www.ihandian.com/zidian/zi-2b80a.html`（`𫠊`，`U+2B80A`）为已核对
示例，页面“字概述”按以下五组呈现：

1. 拼音、部首、笔画。
2. 结构、拆字结构。
3. 仓颉码、四角号码、郑码。
4. 统一字码、CJK、十进制、UTF-32、UTF-8。
5. 汉字表格信息。

## Agent 调用规则

1. 先固定字面、Unicode 码位和规范化状态，再构造单字 URL。
2. 只能调用 `scripts/extract_ihandian_character_reference.py` 处理一个明确字符；
   不做 97,686 行或其他全量网页抓取。
3. 输出必须写为独立、可审计的结构化参考记录，并标记
   `network_dictionary_cross_reference`。
4. 网页字段缺失、网页空白、网络失败或解析失败时记录为缺口；不得按视觉或模型记忆补齐。
5. ihandian 与 ZDIC、辞书资料只能帮助审核员比较；人工审核仍是本探索批次的项目基线。

## 已记录样本

- 结构化记录：`evidence/validation/ihandian/U_2B80A_IHANDIAN_REFERENCE.json`
- 审核摘要：`reports/IHANDIAN_U_2B80A_REFERENCE.md`
- 来源登记：`data/sources/ihandian-dictionary-web.json`
