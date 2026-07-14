# Hanzi Standard Terms

This report records the current learned term model. It is a preparation artifact, not a mapping proposal.

## 笔画 (`stroke`)

Definition: 构成汉字字形的最小连续书写单位。

Learning note: 笔画是字形书写的连续单位；CNBE 审核时必须与笔形、笔顺分开记录。

Forbidden use: 不得把 CNBE 压缩 stroke 字段等同于完整实际笔画数。

Evidence domain: `stroke_count_order_and_shape`

Primary sources:

- `source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md`
- `source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.md`

Supporting sources:

- `knowledge/stroke_order_8105.json`
- `knowledge/stroke_order_8105_clean.json`

## 笔形 (`stroke_shape`)

Definition: 笔画的形态类别及变体，例如横、竖、撇、点、折及附属笔形。

Learning note: 笔形是笔画形态类别；折笔规范负责处理折类笔形及其变体。

Forbidden use: 不得用笔形类别替代笔画数或笔顺序列。

Evidence domain: `stroke_count_order_and_shape`

Primary sources:

- `source/07-折笔规范/GB 13000.1 字符集汉字折笔规范.md`
- `source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md`

Supporting sources:

- `knowledge/ocr/ocr_fold_stroke.json`

## 笔顺 (`stroke_order`)

Definition: 书写汉字时笔画出现的先后顺序。

Learning note: 笔顺是笔画出现的先后顺序；可用数字序列记录。

Forbidden use: 不得把字序、Unicode 顺序或 Excel 行号当作笔顺。

Evidence domain: `stroke_count_order_and_shape`

Primary sources:

- `source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md`

Supporting sources:

- `knowledge/stroke_order_8105.json`
- `knowledge/stroke_order_8105_clean.json`
- `knowledge/ocr/ocr_stroke_order.json`

## 汉字部件 (`hanzi_component`)

Definition: 由笔画组成、具有组配汉字功能的构字单位。

Learning note: 汉字部件是构字单位，必须通过部件规范或审核过的拆分来源确认。

Forbidden use: 不得用 AI 视觉直觉直接生成部件。

Evidence domain: `component_inventory`

Primary sources:

- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`
- `source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md`

Supporting sources:

- `knowledge/component_db.json`
- `knowledge/decomp_rules.json`

## 成字部件 (`character_component`)

Definition: 能够独立成字的汉字部件。

Learning note: 成字部件可以独立成字，仍需在具体拆分层级中确认其部件角色。

Forbidden use: 不得因为部件能成字就自动等同为部首。

Evidence domain: `component_inventory`

Primary sources:

- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`

Supporting sources:

- `knowledge/component_db.json`
- `knowledge/knowledge_base_v2.json`

## 非成字部件 (`non_character_component`)

Definition: 不能独立成字但参与构字的汉字部件。

Learning note: 非成字部件不能独立成字，但可参与构字。

Forbidden use: 不得把非成字部件误登记为独立汉字。

Evidence domain: `component_inventory`

Primary sources:

- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`

Supporting sources:

- `knowledge/component_db.json`
- `knowledge/knowledge_base_v2.json`

## 基础部件 (`basic_component`)

Definition: 在选定规范体系下不再继续拆分的基础构字单位。

Learning note: 基础部件是在选定规范体系中不再继续拆分的构字单位。

Forbidden use: 不得无限细拆到笔画后仍称为部件规范结果。

Evidence domain: `component_inventory`

Primary sources:

- `source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md`

Supporting sources:

- `knowledge/component_db.json`

## 部首 (`radical`)

Definition: 用于检字、归类或索引的类首部件，必须说明采用的部首系统。

Learning note: 部首是检字和归类系统，必须说明采用现代部首表、康熙或 Unicode 系统。

Forbidden use: 不得混用现代部首、康熙部首和 Unicode radical-stroke。

Evidence domain: `radical_classification`

Primary sources:

- `source/02-汉字部首表/GG 0011-2009 汉字部首表.md`

Supporting sources:

- `knowledge/kangxi_radicals.json`
- `knowledge/unicode_rsindex.json`
- `source/15-Unicode-RSIndex/RSIndex.md`

## 偏旁 (`side_component`)

Definition: 传统分析中位于汉字某一方位、参与构字或表义表音的部件概念。

Learning note: 偏旁是传统构字分析概念，可用于解释部件位置和功能。

Forbidden use: 不得用偏旁泛称覆盖正式部件和部首字段。

Evidence domain: `component_inventory`

Primary sources:

- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`

Supporting sources:

- `knowledge/component_db.json`
- `knowledge/yuanliu_chars.json`

## 字形 (`glyph_form`)

Definition: 汉字的规范视觉形体、印刷形体或字形表现。

Learning note: 字形是方块汉字的规范视觉形体，来源应与字表或字形规范关联。

Forbidden use: 不得把字源语义说明当作字形规范。

Evidence domain: `single_component_and_structure`

Primary sources:

- `source/01-通用规范汉字表/通用规范汉字表(8105).md`
- `source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md`

Supporting sources:

- `source/01-通用规范汉字表/通用规范汉字表(8105)_images`
- `knowledge/structured/base_character_data.json`

## 独体字 (`single_component_character`)

Definition: 在对应规范下被视为不能拆分为两个及以上部件的汉字。

Learning note: 独体字是不再拆分为两个及以上部件的汉字，需要独体字规范支持。

Forbidden use: 不得因为笔画少就自动判定为独体字。

Evidence domain: `single_component_and_structure`

Primary sources:

- `source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md`

Supporting sources:

- `knowledge/decomp_rules.json`
- `knowledge/knowledge_base_v2.json`

## 汉字结构 (`hanzi_structure`)

Definition: 汉字内部部件之间的空间组合关系或结构类型。

Learning note: 结构只能落入十二类规范结构，或单独标为独体字。

Forbidden use: 不得写入品字形、三叠结构、会意结构等非规范结构字段。

Evidence domain: `single_component_and_structure`

Primary sources:

- `source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md`
- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`

Supporting sources:

- `knowledge/yuanliu_chars.json`
- `knowledge/structured/cnbe_character_knowledge.json`

## 汉字拆分方法 (`decomposition_method`)

Definition: 将汉字按规范、IDS 或审阅规则拆分为部件序列和结构关系的方法。

Learning note: 拆分方法必须记录层级、部件序列、结构关系和来源。

Forbidden use: 不得只给出语义解释而没有结构和部件证据。

Evidence domain: `component_inventory`

Primary sources:

- `source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md`
- `source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md`

Supporting sources:

- `knowledge/decomp_rules.json`
- `decomp-data/dictionary.json`
- `cjk-decomp/cjk-decomp.txt`

