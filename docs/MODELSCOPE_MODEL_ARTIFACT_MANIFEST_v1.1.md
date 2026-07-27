# CNBE-32 ModelScope 制品对齐清单 v1.1

**状态：已核验下载制品；实验性能结论待复核**  
**核验日期：2026-07-28**  
**制品页：** <https://www.modelscope.cn/models/zairkliu/CNBE-32/summary>

本清单把 GitHub 仓库与 ModelScope 下载制品之间可以直接核验的部分固定下来。它不把模型卡中的自述训练指标升级为独立复现实验结论。

## 公开读取 API 与同步源

- 元数据读取：`GET https://www.modelscope.cn/api/v1/models/zairkliu/CNBE-32`
- 模型卡源文件读取：`GET https://www.modelscope.cn/api/v1/models/zairkliu/CNBE-32/repo?Revision=master&FilePath=README.md`
- 待同步的中文模型卡源文件：[MODEL SCOPE CNBE-32 Model Card](./model_cards/MODELSCOPE_CNBE32_MODEL_CARD.md)

公开 API 只用于核验读取。对 ModelScope 模型仓库 `README.md` 的写入必须经已认证账户完成，并在写入后重新读取上述端点核对内容与文件哈希。

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

## 对齐的 Ollama 使用方式

ModelScope 制品中的 `Modelfile` 已记录为当前下载制品的提示模板。仓库的 `tools/deploy/Modelfile` 使用同一结构编号，并额外写入候选结果与人工审核边界；在 ModelScope 模型卡同步该边界前，两者不宣称字节一致。下载文件与仓库的 `tools/deploy/Modelfile` 置于同一目录后：

```bash
ollama create cnbe-32 -f Modelfile
ollama run cnbe-32 "汉字：好"
```

建议 `temperature <= 0.1`。这只完成模型推理调用，不验证输出字段的语言文字正确性。

## 实验结果的当前边界

ModelScope 模型卡自述包含 5,000 步训练与若干评测数字；但 GitHub 已提交的 `reports/v11_8105_qlora/TRAINING_REPORT.md` 记录的是 1,000 步完成。两者尚未由同一不可变运行清单关联，因此：

- 不在项目首页将 5,000 步、训练时长、loss、66.0%、92.7% 或泛化结论作为已确认项目结果；
- 不以模型输出替代 Unicode 对齐、国家标准证据或人工审核；
- 不允许模型自动写入 CNBE 运行时表；
- 在补齐清单前，模型制品只能作为研究性候选预测器发布。

重新确认实验结论至少需要：模型 revision 或文件哈希、基础模型版本与许可证、训练配置、数据输入哈希、训练/验证/测试切分与随机种子、适配器哈希、原始评测 JSON、评测命令、以及基线比较。

## 未完成的互操作性项

`tools/deploy/api_server.py` 面向 Hugging Face 基础模型加 LoRA 适配器；ModelScope 下载物是 GGUF 推理文件。两者尚未提供“同一权重、同一提示模板、同一输出”的可复现等价验证。因此 API 路径是独立实验路径，不能宣称与 ModelScope GGUF 制品结果等价。

相关材料：

- [ModelScope 模型页](https://www.modelscope.cn/models/zairkliu/CNBE-32)
- [v11 实验说明](../llm_experiments/v11_8105_qlora/README.md)
- [训练报告](../reports/v11_8105_qlora/TRAINING_REPORT.md)
- [字段评测补充](../reports/v11_8105_qlora/FIELD_EVAL_SUPPLEMENT.md)
- [README 证据状态说明](./README_EVIDENCE_STATUS.md)
