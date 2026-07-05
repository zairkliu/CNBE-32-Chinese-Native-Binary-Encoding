# CNBE-32: Chinese Native Binary Encoding / 中文原生二进制编码

A structured 32-bit representation of **97,686 CJK characters** for AI systems, hardware acceleration, and semantic processing — embedding radical, stroke count, and structure type directly into the encoding space.

一种面向 AI 系统和硬件加速的 **97,686 个中日韩统一表意文字**的结构化 32 位编码方案——将部首、笔画数和结构类型直接嵌入编码空间。

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![Zero Collisions](https://img.shields.io/badge/Collisions-0-success)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-601x%20speedup-orange)]()

---

## 项目简介 / Overview

CNBE-32 是一个面向中文 AI 的原生二进制编码方案，将汉字的结构特征（部首、笔画、结构）直接编码到 32 位空间中，使得编码本身即可被 AI 模型和硬件系统直接解析。

与 Unicode 的纯索引定位不同，CNBE-32 的编码空间具有**语义结构**——两位编码相近的汉字在部首、笔画或结构上具有相似性。v1-v7 系列实验完整验证了从单字识别到 RISC-V 硬件实现的 25+ 个子实验。

CNBE-32 is a native binary encoding scheme for Chinese AI that embeds character structural features (radical, stroke, structure) directly into 32-bit code space, making the encoding itself directly parsable by AI models and hardware systems.

Unlike Unicode's pure-index approach, CNBE-32's code space carries **semantic structure** — characters with close codes share radical, stroke, or structural similarity. 25+ sub-experiments (v1-v7) have comprehensively validated the scheme from single-character recognition to RISC-V hardware implementation.

---

## 关键指标 / Key Metrics

| Metric | Value | Notes |
|---|---|---|
| Total characters / 总字符数 | **97,686** | CJK Unified + Extensions A-I, 10 Unicode blocks |
| Encoding collisions / 编码冲突 | **0** | Strategy B verified across all characters |
| Kangxi radicals / 康熙部首 | **214/214** | 8-bit radical field, 100% coverage (Unihan verified) |
| Structure types / 结构类型 | **9+** | Single, Left-Right, Up-Down, enclosures, Pin-Structure |
| Stroke range / 笔画范围 | **1-31** | 5-bit stroke count field (99.82% Unihan verified) |
| Code space utilization / 编码空间利用率 | **0.0023%** | Ample room for future expansion |
| Unihan radical verification | **100%** | 93,672 chars checked against Unicode database |
| GB 18030-2022 comparison | **+9,799 chars** | CNBE covers 11.1% more CJK |

---

## 实验结论 / Experiment Results

### 核心发现 / Key Discoveries

v1 (0.8B): 编码可零样本理解 — 200 单字，100% 有效
v2 (0.8B): 编码提升句子理解 — 48% -> 87%（+81%）
v3 (0.8B): 逐字完整注解最优 — 87% 有效，9% 分心
v4 (0.8B): 论文级长文本有效 — 90.9% -> 100%（+9.1%）
v5a-v5.9 (0.8B-20B): 7 模型横向对比 — 国产 2B 实体 90%
v6.0 (Skill 查表): 8105 字查表 100% — 81.6KB，0.8ns/次
v6.1-v6.2 (0.8B-9B): 多模型长文本对比 — Qwen 4B 为收益拐点
v6.3-v6.5 (0.8B): 数值特征优于文本翻译 — Format F 主优，100%
v6.5.1 (0.8B): 古文验证有效 — 《道德经》100% 有效率
v6.5.2 (0.8B/2B): **CNBE > Unicode** — 结构化编码优势验证
v6.5.3 (0.8B): 硬任务验证 — 繁体/异体/化学方程式
v6.6 (Gemma 4B): **CNBE +17.4pp vs Unicode** — 硬任务首次超越
v7.0 (C): 查表 0.8ns — x86 原生基准
v7.0.1 (RISC-V): QEMU 验证 2.5ns — 交叉编译工具链
v7.1 (Spike): 自定义指令编码验证 — .insn -> SIGILL 测试
v7.1.1 (Spike): **三条指令集成到 Spike 源码** — cnhe.map/extract/cmp
v7.2 (FPGA): Verilog RTL 仿真通过 — 81.6KB BRAM，单周期查表

### 边际收益递减规律 / Marginal Benefit Decay

**核心发现：CNBE 编码的收益随模型规模增大而递减。**

| 模型规模 | 编码收益 | 建议场景 |
|:--------:|:--------:|----------|
| < 1B | 显著（+81%） | 边缘端、教育场景 |
| 1-7B | 中等（+9-17%） | 移动端、轻量部署 |
| > 7B | 趋于 0 | 大模型自身能力充足 |

A key finding: **CNBE's benefit decreases as model size increases.**

| Model Size | CNBE Benefit | Recommended Use |
|:----------:|:------------:|-----------------|
| < 1B | Significant (+81%) | Edge devices, education |
| 1-7B | Moderate (+9-17%) | Mobile, light deployment |
| > 7B | Near 0 | Large models self-sufficient |

### 完整证据链 / Complete Evidence Chain

```
v1  (0.8B)  [单字验证]   ->  编码可被零样本理解
v2  (0.8B)  [句子验证]   ->  编码提升理解能力 48%->87%
v3  (0.8B)  [格式优化]   ->  逐字完整注解最优
v4  (0.8B)  [长文本]     ->  论文级文本有效 90.9%->100%
v5  (0.8B-20B) [多模型] ->  7 模型全量对比
v6  (0.8B-9B)  [数值特征] ->  CNBE > Unicode, 格式 F 最优
v7  (C->RISC-V->Spike->FPGA) [硬件] ->  0.8ns->2.5ns->1cycle
```

All white papers are available under `llm_experiments/` (v1-v6) and `riscv/` (v7).
全部白皮书见 `llm_experiments/`（v1-v6）和 `riscv/`（v7）。

---

## 编码规范 / Encoding Specification

### 32 位编码结构 / 32-bit Code Structure

```
31        24 23       19 18      15 14      10 9        0
+-----------+-----------+----------+----------+----------+
|  Radical  |  Stroke   | Struct.  |  Unused  |   Index |
|  8 bits   |  5 bits   | 4 bits   | 5 bits   |  10 bits|
+-----------+-----------+----------+----------+----------+
  214/214    | 0-31      | 9 types  | Reserved | 0-1023 |
  Kangxi     strokes    structure  for ext.  per-group |
```

| 字段 / Field | 位数 / Bits | 范围 / Range | 说明 / Description |
|-------------|:-----------:|:-----------:|-------------------|
| 部首 / Radical | 8 | 0-213 | 214 个康熙部首 / 214 Kangxi radicals |
| 笔画 / Stroke | 5 | 1-31 | 99.82% 字符覆盖 / 99.82% coverage |
| 结构 / Structure | 4 | 0-8 | 9 种结构类型 / 9 structure types |
| 索引 / Index | 10 | 0-1023 | 组内唯一编号 / Unique ID within group |

---

## 硬件集成 / Hardware Integration

### RISC-V 自定义指令 / RISC-V Custom Instructions

三条自定义指令已集成到 Spike 模拟器中，使用 Custom-0 编码空间（opcode=0x0B）：

| 指令 / Instruction | 功能 / Function | MATCH | MASK | 周期 |
|:-----------------:|----------------|:-----:|:----:|:----:|
| `cnhe.map` | Unicode -> CNBE 查表 | 0x0000000B | 0xFE00707F | 2 |
| `cnhe.extract` | 位域提取（部首/笔画/结构）| 0x0000100B | 0xFE00707F | 1 |
| `cnhe.cmp` | 加权汉明距离计算 | 0x0000200B | 0xFE00707F | 3 |

### 性能基准 / Performance

| 平台 / Platform | 单次查表 / Lookup | 备注 / Notes |
|:--------------:|:----------------:|-------------|
| x86-64 原生 | 0.8 ns | C 语言实现基准 |
| QEMU RISC-V | 2.5 ns | 仿真环境参考值 |
| Spike（周期精确）| ~2 cycle | 自定义指令验证 |
| FPGA（预期）| 1 cycle | 81.6KB BRAM |

### 源码文件 / Source Files

所有硬件实现源码位于 `riscv/src/` 和 `riscv/v7.1.1_custom_insn/`：

| 文件 | 说明 |
|------|------|
| `cnhe_core.v` | Verilog 核心模块（BRAM 查表）|
| `tb_cnhe.v` | Verilog 测试平台 |
| `cnhe_map.h` | Spike cnhe.map 指令行为 |
| `cnhe_extract.h` | Spike cnhe.extract 指令行为 |
| `cnhe_cmp.h` | Spike cnhe.cmp 指令行为 |
| `cnhe_skill_table.{h,cc}` | 81.6KB Skill 查表数据 |
| `test_lookup.c` / `test_cnbe.c` | C 测试程序 |

---

## AI / LLM 集成 / AI / LLM Integration

### 编码注入格式 / Encoding Injection Format

经过 v3 和 v6.3-v6.5 验证的最优格式：

**格式 A（文本注解，通用场景）**：
中(丨,4画,独体)国(囗,8画,全包围)人(人,2画,独体)

**格式 F（裸数字，硬件接口）**：
中0390802 国0480801 人0300202

### 最佳适用场景 / Best Use Cases

| 场景 | 推荐模型 | 预期收益 |
|------|:--------:|:--------:|
| 边缘端识字 | < 1B 模型 | 显著提升 |
| 教育终端 | 1-7B 模型 | 中等提升 |
| 中文 NLU | > 7B 模型 | 边际接近 0 |
| RISC-V 芯片 | 硬件集成 | 单周期查表 |

| Use Case | Recommended Model | Expected Benefit |
|----------|:-----------------:|:----------------:|
| Edge character learning | < 1B models | Significant |
| Education terminals | 1-7B models | Moderate |
| Chinese NLU | > 7B models | Marginal (near 0) |
| RISC-V chips | Hardware integrated | Single-cycle lookup |

---

## 实验详细目录 / Experiment Directory

### LLM 实验 (v1-v6)

`llm_experiments/` 目录包含完整的实验白皮书和原始数据：

| 子目录 | 版本范围 | 核心内容 |
|--------|:--------:|----------|
| `v1_v4_validation/` | v1-v4 | 单字/句子/格式/论文验证 |
| `v5_model_comparison/` | v5-v5.9 | 7 模型横向对比 |
| `v6_numerical_features/` | v6-v6.6 | 数值特征/Unicode对比/硬任务 |
| `results/` | 全部 | 原始 Excel 实验数据（19 个文件）|

### 硬件实现 (v7)

`riscv/` 目录包含从 C 实现到 FPGA 的完整硬件验证：

| 子目录 | 版本 | 核心内容 |
|--------|:----:|----------|
| `v7.0_c_impl/` | v7.0 | C 语言查表基准 |
| `v7.0.1_qemu/` | v7.0.1 | RISC-V 交叉编译 + QEMU |
| `v7.1_spike/` | v7.1 | 自定义指令编码验证 |
| `v7.1.1_custom_insn/` | v7.1.1 | Spike 集成指令源码 |
| `v7.2_fpga/` | v7.2 | Verilog RTL 仿真 |
| `src/` | - | Verilog / C / ASM 源码 |
| `skill_table/` | - | 81.6KB 查表数据 |

---

## 快速开始 / Getting Started

### 使用 Skill 表编码 / Encode with Skill Table

```
import numpy as np

# Load 81.6KB lookup table (8105 chars + extension zones)
table = np.load("riscv/skill_table/skill_table_8105.npy")

def encode(text):
    result = []
    for ch in text.strip():
        idx = ord(ch) - 0x4E00
        if 0 <= idx < len(table) and table[idx] > 0:
            code = int(table[idx])
            radical = (code >> 24) & 0xFF
            stroke = (code >> 19) & 0x1F
            structure = (code >> 15) & 0xF
            result.append(f"{ch}[{radical:03d},{stroke:02d},{structure:02d}]")
        else:
            result.append(ch)
    return "".join(result)

print(encode("你好"))  # Output: 你[009,07,01]好[038,06,01]
```

### RISC-V 交叉编译 / Cross-Compile for RISC-V

```
cd riscv/src
riscv64-linux-gnu-gcc -O2 test_lookup.c -o test_lookup_riscv
qemu-riscv64 ./test_lookup_riscv
```

### Verilog 仿真 / Verilog Simulation

```
cd riscv/src
iverilog -o cnhe_tb cnhe_core.v tb_cnhe.v
vvp cnhe_tb
```

---

## 仓库结构 / Repository Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/                         # 技术文档与设计白皮书
|-- experiments/                  # Python 实验脚本
|-- hardware/                     # Spike v2 补丁 + Verilog CAM
|-- llm_experiments/              # LLM 实验结果（v1-v6，25+ 白皮书）
|   |-- v1_v4_validation/         #   基础验证白皮书
|   |-- v5_model_comparison/      #   多模型对比白皮书
|   |-- v6_numerical_features/    #   数值特征优化白皮书
|   |-- results/                  #   原始 Excel 数据
|   |-- README.md                 #   实验目录说明
|-- riscv/                        # RISC-V 硬件实现（v7）
|   |-- v7.0-v7.2_*/              #   各子实验白皮书
|   |-- src/                      #   Verilog / C / ASM 源码
|   |-- skill_table/              #   81.6KB 查表数据
|   |-- README.md                 #   硬件目录说明
|-- src/                          # CNBE 编码工具
|-- tests/                        # C 测试程序
|-- LICENSE                       # 木兰宽松许可证 v2
|-- README.md                     # 本文件
|-- ...
```

---

## 许可证 / License

本项目采用 **木兰宽松许可证 v2**（Mulan PSL v2）发布。
This project is licensed under the **Mulan Permissive Software License v2** (Mulan PSL v2).

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

See LICENSE for details.

---

## 引用 / Citation

```bibtex
@software{liu2026cnbe32,
  author = {Liu, Zhaoqi},
  title = {CNBE-32: Chinese Native Binary Encoding},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
```

---

**相关链接 / Links**: [LLM 实验目录](llm_experiments/README.md) | [硬件实现目录](riscv/README.md) | [GitHub](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding)

*为中文 AI 生态而生——从编码到硬件。木兰 PSL v2 发布。*
*Built for the Chinese AI ecosystem — from encoding to hardware. Licensed under Mulan PSL v2.*
