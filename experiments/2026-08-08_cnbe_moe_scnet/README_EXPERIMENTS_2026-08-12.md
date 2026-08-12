# CNBE-MoE 实验归档索引（2026-08-12）

## 一、第二轮：544M DCU-128 训练

- 语料：5.44 亿 token，vocab 17,474；
- 模型：d_model=1024，d_ff=2048，12 层，128 专家，Top-2；
- 步数：125,976；
- 最终 eval：loss 4.5915，next-code 23.56%，
  radix 24.09%，struct 44.07%，strokes 26.04%，
  struct head 47.10%，Gini 0.2971；
- 归档：`results_2026-08-11/`；
- 报告：`../../docs/TRAINING_RUN_REPORT_2026-08-11.md`。

## 二、V1 受控对比实验

### 2.1 设计

- 文档：`CONTROL_EXPERIMENTS_V1_DESIGN_2026-08-11.md`；
- 数据：v1 24M token，train 24M / eval 381,237；
- 三组有效对照：MoE-128、Dense same-config、Unicode Dense。

### 2.2 有效结果

| 指标 | MoE-128 | Dense | Dense matched | Unicode |
|---|---:|---:|---:|---:|
| eval_loss | 4.5430 | 7.3033 | 7.2802 | 7.7933 |
| next-code / next-token | 22.96% | 2.61% | 2.61% | 0.0010% |
| struct | 43.05% | 38.41% | 38.41% | N/A |
| expert_gini | 0.1472 | null | null | null |
| params | 289,920,031 | 37,954,591 | 289,858,591 | 38,130,891 |

### 2.3 结论

- MoE-128 显著优于 Dense same-config；
- CNBE 显著优于 Unicode；
- Dense matched-params 已完成（289.86M 参数），仍远低于 MoE-128，
  H1 等参数归因通过。

### 2.4 归档

- `results_2026-08-12/`：三组 metrics、mapping、README_SCIENCE、
  comparison_table、分析文档；
- `control_experiments_v1/`：配置、运行脚本、打包脚本。

## 三、复现入口

```bash
# V1 三组对照
bash control_experiments_v1/scripts/run_v1_control_dcu2.sh

# 科研版打包
python control_experiments_v1/scripts/package_v1_control_results.py \
  --root /scnet_upload_package_DCU
```

## 四、未入库内容

- 模型权重 `final.pt`（保存在云端/本地压缩包，不入 GitHub）；
- 544M 三档导出 zip；
- 临时 staging、patch zip、上传包。
