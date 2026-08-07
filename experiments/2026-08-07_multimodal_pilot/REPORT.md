# CNBE64 多模态试点报告（2026-08-07）

## 试点范围

- 300 字分层：A 8105 核心 100 / B 外 8105 有语义参考 100 / C 扩展与缺口 100
- 每个字生成 256x256 字形图（SimSun -> 微软雅黑回退）
- 每个字构建 CNBE64 + GB18030 指针 + Unihan 语义证据

## 结果

| 项目 | 结果 |
|---|---:|
| 试点字数 | 300 |
| 字形图渲染 | 300 |
| 多字体回退后非空字形 | 300 |
| SimSun 可渲染 / 微软雅黑补齐 | 173 / 127 |
| 证据包 | 300 |
| GGUF cnbe-32 哈希校验 | 通过 |
| GGUF cnbe-qwen9b-punct | 存在（Q4_K_M，5.6 GB） |
| Ollama 新模型 | `cnbe64-pilot` 已注册 |
| 多模态识图 | 2/3 成功（1 次超时） |
| 30 字模型批量解析 | 30/30 |
| 模型结构一致 / 部首一致 / 笔画精确 | 13 / 8 / 5 |

## CNBE64 固化

- RFC：`docs/RFC_CNBE64_v1.md`
- codec：`src/cnbe64/`（可独立导入）
- golden vectors：`spec/cnbe64_golden_vectors.json`
- 测试：`tests/test_cnbe64.py`（4 passed）

## 关键发现

1. **多模态闭环可行**：字形图 -> qwen3.8-max 识图 -> 2/3 成功，成功样例识别“沥”“汧”的部首与结构均正确；1 次因 API 延迟超时。
2. **字体覆盖可通过回退解决**：SimSun 缺 127 个扩展字，微软雅黑补齐后 300/300 有字形；但古籍字形仍需要 OCR 裁剪与历史字形。
3. **GGUF 后续操作要点**：qwen9b 模型必须把 `think:false` 放在请求顶层，否则持续输出 Thinking；修正后 `cnbe64-pilot` 可输出干净 JSON。
4. **已训练模型边界**：30 字批量中结构一致 13/30、部首一致 8/30、笔画精确 5/30；单字“沥”结构/部首正确但笔画 12 vs 标准 7。模型输出只能做候选，不能替代确定性库。
5. **1.5B cnbe-32 模型仍不可靠**：抽样输出为思考式文本且字段错误，确定性 `data/cnbe32.db` 仍应是编码权威。

## 产物

- `results/pilot_scope.json`：300 字分层清单
- `results/pilot_evidence.json`：CNBE64 + GB18030 + 语义证据
- `results/gguf_ollama_verify.json`：GGUF/Ollama 验证
- `results/gguf_pilot_inference.json`：`cnbe64-pilot` 推理
- `results/vision_verify.json`：多模态识图（2 成功 + 1 超时）
- `results/model_batch_30.json`：30 字模型与确定性层对比
- `samples/`：4 张代表性字形图（含 1 张 SimSun 缺字空白样例）

## 下一步

1. 扩充古籍 OCR 裁剪与历史字形，补足“多字体可渲染但非古籍字形”的差距；
2. 扩大多模态识图到 10-30 字并做缓存，统计视觉结构与 CNBE64 的一致性；
3. 用 `cnbe64-pilot` 只生成结构与部首候选，笔画一律回落到确定性库；
4. 在 `cnbe64` 包上实现 golden vectors 的 C/Rust 绑定一致性测试；
5. 按统一 schema 写入 `cnbe64_glyph_image` / `cnbe64_semantic` 证据表。
