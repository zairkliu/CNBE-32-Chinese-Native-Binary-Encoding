# CNBE-32 v11 ModelScope 发布基线

**状态：当前发布模型基线**  
**发布日期：2026-07-27**  
**权威发布面：** <https://www.modelscope.cn/models/zairkliu/CNBE-32/summary>

本文件记录当前发布模型的项目基线。经项目所有者确认，ModelScope 上的 GGUF 制品对应重编码后的 DeepSeek-R1-Distill-Qwen-1.5B 5,000 步 QLoRA 训练；该制品与其模型卡是当前模型版本、训练信息和结果的发布依据。

## 制品身份

| 项目 | 值 |
|---|---|
| 模型 | `zairkliu/CNBE-32` |
| 基础模型 | DeepSeek-R1-Distill-Qwen-1.5B |
| 训练 | QLoRA，4-bit NF4，5,000 steps |
| 文件 | `model-f16.gguf` |
| 格式 | GGUF F16 |
| 大小 | 3,560,415,968 bytes |
| SHA-256 | `542e5edd7594194749de13953bd7d00903ebb4fcdbafdfa07c7ffc4b97eef5f9` |
| 许可证 | MulanPSL-2.0 |

## 发布训练与评测摘要

| 项目 | 发布记录 |
|---|---:|
| 训练样本 | 12,163 |
| 标准轨字符 | 7,602 |
| 训练硬件 | RTX 4060 Ti 8GB |
| 训练时长 | 5.8 小时 |
| 最终训练 loss | 0.1493 |
| 最终验证 loss | 0.09179 |
| 结构分类（13 类） | 66.0% |
| 形近字区分（41 对） | 92.7% |
| 笔画数（±2） | 54.0% |
| 任意单字段正确 | 70.0% |
| 生僻字泛化 | 与已见字持平 |
| 语义聚类 | ratio = 0.99x，作为结构编码边界结果 |

上述指标是当前发布制品的项目发布记录。它们说明研究模型在特定任务和样本上的结果，不构成国家标准符合性、逐字编码正确性或自动写入运行时表的授权。

## 历史材料的归属

- `reports/v11_8105_qlora/TRAINING_REPORT.md` 所记录的 1,000 步 DeepSeek 训练，是模型上传过程中的临时历史状态，不是当前 ModelScope 发布基线。
- Qwen3.5-0.8B 与旧编码相关的演示、脚本、日志和白皮书均归档至 [test/legacy-ai-encoding-baseline](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/tree/test/legacy-ai-encoding-baseline) 分支，不属于重编码后的当前模型。
- 当前发布模型不使用旧 AI 编码作为国家标准或人工审核的替代依据。

## 使用边界

1. 模型输出是候选预测，必须先进行 Unicode 对齐。
2. 结构、部首、笔画、笔顺和拆分仍须按项目的国家规范对齐、证据与人工审核流程处理。
3. 模型输出不得自动写入 JSON、SQLite 或发布数据表。
4. 实验结果不替代 8105 人工审核基线与字段语义冻结规范。

## 链接

- [ModelScope 发布页](https://www.modelscope.cn/models/zairkliu/CNBE-32)
- [ModelScope 制品对齐清单](./MODELSCOPE_MODEL_ARTIFACT_MANIFEST_v1.1.md)
- [字段语义冻结规范](./FIELD_SEMANTICS_FREEZE_v1.1.md)
- [历史 Qwen 归档分支](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/tree/test/legacy-ai-encoding-baseline)
