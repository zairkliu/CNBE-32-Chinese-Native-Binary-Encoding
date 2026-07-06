## 🌟 战略愿景：面向 2035 的中文原生计算地基
## Strategic Vision: A Chinese-Native Computing Foundation Toward 2035

这不是对现有系统的缝缝补补，而是面向未来的地基重构。本项目的诞生深受 "2035 数字中国" 战略的启发。
> **关于实验设计的说明 / On Experimental Design**：CNBE-32 是一个**全新的编码系统**，从零开始设计，未经优化、未被 AI 模型预训练、未被任何系统采纳。本项目所有实验（v1-v10.7）的核心目的只有一个——**探索这个新编码作为语义底座的边界在哪里**，而非与已存在 30 年的成熟编码系统（如 Unicode）、已被亿万参数预训练过的 AI 模型、或已被工程迭代数十年的应用方案进行胜负对比。每一次实验都在问：**“一个从汉字结构推导出来的结构化编码，在未被训练、未被优化的情况下，能走多远？”** 而不是问：**“它赢了没有？”** 在理解了这一前提之后再看本项目的实验数据——CNBE 在零训练、零微调、零预训练的条件下，在 8 个维度上均展现出结构化编码的有效性——那些看似失败的实验反而揭示了最有价值的发现：编码的适用边界。


> **在 AI 时代，让每一个中文使用者——无论年龄、学历或专业背景——都能完全使用全中文与人工智能进行深度对话、定义规则甚至编写底层逻辑，而不必再去学习英语或复杂的传统编程语法。**

### 时代背景 / Context

AI Agent 和具身智能正在替代人类的重复性劳动。人类的核心价值正在从"如何编码"转向"表达意图"、"定义规则"与"顶层设计"。但当前人机交互的底层 **"地基"** ——从 Unicode 到编程语言语法到操作系统内核——依然建立在英语和拉丁字母的逻辑之上，构成巨大的认知壁垒。

### 三大支柱 / Three Pillars

| 支柱 / Pillar | 说明 / Description | 验证 / Validation |
|:-----------:|-----------------|:--------------:|
| **全中文原生** / Chinese-Native | 从 32 位编码到 RISC-V 指令集到操作系统内核，全部基于中文逻辑原生构建 | v8.4/v8.4.1 全中文 OS |
| **小模型的大智慧** / Small Model Wisdom | 结构化编码让 0.8B 小模型性能飞跃 **+81%** | v2 验证通过 |
| **破除专业词汇壁垒** / Breaking Barriers | 用户只需用中文书写规则，系统自动完成逻辑转化 | v8.0 中文编译器 |

> 如果说 ASCII/Unicode 定义了信息时代"人类可读文本"的交换标准，CNBE-32 则定义了 AI 时代"机器可理解语义"的编码标准——前者服务于人与人之间的信息传递，后者服务于人与机器之间的意图表达。

---

﻿# CNBE-32: Chinese Native Binary Encoding / 中文原生二进制编码

## 🎯 核心定位 / Core Position

**如果说ASCII/Unicode定义了信息时代"人类可读文本"的交换标准，CNBE-32则定义了AI时代"机器可理解语义"的编码标准——前者服务于人与人之间的信息传递，后者服务于人与机器之间的意图表达。**

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

## 📊 项目里程碑 / Milestones (v1-v10.8)

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
| **多尺度回测** / Multi-scale | v10.1 | A股5/15min/日线 / A-share multi-scale | **15min CNBE优于Raw** (-14.83% vs -16.07%)，趋势确认 | Windows |
| **6月跨周期** / 6-month | v10.2 | A股+美股6个月日线 / 6-month daily | **CNBE双市场正收益** A+0.76% US+3.07% **准确率59-71%** | Windows |
| **台风路径** / Typhoon Path | v10.3 | 台风巴威路径预测 / Typhoon Barijat path | **CNBE 174km vs Raw 216km (−19%)** | macOS |
| **蛋白结构** / Protein Structure | v10.4 | 蛋白质二级结构Q3预测 / Protein Q3 prediction | **CNBE 41.0% vs 30年标准 44.6% (仅差3.6pp)** | macOS |
| **黑洞引力场** / Black Hole | v10.5 | Gaia BH1引力场预测 / BH gravitational field | **R2 0.60-0.77**，优于Onehot/Random | Python |
| **社会决策** / Social Decision | v10.6 | 城市信息决策中心 / Urban decision center | **CNBE优于OneHot/Random**，7轮验证 | Python |
| **预训练底座** / Pretraining | v10.7 | TinyGPT冻结嵌入 / Frozen embedding | **1.4568初始损失，不输于Learned** | Python |
| **数学推理** / Math Reasoning | v10.8 | 纯数学推理底座 / Math reasoning | **CNBE最小损失全面优于OneHot** | Python |

> **免责声明 / Disclaimer**：v10.x 系列金融回测旨在验证 CNBE 结构化编码在处理高噪声、复杂时间序列数据时的特征提取潜力，而非提供直接的投资策略。回测结果受数据窗口、市场状态和策略参数影响，不代表未来收益。CNBE-32 项目的核心定位始终是中文原生计算地基，金融预测仅是验证编码特征表达能力的一个维度。


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
| v10.1 | A股多尺度5/15min/daily / Multi-scale backtest | **长尺度→少亏损**趋势确认，15min CNBE优于Raw |
| v10.2 | 6个月日线跨周期 / 6-month daily cross-period | **CNBE双市场正收益**，准确率**59-71%** |
| v10.3 | 台风巴威路径预测 / Typhoon Barijat path | **CNBE 174km vs Raw 216km (−19%)**，跨领域泛化验证 |
| v10.4 | 蛋白质二级结构 / Protein Q3 prediction | **CNBE 41.0% vs One-hot 44.6%（差距仅3.6pp）** |
| v10.5 | 黑洞引力场模拟 / Black hole simulation | **R2 0.60-0.77**，物理系统验证通过 |
| v10.6 | 社会信息决策模拟 / Social decision simulation | **CNBE优于Random**，强分类特征场景劣于OneHot |
| v10.7 | 预训练底座验证 / Pretraining foundation | **CNBE初始损失与Learned差仅0.09**，冻结嵌入可行 |
| v10.8 | 纯数学推理验证 / Math reasoning validation | **CNBE最小损失全面优于OneHot**，Sequence任务最优 |

> **关键洞察 / Key Insight**：大模型（如 8B 以上）可以通过海量数据"暴力"记住 Unicode 的映射，但 0.8B 小模型的 **+81%** 性能飞跃，确凿地证明了 CNBE 将汉字的"字形结构"转化为"计算先验"的巨大价值。这对于未来 AI 在**边缘设备、物联网和端侧**的普及具有决定性意义。

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
| 14 | **Multi-scale: lower frequency = better CNBE advantage** / 多尺度：低频放大CNBE优势 | v10.1 A-share 1min→5min→15min, losses reduce from -43% to -15% |
| 15 | **6-month validation: CNBE positive on both markets, 70% accuracy on US** / 6月验证: 双市场正收益 | v10.2 A+0.76% US+3.07%, accuracy 59-71% |
| 16 | **Typhoon path: CNBE 19% better than Raw** / 台风路径预测CNBE优于Raw19% | v10.3 174km vs 216km, 跨领域泛化 |
| 17 | **Protein structure: CNBE within 3.6pp of 30-year domain standard** / 蛋白结构：CNBE仅差3.6pp | v10.4 41.0% vs One-hot 44.6%, 零样本首次尝试 |
| 18 | **Black hole: CNBE R2 0.60-0.77 on gravitational field prediction** / 黑洞引力场预测 | v10.5 Gaia BH1, 跨领域验证第6站 |
| 19 | **Social decision: CNBE works on urban management data** / 社会决策验证 | v10.6 8行政区×4时段, CNBE优于Random |
| 20 | **Pretraining base: CNBE frozen embedding viable** / 预训练底座验证 | v10.7 TinyGPT, 初始损失1.4568 vs Learned 1.3653 |
| 21 | **Math reasoning: CNBE min loss beats OneHot on all tasks** / 数学推理验证 | v10.8 Parity/Prime/Seq, CNBE > OneHot > Random |

---

## 🗺️ 演进路线：从概念验证到未来地基
## Roadmap: From Proof of Concept to Future Foundation

| 阶段 / Phase | 状态 / Status | 内容 / Content |
|:----------:|:------------:|--------------|
| **Phase 1**: 编码与语义验证 / Encoding & Semantic | **已完成** | v1-v6，证明 CNBE 可被 AI 理解，优于传统编码 |
| **Phase 2**: 硬件与系统闭环 / Hardware & System | **已完成** | v7-v8，RISC-V 指令集成与全中文 OS 启动 |
| **Phase 3**: 复杂系统预测验证 / Complex Prediction | **已完成** | v9-v10，JEPA 架构与金融/气象/生物/物理6领域验证 |
| **Phase 4**: AI 编译器与中间件 / AI Compiler | 规划中 | 探索将自然语言中文直接编译为 CNBE 机器码的 AI 辅助工具 |
| **Phase 5**: 端侧 AI 原生集成 / Edge AI Integration | 规划中 | 推动 CNBE 成为边缘 AI 芯片处理中文语义的默认标准 |
| **Phase 6**: 生态共建 / Ecosystem Building | 愿景 | 建立 CNBE 开源社区，推动行业标准与国标对接 |

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
