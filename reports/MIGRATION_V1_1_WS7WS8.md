# v1.1 迁移报告：WS-7 可执行子集 + WS-8 遗产轨隔离

- 日期：2026-07-25
- 依据：PDR_PHASE2（已裁决）D2（双源一致先行修复，证据等级如实标注）、
  D3（遗产轨只隔离不重标）；WS-3 冻结规范 F1–F5
- 脚本：`scripts/migrate_v1_1.py` v1.0.0（默认 dry-run；`--apply` 先备份；
  `--rollback` 恢复；幂等）
- **治理状态：仓库内 `data/cnbe32.db` 尚未被修改。** 本 PR 只提交脚本、
  计划与验证证据；对源表的实际迁移需所有者明确批准后在治理流程内执行。

## 1. 双源配置（每个字段两个独立交叉参考源）

| 字段 | 源 1 | 源 2 | 裁决规则 |
|---|---|---|---|
| strokes | 8105 基线 `stroke_count`（GF 笔顺来源构建） | Unihan `kTotalStrokes` | 双源一致且与库不同 → 修；双源不一致 → 挂起 |
| radix | 8105 基线 `radix`（康熙口径） | Unihan `kRSUnicode`（康熙口径） | 同上；GF 0011 换锚仍待权威映射表 |
| structure | 8105 基线 `structure`（13 类） | cjkvi-ids 首 IDC 映射 | 同上 |

所有修复行的证据等级标注为 `cross_reference_dual:<源>`——**不是国家标准**，
标准文本到手后全量复核（D2 裁决记录）。

## 2. Dry-run 计划（8,105 字范围）

| 操作 | 行数 | 说明 |
|---|---|---|
| update:strokes | **503** | 含 strokes=31 系统性错值的可双源确认部分 |
| update:structure | **111** | 含英文/triangle 标签的可双源确认部分（同时按冻结规范修正 struct_type 双编号） |
| update:radix | **6** | 库的康熙部首与基线高度同源，WS-2 的 754 行"分歧"绝大多数被证实为基线与 Unihan 的归部约定差异，库值正确 |
| insert（可选 `--with-insertions`） | **276** | 8105 缺字从基线补录；`cnbe=NULL` + `needs_encoding=1`，编码为独立门禁步骤 |
| **合计计划行** | **896** | |

**挂起（不猜）348 行**：structure 双源分歧 262 + 基线无结构值 35 + radical 双源分歧 51。
其中 37 行 P1 triangle 仅 1 行获双源确认——其余留待专家裁决，符合"禁止批量改名"纪律。

## 3. 副本 apply 验证（非仓库库文件）

- 更新 620 行 + 插入 276 行，总行数 20,902 → 21,178
- track 分布：**standard 7,327 / legacy 13,576 / provisional 275**
  （provisional = 补录但基线标 REVIEW_REQUIRED 的行，与遗产轨区分）
- 幂等性：二次 `--apply` 计划 0 操作 ✅
- rollback：恢复至 20,902 行原始 schema ✅
- 一致性：standard 轨 `struct_type↔struct_name` 不匹配 = **0**（双编号问题在标准轨清零）✅
- 抽检：乜 strokes 31→2（双源确认）；丧 维持 8 画/24 部/上下 ✅

## 4. WS-8 导出隔离

`scripts/export_dataset.py` 新增 `--track {standard,provisional,legacy}` 过滤
（不传则保持 v1.0 全量行为）；track 列进入导出记录与 manifest。
实测：standard 导出 7,327 行；全量 21,178 行；原 3 个导出测试全部通过。

## 5. 迁移后 8105 标准轨画像（apply 后）

- 标准轨 7,327 行：结构 13 类标签 100% 规范、struct_type 单编号、
  双源确认笔画/部首
- 待专家：348 行挂起 + 275 行 provisional 补全 + 276 行编码补齐
- 遗产轨 13,576 行：内容零改动，仅打标隔离

## 6. 复现

```bash
# dry-run（默认，不写库）
python scripts/migrate_v1_1.py --db data/cnbe32.db \
    --baseline evidence/8105/cnbe8105_standard_baseline.json \
    --ids third_party/cjkvi_ids.txt \
    --unihan-irgsources third_party/Unihan_IRGSources.txt \
    --with-insertions --plan-out migration_plan.jsonl

# 执行（自动备份）；回滚
python scripts/migrate_v1_1.py ... --apply
python scripts/migrate_v1_1.py --rollback data/cnbe32.backup-<ts>.db
```
