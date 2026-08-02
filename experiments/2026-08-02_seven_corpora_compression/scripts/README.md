# 七语料 CNBE 复现脚本

脚本按用途分组：

| 脚本 | 说明 |
|---|---|
| `2_cnbe_encode.py` | 纯字流 -> CNBE-32 二进制流 |
| `3_build_templates.py` | 统计 (radix, stroke, struct) 高频模板 |
| `4_predictive_compress.py` | delta/template/raw + zlib 无损压缩 |
| `5_benchmark.py` | 与 gzip 对比并生成压缩报告 |
| `build_cnbe_volume.py` / `benchmark_volume.py` | 构建与基准 CNBE Volume |
| `step1_build_mapping.py` | 构建负载均衡的结构-专家映射 |
| `step2_cnbe_router.py` | O(1) 查表路由器 |
| `step3_benchmark.py` | FLOPs 与实测路由耗时 |
| `step4_downstream.py` | 路由质量代理任务 |
| `deepseek_api_repro.py` | DeepSeek V4 API 句读/路由/结构复现 |
| `run_sushi_pipeline.py` | 诗集全链路一键复现 |
| `ocr_sushi.py` / `extract_sushi.py` | DJVU 诗集 OCR 提取 |
| `build_sushi_punct_eval.py` | 构建诗集句读 eval |

数据依赖：`cnbe32.db`（仓库 `data/` 下标准库），各语料 `*.chars.txt`。

典型流程：

```bash
python 2_cnbe_encode.py corpus.chars.txt corpus.cnbe --db cnbe32.db
python 3_build_templates.py corpus.cnbe templates.json --top-k 64
python 4_predictive_compress.py corpus.cnbe templates.json compressed --level 6
python 5_benchmark.py corpus.chars.txt corpus.cnbe \
  --delta compressed_delta.zlib --template compressed_template.zlib \
  --raw-zlib compressed_raw.zlib --report compression_report.md
python build_cnbe_volume.py --input corpus.cnbe --output corpus_4096.cnbev --page-size 4096
python step1_build_mapping.py --cnbe corpus.cnbe --output struct_expert_map_16.json --num-experts 16
python step3_benchmark.py --cnbe corpus.cnbe --map struct_expert_map_16.json
python step4_downstream.py --cnbe corpus.cnbe --map struct_expert_map_16.json
```

DeepSeek API 密钥读取自 `~/.codex/auth.json`，模型使用
`deepseek-v4-flash`，必须传 `"reasoning": {"effort": "low"}`。
