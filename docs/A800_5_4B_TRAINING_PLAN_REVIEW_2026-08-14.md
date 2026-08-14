# A800 × 2 5.4B 训练计划审阅稿

日期：2026-08-14
状态：待用户审阅，未推送 GitHub

## 一、当前项目状态

### 1.1 语料

- v2 冻结完成：15,589 份文件，core 14,665 / technical 924；
- train / eval / val 文件级切分：15,288 / 145 / 156；
- train 物理词数：5,069,667,334；
- vocab：20,535（含 code 0）；mapping：14,248 模板 / 128 专家；
- code-0：LM 保留，字段头训练 mask。

### 1.2 论文

- 已更新到 v2 新冻结版本；
- 明确区分“内容 token / 物理词数 / 分片统计”；
- 图 1 已替换为真实收敛曲线（对话记录抽样点）；
- 新增图 4 模型架构；
- 审计报告已追加“修复复检”章节。

### 1.3 前两轮错误教训

1. 最终 checkpoint 必须先于任何 collective 保存；
2. 中间 checkpoint 必须独立保存；
3. 日志与 per-step 指标必须落盘；
4. 路径、脚本、mapping/vocab 必须版本一致；
5. 启动前清理残留进程与显存。

## 二、A800 训练计划

### 2.1 规模

| 项 | 值 |
|---|---:|
| 模型 | d_model=1024、d_ff=2048、12 层、16 头 |
| MoE | 128 专家、Top-2、硬路由 |
| seq_len | 256 |
| batch/GPU | 16 |
| 全局 batch | 8,192 token/step |
| epochs | 1 |
| 总步数 | 约 618,750 |
| checkpoint | 每 10,000 步 |

### 2.2 防错设计

- `step_%06d.pt` 独立保存，resume 从最新 step checkpoint；
- 训练结束先保存 `final.pt`，再进入任何 collective；
- 最终评估单进程执行；
- 每步写 `step_metrics.jsonl`；
- `training.log` 通过 `tee` 落盘；
- 数据/vocab/mapping/脚本全部来自冻结包；
- 启动前先 smoke：100 步 + resume 测试。

## 三、待推送内容

### 3.1 推送

- `experiments/2026-08-14_a800_5_4b/`（配置、脚本、README）；
- `tools/extract_step_curves.py`；
- `tools/patch_corpus_v2_paper.py`；
- 训练代码更新：
  `train_distributed.py`（step checkpoint / resume / step metrics / vocab/mapping 覆盖）；
- 文档：
  `docs/A800_PRETRAIN_PREP_2026-08-14.md`、
  `docs/A800_5_4B_TRAINING_PLAN_REVIEW_2026-08-14.md`、
  `docs/CORPUS_V1_PROJECT_HANDOFF_2026-08-13.md`；
- `results_2026-08-14/step_curves_from_chat/`（论文曲线数据）。

### 3.2 不推送

- 模型权重 `*.pt`；
- 语料码流 `.cnbe`；
- 10.3GB 冻结包；
- 临时 zip / staging / 日志。

## 四、审阅确认点

1. batch=16/GPU 是否接受；如担心显存，改为 batch=8 + grad_accum=2；
2. checkpoint 每 10,000 步是否接受（约 62 个全量 checkpoint）；
3. 训练步数约 618,750 步是否符合预期；
4. 是否同意上述推送清单。

## 五、下一步

用户确认后：

1. 提交并推送 GitHub；
2. 生成 A800 上传包；
3. 在 A800 上跑 smoke；
4. smoke 通过后启动正式训练。
