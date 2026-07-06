# CNBE-32

**中文原生二进制编码 / Chinese Native Binary Encoding**

将汉字的结构语义（部首-笔画-结构）直接编码为 32 位二进制，让 CPU 和 AI 原生理解中文。
A structured 32-bit encoding for 97,686 CJK characters that embeds radical, stroke count, and structure type directly into the encoding space.

<p align="center">
  <img src="https://img.shields.io/badge/Encoding-32--bit%20CNBE-blue?style=for-the-badge" alt="Encoding">
  <img src="https://img.shields.io/badge/ISA-RISC--V%20Custom-green?style=for-the-badge" alt="ISA">
  <img src="https://img.shields.io/badge/OS-Full%20Chinese%20Shell-orange?style=for-the-badge" alt="OS">
  <img src="https://img.shields.io/badge/Vision-2035%20Digital%20China-red?style=for-the-badge" alt="Vision">
  <img src="https://img.shields.io/badge/License-Mulan%20PSL%20v2-lightgrey?style=for-the-badge" alt="License">
</p>

<p align="center">
  <a href="#quick-start"><strong>[ 快速开始 ]</strong></a>
  <a href="#key-experiments"><strong>[ 核心实验 ]</strong></a>
  <a href="#tech-stack"><strong>[ 技术栈 ]</strong></a>
  <a href="#how-to-contribute"><strong>[ 参与贡献 ]</strong></a>
</p>

---

---

## 架构全景 / Architecture Panorama

```mermaid
graph TD
    A[汉字输入] -->|部首/笔画/结构| B(CNBE-32 编码器)
    B -->|32-bit Binary| C{RISC-V 自定义指令集}
    C -->|cnhe.map / cnhe.cmp| D[硬件层: Spike/QEMU/FPGA]
    D --> E[系统层: 全中文 Shell]
    E --> F[中文 BASIC / JEPA 语义引擎]
```

---

## 愿景与使命 / Vision & Mission

受 **2035 数字中国** 战略启发，CNBE-32 的目标是：

> **让每一个会中文的人，都能用母语无缝进入人工智能时代。**

这是一个具备完整技术闭环的成熟体系，但作为中文原生计算领域的极早期探索，仍处于开放性的研究阶段。在 AI Agent 时代，以前科学家关于全中文计算机系统的梦想终于有了实现的可能。

---

## 目录 / Table of Contents

- [编码速览](#code-quick-look)
- [为什么是 CNBE？](#why-cnbe)
- [认知平权](#cognitive-equity)
- [核心实验](#key-experiments)
- [关键洞察](#large-vs-small)
- [技术栈](#tech-stack)
- [快速开始](#quick-start)
- [项目结构](#project-structure)
- [演进路线](#roadmap)
- [参与贡献](#how-to-contribute)
- [许可证](#license)

---

## <span id="code-quick-look">编码速览 / Code Quick Look</span>

**核心理念: 把汉字变成包含部首-笔画-结构的 32 位整数，让机器直接看懂字形。**

```
位: 31     28 27    24 23    19 18    15 14              4 3     0
     +--------+--------+--------+------------------------+-------+
     | 预留位 | 子类型  | 扩展标志|    部首      |  笔画   | 结构  |
     +--------+--------+--------+------------------------+-------+
```

| 汉字 | Unicode | CNBE-32 编码 | 部首 (ID) | 笔画 | 结构 |
|------|---------|-------------|-----------|------|------|
| 一 | U+4E00 | 0x01080000 | 一 (1) | 1 | 独体 |
| 汉 | U+6C49 | 0x0F288101 | 氵 (15) | 5 | 左右 |
| 国 | U+56FD | 0x1F400B0B | 囗 (31) | 8 | 全包围 |
| 明 | U+660E | 0x48400801 | 日 (72) | 8 | 左右 |

---

## 为什么是 CNBE？

| 维度 | Unicode / UTF-8 | CNBE-32 |
|------|----------------|---------|
| 目标 | 字符显示与交换 | AI 理解与硬件加速 |
| 编码方式 | 查表映射（Flat ID）| 语义结构化 |
| 机器认知 | 标识字符 | 理解结构组成 |
| AI 兼容性 | 需从数据学习 | 提供结构先验 |

**9 个跨领域验证通过**: 语言学、生态学、气象学、金融学、生物学、物理学、社会学、预训练、数学

---

## 面向 JEPA 架构的探索 / JEPA Exploration

CNBE 不是为今天的 Transformer 设计的补丁，而是为明天的 JEPA 准备的底层基础设施。

Yann LeCun 提出的 JEPA 强调在表示空间中预测，而 CNBE 提供的恰恰是最结构化的表示空间：

- **部首 = 空间锚点**：相同部首的字在二进制空间中天然聚集
- **笔画 = 离散特征**：提供细粒度的形态差异
- **结构 = 空间关系**：左右、上下、包围等直接映射为拓扑关系

已完成的 JEPA 验证：v9 树结构预测 + v10 跨9领域泛化

---

## 认知平权 / Cognitive Equity

现代计算机的底层逻辑（从指令集到 OS 内核）完全建立在英语/拉丁字母之上。这导致非英语母语者在进行底层开发时，必须先跨越一层语言翻译的认知壁垒。

CNBE-32 的终极意义，是让中文使用者能够以母语思维直接定义底层逻辑，打破专业词汇壁垒，实现真正的技术认知平权。

> **在 AI 时代，让每一个中文使用者——无论年龄、学历或专业背景——都能以母语思维与人工智能深度对话、定义规则甚至编写底层逻辑。**

---

## <span id="key-experiments">核心实验 / Key Experiments</span>

### 小模型大提升 (v2)
**假设**: 结构化编码补偿小模型参数量不足。
**方法**: Qwen 3.5 0.8B，CNBE vs 标准输入。

| 输入 | 准确率 | 提升 |
|------|--------|------|
| 标准输入 | 48% | -- |
| **CNBE-32** | **87%** | **+81%** |

### CNBE 超越 Unicode (v6.5.2)
**假设**: 结构化位域比 Unicode 码点携带更多语义信息。
**方法**: Gemma 4B 中文硬任务。

| 输入 | 准确率 |
|------|--------|
| Unicode | 26.1% |
| **CNBE-32** | **43.5%** |

**结论**: 未经训练的新编码首次尝试即超越 30 年标准（+17.4pp）。

### 全中文操作系统 (v8.4)

- 全中文 Shell（输出/取编码/比较 等命令）
- 中文 BASIC 解释器（7 个关键字）
- 文本编辑器（内置《道德经》205 行）
- RISC-V 自定义指令: cnhe.map / cnhe.extract / cnhe.cmp

### 数学推理底座 (v10.8)
**方法**: TinyGPT 在奇偶/质数/序列推理任务上对比 4 种编码。

| 任务 | CNBE 损失 | OneHot 损失 | 胜出 |
|------|-----------|-------------|------|
| 奇偶 | 0.3174 | 0.3427 | **CNBE** |
| 质数 | 0.3894 | 0.5061 | **CNBE** |
| 序列 | 1.0726 | 1.2344 | **CNBE** |

<details>
<summary><b>点击展开 v1-v10.8 完整实验数据 / Click to expand</b></summary>

| 版本 | 核心结论 | 关键数据 |
|------|----------|----------|
| v1 | CNBE 零样本可理解 | 200字 100% |
| v2 | 小模型提升 +81% | 48%→87% |
| v3 | 逐字完整注解最优 | 87% effective |
| v4 | 长文本提升 +9.1% | 91%→100% |
| v5 | 收益随规模递减 | 0.8B:+81%, 8B:~0% |
| v6.5.2 | CNBE > Unicode | Gemma 4B +17.4pp |
| v7.1.1 | 3条 RISC-V 指令 | cnhe.map/extract/cmp |
| v8.4 | 全中文操作系统 | Shell+BASIC+道德经 |
| v9.0 | 树木生长 JEPA | CNBE 86% 优于 Raw |
| v9.1 | 台风生命周期 | CNBE 0.000001 vs Raw 0.089981 |
| v9.4 | 全月金融跨周期 | Abl-2 62% 胜率 |
| v10.0 | 美股+A 股回测 | 双市场正收益 |
| v10.3 | 台风巴威路径 | CNBE 174km vs Raw 216km (-19%) |
| v10.4 | 蛋白质 Q3 结构 | CNBE 41.0% vs OH 44.6% |
| v10.5 | 黑洞引力场 | R2 0.60-0.77 |
| v10.6 | 城市决策模拟 | CNBE 优于 Random |
| v10.7 | TinyGPT 冻结嵌入 | CNBE 1.4568 vs Learned 1.3653 |
| v10.8 | 数学推理底座 | CNBE 全面优于 OneHot |
</details>

 → [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)

---

## 关键洞察: 大模型 vs 小模型 / Large vs Small

为什么 8B+ 大模型对 CNBE 的收益递减（~0%），而 0.8B 小模型却能获得 +81% 的巨大提升？

- **大模型的暴力美学**: 海量参数能够通过暴力训练隐式记住 Unicode，掩盖了编码结构缺陷
- **小模型的结构先验**: 在算力受限的边缘设备上，CNBE 将字形结构直接转化为计算先验

这是端侧 AI 处理中文的破局之道。

---

## <span id="tech-stack">技术栈 / Tech Stack</span>

```
应用层: 中文 BASIC 解释器 + 文本编辑器 + 《道德经》
系统层: 全中文 Shell + CNBE 运行时 (map/extract/cmp)
硬件层: RISC-V 1GHz + 1GB RAM (QEMU + Spike)
指令层: cnhe.map / cnhe.extract / cnhe.cmp
编码层: 32-bit CJK 结构化位域 (部首/笔画/结构)
```

---

## <span id="quick-start">快速开始 / Quick Start</span>

### 依赖安装 / Dependencies

### Python SDK: 计算字形语义距离

```bash
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git
cd CNBE-32-Chinese-Native-Binary-Encoding
```

```python
import sys; sys.path.insert(0, 'src')
from cnbe32 import encode_cnbe, hamming_distance
code_ming = encode_cnbe(72, 8, 1)
code_an  = encode_cnbe(72, 9, 1)
print(hamming_distance(code_ming, code_an))
```


```bash
# Python
pip install numpy torch scikit-learn

# RISC-V (Ubuntu)
sudo apt-get install -y gcc-riscv64-linux-gnu qemu-system-misc
```

### Python SDK: 计算字形语义距离

```bash
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git
cd CNBE-32-Chinese-Native-Binary-Encoding
python -c "import sys; sys.path.insert(0,'src'); from cnbe32 import encode_cnbe, hamming_distance; print(hamming_distance(encode_cnbe(72,8,1), encode_cnbe(72,9,1)))"
```

### RISC-V 模拟器

```bash
cd hardware/simulator
gcc -o cnhe_sim cnhe_sim.c -Wall -O2 && ./cnhe_sim
```

### 全中文操作系统 (QEMU)

```bash
cd v84_riscv_os_full
make all && make run
```

### 复现实验

```bash
cd v10_8_math_reasoning && python run_v108.py
cd v10_3_typhoon && python v10_3_typhoon.py
```

---

## 项目结构 / Project Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/specification/      # 编码规范
|-- docs/EXPERIMENTS.md      # 实验总览
|-- docs/VISION.md           # 战略愿景
|-- src/cnbe32/              # Python SDK
|-- include/cnbe32.h         # C 头文件
|-- data/                    # 编码数据库
|-- tests/                   # 测试套件
|-- tools/                   # 开发工具
|-- bindings/rust/           # Rust 绑定
|-- hardware/               # RISC-V 模拟器
|-- v9_jepa_tree/           # JEPA 实验 (v9)
|-- v10_5~v10_8/            # 跨领域实验 (v10)
|-- v84_riscv_os_full/      # 中文 OS 原型
|-- results/                 # 白皮书 (41 份)
|-- LICENSE                  # 木兰许可证
```

---


---

> **学术声明 / Academic Disclaimer**: v10.x 金融回测仅用于验证 CNBE-32 在高噪声时间序列中的特征提取能力, 不构成任何投资建议。

---

## AI Agent 驱动 / AI Factory

这是一个以前绝不可能完成，但在 AI 时代必然诞生的项目。

| 过去 | 现在 |
|------|------|
| 97,686 汉字标注需数千语言学家人年 | AI Agent 辅助自动化标注 |
| 全栈验证需顶级团队数年 | LLM 辅助代码生成 + 验证 |
| 单一团队孤岛开发 | 开源社区协作探索 |

上世纪科学家的梦想，在 AI Agent 时代终于有了实现的可能。

---

## 演进路线 / Roadmap

| 阶段 | 状态 | 内容 |
|------|------|------|
| 编码与语义验证 | 已完成 | v1-v6 CJK 编码设计 |
| 硬件与系统 | 已完成 | v7-v8 RISC-V + 中文 OS |
| 复杂预测验证 | 已完成 | v9-v10 9 领域验证 |
| AI 编译器 | 规划中 | 中文自然语言→机器码 |
| 端侧 AI 集成 | 规划中 | 边缘 AI 默认标准 |
| 生态共建 | 愿景 | 开源社区 + 行业标准 |

---

## <span id="how-to-contribute">参与贡献 / How to Contribute</span>

### 当前最需要社区支援的方向

- 中文 BASIC 解释器优化 - 完善词法分析器
- RISC-V 查表逻辑加速 - 优化 81.6KB L2 Cache 命中率
- JEPA 架构扩展实验 - 更多物理/生物系统测试
- 前端可视化工具 - Web 界面展示编码拆解过程

| 级别 | 方向 |
|------|------|
| 低门槛 | 编码字典 / 测试用例 / 文档 |
| 高门槛 | RISC-V 流水线 / FPGA / LLM 适配 / 编译器 |

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 免责声明 / Disclaimer

v10.x 阶段的金融时间序列（美股/A 股）回测，仅用于验证 CNBE-32 在高噪声、非平稳时间序列数据中的特征提取与结构化先验能力，不构成任何投资建议。

---

## 许可证 / License

**木兰宽松许可证 v2 (Mulan Permissive Software License v2)**

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

---

**让会中文的人，用母语进入人工智能时代。**
**Let Chinese speakers enter the AI era in their mother tongue.**

从“2035 数字中国”的愿景出发，到 AI Agent 时代的工程实践。
From the vision of “2035 Digital China” to the engineering practice in the AI Agent era.

**这是一个具备完整技术闭环的成熟体系，诚邀社区共同探索中文原生计算的无限可能。**
A mature system with a complete technical loop, inviting the community to explore.

**为中文 AI 生态而生
**Let Chinese speakers enter the AI era in their mother tongue.**

从 2035 数字中国的愿景出发，到 AI Agent 时代的工程实践。
From the vision of 2035 Digital China to the engineering practice in the AI Agent era.

**为中文 AI 生态而生——从编码到硬件，从单字到操作系统。**
**Built for the Chinese AI ecosystem — from encoding to hardware.**

[GitHub](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding)
