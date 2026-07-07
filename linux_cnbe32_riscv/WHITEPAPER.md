# CNBE-32 Linux RISC-V 技术白皮书

## 项目定位

本项目是将 **Linux 0.01**（1991年 Linus Torvalds 发布的第一个 Linux 内核版本）从 x86 架构转译为 **RISC-V 64 + CNBE-32 中文原生二进制编码** 版本的技术探索性实验。

## 声明

> **本项目由 AI Agent（基于 GPT-5 的 Codex）自动生成，纯属技术探讨与概念验证。**
>
> - ❌ **未经任何 RISC-V 硬件或 QEMU 模拟器实机测试**
> - ❌ **在当前状态下无法编译通过**，存在多处架构不一致和编码问题
> - ❌ **不适用于生产环境或任何实际部署**
> - ✅ 作为 **CNBE-32 中文编码 + 全中文操作系统** 的概念验证和架构参考

## 项目背景

### CNBE-32 编码方案

CNBE-32（Chinese Native Binary Encoding）是一种将汉字编码为 32 位结构化位域的编码方案：

```
[31:24] 部首区 (8bit) | [23:19] 笔画区 (5bit) | [18:15] 结构区 (4bit)
[14:4]  字库区 (11bit) | [3:0]   扩展区 (4bit)
```

每个汉字被编码为部首、笔画、结构的三维语义向量，使得汉字之间可以计算语义距离。

### Agent 转译过程

项目代码由 AI Agent 通过以下流程自动生成：

1. **Stage 1**: 建立共享基础设施（CNBE-32 运行时、链接脚本、构建系统）
2. **Stage 2**: 并行子系统转译（Boot、Init、Kernel、MM、FS、LIB 等共 9 个子系统）
3. **Stage 3**: 集成合并与依赖检查

每一行代码均由 AI 大语言模型生成，未经过人工审查或验证。

## 技术架构

### 系统层次

```
应用层: 中文 BASIC 解释器 + 中文编译器 + 道德经
系统层: 全中文 Shell + CNBE-32 运行时 (map/extract/cmp)
编译器: 词法分析 → 递归下降解析 → 字节码生成 → 栈式VM执行
编码层: 20902 CJK 汉字 × 32位结构化位域 (部首/笔画/结构)
硬件层: RISC-V 1GHz + 32MB L3 + 1GB RAM (QEMU virt 目标)
```

### 核心组件

| 组件 | 功能 | 代码量 |
|------|------|--------|
| CNBE-32 运行时 | Unicode↔CNBE 映射、部首/笔画/结构位域提取、语义距离计算 | ~3.8KB |
| 中文 BASIC 解释器 | 16 个中文关键字、中文变量名、程序模式、用户函数 | ~54KB (1748行) |
| 中文编译器 | 词法分析→递归下降解析→字节码→栈式虚拟机，27条指令 | ~46KB (1315行) |
| 全中文 Shell | 交互式命令行界面，中文> 提示符 | ~3.5KB |
| 272KB 编码表 | 20902 个 CJK 汉字的完整 CNBE-32 编码 | 272KB |

### 文件统计

| 类型 | 数量 | 行数 |
|------|------|------|
| C 源文件 | 49 | ~9,886 |
| 汇编文件 | 6 | ~1,852 |
| 头文件 | 36 | ~7,354 |
| 编码表 | 1 | 20,902 条目 |
| **总计** | **91** | **~19,092** |

## 已知问题

以下是本项目中已识别但尚未修复的关键问题：

| # | 问题 | 影响 | 位置 |
|---|------|------|------|
| 1 | **编码损坏** — 部分文件的中文注释以 GBK/ANSI 编码保存，导致乱码 | 所有支持中文流程 | `sched.c`, `hd.c`, `exit.c`, `memory.c` 等 |
| 2 | **Sv32 vs Sv39 不一致** — `mm/memory.c` 使用 32位页表，boot 使用 Sv39 64位页表 | 内存管理完全失效 | `mm/memory.c` vs `boot/start.S` |
| 3 | **错误指令宽度** — `SAVE_CONTEXT` 使用 `sw`/`lw`（32位），但目标是 RV64 | 编译报错 | `include/asm/system.h` |
| 4 | **未实现的 trap handler 函数** — `riscv_set_trap_handler` 声明但未定义 | 链接失败 | `include/asm/system.h` → `kernel/traps.c` |
| 5 | **`move_to_user_mode` 不完整** — 缺少 mepc 设置和 SATP 切换 | 用户模式无法进入 | `include/asm/system.h` |
| 6 | **`include/linux/head.h` 为空壳** | 编译问题 | `include/linux/head.h` |
| 7 | **无块设备驱动** — `hd.c` 有请求层但无 virtio 后端 | 无法挂载文件系统 | `kernel/hd.c` |
| 8 | **时间初始化不可靠** — 简化实现不与 QEMU RTC 同步 | 时间不准 | `init/main.c` |
| 9 | **`cnbe_compiler.c` 错误引用头文件** — 使用相对路径而非系统路径 | 编译警告/错误 | `kernel/cnbe_compiler.c` |

## 构建指南（仅供参考）

> 以下命令仅为展示，当前代码无法在未经修复的情况下编译通过。

```bash
# 安装 RISC-V 交叉编译器
sudo apt-get install gcc-riscv64-linux-gnu qemu-system-misc

# 编译
cd linux-cnbe32-riscv
make all

# 在 QEMU 中运行
make run
```

## 许可证

- 原始 Linux 0.01 代码：由 Linus Torvalds 于 1991 年发布，遵循 GNU GPL v2
- CNBE-32 编码方案与编码表：遵循 Mulan PSL v2
- 本项目生成的转译代码：GNU GPL v2（继承自原始 Linux 0.01）

## 致谢

- Linux 0.01 by Linus Torvalds (1991)
- CNBE-32 中文原生二进制编码项目
- RISC-V 国际基金会开源 ISA 规范
- OpenAI GPT-5 / Codex Agent 自动生成

---

**让会中文的人，用母语进入操作系统底层。**  
*——但请注意，这只是一个 AI Agent 生成的实验性概念验证。*
