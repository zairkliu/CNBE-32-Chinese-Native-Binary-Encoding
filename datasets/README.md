# CNBE-32 汉字结构标注数据集（8105 范围）

> 状态：草稿（数据集卡片）｜ 锚定发布检查点：`v1.0.4`
> 生成方式：`scripts/export_dataset.py` 从 `data/cnbe32.db` 导出，产物哈希见 `dataset_manifest.json`

## 这是什么

CNBE-32 项目的汉字结构标注数据，ML 可读格式（JSONL；pandas/pyarrow 可用时附 Parquet）。
每行一个汉字，包含：Unicode 码位、部首字段、笔画数、结构类型、字形索引、扩展位、
CNBE-32 编码值、**证据等级**与审核状态。

## 证据等级（evidence_tier）

| 取值 | 含义 |
|---|---|
| `national_standard` | 有国家标准证据 |
| `standard_derived` | 由国家标准证据推导 |
| `agent_standard` | Agent 受控生成、按项目规则产出 |
| `source_gap` | 来源缺口 |
| `unresolved` | 未决 / 来源未携带等级 |

`tier_source` 字段标注等级来源：`source_column`（源数据自带）或
`default_no_source`（源数据未携带，按诚实默认置为 `unresolved`）。
**本数据集不伪造证据等级。**

## 覆盖声明（措辞纪律）

- 本数据集"以国家语言文字规范为对齐目标"，**不是**"符合国家标准"的产品；
- 8105 人审结构基线已完成（8105/8105）；运行时数据当前覆盖 7310/8105（90.2%），
  276 行缺失、795 行强制批准待修补——两轨并行，引用时请注明所引轨道；
- 结构分类标签与 GF 0017-2013 §3.12 一一对应；
- 部首字段**尚未锚定** GF 0011-2009《汉字部首表》，语义冻结前请勿将部首编号
  用于跨项目交换；
- 字符身份由 Unicode 码位承担；本数据集不替代 Unicode 或 GB 18030。

完整对齐状态见 `docs/CNBE_STANDARDS_COMPLIANCE_STATEMENT.md`。

## 许可

MulanPSL-2.0（与仓库一致）
