# CNBE Knowledge Bridge：GitHub 技术融合计划

日期：2026-08-10
状态：MVP 已落地，进入平台集成阶段

## 一、GitHub 检索结果

| 仓库 | 能力 | 与本项目的融合点 |
|---|---|---|
| `howl-anderson/hanzi_chaizi` | 20,000+ 汉字拆字 | 为 CNBE 补 IDS/部件字段 |
| `cjkvi/cjkvi-ids` | 标准 IDS 分解数据库 | 与 CNBE radix/struct 交叉验证 |
| `mreichhoff/kanji-linear-algebra` | IDS 组合运算 | 验证 CNBE 组字与拆字 |
| `Radically/radically` | 部件化 CJK 搜索 | CNBE 字段检索的中文替代对照 |
| `houbb/nlp-hanzi-similar` | 四角/拼音/结构/偏旁/笔画相似度 | 与 CNBE 加权距离做消融 |
| `shibing624/pycorrector` | 中文文本纠错 | OCR 后处理候选融合 |
| `woniu9524/book-proofreading` | 古籍校勘、繁简/异体转换 | 古籍校验与异体归一化 |
| `Jason9339/traditional-chinese-historical-document-ocr-llm-fusion` | TrOCR + LLM 历史文档 OCR | 字形候选打分融合 |
| `Langchain-Chatchat` | 本地中文 RAG 生态 | RAG 向量索引与 CNBE 字段过滤 |
| `Alibaba-NLP/VRAG` | 多模态 RAG 框架 | OCR 图件与文本联合检索 |

## 二、融合架构

```text
AI / LLM
  ^  prompt = CNBEState.to_ai_prompt() + retrieved knowledge
  |
CNBE Knowledge Bridge (repo/src/cnbe32/knowledge_bridge.py)
  |-- CNBEState：32 位二进制编码 -> AI 可读状态
  |-- self_validate()：数据库自验（字段、反向碰撞、索引唯一性）
  |-- retrieve_knowledge()：中文知识库 / RAG 结构检索
  |-- ocr_candidates()：OCR 字形候选排序
  |-- ancient_validate()：古籍校验与摘录
  |
SQLite cnbe32.db（unicode/char/cnbe/radix/stroke/struct/index/track）
```

CNBE 的优势在于：检索和校验不是只看 Unicode 码点，而是看
`(radix, stroke, struct, index, ext)` 结构化字段，计算机和 AI
都能直接读取同一个二进制状态。

## 三、三个中文优势场景

### 1. 中文知识库 / RAG

- 精确字命中优先，结构近邻作为召回与重排；
- 后续接入 Langchain-Chatchat 类向量索引时，CNBE 字段作为硬过滤 +
  重排键；
- 保留“按部首/笔画/结构查询”的中文原生检索入口。

### 2. 古籍验证和摘录

- `difflib` 找出 OCR 与真值差异，再用 CNBE 距离区分“形近可疑”与
  “无关差异”；
- 融合 `book-proofreading` 的异体归一化，融合 `cjkvi-ids` 的部件
  证据链；
- 输出校勘笔记 + 摘录文本，直接进 `guji-platform` 校对工作流。

### 3. OCR 字形对比

- 候选字按 CNBE 字段距离排序，返回字段差异（部首/笔画/结构/索引）；
- 融合 `nlp-hanzi-similar` 与 `pycorrector` 做候选合并；
- 对“己/已/巳”“戊/戌/戍”这类形近字，CNBE 距离可作为确定性先验。

## 四、MVP 已落地

- SDK 模块：`repo/src/cnbe32/knowledge_bridge.py`
- 演示脚本：`repo/tools/cnbe_knowledge_bridge_demo.py`
- 测试：`repo/tests/test_knowledge_bridge.py`（6 项 PASS）
- 演示输出：`repo/results/cnbe_knowledge_bridge_demo.json`

自验结果（`repo/data/cnbe32.db`）：

| 项目 | 值 |
|---|---:|
| 总行数 | 21,184 |
| standard 轨 | 7,602 |
| 字段越界 | 0 |
| 重编码不一致 | 0 |
| 反向编码碰撞 | 4 |

反向碰撞说明当前 `field_weighted_distance` 仍存在“同字段不同字距离为 0”
的伪度量问题，这也与数学深化实验结论一致，下一步需要用 index/ext 参与
距离或建立等价类表。

## 五、下一步

1. 把 `CNBEKnowledgeBridge` 接入 `guji-platform` 的 `TruthLibrary` 与
   Web 工作台；
2. 从 `cjkvi-ids` / `hanzi_chaizi` 导入 IDS 与部件字段，交叉验证
   radix/struct；
3. 引入向量检索库（Langchain-Chatchat 风格），CNBE 字段作为过滤 +
   重排；
4. 接入 `book-proofreading` 异体归一化，完善古籍摘录与校勘；
5. 用 `nlp-hanzi-similar` / `pycorrector` 与 CNBE 距离做 OCR 消融；
6. 同时推进 P0 全量控制训练（见 `NEXT_PHASE_PLAN_2026-08-10.md`）。
