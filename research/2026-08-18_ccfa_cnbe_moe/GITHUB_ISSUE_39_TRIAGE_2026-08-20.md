# Issue #39 字段级缺陷处置记录

## 结论

Issue #39 是 v1.1 字段语义冻结（PDR WS-3）的直接输入，四项缺陷全部实证成立，不阻塞 WS-1 数据集发布，但其中结构标签问题触及治理红线，建议单独排期。

## 四项缺陷与处置

### 1. 结构标签超集

现状：`struct_name` 共 26 个 distinct 取值，既有中英混用，也有未批准的 `triangle`。

处置：统一为单一语言标签集，建议与 GF 0017-2013 §3.12 对齐；`triangle` 按治理流程提交标准证据说明后决定并入或新增。

### 2. 笔画数截断

现状：`MAX(strokes)=31`，`龘` 等 48 画字被记为 31。

处置：导出层先标记 `stroke_count_capped=true`；v1.1 冻结溢出规则，真实笔画进入 CNBE64 扩展层。

### 3. 字形索引耗尽

现状：`MAX(idx)=2047`，20,902 行共享 2,048 槽，碰撞语义无文档。

处置：作为最高优先级，先补 8105 范围无碰撞测试，再冻结寻址协议。

### 4. 部首超集

现状：`COUNT(DISTINCT radix)=214`，超出 GF 0011-2009 的 201 主部首 13 个。

处置：产出 `radix ↔ GF 0011 部首` 映射表，对 13 个超集编号逐一裁定归属。

## 复现命令

```bash
python scripts/export_dataset.py --db data/cnbe32.db --out datasets/8105
sqlite3 data/cnbe32.db "SELECT MAX(strokes), MAX(idx), COUNT(DISTINCT radix) FROM cnbe32"
sqlite3 data/cnbe32.db "SELECT struct_name, COUNT(*) FROM cnbe32 GROUP BY struct_name ORDER BY 2 DESC"
```

## 状态

- 已写入项目维护总报告 `GITHUB_REPOSITORY_MAINTENANCE_2026-08-20.md`。
- Issue 保持 open，等待 WS-3 排期和修复分支。
