# 2026-08-02 永乐大典失败实验与句读转向

本目录沉淀 2026-08-02 全部失败结果、教训、白皮书与 14B 训练方案。

## 核心结论

1. 1.5B 不能做 400-500 字整页 OCR 转录（精确匹配约 20%）。
2. OCR 只做定位与兜底；页面锚定真值库命中 100%。
3. 识典公开《诗话六十三》与人工校订逐字一致 100%。
4. LLM 重新定位为“古籍句读专家”，只在真值纯文本上加工。
5. 下一步使用全部失败教训训练 DeepSeek-R1-Distill-Qwen-14B。
6. 14B 与 0.8B 架构不兼容，采用知识迁移：混入原 CNBE 178K 样本防遗忘。

## 文件

| 文件 | 说明 |
|---|---|
| `FAILURE_SUMMARY_2026-08-02.md` | 今日失败结果总结 |
| `WHITEPAPER_2026-08-02_14B.md` | 14B 训练路线白皮书 |
| `BOUNDARY_ANALYSIS.md` | 小模型上 LLM 与 CNBE 能力边界的真实讨论 |
| `qlora_config_14b.yaml` | 14B QLoRA 配置 |
| `dataset_report.md` | 句读数据集报告（295 条短样本） |
| `punctuator_eval.json` | 规则句读基线 F1 评测 |
| `skill/` | 古籍句读 14B 训练 Skill |

## 训练命令

```bash
cd guji-platform
python llm/train_punctuator.py --config llm/qlora_config_14b.yaml --output-dir llm/outputs/cnbe-punct-14b-v1
```

大模型权重与完整训练数据（1.47GB）不放入 Git，随
`outputs/training_data_2026-08-02_full.zip` 归档。
