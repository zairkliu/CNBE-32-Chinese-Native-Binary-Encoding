# CNBE-32 中文原生二进制编码

> **项目状态：** 研究原型。
>
> **当前 Python SDK 随包数据库：** 20,902 个 Basic CJK 条目。
>
> 更大的 **97,686 CJK** 数字指的是计划中 / 实验性的扩展编码范围，不代表当前 Python SDK 随包数据库覆盖范围。
>
> **稳定部分：** Python 位域编码 / 解码、距离函数，以及数据库可用时的 Basic CJK 查询。
>
> **实验部分：** LLM、JEPA、RISC-V、OS、金融、生物、物理等研究原型。

CNBE-32 是一个面向 CJK 字符的 32 位结构化编码实验。它探索是否可以把部首 / radix、笔画数、字形结构、字形索引和扩展位等 CJK 结构特征表示为紧凑的二进制格式，用于 AI 和硬件方向的实验。

当前仓库已经建立了较稳定的 Python SDK 工程基线，同时保留了若干研究原型。Python SDK 是目前最稳定的部分；其他目录除非包含可复现实验脚本、数据集和验证说明，否则都应视为实验性内容。

---

## 为什么是 CNBE-32？

大多数通用文本编码把字符表示为标识符。CNBE-32 实验的是另一种方向：把一部分 CJK 字符结构属性直接编码进固定 32 位值。

目标不是替代 Unicode。CNBE-32 更适合作为辅助表示，用于实验：

- CJK-aware 模型输入；
- 字符结构特征；
- 紧凑查询表；
- 面向硬件的编码测试；
- 可复现的 CJK 特征基准。

---

## 当前稳定范围

当前稳定 Python SDK 支持：

- CNBE-32 字段编码与解码；
- 所有位域范围的严格校验；
- 真正的 bit-level Hamming distance；
- 旧版字段加权距离；
- 可选 SQLite 数据库查询；
- 显式 `SkillTable` 构造；
- wheel 构建与安装；
- pytest 测试；
- ruff lint；
- GitHub Actions CI。

随包 SDK 当前目标是 **20,902 条 Basic CJK 数据库**。

---

## 实验范围

仓库还包含以下方向的探索性工作：

- LLM prompt 与特征实验；
- JEPA 风格表示学习；
- RISC-V 与硬件指令原型；
- OS 与 kernel 层实验；
- 金融、生物、物理、社会科学风格实验。

除非对应目录包含以下材料，否则实验结果应理解为**初步研究原型**：

- 固定数据集版本；
- 可复现实验脚本；
- baseline 对比；
- 随机种子或确定性设置；
- 原始结果或产物；
- 必要时的训练 / 测试集隔离。

---

## 覆盖范围术语

CNBE-32 使用几个容易混淆的覆盖范围术语：

- **Python SDK 随包数据库：** 当前为 20,902 个 Basic CJK 条目。
- **实验性扩展范围：** 97,686 个 CJK 字符，作为设计 / 研究目标。
- **具体实验覆盖范围：** 取决于每个实验使用的数据集和复现脚本。

除非特别说明，Python SDK 文档中的示例都指向随包的 20,902 条 Basic CJK 数据库。

关于碰撞率、完整覆盖或扩展 CJK 覆盖的说法，都只能在对应实验的数据集和脚本范围内解释。

---

## 证据等级

本仓库包含研究原型和早期实验。除非对应实验包含以下内容，否则结果应理解为初步结果：

- 固定数据集版本；
- 可复现脚本；
- baseline 对比；
- 随机种子或确定性设置；
- 原始输出或结果产物；
- 必要时的训练 / 测试集隔离。

Python SDK hardening 工作的重点是让核心编码器、解码器、距离函数、数据库加载和测试变得可复现。

---

## 位域布局

CNBE-32 使用 32 位布局：

| 字段 | 位数 | 说明 |
|---|---:|---|
| Radical / Radix | 8 | 部首或结构根字段 |
| Stroke | 5 | 笔画数字段 |
| Structure | 4 | 字符结构字段 |
| Glyph Index | 11 | Basic CJK 字形索引字段 |
| Extension | 4 | 实验性扩展字段 |

当前 Python SDK 会在编码前校验所有字段。非法值会抛出 `CNBEValueError`，不会静默截断。

---

## Python SDK 安装

本地安装：

```bash
python -m pip install .
```

开发安装：

```bash
python -m pip install -U pip build pytest ruff
python -m pip install -e .
```

---

## Python SDK 示例

```python
from cnbe32 import (
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
)

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
print(field_weighted_distance(a, b))
```

---

## 距离函数

推荐使用：

* `bit_hamming_distance(a, b)`：真正的 bit-level Hamming distance。
* `field_weighted_distance(a, b)`：旧版 CNBE 字段加权距离。

已弃用：

* `hamming_distance(a, b)`

`hamming_distance` 为兼容旧代码保留，但它不是真正的 bit-level Hamming distance。

---

## 数据库加载

Python SDK 按以下顺序解析 `cnbe32.db`：

1. `CNBE32_DB_PATH`
2. 随包数据：`cnbe32/data/cnbe32.db`
3. 源码 checkout fallback：`data/cnbe32.db`

示例：

```bash
export CNBE32_DB_PATH=/path/to/cnbe32.db
```

如果数据库缺失，数据库查询函数会给出清晰错误，说明如何提供文件。

---

## SkillTable

`SkillTable` 用于 Basic CJK code point offset 实验。

使用：

```python
from cnbe32 import SkillTable

table = SkillTable.empty()
```

或：

```python
table = SkillTable.from_file("skill_table.npy")
```

不支持无参数直接 `SkillTable()`。这样可以避免用户以为加载了真实表，实际却得到全零表。

---

## 开发检查

运行完整本地验证：

```bash
python -m compileall src tests
python -m build
python -m pip install --force-reinstall dist/*.whl
pytest
ruff check src tests
```

CI 会在 Python 3.10、3.11、3.12 上运行 compile、build、wheel install、pytest 和 ruff。

---

## 仓库状态

| 区域                   | 状态       |
| -------------------- | -------- |
| Python SDK 位域编码 / 解码 | 稳定基线     |
| Python SDK 测试与 CI    | 稳定基线     |
| Basic CJK 数据库查询      | 数据库可用时稳定 |
| 扩展 CJK 覆盖            | 实验目标     |
| LLM / JEPA 实验        | 研究原型     |
| RISC-V / 硬件实验        | 研究原型     |
| OS / kernel 实验       | 研究原型     |
| 金融 / 生物 / 物理实验       | 研究原型     |

---

## 路线图

建议后续工作：

1. 保持 Python SDK build、install、test、lint 流水线为绿色。
2. 为每个实验补充可复现脚本。
3. 区分稳定 SDK claim 和具体实验 claim。
4. 发布数据来源和覆盖验证脚本。
5. 为 Python、C、Rust、硬件原型增加共享 golden vectors。
6. 增加 Unicode codepoint、one-hot、IDS-style features、learned embeddings 等 baseline。

---

## 许可证

MulanPSL-2.0
