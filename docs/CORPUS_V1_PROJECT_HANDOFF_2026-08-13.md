# CNBE 中文出版物合并去重语料库 v1 项目交接

日期：2026-08-13
状态：清洗与质量校准已完成，待进入“冻结训练语料”阶段

## 一、已完成

### 1.1 语料合并与去重

- 来源：01_v2 / 02_v2.1 / 03_v2.2 / 殆知阁古籍精校；
- 扫描 15,013 条，精确重复 16 组，近重复 0 组；
- 去重后保留 14,997 条：
  - core（中文占比 ≥70%）：13,515 本；
  - technical（30%-70%）：868 本；
  - excluded：614 本。

### 1.2 质量校准

- CNBE 码覆盖率：96.95%（20,533 / 21,180）；
- CJK 编码覆盖率：core 99.9996%，technical 99.9984%；
- Top-100 非空码占比：43.73%（中文自然 Zipf 分布）；
- 结构熵：H(radix)=5.95、H(strokes)=3.71、H(struct)=2.12；
- core/technical KL 散度：0.2086；
- 去重交叉验证：500 对 max Jaccard 0.003；
- manifest 完整性：14,383 / 14,383；
- 乱码率：core 0.0047%，technical 0.017%。

### 1.3 人工抽检与修复

- 两轮人工抽查，累计修复 11 本版权/水印残留；
- 修复后出版信息与水印命中为 0；
- 已重建 `shards_core`（69 个）与 `shards_technical`（4 个）。

### 1.4 已入库脚本

- `repo/tools/audit_merge_corpus.py`
- `repo/tools/quality_calibration.py`
- `repo/tools/fix_manual_audit_findings.py`
- `repo/tools/build_llm_shards.py`
- `repo/tools/corpus_sampling_tool.py`
- `repo/tools/export_training_results.py`

## 二、当前产物

```text
D:\1 训练语料\CNBE中文出版物合并去重_v1\
├── core\                 # 13,515 本
├── technical\            # 868 本
├── shards_core\          # 69 个 LLM shard
├── shards_technical\     # 4 个 LLM shard
├── corpus_manifest.json  # 14,383 条
├── dedup_report.json
├── quality_audit.json
└── quality_check\
    ├── quality_report.json
    ├── manual_audit_fix_report.json
    ├── manual_sample_40.*
    └── manual_sample_40_cleaned_*.zip
```

## 三、剩余工作

### P0：冻结为正式训练语料（下一步优先）

1. 生成 `canonical_manifest.json`
   - 每个文件记录：slug、bucket、batch、sha256、字符数、CJK、meta 分；
   - 冻结 train / eval / val 切分；
   - 固定 seed。

2. 生成最终 CNBE 资产
   - 从最终语料构建 `vocab.json`；
   - 构建 128 专家 `mapping_128.json`；
   - 输出覆盖率与结构熵报告。

3. 确定 code-0 策略
   - 约 21.6% 为标点/英文/空白；
   - 决定：保留、mask、或单独字段；
   - 写入训练配置，避免每轮不一致。

4. 生成训练包
   - `scnet_upload_package_CORPUS_V1_FROZEN.tar.gz`；
   - 包含 shards、manifest、vocab、mapping、config、eval 脚本。

### P1：语料扩展与复核

1. 新增 3000+ 本出版物或古籍：
   - 先转纯文本；
   - 跑同一套清洗/去重/质量门禁；
   - 增量合并到 v1，生成 v2。

2. 全量 SHA256 校验与版权残留复扫。

3. 在冻结语料上完成多组稳健性复现：
   - seed 43/44；
   - 544M 语料上的 MoE/Dense/Unicode 对照；
   - 等计算预算对照。

### P2：训练与模型方向

1. 路由均衡优化：balance_weight 0.02-0.05，目标 Gini ≤0.20；
2. 256 专家评估；
3. Structure-MLM / 对比学习；
4. 与 RAG、古籍验证、OCR 字形对比集成。

## 四、新对话启动清单

新对话开始时直接贴这段：

```text
项目：CNBE 中文出版物合并去重语料库 v1 冻结。
现状：清洗、去重、质量校准、人工抽检修复均完成。
数据：D:\1 训练语料\CNBE中文出版物合并去重_v1
交接文档：repo/docs/CORPUS_V1_PROJECT_HANDOFF_2026-08-13.md
下一步：P0 生成 canonical_manifest、冻结 vocab/mapping、确定 code-0 策略、打训练包。
```

## 五、关键指标速查

| 指标 | 值 |
|---|---:|
| 总书数（去重后） | 14,997 |
| core / technical | 13,515 / 868 |
| 总字符 | 约 51.4 亿 |
| CNBE 唯一码 | 20,533 |
| 覆盖率 | 96.95% |
| CJK 覆盖率 | 99.9996% |
| Top-100 占比 | 43.73% |
| 精确重复 | 0（已剔除） |
| 近重复 | 0 |
| manifest 匹配 | 100% |
