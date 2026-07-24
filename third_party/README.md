# third_party/ — 交叉参考源（不入库说明）

本目录记录 WS-2 交叉验证使用的第三方开源参考源。**这些文件不提交进仓库**：
体积大（合计约 24 MB）、受各自许可证约束、且属于"可复现拉取"的外部证据，
不是 CNBE-32 的一手数据。任何人可用 `scripts/cross_validate.py` 按下述来源
重新拉取并复现 `reports/8105_CROSS_VALIDATION.md` 与 `data/review_queue.jsonl`。

## 证据等级声明

以下来源均为**交叉参考源（cross-reference）**，不是国家标准。
与 CNBE 记录分歧时，含义是"该行需要专家裁决"，而不是"CNBE 错误"。
国家标准锚定（GF 0011 / GF 0013 等）走治理流程（`docs/CNBE8105_ENCODING_GOVERNANCE.md`）。

## 来源清单

### 1. cjkvi-ids（CHISE IDS Database）

- 用途：汉字 IDS 分解，用于**结构**比对。
- 上游仓库：<https://github.com/cjkvi/cjkvi-ids>（master 分支 `ids.txt`）
- 本次使用文件：`cjkvi_ids.txt`，2,161,631 字节（2026-07-24 拉取）
- 拉取方式（镜像更稳定）：
  `curl -L https://cdn.jsdelivr.net/gh/cjkvi/cjkvi-ids@master/ids.txt -o cjkvi_ids.txt`
- 许可证：见上游仓库（GNU GPLv2）。本仓库不复制其文件，仅引用比对结果。
- 语义注意：CHISE IDS "凡可拆皆拆"，与 GF 0013"独体字只拆笔画"是**约定差异**，
  脚本将"CNBE 独体字 ↔ IDS 可拆"归类为 `convention_difference`，不计入实质分歧。

### 2. Unihan 17.0.0（Unicode.org）

- 用途：`kRSUnicode`（康熙 214 部首 + 部外笔画）与 `kTotalStrokes`，用于**部首 / 笔画**比对。
- 上游：<https://www.unicode.org/Public/17.0.0/ucd/Unihan.zip>
  本次仅使用其中的 `Unihan_IRGSources.txt`（13,352,717 字节）。
- 语义注意：`kRSUnicode` 是**康熙 214 部首体系**，不是 GF 0011-2009 的 201 部首。
  因此 WS-2 的部首一致率验证的是 Unicode/康熙传统，**不能**作为 GF 0011 锚定证据；
  GF 0011 锚定属于 WS-3 工作流。

### 3. 8105 范围文件（项目内生成）

- 用途：限定交叉验证范围到《通用规范汉字表》8105 字。
- 生成方式：从仓库内 `evidence/8105/cnbe8105_standard_baseline.json` 的字表提取，
  每行一字（`scope_8105.txt`，40,721 字节）。该基线文件已在仓库内，无需外部拉取。

## 复现命令

```bash
# 8105 范围内验证（入库报告对应的运行方式）
python scripts/cross_validate.py \
    --db data/cnbe32.db \
    --ids third_party/cjkvi_ids.txt \
    --unihan-irgsources third_party/Unihan_IRGSources.txt \
    --scope-file third_party/scope_8105.txt \
    --out-report reports/8105_CROSS_VALIDATION.md \
    --out-queue data/review_queue.jsonl

# 全量 20,902 行对照（背景数据，队列不入库）
python scripts/cross_validate.py \
    --db data/cnbe32.db \
    --ids third_party/cjkvi_ids.txt \
    --unihan-irgsources third_party/Unihan_IRGSources.txt
```
