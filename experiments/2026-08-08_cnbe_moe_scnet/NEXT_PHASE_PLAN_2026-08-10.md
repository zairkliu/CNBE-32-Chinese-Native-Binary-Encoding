# CNBE-MoE 下一阶段计划 v2（2026-08-10 复盘后重制）

基准：SCNet L20 128 共享专家第一轮云训练已完成，复盘见
`RETRO_128_EXPERIMENT_2026-08-10.md`。

总体判断：**停止“堆专家 + 堆参数 + 盲扩语料”路线**。当前缺失的不是
算力，而是两个控制实验和一套不浪费算力的 MoE 实现。先补对照、先修
实现，再谈任何规模化。

## 一、边界（红线）

1. CNBE-MoE 不是中文语言模型项目；不因“模型更大”而上云；
2. 没有 Dense same-config 对照，不训练；
3. 涉及编码优势时必须有 Unicode same-config 对照；
4. 没有 a priori 停止条件，不训练；
5. 只在既有 24M 语料上换专家数（64/128/256），不训练；
6. 语料扩量默认不启动，除非 P2 证明“编码覆盖/泛化”是瓶颈。

## 二、P0：补齐两个缺失对照（最高优先，现有 L20 即可）

### P0.1 Dense same-config

- 同一 24,381,237 CNBE 码、同一 seed、同一模型主体参数；
- 仅关闭 MoE（`use_moe: false`），dense FFN 使用同一 d_ff；
- 输出：next-code / radix / struct / strokes / eval_loss。

判定：

| 指标 | 停止/回退条件 |
|---|---|
| MoE next-code ≤ Dense next-code | 停止 MoE 路线，回到编码规范层 |
| MoE struct ≤ Dense struct | 同上 |
| MoE Gini > 0.30 | 修路由后再跑，不继续加专家 |

### P0.2 Unicode same-config

- 同一 7 语料原始文本，按 Unicode 码点建词表；
- 同一模型结构、同参数规模、同步数；
- 输出：next-token 准确率与 loss；字段指标不适用。

判定：

| 指标 | 停止/回退条件 |
|---|---|
| CNBE next-code ≤ Unicode next-token | 停止“CNBE 优于 Unicode”的主张 |
| CNBE 字段头无有效学习曲线 | 回编码字段设计找原因 |

### P0.3 已就绪命令

```bash
python scripts/train_distributed.py \
  --config config/scnet_moe_config_dense_l20.yaml \
  --cnbe-paths /scnet_upload_package/data/*.cnbe \
  --output /scnet_upload_package/output/dense_metrics.json \
  --checkpoint-dir /scnet_upload_package/output/dense_checkpoints

python scripts/build_unicode_dataset.py \
  --chars-paths /scnet_upload_package/data_src/*.chars.txt \
  --output-dir /scnet_upload_package/data_unicode

python scripts/train_unicode_baseline.py \
  --config config/scnet_moe_config_unicode_l20.yaml \
  --codepoint-paths /scnet_upload_package/data_unicode/unicode.u32 \
  --output /scnet_upload_package/output/unicode_metrics.json \
  --checkpoint-dir /scnet_upload_package/output/unicode_checkpoints
```

## 三、P1：修 MoE 实现（不修完不上专家实验）

当前实现有三个必须修复的结构问题：

1. **Top-2 第二专家无语义**：`(primary + 1) % E` 改为真实路由
   （上下文/层相关或可学习路由，至少要有独立打分）；
2. **8 层共用同一路由**：路由结果加入 layer/context 维度，
   否则专家角色在层间完全重叠；
3. **向量化 grouped GEMM 全专家 padding**：128 专家实测约 4.2x
   浪费；只计算非空专家，或限制 max bucket，目标 padding ≤ 1.5x。

每个训练 run 必须输出专家利用度：

| 指标 | 目标 |
|---|---|
| padding factor | ≤ 1.5 |
| 层间专家-上下文槽位 | = E × L，而非 E |
| tokens/expert 最大/最小比 | ≤ 5 |
| Gini | ≤ 0.20 |

## 四、P2：编码泛化实验（替代盲扩语料）

用“留一交叉”回答编码泛化：

```text
训练：7 语料中任选 6 本
评估：剩下 1 本作为未见文本
轮换 7 次
```

输出：

- 未见文本的 CNBE 覆盖率；
- next-code / radix / struct / strokes 按未见语料分列；
- 未知码率与字段漂移报告。

这个实验不需要 100M 语料，却直接回答“CNBE 编码是否泛化到未见文本”。

## 五、P3：语料扩量（独立立项，默认关闭）

只有满足以下条件才立项：

1. P2 显示覆盖/泛化是瓶颈；
2. 扩量服务于编码验证，而不是“把模型跑大”；
3. 先做 10M-100M 字公开文本的编码覆盖率与人工复核；
4. 有独立预算和负责人，不走 CNBE-MoE 训练预算。

## 六、执行顺序、预算与停止条件

| 阶段 | 内容 | 资源 | 预计 |
|---|---|---|---|
| P0 | Dense + Unicode 对照 | L20 单卡或本地 GPU | 1-2 天 |
| P1 | 修 MoE 实现 | 本地 | 2-3 天 |
| P2 | 留一交叉泛化 | L20 单卡 | 1-2 天 |
| P3 | 语料扩量 | 另行立项 | 不预设 |

停止条件（写进每个实验卡）：

- P0.1：MoE 不优于 Dense，停止 MoE 路线；
- P0.2：Unicode 不低于 CNBE，停止编码优势主张；
- P1：padding > 1.5 或层间无分化，不允许上云；
- 任何阶段：指标不改变决策，就停止，不“再跑一轮看看”。

## 七、归档纪律

- 每个实验先填 `EXPERIMENT_CARD.md`；
- 每日结果写入 `repo/outputs/experiment_logs/YYYY-MM-DD.md`；
- 小指标、配置、脚本、报告入 Git；checkpoint、私有语料、mapping 不上传；
- 边界纪律固化在 skill `cnbe-moe-boundary`。

## 八、P0 执行状态（2026-08-10 更新）

- 本地小规模三组对照已跑通：MoE-8 / Dense(CNBE) / Dense(Unicode)，
  40 步，100k 字，结果见 `CONTROL_TRAINING_LOCAL_2026-08-10.md`；
- 脚本已支持 `--steps` 覆盖与 `use_moe` 配置开关；
- 下一步：把同一套包上传 L20 执行全量 Dense / Unicode 对照；
- 全量对照通过前，不再申请 256 专家或盲扩语料。

## 九、云训练环境登记（2026-08-10）

- 资源组：113 组 `hx1hgbwnormal`；
- 加速卡：异构加速卡 BW × 2，面板显示总显存 256GB；
- CPU：30 核；内存 118GB；
- 镜像：`jupyterlab-pytorch:2.9.0-ubuntu22.04-dtk26.04-py3.11-devel`；
- 启动：`scnet_startup_dcu2.sh`；
- 出版物清洗完成后，先 CNBE 编码、覆盖率复核，再合并 24M 语料并重建
  vocab/mapping；
- 详见 `repo/docs/SCNET_BW2_256GB_ENV_2026-08-10.md`。

## 十、出版物语料入库状态（2026-08-10）

- 1,281 本 MD 已完成清洗，输出 5.48 亿字符；
- 1,237 本通过质量过滤并完成 CNBE 编码，2.08GB；
- 与既有 24M 语料合并：总 tokens 544,003,069，唯一码 17,474；
- 合并训练包：`D:\训练语料\merged_training_package\`；
- 新增合并语料配置（128/256/Dense/Unicode）；
- 上云后先跑对照，再跑 MoE；
- 详见 `repo/docs/PUBLICATION_CORPUS_INGEST_REPORT_2026-08-10.md`。

## 十一、DeepSeek 三步法可行性评估（2026-08-10）

- Structure-MLM：可行，先处理 code 0 噪音，再做小规模消融；
- 伪度量对比学习：需先修度量和形近字评测集，不能直接当监督；
- 256 结构路由 MoE：当前硬路由已是结构路由，128 先跑出证据再谈；
- 修正环境：BW2 总显存 256GB，不是 128GB；
- 详见 `repo/docs/DEEPSEEK_STRUCTURE_MLM_FEASIBILITY_2026-08-10.md`。

## 十二、上传包就绪（2026-08-10）

- 上传包：`D:\训练语料\scnet_upload_package_MERGED_DCU.tar.gz`（约 1.5GB）；
- 包含代码、1244 个 .cnbe、1237 本清洗文本、merged assets、4 份合并配置；
- 上机流程：解压 -> smoke -> Dense/Unicode 对照 -> 128 专家 MoE；
- 256 专家仅在对照与 128 结果支持时启动。
