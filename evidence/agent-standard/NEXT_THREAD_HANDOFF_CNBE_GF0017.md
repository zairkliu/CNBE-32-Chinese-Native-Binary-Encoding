# CNBE Next Thread Handoff: GF0017 Batch Audit And Encoding Preparation

你是仓库管理员。你的任务不是直接大规模改编码，而是继续推动 CNBE 项目进入“可复现、可截断、可恢复”的规范化批量编码阶段。

## Current Role Contract

- 你是仓库管理员。
- 对方或执行端是仓库执行员。
- 仓库管理员负责制定标准、审核输出、决定是否进入下一阶段。
- 仓库执行员负责按标准执行，不得擅自合并、推送、发布或跳过审核。

每次对用户输出时，开头必须写：

```text
我是仓库管理员。
```

## Current Repository

Active repo:

```text
/Users/liuzhaoqi/Documents/Codex/2026-07-09/wan/CNBE-32-Chinese-Native-Binary-Encoding
```

Research knowledge base:

```text
/Users/liuzhaoqi/Documents/cnbe-research
```

Important local skill just created:

```text
/Users/liuzhaoqi/.codex/skills/cnbe-gf0017-batch-audit
```

Invoke it in the new thread when auditing batch encoding:

```text
Use $cnbe-gf0017-batch-audit
```

## What Was Completed

1. Built GF0017 50-point normativity scoring model.
2. Mapped GF0017 section 5.1 to CNBE encoding work.
3. Generated per-character 8105 scoring report.
4. Created a reusable batch-audit skill.
5. Fixed the process rule: Unicode alignment is always the first step.
6. Fixed batch safety rule: if a blocker appears, stop current work, write checkpoint, write blocker report, and resume only after full audit.

## Key Outputs

Scoring model:

```text
evidence/gf0017/gf0017_cnbe50_scoring_model.json
evidence/gf0017/GF0017_CNBE50_SCORING_MODEL.md
evidence/gf0017/GF0017_NORMATIVE_SCORING_SOURCE_MAP.md
```

Per-character scoring report:

```text
scripts/score_cnbe8105_gf0017_normativity.py
evidence/gf0017/cnbe8105_gf0017_normativity_scores.json
evidence/gf0017/CNBE8105_GF0017_NORMATIVITY_SCORE_REPORT.md
tests/test_cnbe8105_gf0017_normativity.py
```

Existing supporting reports:

```text
evidence/8105/cnbe8105_standard_baseline.json
evidence/8105/cnbe8105_current_cnbe_snapshot.json
evidence/8105/cnbe8105_encoding_comparison.json
evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md
evidence/8105/cnbe8105_auto_fix_candidates.json
evidence/8105/CNBE8105_AUTO_FIX_CANDIDATES.md
evidence/8105/cnbe8105_radical_code_map.json
evidence/8105/CNBE8105_RADICAL_CODE_MAP.md
evidence/8105/cnbe8105_dry_run_patch.json
evidence/8105/CNBE8105_DRY_RUN_PATCH.md
```

## Validation Results

The following passed:

```bash
python3 scripts/score_cnbe8105_gf0017_normativity.py
python3 scripts/validate_format_integrity.py
python3 -m pytest tests/test_cnbe8105_encoding_comparison.py tests/test_cnbe8105_auto_fix_candidates.py tests/test_cnbe8105_radical_code_map.py tests/test_cnbe8105_dry_run_patch.py tests/test_cnbe8105_gf0017_normativity.py
```

Result:

```text
18 passed
FORMAT INTEGRITY PASS
```

GF0017 score summary:

```text
Rows scored: 8105
Average score: 44.4524 / 50
Minimum score: 33 / 50
Maximum score: 49 / 50
CNBE32_FIELD_REPAIR_CANDIDATE: 6314
EVIDENCE_GAP: 1244
HUMAN_REVIEW_REQUIRED: 292
ADD_OR_EXCLUDE_CHARACTER: 276
```

Important caveat:

```text
character_set_coverage and stroke_shape retain SOURCE_GAP labels because standalone local source files for GB2312, 现代汉语通用字表, and 印刷通用汉字字形表 have not been confirmed.
```

## Current Git Status Warning

Worktree contains many untracked reports/scripts/tests and one modified file:

```text
M scripts/validate_format_integrity.py
?? reports/...
?? scripts/audit_cnbe8105_encoding_comparison.py
?? scripts/build_cnbe8105_auto_fix_candidates.py
?? scripts/build_cnbe8105_radical_code_map.py
?? scripts/build_cnbe8105_dry_run_patch.py
?? scripts/score_cnbe8105_gf0017_normativity.py
?? tests/test_cnbe8105_*.py
```

Do not push or commit unless user explicitly authorizes.

## Next Suggested Step

The next professional step is:

```text
Build a checkpointed batch-audit runner that uses $cnbe-gf0017-batch-audit rules.
```

Recommended implementation:

1. Create a read-only batch runner:

```text
scripts/run_cnbe_gf0017_batch_audit.py
```

2. Inputs:

```text
--scores evidence/gf0017/cnbe8105_gf0017_normativity_scores.json
--batch-size 100
--start-offset 0
--checkpoint reports/cnbe_gf0017_batch_checkpoint.json
--output reports/cnbe_gf0017_batch_audit_run.json
--markdown reports/CNBE_GF0017_BATCH_AUDIT_RUN.md
```

3. Behavior:

- Read existing score JSON.
- Process rows in deterministic standard-rank order.
- Validate Unicode first for every row.
- Stop immediately on blocker.
- Write checkpoint:
  - `last_verified_offset`
  - `blocker_offset`
  - `blocker_char`
  - `blocker_unicode`
  - `failed_gate`
  - `resume_from`
- Do not rewrite CNBE source data.

4. Tests:

```text
tests/test_cnbe_gf0017_batch_audit_runner.py
```

Test cases:

- Unicode mismatch causes blocker.
- Source gap causes non-final status.
- Evidence gap stops or routes to review depending mode.
- Resume starts from last verified offset + 1.
- Script is read-only.

## New Thread Opening Prompt

Paste this into the new Codex thread:

```text
我是仓库管理员。请继续 CNBE 项目。先阅读这个交接文件：

/Users/liuzhaoqi/Documents/Codex/2026-07-09/wan/CNBE-32-Chinese-Native-Binary-Encoding/evidence/agent-standard/NEXT_THREAD_HANDOFF_CNBE_GF0017.md

然后使用 $cnbe-gf0017-batch-audit，给出下一步执行计划。不要提交、不要推送、不要改编码数据库。下一步优先设计并实现只读 checkpointed batch-audit runner，用 GF0017 50 分评分报告作为输入，遇到 blocker 必须截断并写 checkpoint，全部审核后才能从断点继续。所有编码规则第一步必须先完成 Unicode 对齐与兼容检查。
```
