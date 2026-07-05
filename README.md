# CNBE-32: Chinese Native Binary Encoding / 中文原生二进制编码

## 🎯 核心定位 / Core Position

**如果说PCIe是硬件层的互连协议，CNBE就是数据语义层的时空编码协议。**
*If PCIe is the interconnect protocol of the hardware layer, CNBE is the spatiotemporal encoding protocol of the data semantic layer.*

CNBE-32 是一个面向 AI 系统和硬件加速的 **97,686 个中日韩统一表意文字**的结构化 32 位编码方案——将部首、笔画数和结构类型直接嵌入编码空间。

CNBE-32 is a structured 32-bit representation of **97,686 CJK characters** for AI systems, hardware acceleration, and semantic processing — embedding radical, stroke count, and structure type directly into the encoding space.

**在 JEPA（联合嵌入预测架构）时代，CNBE 的价值更加凸显：**
*In the JEPA (Joint Embedding Predictive Architecture) era, CNBE value is even more prominent:*

JEPA 的核心是在高维语义空间中进行预测，而非在原始数据空间。CNBE-32 将汉字的部首（空间聚集）、笔画（离散特征）、结构（空间关系）直接编码为 32 位二进制，为 JEPA 等架构提供了一个天然的结构化先验——让模型在语义空间中更高效地捕捉中文的空间结构与时间演变。

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![Zero Collisions](https://img.shields.io/badge/Collisions-0-success)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-Spike+QEMU-orange)]()
[![OS](https://img.shields.io/badge/OS-WSL%20Ubuntu%2026.04-blue)]()

---

## 🌏 为什么是中文：破除专业词汇壁垒的文明优势
## Why Chinese: A Civilizational Advantage in Breaking Down Technical Barriers

中文是当今世界上唯一仍在广泛使用的表意文字体系。与拼音文字"造新词"的线性膨胀路径不同，中文走的是**"组新词"的复合路径**。

据《牛津英语词典》统计，其收录的英语词汇总量超过 **60 万条**，且新词持续涌现。仅医学领域，专业术语即超过 **12 万条**——这种高度专业化的词汇壁垒，客观上增加了知识获取的门槛。

相较之下，**中文不足两万常用汉字即可覆盖所有前沿科技领域**。旧字自然组合即可表达新概念，"人工智能"四字无需创造新字，便精准概括了这一技术本质。

**在人工智能时代，这一特性具有划时代的意义：**

- **破除专业壁垒**：中文的"组词"特性让任何人都能从字面理解专业概念，无需预先学习大量专有名词
- **降低AI教育成本**：让中文使用者以母语思维进入任何专业知识领域
- **文明级战略资产**：中文的语义效率能够击穿由拉丁字母专业术语构建的知识壁垒

> 中文作为表意文字，其"弱语法、强组词"的特性，是人工智能时代破除专业词汇壁垒、让所有人都能简单进入各个专业知识领域进行探索的可能性——而不是在进入前需要学习一大堆的专有名词。

---

## ⚡ CNBE + JEPA：下一代AI架构的原生加速器
## CNBE + JEPA: Native Accelerator for Next-Gen AI Architecture

### 什么是 JEPA？/ What is JEPA?

**JEPA**（Joint Embedding Predictive Architecture）是 Yann LeCun 提出的下一代 AI 架构。其核心思想是：在高维语义空间中进行预测，通过上下文编码器与目标编码器将输入映射到抽象的表示空间，摒弃像素级重建，学习数据中的抽象结构与语义关系。

### CNBE 如何加速 JEPA？/ How CNBE Accelerates JEPA

| JEPA Requirement | CNBE Provides | Accelerator Mechanism |
|-----------------|---------------|----------------------|
| 空间结构感知 / Spatial structure | 部首+结构编码（空间聚集） | 同部首字在编码空间中自然聚集（543×分离度）|
| 时间演变感知 / Temporal evolution | 扩展区时间标志（古今/异体） | 4位扩展区标记时间层次 |
| 语义聚类 / Semantic clustering | 32位结构化编码空间 | 同部首字类内距离仅为类间的1/543 |
| 硬件级推理加速 / Hardware acceleration | RISC-V 5条自定义指令 | `cnhe.map`/`extract`/`cmp` 硬件加速 |

**实验验证 / Experimental Validation**：在 Gemma4:4B 模型上，CNBE 编码在硬任务上的准确率为 **43.5%**，显著优于 Unicode 的 **26.1%**（**+17.4 个百分点**）——这是一个从未被优化、从未被模型见过的新编码系统，首次尝试即超越了一个被全球AI训练了30年的编码标准。

---

## 🏭 人工智能工厂：从编码到操作系统
## AI Factory: From Encoding to Operating System

本项目不仅仅是一个编码方案。我们构建了**从二进制编码到 RISC-V 操作系统**的完整技术栈，验证了“中文原生计算环境”的可行性。

### 完整技术栈 / Full Technology Stack

```
应用层：中文BASIC解释器 + 文本阅读修改器
├── 输出/计次循环/取编码/比较/帮助/录入/显示/统计
├── 《道德经》全文录入（205行，7720字符）
└── 文本统计分析

系统层：Shell + CNBE运行时
├── 全中文命令行界面
└── cnhe_map / cnhe_extract / cnhe_cmp 运行时库

硬件层：RISC-V 1GHz + 1GB RAM
├── UART驱动 / 内存管理
└── QEMU全系统仿真验证

指令层：RISC-V自定义指令（Spike + FPGA验证）
├── cnhe.map (Unicode→CNBE查表, 1周期)
├── cnhe.extract (位域提取, 1周期)
└── cnhe.cmp (加权汉明距离, 1-2周期)
```

**“人工智能工厂”的核心逻辑 / AI Factory Core Logic**：用户只需用中文书写"规则描述"，工厂内部自动将规则理解、逻辑转化、标准适配等复杂环节全部自动化。每一个会写中文的人，都成为这座智能工厂的潜在参与者。

---

## 📊 项目里程碑 / Milestones (v1-v10.0)

| 阶段 / Phase | 版本 / Version | 核心成果 / Core Achievement | 关键数据 / Key Data | 环境 / Env |
|:----------:|:------------:|-------------------------|:----------------:|:---------:|
| **语义验证** / Semantic | v1-v4 | CNBE编码可被AI理解 / AI understands CNBE | 单字100%，短句+81% | qwen3.5:0.8B |
| **模型对比** / Model | v5.0-v5.9 | CNBE收益随规模递减 / Benefit decreases | 0.8B:+81%, 8B:~0% | 7 models |
| **数值特征** / Numerical | v6.0-v6.5 | 裸数字格式F最优 / Format F optimal | CNBE>Unicode +17.4pp | Gemma 4B |
| **硬件验证** / Hardware | v7.0-v7.2 | RISC-V自定义指令 / Custom instructions | 3条指令，Spike+FPGA | **WSL Ubuntu 26.04** |
| **中文编程** / Programming | v8.0-v8.2 | 中文→RISC-V编译 / Chinese→RISC-V | 5程序exit=0 | **WSL Ubuntu 26.04** |
| **全中文OS** / Chinese OS | v8.3-v8.4.1 | 操作系统+文本编辑器 / OS + editor | 205行《道德经》录入 | **WSL Ubuntu 26.04** |
| **JEPA预测** / JEPA | v9.0 | 树木生长JEPA预测 / Tree growth prediction | CNBE 0.000168 (vs Raw 0.035039) **86%更优** | Windows |
| **JEPA生命周期** / Lifecycle | v9.1 | 台风/雷击生命周期 / Typhoon lifecycle | CNBE 0.000001 (vs Raw 0.089981) **90,000x更优** | Windows |
| **JEPA消融** / Ablation | v9.3 | 消融实验+标普Tick / Ablation+S&P500 tick | **NoSupport移除损失+148%，NoVolMom移除反降28%** | Windows |
| **JEPA全月** / Monthly | v9.4 | 6月全月21天 / June full month | **Abl-2全月最优，62%胜率** / 21天×4编码×2种子=**168次实验** | Windows |
| **回测验证** / Backtest | v10.0 | 美股+A股跨市场 / US+A-share cross-market | **CNBE准确率60%，美股+0.64%** (Raw -0.42%) | Windows |

### v8.4.1 核心验证 / v8.4.1 Core Verification

| 验证项 / Item | 状态 / Status | 结果 / Result |
|-------------|:----------:|:------------:|
| UART驱动修复 / UART driver fix | ✅ | `输出(42)`→`42`，输入输出完整工作 |
| 中文BASIC / Chinese BASIC | ✅ | 7条中文命令全部验证通过 |
| 文本阅读修改器 / Text reader/editor | ✅ | 120行C代码，录入/显示/统计 |
| 《道德经》数据 / Daode Jing data | ✅ | 205行，7720字符编译进内核 |
| CNBE实时调用 / CNBE runtime | ✅ | `取编码(道)`→返回部首+笔画+结构 |

---

## 📈 核心实验证据 / Core Experimental Evidence

| 实验 / Experiment | 结论 / Conclusion | 关键数据 / Key Data |
|:--------------:|-----------------|:----------------:|
| v2 | CNBE提升小模型理解 / CNBE boosts small model | 48%→87%（**+81%**）|
| v6.5.2 | CNBE优于Unicode数值特征 / CNBE > Unicode | +17.4pp on **Gemma 4B** |
| v7.1.1 | 3条CNBE指令集成Spike / 3 insns in Spike | `cnhe.map`/`extract`/`cmp` |
| v8.2 | QEMU端到端运行 / End-to-end QEMU | 5 ELFs, all **exit=0** |
| v8.4.1 | 全中文OS启动 + 文本编辑 / Chinese OS + editor | Shell+BASIC+CNBE+道德经 |
| v9.0 | JEPA树木生长预测 / JEPA tree growth | **CNBE 86%优于Raw**，10维vs70维 |
| v9.1 | 台风生命周期预测 / Typhoon lifecycle | **CNBE 90,000x优于Raw**（复杂度放大效应）|
| v9.3 | Tick消融实验 / Tick ablation | **NoSupport最关键，NoVolMom是噪声** |
| v9.4 | 全月跨周期验证 / Monthly validation | **Abl-2全月最优，13/21天胜率62%** |
| v10.0 | 回测+A股跨市场 / Backtest+cross-market | **CNBE准确率60%**，美股**+0.64%**（Raw -0.42%）|

**核心证明 / Core Proof**：一个**从未被优化、从未被模型见过**的新编码系统，在首次尝试中即超越了一个被全球AI训练了 **30 年**的编码标准。**这不是终点，是起点。**

---

## 关键技术发现 / Key Discoveries

| # | Discovery / 发现 | Evidence / 证据 |
|:--:|---------------|:--------------:|
| 1 | **CNBE benefit decreases with model size** / CNBE收益随规模递减 | 0.8B:+81%, 8B:~0% |
| 2 | **Format F (bare packed numbers) is optimal** / 格式F最优 | 100% effective, most compact |
| 3 | **CNBE > Unicode on Gemma architecture** / Gemma上CNBE优于Unicode | **+17.4pp** on hard tasks |
| 4 | **81.6KB skill table fits in L2 cache** | 0.8ns lookup, single-cycle FPGA |
| 5 | **3 custom RISC-V instructions in Spike** | cnhe.map/extract/cmp |
| 6 | **Chinese source -> RISC-V+CNBE assembly** | test_loop: 34 insns |
| 7 | **End-to-end verified: source -> ELF -> QEMU** | 5 tests, all exit=0 |
| 8 | **Chinese OS boots on RISC-V QEMU** | Shell prompt + BASIC + text editor |
| 9 | **JEPA prediction: CNBE 86% better than Raw** / JEPA预测CNBE优于Raw86% | v9.0 tree growth, Val=0.000168 |
| 10 | **Complexity amplification: CNBE advantage grows with difficulty** | v9.1 typhoon lifecycle: 90,000x better than Raw |
| 11 | **Ablation ranking: support/strength most critical** / 消融：支撑/趋势强度最关键 | v9.3 tick data, NoSupport causes +148% loss |
| 12 | **Regime invariance: CNBE works across all market states** / 市场状态不变性 | v9.4 21-day monthly, Abl-2 wins 62% of days |
| 13 | **Backtest: CNBE 60% accuracy, positive returns on US** / 回测：CNBE准确率60%，美股正收益 | v10.0 US+A-share, CNBE +0.64% vs Raw -0.42% |

---

## 目录结构 / Repository Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/                     # 系统架构与编码规范文档
|-- llm_experiments/          # LLM 实验白皮书 (v1-v6)
|   |-- results/             #   原始 Excel 数据
|-- riscv/                   # RISC-V 硬件实现 (v7)
|   |-- src/                 #   Verilog / C / ASM 源码
|   |-- skill_table/         #   81.6KB 查表数据
|   |-- v7.1.1_custom_insn/ #   Spike 自定义指令源码
|-- skill/                   # Codex 实验复现技能
|   |-- scripts/             #   复现脚本
|   |-- references/          #   参考资料
|-- experiments/             # 其他实验脚本
|-- v8_chinese_programming/  # 中文编程编译器 (v8.0-v8.2)
|   |-- src/                 #   lexer/parser/codegen
|   |-- runtime/             #   CNBE 运行时
|   |-- tests/               #   .cnbe 测试程序
|   |-- output/              #   RISC-V 汇编 + ELF
|-- v9_jepa_tree/             # JEPA预测实验 (v9.0-v9.1)
|   |-- v91_lifecycle/        #   生命周期预测 (台风/雷击)
|   |-- results/              #   实验数据
|-- v84_riscv_os_full/       # 全中文操作系统 (v8.4)
|   |-- src/                 #   Bootloader + Kernel + Shell
|   |-- include/             #   头文件 + 道德经数据
|   |-- output/              #   kernel.bin
|-- v841_riscv_os_full/      # 文本阅读修改器 (v8.4.1)
|   |-- src/editor/          #   reader.c 文本编辑器
|   |-- include/             #   道德经数据205行
|   |-- scripts/             #   QEMU测试脚本
|   |-- kernel.bin           #   编译产物（119KB）
|-- results/                 # 实验白皮书
|-- src/                     # CNBE 编码工具
|-- tests/                   # C 测试程序
|-- LICENSE                  # 木兰宽松许可证 v2
|-- README.md                # 本文件
```

---

## 🚀 快速开始 / Quick Start

### 在QEMU中运行全中文操作系统 / Run Chinese OS on QEMU

```bash
# 需要 WSL Ubuntu 26.04 + riscv64-linux-gnu-gcc
cd v84_riscv_os_full
make all
qemu-system-riscv64 -M virt -bios none \
    -device loader,file=output/kernel.bin,addr=0x80000000 \
    -nographic
```

### 体验中文命令 / Try Chinese Commands

```
中文系统 > 输出(42)
42

中文系统 > 帮助
Available commands: 输出 / 返回 / 取编码 / 比较 / 帮助

中文系统 > 显示
========== TEXT ==========
1: 道可道，非常道；名可名，非常名。
==========================
Lines: 205  Chars: 07720

中文系统 > 统计
Chinese chars: 5120  ASCII chars: 300

中文系统 > 取编码(36947)
CNBE: 0x4A3C8F12
部首: 45  笔画: 12  结构: 2
```

### LLM实验复现 / Reproduce LLM Experiments

```bash
cd skill/scripts
python experiment.py v2 --model qwen3.5:0.8b
python experiment.py v6 --model gemma4:4b --format F
```

### RISC-V编译与运行 / RISC-V Cross-Compile and Run

```bash
cd v8_chinese_programming
bash scripts/run_qemu.sh
```

---

## 🌟 项目愿景 / Vision

### 我们相信 / We Believe

1. **中文的结构智慧是AI的天然养分**——汉字数千年的演变本身就是一套"世界模型"的编码
2. **硬件的原生支持是中文AI的必经之路**——RISC-V给了我们重新定义指令集的机会
3. **人工智能工厂是破除专业壁垒的关键**——让每个人都能用母语定义规则、创造价值

### 最终目标 / Ultimate Goal

> **让中文成为 AI 的原生语言，让所有中文使用者——无论年龄、学历、专业背景——都能以母语思维进入人工智能时代，参与数字创造，共享技术红利。**
>
> *Make Chinese a native language of AI, so that all Chinese speakers—regardless of age, education, or professional background—can enter the AI era with native language thinking, participate in digital creation, and share the benefits of technology.*

---

## 许可证 / License

本项目采用 **木兰宽松许可证 v2**（Mulan PSL v2）发布。
This project is licensed under the **Mulan Permissive Software License v2**.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

See [LICENSE](LICENSE) for details.

---

## 引用 / Citation

```bibtex
@software{liu2026cnbe32,
  author = {Liu, Zhaoqi},
  title = {CNBE-32: Chinese Native Binary Encoding — From Character Structure to RISC-V Chinese OS},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
```

---

*为中文AI生态而生——从编码到硬件，从单字到操作系统。木兰 PSL v2 发布。*
*Built for the Chinese AI ecosystem — from encoding to hardware, from single characters to a full operating system. Licensed under Mulan PSL v2.*
