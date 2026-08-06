# CNBE API Pipeline

面向 CNBE 项目 API 自动化的任务客户端与实验入口。

## 客户端

- `clients/ocr_client.py`：PaddleOCR-VL-1.6 批量 OCR 任务客户端，支持任务提交、轮询、断点续跑、按页缓存。
- `clients/llm_client.py`：DeepSeek V4 API 结构化输出客户端，密钥从环境变量或 `~/.codex/auth.json` 读取，不落盘。
- `clients/evidence.py`：Unihan / CHISE IDS / 部首映射的本地证据聚合器，只做交叉参考，不构成国标锚定。

## 实验

`run_legacy_prefill.py` 对 8105 剩余 491 条 legacy 行生成候选预填：

1. 确定性证据层：Unihan 部首/笔画 + CHISE 结构推导，生成 top-1 候选与置信度；
2. 可选 LLM 层：DeepSeek V4 对每条生成候选、置信度与裁决理由，记录原始响应；
3. 输出 JSON、XLSX、结果统计与报告（`results/`）；不写发布库。

`run_full_prefill.py` 面向 97,686 全量目录，支持 `--llm-mode`（`none` / `incomplete` / `sample` / `all`）、并发与预算守卫；`probe_full_catalog.py` 零 API 全量覆盖率探针。

## 运行

```bash
PYTHONPATH=repo/src python3 experiments/2026-08-07_api_pipeline/run_legacy_prefill.py \
    --llm-limit 20

PYTHONPATH=repo/src python3 experiments/2026-08-07_api_pipeline/probe_full_catalog.py

PYTHONPATH=repo/src python3 experiments/2026-08-07_api_pipeline/run_full_prefill.py \
    --limit 500 --llm-mode sample --sample-size 20 --workers 2
```

LLM 层未配置密钥时自动跳过并记录 `LLM_SKIPPED`。

工作流规范与全量可行性：

- `repo/docs/API_EVIDENCE_PIPELINE.md`
- `repo/reports/FULL_CATALOG_SCALING_FEASIBILITY_2026-08-07.md`
