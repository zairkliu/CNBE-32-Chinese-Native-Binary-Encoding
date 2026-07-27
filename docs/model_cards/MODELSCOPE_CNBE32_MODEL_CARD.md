---
license: other
license_name: mulanpsl-2.0
language:
- zh
tags:
- cnbe-32
- chinese-encoding
- qwen2
- qlora
- cjk
- gguf
pipeline:
- text-generation
library_name: gguf
---

# CNBE-32 模型卡

## 1. 制品定位

本页对应 `zairkliu/CNBE-32` 的 GGUF 推理制品。CNBE-32 是面向 CJK 汉字的研究性 32 位结构特征编码；Unicode 码位仍是字符身份和兼容层。该模型是**研究性候选预测器**，不替代 Unicode，不构成国家标准，也不能作为运行时编码表的权威写入来源。

项目以 8105 通用规范汉字表作为发布轨道的标准核心，并处于国家语言文字规范对齐过程中；不宣称整体“符合国家标准”。

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

## 3. 字段语义

```text
位[31:24]  部首索引（8 位；项目内部编号，GF 0011-2009 锚定尚未完成）
位[23:19]  笔画数（5 位）
位[18:15]  结构类型（4 位）
位[14:4]   字形索引（11 位；有损兼容字段，已弃用，不能寻址）
位[3:0]    扩展标志（4 位；实验字段）
```

结构类型唯一采用中文轨 13 值：

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

历史编号不得混用。详细字段状态见 GitHub 的字段语义冻结规范。

## 4. 使用方式

将 `model-f16.gguf` 和本制品的 `Modelfile` 放在同一目录：

```bash
ollama create cnbe-32 -f Modelfile
ollama run cnbe-32 "汉字：好"
```

或使用 llama.cpp：

```bash
./main -m model-f16.gguf -p "汉字：好" -n 128 --temp 0.1
```

建议 `temperature <= 0.1`。模型可以生成候选结构化输出，但一次成功调用不代表输出经过语言文字审核。

## 5. 输出处理边界

1. 保存原始模型响应并标记为候选结果。
2. 先完成 Unicode 身份对齐。
3. 再通过国家标准证据、来源分层和人工审核检查结构、部首、笔画、笔顺与拆分。
4. 未经明确授权的模型输出不得自动写入 JSON、SQLite 或发布制品。
5. 模型预测不构成汉字属性、CNBE 编码或教学/科研结论的权威证据。

## 6. 实验状态

本模型关联 QLoRA 实验材料。当前公开材料中的训练步数和评测数字尚未由同一不可变运行清单绑定模型 revision、数据切分、随机种子、适配器校验和、原始评测输出与基线比较。因此，本模型卡不发布性能数字，也不作泛化、OCR 效果或下游收益主张。

待补齐运行清单后，才能将对应实验结论作为可复现实验报告重新发布。

## 7. 相关材料

- GitHub 仓库：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding>
- 制品对齐清单：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/MODELSCOPE_MODEL_ARTIFACT_MANIFEST_v1.1.md>
- README 证据状态：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/README_EVIDENCE_STATUS.md>
- 字段语义冻结规范：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/docs/FIELD_SEMANTICS_FREEZE_v1.1.md>
- 训练报告：<https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding/blob/main/reports/v11_8105_qlora/TRAINING_REPORT.md>

## 8. 许可证

[MulanPSL-2.0](https://license.coscl.org.cn/MulanPSL2)
