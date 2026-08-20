---
license: other
license_name: mulanpsl-2.0
language:
- zh
tags:
- cnbe-32
- chinese-encoding
- deepseek-r1-distill-qwen
- qlora
- cjk
- gguf
pipeline:
- text-generation
library_name: gguf
---

# CNBE-32 模型卡

## 1. 发布定位

本页对应 `zairkliu/CNBE-32` 的当前发布 GGUF 推理制品。经项目所有者确认，它是重编码后 DeepSeek-R1-Distill-Qwen-1.5B 的 5,000-step QLoRA 模型基线。

CNBE-32 是面向 CJK 汉字的研究性 32 位结构特征编码；Unicode 码位仍是字符身份和兼容层。模型是**研究性候选预测器**：它不替代 Unicode，不构成国家标准，也不是运行时编码表的权威写入来源。

项目以 8105 通用规范汉字表作为发布轨道的标准核心，正在进行国家语言文字规范对齐；不宣称整体“符合国家标准”。

## 2. 可核验下载制品

| 项目 | 值 |
|---|---|
| 文件 | `model-f16.gguf` |
| 格式 | GGUF F16 |
| 精确大小 | `3,560,415,968` bytes |
| SHA-256 | `542e5edd7594194749de13953bd7d00903ebb4fcdbafdfa07c7ffc4b97eef5f9` |
| 架构 | `qwen2` |
| 层数 / 隐藏维度 | 28 / 1,536 |
| 词表大小 | 151,936 |
| 许可证 | MulanPSL-2.0 |

下载后先核验：

```bash
sha256sum model-f16.gguf
# 期望：542e5edd7594194749de13953bd7d00903ebb4fcdbafdfa07c7ffc4b97eef5f9
```

哈希不一致时不得加载、转发或作为本模型制品引用。

## 3. 发布训练与评测摘要

| 项目 | 发布记录 |
|---|---:|
| 基础模型 | DeepSeek-R1-Distill-Qwen-1.5B |
| 训练方法 | QLoRA，4-bit NF4 |
| 训练步数 | 5,000 |
| 训练样本 / 标准轨字符 | 12,163 / 7,602 |
| 训练硬件 / 时长 | RTX 4060 Ti 8GB / 5.8 小时 |
| 最终训练 / 验证 loss | 0.1493 / 0.09179 |
| 结构分类（13 类） | 66.0% |
| 形近字区分（41 对） | 92.7% |
| 笔画数（±2） | 54.0% |
| 任意单字段正确 | 70.0% |
| 生僻字泛化 | 与已见字持平 |
| 语义聚类 | ratio = 0.99x，作为结构编码边界结果 |

以上是当前发布制品在模型卡定义的实验条件下的记录，不是逐字编码正确率、国家标准符合性、通用 OCR 性能或教学结论。

## 4. 字段语义

```text
位[31:24]  部首索引（8 位；项目内部编号，GF 0011-2009 锚定尚未完成）
位[23:19]  笔画数（5 位）
位[18:15]  结构类型（4 位）
位[14:4]   字形索引（11 位；有损兼容字段，已弃用，不能寻址）
位[3:0]    扩展标志（4 位；实验字段）
```

结构类型唯一采用中文轨 13 值：0 独体字、1 上下、2 上中下、3 左右、4 左中右、5 左上包、6 右上包、7 左三包、8 左下包、9 上三包、10 下三包、11 全包围、12 镶嵌。历史编号不得混用。

## 5. 使用方式

将 `model-f16.gguf` 和本制品的 `Modelfile` 放在同一目录：

```bash
ollama create cnbe-32 -f Modelfile
ollama run cnbe-32 "汉字：好"
```

建议 `temperature <= 0.1`。模型可生成候选结构化输出，但调用成功不代表输出经过语言文字审核。

## 6. 输出处理边界

1. 保存原始模型响应并标记为候选结果。
2. 先完成 Unicode 身份对齐。
3. 再通过国家标准证据、来源分层和人工审核检查结构、部首、笔画、笔顺与拆分。
4. 未经明确授权的模型输出不得自动写入 JSON、SQLite 或发布制品。
5. 模型预测不构成汉字属性、CNBE 编码或教学/科研结论的权威证据。

## 7. 历史材料

GitHub 的 1,000-step DeepSeek 报告是模型上传期间的中间记录；当前发布基线为本页所述 5,000-step ModelScope 制品。重编码前 Qwen3.5-0.8B 实验已归档至 legacy 分支，不属于当前模型主线。

## 8. 相关材料

- GitHub 仓库：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding>
- 发布基线：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/V11_MODELSCOPE_RELEASE_BASELINE.md>
- 制品对齐清单：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/MODELSCOPE_MODEL_ARTIFACT_MANIFEST_v1.1.md>
- 字段语义冻结规范：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/FIELD_SEMANTICS_FREEZE_v1.1.md>

## 9. 许可证

[MulanPSL-2.0](https://license.coscl.org.cn/MulanPSL2)
