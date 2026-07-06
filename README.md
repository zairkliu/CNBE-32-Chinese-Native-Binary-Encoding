# CNBE-32 · Chinese Native Binary Encoding / Chinese Native Binary Encoding

**将汉字的结构语义直接编码为 32 位二进制。A structured 32-bit encoding for 97,686 CJK characters that embeds radical, stroke count, and structure type directly into the encoding space, making machines understand Chinese at the binary level.**

> 这不是 Unicode 的替代品，而是 Unicode 之上的语义增强层。让 CPU 和 AI 不仅能显示汉字，更能理解汉字。
> This is not a replacement for Unicode. It is a semantic enhancement layer that lets machines understand Chinese characters at the binary level, not just display them.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-Spike+QEMU-orange)]()

---

## 编码速览 / Code Quick Look

**一个汉字，一个 32 位二进制数。One character, one 32-bit binary.**

```
位: 31     28 27    24 23    19 18    15 14              4 3     0
     +--------+--------+--------+------------------------+-------+
     | 预留位 | 子类型  | 扩展标志|    部首      |  笔画   | 结构  |
     +--------+--------+--------+------------------------+-------+
```

| 汉字 | Unicode | 编码值 CNBE Code | 部首 Radical | 笔画 Stroke | 结构 Structure |
|------|---------|-----------------|-------------|-------------|---------------|
| 一 | U+4E00 | `0x01080000` | 一 (ID=1) | 1 | 独体 Single |
| 汉 | U+6C49 | `0x0F288101` | 氵 (ID=15) | 5 | 左右 Left-Right |
| 国 | U+56FD | `0x1F400B0B` | 囗 (ID=31) | 8 | 全包围 Full-Wrap |
| 明 | U+660E | `0x48400801` | 日 (ID=72) | 8 | 左右 Left-Right |

---

## 为什么是 CNBE？/ Why CNBE-32?

| 维度 Aspect | Unicode / UTF-8 | CNBE-32 |
|------------|----------------|---------|
| 目标 Purpose | 字符显示与交换 Display & exchange | AI 理解与硬件加速 AI understanding |
| 编码方式 Encoding | 查表映射 Flat ID | 语义结构化 Semantic structured |
| 机器认知 Machine | 标识字符 Identifies | 理解结构 Understands composition |
| AI 兼容性 AI | 需从数据学习 Must learn | 提供结构先验 Provides structural prior |

**9 个跨领域验证通过 / 9 domains validated**: 语言学 linguistics, 生态 ecology, 气象 meteorology, 金融 finance, 生物 biology, 物理 physics, 社会 sociology, 预训练 pretraining, 数学 mathematics

---

## 核心实验 / Key Experiments

### 1. 小模型大提升 (v2) / Small Model, Big Boost

**假设 Hypothesis**：结构化编码补偿小模型参数量不足。Structured encoding compensates for small model capacity.
**方法 Method**：Qwen 3.5 0.8B，CNBE vs 标准输入。CNBE vs standard input on Chinese sentence understanding.

| 输入 Input | 准确率 Accuracy | 提升 Improvement |
|-----------|----------------|-----------------|
| 标准 Standard | 48% | -- |
| **CNBE** | **87%** | **+81%** |

**结论 Conclusion**：CNBE 对小模型有显著知识补偿效应。Significant knowledge compensation for small models.

### 2. CNBE 超越 Unicode (v6.5.2)

**假设 Hypothesis**：结构化位域比 Unicode 码点携带更多语义信息。
**方法 Method**：Gemma 4B 中文硬任务。Chinese hard tasks (reasoning, classical text).

| 输入 Input | 准确率 Accuracy |
|-----------|----------------|
| Unicode | 26.1% |
| **CNBE** | **43.5%** |

**结论 Conclusion**：未经训练的新编码首次尝试即超越 30 年标准（+17.4pp）。

### 3. 全中文操作系统 (v8.4) / Full Chinese OS

**假设 Hypothesis**：CNBE 能构建完整的中文原生软件栈。

- 全中文 Shell（输出/取编码/比较等命令）
- 中文 BASIC 解释器（7 个关键字）
- 文本编辑器（内置《道德经》205 行）
- RISC-V 自定义指令：cnhe.map/extract/cmp

**结论 Conclusion**：从编码到操作系统的完整技术栈已验证。

### 4. 数学推理底座 (v10.8) / Math Reasoning Foundation

**假设 Hypothesis**：CNBE 冻结嵌入可替代 Transformer 可训练嵌入。
**方法 Method**：TinyGPT 在奇偶/质数/序列推理任务上对比 4 种编码。

| 任务 Task | CNBE 最优 | OneHot 最优 | 胜出 |
|-----------|-----------|-------------|------|
| 奇偶 Parity | **0.3174** | 0.3427 | **CNBE** |
| 质数 Prime | **0.3894** | 0.5061 | **CNBE** |
| 序列 Sequence | **1.0726** | 1.2344 | **CNBE** |

**结论 Conclusion**：结构化编码在零训练条件下接近可训练嵌入性能。

---

## 技术栈 / Tech Stack

```
应用层 Application: 中文 BASIC + 文本编辑器 + 《道德经》录入
系统层 System: Shell + CNBE 运行时 (cnhe_map/extract/cmp)
硬件层 Hardware: RISC-V 1GHz + 1GB RAM (QEMU + Spike)
指令层 Instructions: cnhe.map / cnhe.extract / cnhe.cmp
编码层 Encoding: 32-bit CJK structured bit field (部首/笔画/结构)
```

---

## 快速开始 / Quick Start

### Python SDK

```bash
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git
cd CNBE-32-Chinese-Native-Binary-Encoding
python -c "import sys; sys.path.insert(0,'src'); from cnbe32 import encode_cnbe; print(hex(encode_cnbe(1,1,0)))"
```

### RISC-V 模拟器 / Simulator

```bash
cd hardware/simulator
gcc -o cnhe_sim cnhe_sim.c -Wall -O2 && ./cnhe_sim
```

### 中文操作系统 / Chinese OS (QEMU)

```bash
cd v84_riscv_os_full
make all && make run
```

### 复现实验 / Reproduce Experiments

```bash
cd v10_8_math_reasoning && python run_v108.py
cd v10_3_typhoon && python v10_3_typhoon.py
```

---

## 项目结构 / Project Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/specification/      # 编码规范 Encoding specification
|-- src/cnbe32/              # Python SDK (核心/编码器)
|-- include/cnbe32.h         # C 头文件 C header
|-- data/                    # 编码数据库 Database (CSV)
|-- tests/                   # 测试套件 Test suite
|-- tools/                   # 开发工具 Dev tools
|-- bindings/rust/           # Rust/WASM 绑定
|-- hardware/               # RISC-V 模拟器 + FPGA
|-- v9_jepa_tree/           # JEPA 预测实验 (v9)
|-- v10_5~v10_8/            # 跨领域实验 (v10)
|-- v84_riscv_os_full/      # 中文操作系统原型
|-- results/                 # 白皮书 White papers
|-- docs/EXPERIMENTS.md      # 实验总览 Experiment overview
|-- docs/VISION.md           # 战略愿景 Strategic vision
|-- docs/COMPARISON.md       # 方案对比 Comparison
|-- pyproject.toml           # Python 项目配置
|-- LICENSE                  # 木兰许可证 Mulan PSL v2
```

---

## 里程碑 / Milestones (v1-v10.8)

| 阶段 Phase | 版本 | 核心结论 Key Result |
|-----------|------|--------------------|
| 编码语义验证 Semantic | v1-v4 | AI 理解 CNBE（0.8B +81%）|
| 多模型对比 Model | v5 | 收益随规模递减 |
| 数值特征 Numerical | v6 | 裸数字最优 >Unicode |
| 硬件验证 Hardware | v7 | 3 条 RISC-V 指令 |
| 中文操作系统 Chinese OS | v8 | 全中文技术栈 |
| JEPA 预测 | v9.0-v9.4 | 结构化编码优势确认 |
| 金融回测 Finance | v10.0-v10.2 | 双市场正收益 |
| 跨领域 Cross-Domain | v10.3-v10.8 | 9 个领域验证通过 |

**完整白皮书 Full white papers**: [results/](results/) 目录 (41 份文档)

---

## 演进路线 / Roadmap

| 阶段 Phase | 状态 Status | 内容 Content |
|-----------|-------------|-------------|
| 编码与语义验证 Encoding & Semantics | 已完成 Done | v1-v6 CJK 编码设计 |
| 硬件与系统 Hardware & System | 已完成 Done | v7-v8 RISC-V + 中文 OS |
| 复杂预测验证 Complex Prediction | 已完成 Done | v9-v10 9 领域验证 |
| AI 编译器 AI Compiler | 规划中 Planning | 中文自然语言→机器码 |
| 端侧 AI 集成 Edge AI | 规划中 Planning | CNBE 成为边缘 AI 默认标准 |
| 生态共建 Ecosystem | 愿景 Vision | 开源社区 + 行业标准 |

---

## 参与贡献 / How to Contribute

详见 See [CONTRIBUTING.md](CONTRIBUTING.md)

- **低门槛 Low barrier**: 编码字典 Encoding dictionary / 测试用例 Test cases / 文档 Documentation
- **高门槛 High barrier**: RISC-V 流水线 Pipeline / FPGA / LLM 适配 / 编译器  Compiler

---

## 许可证 / License

**木兰宽松许可证 v2 (Mulan Permissive Software License v2)**

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

---

**为中文 AI 生态而生——从编码到硬件，从单字到操作系统。**
**Built for the Chinese AI ecosystem -- from encoding to hardware, from single characters to a full operating system.**
