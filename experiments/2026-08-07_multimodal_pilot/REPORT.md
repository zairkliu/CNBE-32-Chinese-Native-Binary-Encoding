# CNBE64 多模态试点报告（2026-08-07）

## 试点范围

- 300 字分层：A 8105 核心 100 / B 外 8105 有语义参考 100 / C 扩展与缺口 100
- 每个字生成 256x256 字形图（SimSun）
- 每个字构建 CNBE64 + GB18030 指针 + Unihan 语义证据

## 结果

| 项目 | 结果 |
|---|---:|
| 试点字数 | 300 |
| 字形图渲染 | 300 |
| 非空字形（SimSun 可渲染） | 173 |
| 空字形（系统字体缺字） | 127 |
| 证据包 | 300 |
| GGUF cnbe-32 哈希校验 | 通过 |
| GGUF cnbe-qwen9b-punct | 存在（Q4_K_M，5.6 GB） |
| Ollama 新模型 | `cnbe64-pilot` 已注册 |
| 多模态识图 | 1/1 正确识别“沥”的部首与结构 |

## 关键发现

1. **多模态闭环可行**：字形图 -> qwen3.8-max 识图 -> 识别“沥”为左右结构、氵部首，与 CNBE64 结构字段一致。
2. **系统字体覆盖不足**：SimSun 对 300 字试点有 127 个扩展字渲染为空，需改用古籍 OCR 裁剪、历史字形或更大字体集合。
3. **GGUF 后续操作要点**：qwen9b 模型必须把 `think:false` 放在请求顶层，否则持续输出 Thinking；修正后 `cnbe64-pilot` 可输出干净 JSON。
4. **已训练模型边界**：`cnbe64-pilot` 对“沥”输出结构“左右”、部首“氵”正确，但笔画猜为 12（标准应为 7），说明结构/部首可用作候选，笔画仍需确定性库或人工裁决。
5. **1.5B cnbe-32 模型仍不可靠**：抽样输出为思考式文本且字段错误，确定性 `data/cnbe32.db` 仍应是编码权威。

## 产物

- `results/pilot_scope.json`：300 字分层清单
- `results/pilot_evidence.json`：CNBE64 + GB18030 + 语义证据
- `results/gguf_ollama_verify.json`：GGUF/Ollama 验证
- `results/gguf_pilot_inference.json`：`cnbe64-pilot` 推理
- `results/vision_verify.json`：多模态识图
- `samples/`：4 张代表性字形图（含 1 张扩展字缺字样例）

## 下一步

1. 扩充字形来源：古籍 OCR 裁剪 + 更大字体，补齐 127 个空字形；
2. 扩大多模态识图到 30 字，统计“视觉结构 vs CNBE64 结构”一致性；
3. 用 `cnbe64-pilot` 批量生成结构/部首候选，与确定性层做一致性评估；
4. 笔画字段回落到确定性库与人工审核，不信任生成模型；
5. 按统一 schema 写入 `cnbe64_glyph_image` / `cnbe64_semantic` 证据表。
