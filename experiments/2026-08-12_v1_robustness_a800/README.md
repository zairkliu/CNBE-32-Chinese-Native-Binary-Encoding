# V1 稳健性复核（DCU 优先执行版）

日期：2026-08-12

## 一、现状修正

原方案中“Dense matched-params 待执行”已更新为**已完成**：

| 条件 | eval_loss | next-code | struct | params |
|---|---:|---:|---:|---:|
| MoE-128 | 4.5430 | 22.96% | 43.05% | 289,920,031 |
| Dense same-config | 7.3033 | 2.61% | 38.41% | 37,954,591 |
| Dense matched-params | 7.2802 | 2.61% | 38.41% | 289,858,591 |
| Unicode Dense | 7.7933 | 0.0010% | N/A | 38,130,891 |

## 二、DCU 可执行范围

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 环境与工件冻结 MANIFEST | 待执行 |
| A | 四组独立重评估 + 预测 MD5 | 待执行 |
| B | DCU 多种子复现（seed 43/44） | 待执行 |
| D | 等墙钟时间对照（可选，DCU） | 待执行 |
| E | 汇总 RESULTS.md | 待执行 |

A800 阶段 C 暂不执行，待资源确认后再推进。

## 三、目录

```text
experiments/2026-08-12_v1_robustness_a800/
├── README.md
└── scripts/
    ├── stage_a_eval.sh
    └── stage_b_multiseed.sh
```

## 四、执行顺序

1. 生成 MANIFEST：

```bash
python /scnet_upload_package_MERGED_DCU/tools/generate_v1_manifest.py \
  --output /scnet_upload_package_DCU/output/v1_robustness/MANIFEST.json
```

2. 阶段 A 独立重评估：

```bash
bash scripts/stage_a_eval.sh
```

3. 阶段 B 多种子：

```bash
bash scripts/stage_b_multiseed.sh 43
```

时间允许时补 seed 44：

```bash
bash scripts/stage_b_multiseed.sh 44
```

## 五、提交规则

- 只提交配置、脚本、哈希、指标 JSON、结果摘要；
- checkpoint、日志、原始语料不推送 GitHub；
- 结论使用“固定设置下的观察”表述。
