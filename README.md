# CNBE-32: Chinese Native Binary Encoding / 中文原生二进制编码

A structured 32-bit representation of **97,686 CJK characters** for AI systems, hardware acceleration, and semantic processing — embedding radical, stroke count, and structure type directly into the encoding space.

一种面向 AI 系统和硬件加速的 **97,686 个中日韩统一表意文字**的结构化 32 位编码方案——将部首、笔画数和结构类型直接嵌入编码空间。

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![Zero Collisions](https://img.shields.io/badge/Collisions-0-success)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-Spike+QEMU-orange)]()
[![OS](https://img.shields.io/badge/OS-WSL%20Ubuntu%2026.04-blue)]()

---

## 项目简介 / Overview

CNBE-32 是一个面向中文 AI 的原生二进制编码方案，将汉字的结构特征（部首、笔画、结构）直接编码到 32 位空间中，使得编码本身即可被 AI 模型和硬件系统直接解析。

与 Unicode 的纯索引定位不同，CNBE-32 的编码空间具有语义结构——两位编码相近的汉字在部首、笔画或结构上具有相似性。v1-v8.4 系列实验完整验证了从单字识别到 RISC-V 全中文操作系统的 30+ 个子实验。

**RISC-V 实验环境**：所有硬件相关实验在 **WSL Ubuntu 26.04 LTS** 上完成，使用预装的 riscv64-linux-gnu-gcc 15.2.0 工具链和 qemu-system-riscv64 10.2.1 模拟器。

CNBE-32 is a native binary encoding scheme for Chinese AI that embeds character structural features (radical, stroke, structure) directly into 32-bit code space.

**RISC-V Environment**: All hardware experiments run on **WSL Ubuntu 26.04 LTS** with pre-installed riscv64-linux-gnu-gcc 15.2.0 and qemu-system-riscv64 10.2.1.

---

## 关键指标 / Key Metrics

| Metric | Value | Notes |
|---|---|---|
| Total characters / 总字符数 | **97,686** | CJK Unified + Extensions A-I |
| Encoding collisions / 编码冲突 | **0** | Strategy B verified |
| Kangxi radicals / 康熙部首 | **214/214** | 8-bit radical field, 100% |
| Structure types / 结构类型 | **9+** | Single, Left-Right, Up-Down, enclosures |
| Skill table size | **81.6 KB** | 20902 entries, L2 cache-fit |
| Spike custom instructions | **3** | cnhe.map, cnhe.extract, cnhe.cmp |
| FPGA lookup | **1 cycle** | BRAM-based, single-cycle |
| OS boot verified | **QEMU RISC-V** | Chinese BASIC shell prompt |

---

## 实验证据链 / Experiment Chain (v1-v8.4)

All experiments are reproducible. Environment: Python 3.14+ for LLM tests, WSL Ubuntu 26.04 for RISC-V. Each experiment has a published white paper in the repo.

### v1-v4: 编码语义验证 / Encoding Semantic Validation

| Exp | Task | Key Finding | Data | Model / Env |
|:---:|------|-------------|:----:|:----------:|
| v1 | Single char understanding | CNBE zero-shot understood | 200 chars, 100% | qwen3.5:0.8B |
| v2 | Sentence comprehension | CNBE improves by +81% | 48%->87% | qwen3.5:0.8B |
| v3 | Format optimization | Format A (per-char) best | 87% eff, 9% distr | qwen3.5:0.8B |
| v4 | Long text (On Protracted War) | CNBE helps paper-level text | 91%->100%(+9.1%) | qwen3.5:0.8B |
| v7.3 | Feature space validation | CNBE 3D features parsable | 2/3 hard tasks win | sklearn + numpy |

### v5-v6: 模型对比与数值特征 / Model Comparison

| Exp | Task | Key Finding | Data | Model / Env |
|:---:|------|-------------|:----:|:----------:|
| v5a-v5.9 | 7-model comparison | CNBE benefit decreases with size | 0.8B:+81%, 8B:~0% | 7 models |
| v6.0 | Skill table | 8105 char lookup, 100% correct | 81.6KB, 0.8ns | numpy |
| v6.3-v6.5 | Numerical format | Format F (bare numbers) optimal | 100% effective | qwen3.5:0.8B |
| v6.5.2 | CNBE vs Unicode | CNBE > Unicode on Gemma | +17.4pp | Gemma 4B |
| v6.6 | Hard task comparison | First hard task win vs Unicode | +17.4pp | Gemma 4B |

### v7: RISC-V 硬件验证 / RISC-V Hardware

| Exp | Task | Key Finding | Metric | Environment |
|:---:|------|-------------|:------:|:----------:|
| v7.0 | C language lookup | 0.8ns per lookup | x86 baseline | Windows |
| v7.0.1 | RISC-V cross-compile | QEMU verified at 2.5ns | RISC-V | **WSL Ubuntu 26.04** |
| v7.1 | Custom instruction encoding | .insn SIGILL test passed | encoding verified | **WSL Ubuntu 26.04** |
| v7.1.1 | Spike integration | 3 insns in Spike source | cnhe.map/extract/cmp | **WSL Ubuntu 26.04** |
| v7.2 | FPGA RTL | Verilog simulation passed | 81.6KB BRAM, 1 cycle | Windows |

### v8: 中文编程语言与操作系统 / Chinese Programming & OS

| Exp | Task | Key Finding | Metric | Environment |
|:---:|------|-------------|:------:|:----------:|
| v8.0 | Chinese compiler | Chinese->RISC-V+CNBE mapping | test_loop=34 insns | Windows |
| v8.1 | Skill table integration | All 4 tests compile | test_struct=48 insns | Windows |
| v8.2 | QEMU verification | 5 tests run, all exit=0 | ELFs verified | **WSL Ubuntu 26.04** |
| v8.3 | Chinese OS | RISC-V OS with Chinese BASIC | kernel boots on QEMU | **WSL Ubuntu 26.04** |

---

## 关键技术发现 / Key Discoveries

| # | Discovery | Evidence |
|:--:|-----------|----------|
| 1 | **CNBE benefit decreases with model size** | 0.8B:+81%, 8B:~0% |
| 2 | **Format F (bare packed numbers) is optimal** | 100% effective, most compact |
| 3 | **CNBE > Unicode on Gemma architecture** | +17.4pp on hard tasks |
| 4 | **81.6KB skill table fits in L2 cache** | 0.8ns lookup, single-cycle FPGA |
| 5 | **3 custom RISC-V instructions in Spike** | cnhe.map/extract/cmp |
| 6 | **Chinese source -> RISC-V+CNBE assembly** | test_loop: 34 insns |
| 7 | **End-to-end verified: source -> ELF -> QEMU** | 5 tests, all exit=0 |
| 8 | **Chinese OS boots on RISC-V QEMU** | Shell prompt + BASIC interpreter |

---

## 目录结构 / Repository Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/                     # 系统架构与编码规范文档
|-- llm_experiments/          # LLM 实验白皮书 (v1-v6)
|   |-- v1_v4_validation/    #   基础验证
|   |-- v5_model_comparison/ #   多模型对比
|   |-- v6_numerical_features/ # 数值特征优化
|   |-- results/             #   原始 Excel 数据
|-- riscv/                   # RISC-V 硬件实现 (v7)
|   |-- src/                 #   Verilog / C / ASM 源码
|   |-- skill_table/         #   81.6KB 查表数据
|   |-- v7.1.1_custom_insn/ #   Spike 自定义指令源码
|-- skill/                   # Codex 实验复现技能
|-- experiments/v73/         # v7.3 特征空间验证
|-- v8_chinese_programming/  # 中文编程编译器 (v8.0-v8.2)
|   |-- src/                 #   lexer/parser/codegen
|   |-- runtime/             #   CNBE 运行时 (skill table)
|   |-- tests/               #   .cnbe 测试程序
|   |-- output/              #   RISC-V 汇编 + ELF
|   |-- scripts/             #   QEMU/Spike 运行脚本
|-- v83_riscv_os/            # RISC-V 中文操作系统 (v8.3)
|-- v84_riscv_os_full/       # RISC-V 中文操作系统完整验证 (v8.4)
|   |-- src/boot/            #   Bootloader (start.S)
|   |-- src/kernel/          #   内核入口 (UART + 初始化)
|   |-- src/shell/           #   命令行 Shell
|   |-- src/basic/           #   中文 BASIC 解释器 + CNBE
|   |-- output/              #   kernel.elf + kernel.bin
|   |-- results/             #   QEMU 运行日志
|-- experiments/             # 其他实验脚本
|-- src/                     # CNBE 编码工具
|-- tests/                   # C 测试程序
|-- LICENSE                  # 木兰宽松许可证 v2
|-- README.md                # 本文件
```

---

## 快速开始 / Quick Start

### LLM 实验复现 / Reproduce LLM Experiments

```bash
cd skill/scripts
python experiment.py v2 --model qwen3.5:0.8b
python experiment.py v6 --model gemma4:4b --format F
```

### RISC-V 编译与运行 / RISC-V Cross-Compile and Run

```bash
# 需要 WSL Ubuntu 26.04 + riscv64-linux-gnu-gcc
cd v8_chinese_programming
bash scripts/run_qemu.sh
# 或手动：
python3 src/compiler.py tests/test_loop.cnbe -o output/test_loop.s
riscv64-linux-gnu-gcc -static -O2 output/test_loop.s \
    src/runtime/cnbe_runtime.c -o output/test_loop.elf
qemu-riscv64 output/test_loop.elf
```

### 中文操作系统启动 / Boot Chinese OS on QEMU

```bash
cd v84_riscv_os_full
make all                                    # 编译内核
qemu-system-riscv64 -M virt -bios none \    # 启动
    -device loader,file=output/kernel.bin,addr=0x80000000 \
    -nographic
```

---

## 许可证 / License

本项目采用 **木兰宽松许可证 v2**（Mulan PSL v2）发布。
This project is licensed under the **Mulan Permissive Software License v2** (Mulan PSL v2).

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

See [LICENSE](LICENSE) for details.

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

*为中文 AI 生态而生——从编码到硬件。木兰 PSL v2 发布。*
*Built for the Chinese AI ecosystem — from encoding to hardware. Licensed under Mulan PSL v2.*