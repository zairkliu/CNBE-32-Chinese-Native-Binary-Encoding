# Linux 0.01 CNBE-32 RISC-V

将 Linux 0.01 转译为 **RISC-V 64 + CNBE-32 中文原生二进制编码** 的全中文操作系统内核技术探讨。

> ⚠️ **声明：本项目由 AI Agent 自动生成，未在 RISC-V 硬件或 QEMU 上验证，当前状态无法编译运行。仅供技术探讨和概念验证参考。** 详见 [WHITEPAPER.md](WHITEPAPER.md) 白皮书。

## 项目概述

本项目基于 **CNBE-32 (Chinese Native Binary Encoding)** 编码思路，将 Linux 0.01 (1991年) 从 x86 架构转译为 RISC-V 64 + 全中文系统。

### 四大核心组件

| 组件 | 功能 |
|------|------|
| **CNBE-32 运行时** | Unicode↔CNBE 映射、部首/笔画/结构位域提取、语义距离计算 |
| **中文 BASIC 解释器** | 16 个中文关键字、中文变量名、程序模式、用户函数 |
| **中文编译器** | 词法分析→递归下降解析→字节码生成→栈式虚拟机，27条指令 |
| **全中文 Shell** | 交互式命令行界面 |

### 目标硬件

| 参数 | 规格 |
|------|------|
| 处理器 | RISC-V 1GHz (QEMU virt 平台) |
| 内存 | 1GB RAM |
| L3 缓存 | 32MB (可容纳 81.6KB CNBE 表) |
| 存储 | 1GB Storage |

## 项目结构

```
linux-cnbe32-riscv/
├── boot/start.S          # RISC-V 启动代码
├── init/main.c           # 内核入口 + CNBE-32 初始化
├── kernel/               # 内核核心 (19个文件)
│   ├── cnbe_basic.c      # 中文 BASIC 解释器
│   ├── cnbe_compiler.c   # 中文编译器
│   ├── cnbe_shell.c      # 中文交互 Shell
│   └── ...
├── mm/                   # 内存管理 (Sv39 页表)
├── fs/                   # 文件系统 (18个文件)
├── lib/                  # 内核库 (12个文件)
├── cnbe/cnbe.c           # CNBE-32 运行时
├── include/              # 头文件 (36个)
│   ├── asm/              # RISC-V 架构头文件
│   ├── linux/            # 内核接口头文件
│   └── cnbe_table_data.h # 20902 条目 CNBE 编码表
└── tools/                # 编码表生成工具
```

## 已知限制

代码存在多处已知问题，详见 [WHITEPAPER.md](WHITEPAPER.md#已知问题) 中的完整问题清单。主要问题包括：编码损坏、Sv32/Sv39 页表不一致、未实现的 trap handler、不完整的用户模式切换等。

## 致谢

- Linux 0.01 by Linus Torvalds (1991)
- CNBE-32 中文原生二进制编码项目
- RISC-V 国际基金会开源 ISA 规范
- 本代码由 AI Agent (GPT-5 / Codex) 自动生成

---

**让会中文的人，用母语进入操作系统底层。**
