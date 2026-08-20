# GitHub 仓库维护总报告 2026-08-20

## 结论

- 远端分支：55 个收敛为 1 个（仅 `main`），开放 PR 为 0。
- 主分支当前头：`ed55136`。
- CI 基线已修复：pytest、ruff、format、build、release 校验在三个 Python 版本上通过。
- 新增的 wasm-deploy 已修正构建路径，并在等待最终绿。
- 开放 Issue 2 个：#35 Agent smoke test、#39 字段级数据缺陷。

## CI 修复记录

```text
655dc3d fix: harden reproducibility and format gates
3f7153f chore: store Wikipedia structure index with LFS
9c29fa1 ci: enable LFS checkout for Wikipedia index
7569ea2 ci: revert wasm emsdk pin to latest
3da1c6d fix(ci): correct WASM source paths in deploy workflow
ed55136 fix(wasm): include stdlib.h for abs() declaration
```

主要问题：

- 运行时 DB 为 21,184 行，而 JSON 和测试断言停留在 21,178 行，导致大面积 pytest 失败，已在 `dec8904` 对齐。
- 60MB Wikipedia 结构索引转 LFS 后，CI 未启用 `lfs: true`，已修复。
- wasm-deploy 的构建路径指向 `hardware/cnbe_wasm.c`，实际文件在 `hardware/wasm/`，已修正；同时补上 `stdlib.h` 声明 `abs()`。

## 分支清理

- 已合并进 main：3 个有效分支。
- 已删除/归档：其余全部废弃分支。
- 删除前本地完整备份：

```text
C:\Users\zairk\Documents\Codex\2026-08-14\wo\work\github-branch-backup-2026-08-20.bundle
C:\Users\zairk\Documents\Codex\2026-08-14\wo\work\github-branch-backup-2026-08-20-v2.bundle
```

## 开放 Issue 状态

### #35 Agent smoke test

要求的四个文件均已存在，`tests/test_repository_published_agent_skill.py` 本地 8 个用例通过。建议在 GitHub 页面按 Issue 原要求回复验证摘要后关闭。

### #39 字段级数据缺陷

四项缺陷已实证：

1. `struct_name` 26 个取值，超出治理批准的 13 标签集，且中英混用。
2. `strokes` 被静默截断在 31，与真实 31 画字不可区分。
3. `idx` 顶格 2047，20,902 行共享 2,048 槽，碰撞语义无文档。
4. `radix` 214 个，超出 GF 0011-2009 的 201 主部首。

处置文档见 `GITHUB_ISSUE_39_TRIAGE_2026-08-20.md`。

## 后续建议

- 在 GitHub 页面关闭 #35，并回复验证摘要。
- #39 按 WS-3 字段语义冻结排期，先补 8105 无碰撞测试，再冻结寻址协议。
- 分支纪律已写入 `CNBE_MOE_A800_PROJECT/SKILL_CNBE_MOE_A800.md` 和 `cnbe-moe-boundary` skill。
