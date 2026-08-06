# CNBE API Evidence Pipeline

## 目的

把 2026-08-07 验证过的“OCR 任务客户端 + 证据聚合 + 确定性候选 + LLM 结构化候选 + 人工审核包”固定为可复现工作流，为 97,686 全量候选预填建立可执行入口。

## 工作流

```text
范围清单（8105 legacy / 97,686 全量）
  -> Stage 1 证据聚合（Unihan / CHISE IDS / 部首映射，只读）
  -> Stage 2 确定性候选 + CNBE 往返校验
  -> Stage 3 LLM 结构化候选（可选，缓存 + 预算守卫）
  -> Stage 4 审核包（JSON / XLSX / 置信度分层）
  -> Stage 5 人工审核与裁决（独立门禁）
  -> Stage 6 应用候选（默认 BLOCKED，需治理授权）
```

## 入口

| 入口 | 用途 |
|---|---|
| `experiments/2026-08-07_api_pipeline/run_legacy_prefill.py` | 8105 剩余 491 条 legacy 预填 |
| `experiments/2026-08-07_api_pipeline/run_full_prefill.py` | 97,686 全量预填（支持 limit / llm-mode / workers） |
| `experiments/2026-08-07_api_pipeline/probe_full_catalog.py` | 全量证据覆盖率探针，零 API 调用 |
| `experiments/2026-08-07_api_pipeline/clients/ocr_client.py` | PaddleOCR-VL-1.6 批量 OCR 任务客户端 |

## 配置

`pipeline_config.json` 固定以下边界：

- 证据路径：Unihan / CHISE IDS / 部首映射 / 运行时库；
- LLM：模型、Base URL、最大输出 token、温度；
- 置信度：high >= 0.95，medium >= 0.80；
- 预算守卫：最大调用数 20,000，最大 token 20,000,000；
- 门禁：候选预填不写发布库，GF0011/GF0012/GF0013 权威裁决保持独立。

## 缓存与恢复

- OCR：`jobs.json` + `pages/` + `raw/`，已产出页面自动跳过；
- LLM：`llm_audit.jsonl` 记录 Unicode、模型、状态、耗时、usage、原始响应，重跑按 Unicode 命中缓存；
- XLSX 被 Excel 占用时自动写 `*_pending.xlsx`，不中断流程。

## 置信度分层

- `high`：确定性候选完整，且 LLM 一致且置信度 >= 0.95；
- `medium`：确定性候选完整，未经 LLM 确认；
- `low`：证据缺失、分解歧义或笔画溢出（>31）。

`run_full_prefill.py` 同时报告 `agreement`（严格一致）与 `consistent`（一致或补全），避免把“LLM 补齐缺失字段”误判为冲突。

## 全量扩展路径

1. 完成 8105 legacy 491 预填与人工审核；
2. 按既有治理执行 300 字全量试点，固定证据覆盖率与 LLM 一致率基线；
3. 全量证据层（97,686，本地零 API 成本）；
4. LLM 只处理证据不完整行与 QA 抽样；
5. 分层人工审核：完整候选按 QA 抽样，低置信/不完整行全量审核；
6. 治理授权后生成隔离的全量候选库，不替换 SDK 数据库。
