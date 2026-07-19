<p align="center">
  <strong>CNBE-32</strong><br>
  中文原生二进制编码
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./README_ZH.md">简体中文</a> ·
  <a href="./README_EN.md">English mirror</a>
</p>

<p align="center">
  <img alt="项目状态" src="https://img.shields.io/badge/status-research%20prototype-orange">
  <img alt="Python SDK" src="https://img.shields.io/badge/Python%20SDK-stable%20baseline-blue">
  <a href="https://pypi.org/project/cnbe32/"><img alt="PyPI" src="https://img.shields.io/pypi/v/cnbe32.svg"></a>
  <img alt="Basic CJK DB" src="https://img.shields.io/badge/Basic%20CJK-20%2C902%20entries-green">
  <img alt="Extended scope" src="https://img.shields.io/badge/97%2C686-experimental%20target-lightgrey">
</p>

一个面向 CJK 字符的 32 位结构指纹实验：如果中文编码不只告诉电脑"这是哪个字"，还告诉它"这个字长得有什么结构"，会怎样？

> **CNBE-32 是研究原型。**
> 当前 Python SDK 随包数据库目标是 **20,902 个 Basic CJK** 条目。
> 更大的 **97,686 CJK** 数字是计划中 / 实验性的扩展范围，不代表当前随包 SDK 覆盖。
> 最新发布包是 **cnbe32 1.0.4**，对应 GitHub `v1.0.4` 发布检查点。

## 当前标准重启状态

CNBE 正在按更严格的国家语言文字规范证据链重新组织。

**8105 通用规范汉字表**现在是本轮重写编码的国家标准核心。现有 CNBE 行在通过新的证据门禁前，只能视为旧版 / 当前运行时数据。20,902 行 Agent 预编码池是项目候选输出，97,686 行全目录仍是扩展研究目标。

本轮重启目标是把 CNBE 重建为一个对齐国家语言文字规范的编码项目：Agent 负责受控执行汉字结构工作，每个可提升结果都必须携带证据和审核状态，仓库结构必须区分运行时代码、证据、报告、历史实验和科研复现产物。

当前已确认状态：

- 发布检查点：`v1.0.4`
- 已发布 Python 包：`cnbe32==1.0.4`
- 8105 基线行数：`8105`
- 当前 CNBE 中落入 8105 范围的行数：`7829`
- 当前 CNBE 中缺失的 8105 行数：`276`
- 人工审核通过的 8105 Agent 结构基线：`8105 / 8105`
- 已从批准后的 8105 dry run 提升到运行时 CNBE32 的行数：`6712`
- 额外完成的保守标准化运行时修复行数：`598`
- 当前已修复的 8105 运行时总行数：`7310`
- 强制通过但保留到后续插入 / 部首策略队列的行数：`795`
- 运行时 JSON 和 SQLite 数据库已从批准后的 20,902 行源表重建

治理文档：

- [CNBE 8105 编码治理](./docs/CNBE8105_ENCODING_GOVERNANCE.md)
- [CNBE 研究定位声明](./docs/CNBE_RESEARCH_POSITION_STATEMENT.md)
- [CNBE 可复现 Agent 工作流](./docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md)
- [CNBE 数据可复现契约](./docs/DATA_REPRODUCIBILITY_CONTRACT.md)
- [CNBE 版本治理](./docs/CNBE_VERSION_GOVERNANCE.md)
- [仓库结构](./docs/REPOSITORY_STRUCTURE.md)
- [CNBE 结构类型运行时规范](./spec/struct_types.json)
- [仓库发布版 Agent skill](./skill/cnbe-hanzi-structure-encoding-agent/SKILL.md)
- [GitHub Copilot 云端智能体状态](./docs/COPILOT_CLOUD_AGENT_LIMITATION.md)
- [CNBE 8105 编码比对报告](./evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md)
- [CNBE 8105 运行时提升报告](./reports/8105_CNBE32_RUNTIME_PROMOTION.md)
- [CNBE 8105 标准化运行时修复](./reports/8105_STANDARDIZED_RUNTIME_REPAIR.md)

早期 AI 生成的目录字段现在只作为历史测试基线处理。它们可用于定位旧版
回归问题，但不能作为结构、部首、笔画、教学或科研声明的依据。

## 项目合理性

CNBE-32 只有在编码流程比早期 AI 生成目录更严格时才有研究价值。本项目
当前的合理性建立在以下边界上：

- 以 Unicode 作为兼容身份，不把 CNBE 描述成 Unicode 的替代品；
- 以 8105 通用规范汉字表作为发布轨道的国家标准核心；
- 用 GF / GB / GG 语言文字规范处理笔画、笔顺、部件、部首、独体字、
  结构和拆分；
- 辞书、字源资料、Wikipedia、ZDIC 只作为审核上下文或来源发现辅助，
  除非字段明确标注为非国家标准上下文；
- CNBE32 作为紧凑运行时载体，32 位容纳不下的证据保留给 CNBE64 /
  CNBE128 或审核归档；
- 只发布能够追溯到已提交证据、报告、测试和发布说明的检查点。

因此，本仓库不是一个来源不明的大型生成表，而是一个对齐规范、可审核、
可复现的中文结构编码研究流程。

关于当前方向、时间点、复现路径、技术可能性和科研价值的一页式说明，见
[CNBE 研究定位声明](./docs/CNBE_RESEARCH_POSITION_STATEMENT.md)。

## Agent 与自动化边界

仓库包含 GitHub 兼容的 Agent profile 和 Copilot 指令，但 GitHub
Copilot cloud agent 执行能力属于可选付费集成，不是开源复现、科研审核
或发布轨道 CNBE 工作的必要依赖。

项目的可复现基线保存在已提交的 skill、测试、报告、review packet 和普通
GitHub Actions 中。没有 Copilot cloud agent 访问权限的维护者，仍可在
本地或通过普通 pull request 执行 CNBE Agent 工作流。详见
[GitHub Copilot 云端智能体状态](./docs/COPILOT_CLOUD_AGENT_LIMITATION.md)。

---

## 为什么有趣

Unicode 告诉计算机"这是哪一个字符"。

CNBE-32 问的是一个不同的问题：

> 能不能把 CJK 字符的一部分视觉和结构逻辑，直接放在紧凑的二进制形式里？

这让 CNBE-32 在以下方向值得实验：CJK-aware 嵌入、低层查找表、硬件友好的文本特征、面向特定语言的模型输入。

---

## 一张图看懂

```text
31              24 23        19 18     15 14                 4 3        0
┌────────────────┬────────────┬─────────┬─────────────────────┬──────────┐
│ Radical/Radix  │  Stroke    │ Struct  │     Glyph Index     │   Ext    │
│     8 bits     │  5 bits    │ 4 bits  │       11 bits       │  4 bits  │
└────────────────┴────────────┴─────────┴─────────────────────┴──────────┘
```

把它理解为一张紧凑的结构指纹，而非替代 Unicode。

---

## 快速开始

```bash
python -m pip install cnbe32
```

```python
from cnbe32 import encode_cnbe, decode_cnbe, bit_hamming_distance

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
```

---

## 当前稳定部分

- CNBE-32 字段编码与解码
- 所有位域范围的严格校验
- 真正的 bit-level Hamming distance 及旧版字段加权距离
- 可选 SQLite 数据库查询
- 显式 `SkillTable` 构造
- wheel 构建、pip install、pytest、ruff、GitHub Actions CI

---

## 当前实验部分

- LLM prompt 与特征实验
- JEPA 风格表示学习
- RISC-V 与硬件指令原型
- OS 与 kernel 层实验
- 金融、生物、物理、社会科学风格实验

除非对应目录包含固定数据集版本、可复现脚本、baseline 对比、随机种子、原始结果产物和训练/测试分离，否则应视为**初步研究原型**。

---

## 覆盖范围术语

| 术语 | 含义 |
|---|---|
| **8105 国家标准核心** | 8,105 个通用规范汉字，作为发布轨道的标准基线 |
| **Python SDK 随包数据库** | 20,902 个 Basic CJK 运行时条目（随 wheel 发布） |
| **Agent-standard 候选范围** | 项目受控候选输出，必须向 8105 对齐后才能提升 |
| **实验性扩展范围** | 97,686 个 CJK 字符作为设计 / 研究目标，不是已验证发布声明 |
| **具体实验覆盖范围** | 取决于每个实验使用的数据集和复现脚本 |

关于碰撞率、完整覆盖或扩展 CJK 覆盖的说法，都只能在对应实验的数据集和脚本范围内解释。

---

## 证据等级

本仓库包含研究原型和早期实验。除非对应实验包含以下内容，否则结果应理解为初步结果：

- 固定数据集版本
- 可复现脚本
- baseline 对比
- 随机种子或确定性设置
- 原始输出或结果产物
- 必要时的训练 / 测试集隔离

---

## 位域布局

| 字段 | 位数 | 说明 |
|---|---:|---|
| Radical / Radix | 8 | 部首或结构根字段 |
| Stroke | 5 | 笔画数字段 |
| Structure | 4 | 字符结构字段 |
| Glyph Index | 11 | Basic CJK 字形索引字段 |
| Extension | 4 | 实验性扩展字段 |

---

## Python SDK 示例

```python
from cnbe32 import (
    encode_cnbe, decode_cnbe,
    bit_hamming_distance, field_weighted_distance,
)

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
print(field_weighted_distance(a, b))
```

---

## 给 geek 的看点

| 如果你喜欢... | CNBE-32 给你... |
|---|---|
| 位域 | 一个固定的 32 位 CJK 结构布局 |
| 语言内部 | 部首、笔画、结构、字形索引字段 |
| ML 特征 | 紧凑的 CJK-aware 特征输入 |
| 硬件实验 | 可在 RISC-V / 指令原型附近测试的布局 |
| 奇奇怪怪的编码想法 | 一个中文原生表示的研究沙盒 |

---

## 给中文文字爱好者的解释

汉字不是随意排列的符号。很多汉字天然带有可见的结构：部件、笔画、布局、历史字形。

CNBE-32 不声称"理解"汉字。它只是试着把其中一部分可见结构编码成计算机可以直接使用的形式。

---

## 路线图

1. 保持 Python SDK 构建、安装、测试、lint 流水线绿色。
2. 为每个实验补充可复现脚本。
3. 区分稳定 SDK claim 和具体实验 claim。
4. 发布数据来源和覆盖验证脚本。
5. 为 Python、C、Rust、硬件原型增加共享 golden vectors。
6. 增加 baseline（Unicode codepoint、one-hot、IDS、learned embeddings）。

---


## 实现一致性

CNBE-32 在 [spec/golden_vectors.json](./spec/golden_vectors.json) 中提供机器可读的 golden vectors，用于验证 Python、C、Rust 和硬件方向实现的位域编码 / 解码一致性。同一组 vectors 现在由 Python 测试、最小 C 一致性测试和最小 Rust 一致性测试共同验证。


## 项目维护

- [变更记录](./CHANGELOG.md)
- [发布流程](./RELEASE.md)
- [v1.0.4 发布说明](./docs/releases/v1.0.4.md)
- [贡献指南](./CONTRIBUTING.md)
- [安全策略](./SECURITY.md)

## 许可证

MulanPSL-2.0
