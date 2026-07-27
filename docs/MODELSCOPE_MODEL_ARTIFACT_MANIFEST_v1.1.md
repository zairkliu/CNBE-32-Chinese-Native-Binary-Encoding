# CNBE-32 ModelScope 制品对齐清单 v1.1

**状态：当前发布模型基线的可核验制品记录**  
**核验日期：2026-07-28**  
**制品页：** <https://www.modelscope.cn/models/zairkliu/CNBE-32/summary>

经项目所有者确认，ModelScope 的 `zairkliu/CNBE-32` GGUF 制品及其模型卡，是当前重编码后 DeepSeek-R1-Distill-Qwen-1.5B、5,000 步 QLoRA 发布模型的项目基线。本清单固定制品身份、字段编号、发布实验摘要与使用边界。

## 公开读取 API 与同步源

- 元数据读取：`GET https://www.modelscope.cn/api/v1/models/zairkliu/CNBE-32`
- 模型卡源文件读取：`GET https://www.modelscope.cn/api/v1/models/zairkliu/CNBE-32/repo?Revision=master&FilePath=README.md`
- GitHub 中文模型卡源文件：[MODELSCOPE_CNBE32_MODEL_CARD.md](./model_cards/MODELSCOPE_CNBE32_MODEL_CARD.md)

公开 API 仅用于读取核验。对 ModelScope 模型仓库 `README.md` 的写入必须经已认证账户完成，并在写入后重新读取上述端点核对内容与文件哈希。

## 已核验制品

| 项目 | 值 |
|---|---|
| 制品名 | `zairkliu/CNBE-32` |
| 发布格式 | GGUF F16 |
| 文件 | `model-f16.gguf` |
| 精确大小 | `3,560,415,968` bytes |
| SHA-256 | `542e5edd7594194749de13953bd7d00903ebb4fcdbafdfa07c7ffc4b97eef5f9` |
| 架构 | `qwen2` |
| 词表大小 | `151,936` |
| 层数 | `28` |
| 隐藏维度 | `1,536` |
| 最大位置长度 | `131,072` |
| 许可证 | MulanPSL-2.0 |
| 当前页面 revision | `master` |

下载后必须先验明文件身份：

```bash
sha256sum model-f16.gguf
# 必须等于 542e5edd7594194749de13953bd7d00903ebb4fcdbafdfa07c7ffc4b97eef5f9
```

## 发布训练与评测摘要

当前发布模型卡记录：12,163 个训练样本、7,602 个标准轨字符、RTX 4060 Ti 8GB、5.8 小时训练、5,000 steps、最终训练 loss 0.1493、最终验证 loss 0.09179。其任务内结果包括 13 类结构 66.0%、41 对形近字区分 92.7%、笔画数 ±2 为 54.0%、任意单字段正确 70.0%。

这些数字是当前发布制品在模型卡所述任务与样本条件下的发布实验记录；它们不构成国家标准符合性、逐字编码正确率、通用 OCR 性能或自动数据写入授权。

## 结构编号的唯一规范

模型提示、GitHub 部署文件和数据解释统一采用字段冻结草案中的中文轨 13 值编号：

| 值 | 结构 |
|---:|---|
| 0 | 独体字 |
| 1 | 上下 |
| 2 | 上中下 |
| 3 | 左右 |
| 4 | 左中右 |
| 5 | 左上包 |
| 6 | 右上包 |
| 7 | 左三包 |
| 8 | 左下包 |
| 9 | 上三包 |
| 10 | 下三包 |
| 11 | 全包围 |
| 12 | 镶嵌 |

来源：[字段语义冻结规范 v1.1 §2](./FIELD_SEMANTICS_FREEZE_v1.1.md)。历史英文轨编号及历史部署提示不得与本表混用。

## 历史材料与归档

- `reports/v11_8105_qlora/TRAINING_REPORT.md` 的 1,000-step DeepSeek 记录，是模型上传期间的历史中间状态；它不覆盖当前发布的 5,000-step ModelScope 基线。
- 重编码前 Qwen3.5-0.8B 的演示、脚本、日志与白皮书已归档至 [legacy-ai-encoding-baseline 分支](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/tree/test/legacy-ai-encoding-baseline)，不属于当前发布模型或数据主线。

## 对齐的 Ollama 使用方式

ModelScope 制品中的 `Modelfile` 已记录为当前下载制品的提示模板。仓库的 `tools/deploy/Modelfile` 使用同一结构编号，并额外写入候选结果与人工审核边界；两者不宣称字节一致。下载文件与仓库的 `tools/deploy/Modelfile` 置于同一目录后：

```bash
ollama create cnbe-32 -f Modelfile
ollama run cnbe-32 "汉字：好"
```

建议 `temperature <= 0.1`。这只完成模型推理调用，不验证输出字段的语言文字正确性。

## 使用边界

- 模型输出必须作为候选结果保存，并先完成 Unicode 身份对齐。
- 结构、部首、笔画、笔顺与拆分仍须经过国家规范对齐、来源证据和人工审核。
- 模型输出不得自动写入 JSON、SQLite 或发布运行时表。
- `tools/deploy/api_server.py` 使用 Hugging Face 基础模型与可选 LoRA；它与 GGUF 制品尚未提供逐权重、逐提示、逐输出等价证明，因此是独立实验部署路径。

相关材料：

- [ModelScope 发布基线](./V11_MODELSCOPE_RELEASE_BASELINE.md)
- [ModelScope 中文模型卡](./model_cards/MODELSCOPE_CNBE32_MODEL_CARD.md)
- [README 证据状态说明](./README_EVIDENCE_STATUS.md)
