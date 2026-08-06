# CNBE64 多模态语义研究基座设计（2026-08-07）

## 三层定位

| 层 | 编码 | 作用 | 边界 |
|---|---|---|---|
| 身份层 | Unicode | 全局唯一字符标识 | 唯一主键，不进入 CNBE 位域语义 |
| 结构层 | CNBE32 | 部首/笔画/结构/索引/扩展 | 紧凑结构指纹，不承载语义内容 |
| 对齐/档案层 | CNBE64 | CNBE32 + GB18030 指针 + 版本/状态 | 交换与档案载体，不是语义本身 |

Unicode 是 21 bit 全局身份空间；CNBE64 的 GB18030 槽位是 21 bit 交换指针空间，实测 97,686 字最大指针 329,207（19 bit），可完整覆盖。两者不冲突：Unicode 负责“是什么字”，CNBE64 负责“结构指纹 + 与 GB18030 对齐”，语义证据放在独立证据表。

## CNBE64 语义研究基座

```text
Unicode（主键）
  -> CNBE64（结构 + GB18030 对齐 + 状态）
  -> 字形图像证据（字体渲染 / 古籍 OCR 裁剪 / 历史字形）
  -> 多模态嵌入（视觉字形编码 + 文本语义编码）
  -> 字义/读音/变体证据（Unihan、词典、语料）
  -> 下游任务（OCR 纠错 / 变体归一 / 形近消歧 / 字形演化 / 语义聚类）
```

64 位成为“研究基石”的方式不是把语义塞进位域，而是让 CNBE64 成为稳定、定长、可随机访问的**关联键**：

- 同一个 Unicode 下的 CNBE64 连接字形图、OCR 输出、语义记录、RISC-V skill table；
- 低 32 位保留 CNBE32，RISC-V/硬件与现有实验不失效；
- 高 32 位提供 GB18030 对齐和映射状态，作为跨系统交换锚点；
- 多模态模型输出进入证据表，带模型版本、置信度、来源，不直接改写 CNBE 位域。

## 实测语义证据覆盖率

对全量 97,686 字（Unihan 17.0.0 交叉参考）：

| 字段 | 覆盖 | 比例 |
|---|---:|---:|
| kDefinition | 22,988 | 0.2353 |
| kMandarin | 44,346 | 0.4540 |
| kHanyuPinyin | 34,130 | 0.3494 |
| kCantonese | 29,915 | 0.3062 |
| 任一语义（释义/读音） | 46,857 | 0.4797 |
| 任一变体 | 15,398 | 0.1576 |
| kRSUnicode / kTotalStrokes | 97,686 | 1.0000 |

约 48% 的字已有基础语义交叉参考；另一半需要词典、语料与多模态模型补齐。因此“图像 + 多模态增强”不是可选项，而是全量语义研究的必要补充。

## 数据表建议

### cnbe64_char

```text
unicode (PK)
char
cnbe32
cnbe64
gb18030_pointer
gb18030_status  # MAPPED / CONFLICT / MISSING / UNKNOWN
version
```

### cnbe64_glyph_image

```text
image_id (PK)
unicode (FK)
source          # font / ocr_crop / historical / manuscript
page / bbox
image_sha256
ocr_text
ocr_confidence
model_version
```

### cnbe64_semantic

```text
unicode (FK)
field           # definition / mandarin / hanyu_pinyin / variant / gloss
value
source          # unihan / dictionary / multimodal_model / human_review
confidence
embedding       # 定长向量，记录模型与维度
model_version
```

## 多模态管线

1. 输入：古籍页面、字体渲染、历史字形图；
2. OCR：PaddleOCR-VL-1.6 / DeepSeek OCR 输出文本与版面框；
3. CNBE 定位：OCR 候选 -> CNBE64 结构字段重排；
4. 视觉校验：字形裁剪 -> 视觉模型 -> 与候选结构字段一致性打分；
5. 语义增强：释义/读音/变体 -> 文本嵌入；
6. 证据入库：图像哈希、OCR 原文、模型版本、置信度全部保留；
7. 可视化：按 Unicode/CNBE64 聚合展示字形图、结构、GB18030、语义证据。

## 边界

- 多模态模型输出是交叉参考证据，不是国标语义权威；
- 6,625 个 GB18030 重复指针行必须保留 Unicode 主键并单独裁决；
- 语义缺失不能用模型“补写”冒充来源，必须带来源与置信度；
- CNBE128 继续保留给完整笔画序、拆字树、历史字形全证据；
- CNBE64 是研究关联键，不是语义内容本身。

## 下一步

1. 按 `cnbe64_char` 表生成 97,686 行 CNBE64 候选（探针已完成）；
2. 建立字形图像清单：字体渲染全覆盖 + 古籍 OCR 裁剪；
3. 300 字多模态试点：OCR -> 视觉校验 -> 语义补全；
4. 对 6,625 冲突指针与语义缺口建立裁决队列；
5. 在治理授权后实现 CNBE64 SDK、golden vectors 与可视化 Studio。
