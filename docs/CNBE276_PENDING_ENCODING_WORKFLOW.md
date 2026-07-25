# CNBE-32 8105 待编码 276 行受治理编码工作流方案

- 版本：v1.0 · 2026-07-25
- 状态：**方案，待所有者批准（G0）**；批准前不改动任何源表数据
- 对应 Roadmap 第 8 条；上接 v1.1 迁移（PR #50）与字段语义冻结 v1.1（WS-3）
- 清单锚定：[`evidence/8105/PENDING_276_ENCODING_INVENTORY.csv`](../evidence/8105/PENDING_276_ENCODING_INVENTORY.csv)，SHA-256 `39d7e3295d18d6d262d8049de3465b10a47c760e0358b913276c82920931debf`

## English abstract

This document defines the governed encoding workflow for the 276 rows marked
`needs_encoding=1` in the v1.1 repository database (21,178 rows). A local
dual-source triage reusing the WS-2 parsing logic stratifies the 276 rows into
five tiers: **T0** 1 row complete except the CNBE value itself (㬎 U+3B0E),
**T1** 124 rows with dual-source-agreed structure (baseline cjk-decomp vs
cjkvi-IDS) and dual-source-agreed strokes (GF stroke-order baseline vs Unihan
kTotalStrokes), **T2** 36 rows with agreed structure but conflicting stroke
counts, **T3** 111 rows with only a single structure source, and **T4** 4 rows
with conflicting structure sources. T1 becomes encodable after a second
independent radical source (programmatic ZDIC extraction) confirms the Unihan
kRSUnicode radical; T2/T3/T4 route to the unified expert-adjudication queue
together with the 348 rows hung by the v1.1 migration. Every batch runs under
the Agent invocation contract, stops on blockers, requires human review before
any source-table write, writes with idempotent apply/rollback tooling, and is
recorded in `migration_meta`. Nothing in this workflow may be labeled
`national_standard`; the highest reachable evidence level is
`standard_derived` (`cross_reference_dual`). Radicals are written in the Kangxi
numbering consistent with the current standard track; the GF 0011-2009
re-anchoring remains a separate migration pending the authoritative mapping
table (freeze §4 / adjudication item A1).

## 1. 对象与实证基线

仓库数据库 v1.1（21,178 行，`track` 列：standard 7,327 / provisional 275 /
legacy 13,576）中 `needs_encoding=1` 共 **276 行**：

| 子集 | 行数 | 库内现状 |
|---|---:|---|
| provisional | 275 | `cnbe/radix/radix_name/struct_type/struct_name` 全 NULL；`strokes`、`idx` 已在库（strokes 源自 8105 基线 GF 笔顺字段；provisional = 基线标 `REVIEW_REQUIRED` 的补录行） |
| standard | 1 | 㬎 U+3B0E：radix=72（日）、strokes=14、struct=上中下 已在库且基线证据 `COMPLETE`，仅 `cnbe` 为 NULL |

全量特征（276/276 本地核验）：

- Unicode 范围 U+3447 – U+2CE93，横跨基本区扩展 A 至扩展 B/F 平面；
- 笔画 4–23，**全部 ≤ 31**，5-bit 笔画字段无溢出，本批与 WS-6 编码协议问题无关；
- `idx` 全部满足 `(unicode − 0x4E00) mod 2048`（0 例外），编码时直接沿用库内值；
- 8105 范围成员资格由补录构造保证，无需重新判定。

## 2. 双源证据试演分层（2026-07-25，可复现）

试演复用 WS-2 `cross_validate.py` 的解析逻辑：`IDC_TO_STRUCT` 首 IDC→结构映射、
Unihan `kRSUnicode`/`kTotalStrokes` 解析；基线 `cjk_decomp` 字母码→结构映射由
8,105 基线中 6,831 条已知结构行**实证投票**生成（纯度表见附录 B）。

三条证据腿独立判定后交叉分层：

| 层 | 行数 | 判定 | 处置方向 |
|---|---:|---|---|
| **T0** | 1 | 库内字段已齐，仅缺 cnbe 值 | 直接计算 cnbe，单独人审确认 |
| **T1** | 124 | 结构双源一致 ∧ 笔画双源一致 | 部首补第二源确认 → 编码候选 |
| **T2** | 36 | 结构双源一致 ∧ 笔画双源**分歧** | 笔画先行裁决（A2 依赖），再回 T1 管道 |
| **T3** | 111 | 结构仅单源（cjkvi-IDS） | 补第二源（ZDIC 程序化抽取/辞海）；分歧或缺口 → 专家队列。其中 5 行同时笔画分歧 |
| **T4** | 4 | 结构双源**分歧**（㬚、𠙶、𪨶、𫔶，详见附录 C） | 直接进专家裁决队列 |

分腿汇总：

- **结构腿**：双 IDS 源一致 160 / 单源 111 / 分歧 4 / 库内已完成 1；
- **笔画腿**：基线 GF 笔顺 vs Unihan `kTotalStrokes` 一致 234 / 分歧 41 /
  库内已完成 1；分歧 41 行的库内 strokes 为基线单源值，**裁决前禁止编码**；
- **部首腿**：Unihan `kRSUnicode`（康熙口径）覆盖 276/276，但属**单一交叉参考源**；
  按 D2 双源纪律，须第二独立来源（ZDIC 程序化抽取，按技能硬规则用解析器而非
  模型解读）确认后方可入库，分歧/缺口行进专家队列。

关键实证发现（附录 B）：`cjk_decomp` 字母码仅 `a`（左右，纯度 99.5%，n=4,350）
与 `d`（上下，纯度 94.0%，n=1,675）可单源参考；`b/l/m/r/s/w` 纯度 42–68%，
**仅允许在双源一致模式下使用，禁止单源采信**。

## 3. 批次设计

执行顺序：T0 → T1 → T2 → T3 → T4（T4 不进编码管道，只登记队列）。

每批开工前按技能 Stage 0 声明运行契约，缺一即停：

```text
run_id                例：PENC276-T1-20260725-R1
operator_role         执行角色（Agent + 人审员）
input_scope           本批 row_id 区间 + 清单 CSV SHA-256
input_artifacts       基线 JSON / cjkvi_ids.txt / Unihan_IRGSources.txt 及其 SHA-256
unicode_gate          Unicode 身份校验方式（只读，不改写）
authority_order       national_standard > core_reference > network_cross_reference
allowed_outputs       候选包 / dry-run 计划 / 验证报告 / 人审包
forbidden_outputs     源表写入 / 发版 / national_standard 标注 / LLM 记忆生成
stop_conditions       Unicode 歧义 / 结构分歧 / 部首单源 / 笔画分歧 / 校验失败
verification_commands 验证器命令与测试清单
```

## 4. 单行处理流水线

对齐治理文档 13 门与技能 Stage 1–8，逐行执行：

1. **Unicode 身份**：库内值只读复核（char ↔ unicode ↔ idx 三者一致）；
2. **范围**：8105 成员（构造保证，记录来源）；
3. **标准证据 join**：基线 `evidence_status` / `evidence_issues` 原样存档；
4. **笔画**：基线 GF 笔顺值 vs Unihan `kTotalStrokes`；一致 → 沿用；分歧 → 挂起
   （T2），等待 A2（GF 0013 逐字笔画真值）或专家裁定，**不用模型猜**；
5. **结构**：双 IDS 源（基线 `cjk_decomp` 字母映射 + cjkvi-IDS 首 IDC）一致 →
   候选；单源 → 补 ZDIC/辞海第二源；分歧 → 挂起（T4）；合法值仅为冻结的
   13 个中文标签；
6. **分解记录**：`cjk_decomp` 原文与 cjkvi-IDS 原文双份存档（CNBE64/128 扩展
   证据，本批不入 32 位字段）；
7. **部首/偏旁分离**：`kRSUnicode` + ZDIC 程序化抽取双源一致 → 候选
   （康熙口径，附形归并留待 A1）；分歧/缺口 → 专家队列；
8. **独体字检查**：双 IDS 源均无 IDC 算子时按独体字流程核验；
9. **GF0017 评分**：仅对有证据项打分并记录来源状态；缺口保留
   `NOT_SCORABLE_SOURCE_GAP`，不折算成分数或标签；
10. **分级**：本批最高 `standard_derived`（证据级标注
    `cross_reference_dual:<源组合>`，沿用 D2 口径）；**禁止**标注
    `national_standard`；缺口行 `source_gap` / `unresolved`；
11. **阻断即停**：任一校验失败即停批，从 checkpoint 恢复；
12. **人审授权**：候选包 + 抽样人审通过后，所有者书面授权写源表；
13. **SQLite 写入**：单独授权步骤，幂等脚本 + 自动备份 + 事后校验。

## 5. 编码计算与入库校验

**CNBE 位段组装**（与规范一致）：`radix(8) | stroke(5) | struct(4) | idx(11) | ext(4)`。

- `struct_type` 用冻结中文轨编号（0 独体字 … 12 镶嵌），与 `struct_name` 严格一致；
- `idx` 沿用库内值（公式已验证 276/276）；`ext` 新行 = 0；
- 每行编码值必须通过 golden vectors 的 encode/decode round-trip；
- 笔画 ≤ 23，无 5-bit 溢出；将来遇 >31 画的字走 WS-6 协议，不在本批。

**入库校验器**（gate 项，任一失败即阻断）：

1. `struct_name ∈ 13 规范标签` 且 `struct_type` 冻结编号一致；
2. `strokes` 为 [1,31] 整数且双源一致记录存在；
3. `radix ∈ [1,214]`（康熙口径，与标准轨现状一致；GF 0011 换锚按冻结 §4
   待 A1 权威映射表后统一迁移，本批在迁移元数据中登记口径）；
4. `cnbe` 位段与 radix/strokes/struct_type/idx/ext 逐字段回算一致；
5. `needs_encoding: 1→0`；`track: provisional→standard`（仅限人审通过行）；
6. **不变量**：276 行以外的 20,902 行零改动；`unicode/char/idx` 不改写；
7. **幂等**：二次 `--apply` 计划 0 操作；`--rollback` 可完整恢复。

## 6. 人审与抽样

- T0：单行独立人审确认（字段已在库，核对 cnbe 回算值即可）；
- T1：确定性等距抽样 ≥ 10%（≥ 13 行，按 unicode 排序）进入人审包；
  人审包沿用 P1 评审包约定：EDITABLE CSV、评审列空白、UTF-8；
- T2/T3：证据补齐后回到 T1 同一抽样与人审管道，不另设捷径；
- 人审不通过的行进专家队列并记录原因码，不降级入库。

## 7. 授权点

| 门 | 内容 | 通过标准 |
|---|---|---|
| G0 | 本方案批准 | 所有者确认方案与清单锚定 |
| G1 | 批次 dry-run 报告 | 计划 JSONL + 验证器全绿 + 抽样人审记录 |
| G2 | 写源表授权 | 所有者明确书面授权（治理第 12 门） |
| G3 | 写入与事后校验 | 备份 + apply + 校验报告 + `migration_meta` v1.2 记录 + README/治理状态更新 |

发版、tag、GitHub release、PyPI 均为**独立授权事项**，不在本方案范围。

## 8. 与既有治理队列的统一

- **专家裁决统一队列**：v1.1 迁移挂起 348 行 + 本批 T2 36 行 + T3 分歧/缺口行 +
  T4 4 行，同一队列、同一裁决机制；全部待 A1（GF 0011 康熙214→201 映射表）、
  A2（GF 0013 笔画真值）、A3（拆字验证）学术输入，暂不求快、不降级；
- **与 P1 外审 / WS-4 的关系**：本批编码完成前不影响 P1 外审与 WS-4 基准的
  阻断状态；完成后可从 T1 抽样加入下一轮外部评审包，保持同一评审纪律；
- **与 WS-6 的关系**：本批无 >31 画字，不触碰编码协议问题。

## 9. 产出物清单

| 产物 | 状态 |
|---|---|
| `evidence/8105/PENDING_276_ENCODING_INVENTORY.csv`（276 行分层清单，SHA-256 锚定） | 本 PR 交付 |
| 每批候选包 JSONL + dry-run 计划 + 验证报告 + 人审包 | 各批 G1 时交付 |
| 写入后迁移报告 + `migration_meta` v1.2 记录 + README 状态更新 | 各批 G3 时交付 |
| 输入 manifest（基线 JSON、cjkvi_ids.txt、Unihan_IRGSources.txt 的 SHA-256） | 首批 G1 时交付 |

## 10. 明确禁止（摘自治理文档与技能硬规则，重申适用）

- 禁止用 LLM 记忆或视觉直觉生成部首、结构、笔画；
- 禁止单源采信低纯度 `cjk_decomp` 字母码（b/l/m/r/s/w）；
- 禁止把 `cross_reference` 证据标注为 `national_standard`；
- 禁止未经所有者授权写源表、重建数据库、发版；
- 禁止改动 276 行以外的任何数据行；
- 禁止因 CNBE32 位宽压力削弱汉字证据（冻结 §3：数据层存真值）。

## 附录 A — 复现方法

分层试演脚本逻辑：解析基线 `characters[char].cjk_decomp` 首字母 → 由 6,831 条
已知结构行投票生成字母映射；解析 `cjkvi_ids.txt` 首 IDC → `IDC_TO_STRUCT`
（与 WS-2 `cross_validate.py` 同一映射表）；解析 `Unihan_IRGSources.txt` 的
`kRSUnicode`/`kTotalStrokes`（与 WS-2 同一解析函数）；276 行清单取自 v1.1 库
`needs_encoding=1`。第三方文件获取方式见 `third_party/README.md`（不入库，
脚本可复现拉取）。清单 CSV 的 SHA-256 见文首，任何重跑必须先核对锚定值。

## 附录 B — cjk_decomp 字母码纯度表（8,105 基线实证）

| 字母 | 多数结构 | 纯度 | n | 处置 |
|---|---|---:|---:|---|
| a | 左右 | 0.995 | 4,350 | 可作双源之一 |
| d | 上下 | 0.940 | 1,675 | 可作双源之一 |
| w | 镶嵌 | 0.652 | 115 | 仅双源一致模式 |
| l | 镶嵌 | 0.682 | 22 | 仅双源一致模式 |
| b | 镶嵌 | 0.556 | 9 | 仅双源一致模式 |
| m | 上下 | 0.500 | 8 | 仅双源一致模式 |
| r | 上下 | 0.431 | 51 | 仅双源一致模式 |
| s | 左上包 | 0.426 | 631 | 仅双源一致模式 |

## 附录 C — T4 结构双源分歧四行详情

| 字 | Unicode | cjk_decomp 源 | cjkvi-IDS 源 |
|---|---|---|---|
| 㬚 | U+3B1A | 左右 | 左中右 |
| 𠙶 | U+20676 | 左上包 | 下三包 |
| 𪨶 | U+2AA36 | 上下 | 上中下 |
| 𫔶 | U+2B536 | 左上包 | 上三包 |

四行连同笔画分歧 41 行、结构单源 111 行，均不在本批编码范围，等待专家裁决
或第二证据源补齐后回流。
