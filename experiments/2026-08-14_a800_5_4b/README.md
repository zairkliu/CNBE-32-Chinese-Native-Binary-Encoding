# CNBE v2 5.4B A800 × 2 训练计划

日期：2026-08-14

## 一、目标

在 A800 × 2 上对 v2 冻结语料完成 1 epoch CNBE-MoE-128 训练，并完整保存：

- 最终 checkpoint（先于任何 collective）；
- 独立 step checkpoint；
- per-step 训练曲线；
- 论文所需的 MANIFEST / ENVIRONMENT / REPRODUCE。

## 二、规模

| 项 | 值 |
|---|---:|
| train 物理词数 | 5,069,667,334 |
| eval 物理词数 | 47,611,359 |
| seq_len | 256 |
| batch/GPU | 16 |
| 全局 batch | 8,192 token/step |
| 总步数 | 约 618,750 |
| checkpoint | 每 10,000 步 |

若 batch=16 OOM，使用 batch=8 + grad_accum=2，保持全局 batch 不变。

## 三、目录

```text
2026-08-14_a800_5_4b/
├── configs/
│   ├── v2_moe128_a800.yaml
│   ├── v2_moe128_a800_smoke.yaml
│   └── v2_eval_a800.yaml
└── scripts/
    ├── run_a800.sh
    └── smoke_a800.sh
```

## 四、使用

```bash
# 1. smoke
bash scripts/smoke_a800.sh

# 2. 正式训练
bash scripts/run_a800.sh

# 3. 中断后续训
RESUME=1 bash scripts/run_a800.sh
```

## 五、防错要求

1. `final.pt` 先于任何 collective 保存；
2. step checkpoint 独立保存，resume 从最新 `step_*.pt`；
3. 日志与 step metrics 落盘，不依赖终端；
4. 启动前检查残留进程与显存；
5. 数据、vocab、mapping、脚本全部来自冻结包。

## 六、论文资料

训练完成后：

```text
/output/run_2026-08-14/
├── training.log
├── step_metrics.jsonl
├── train_metrics.json
├── eval_metrics.json
├── eval_pred_hash.json
└── checkpoints/
```

用 `extract_step_curves.py` 把 `step_metrics.jsonl` 转成论文图 1 所需 CSV/JSON。
