 > ⚠️ **声明：本项目由 AI Agent 自动生成，未在 RISC-V 硬件或 QEMU 上验证，代码存在多处架构不一致问题，当前状态无法编译运行。此文档为 Agent 生成的技术描述，供概念验证参考。** 详见 [WHITEPAPER.md](WHITEPAPER.md)。
 
 # Linux 0.01 CNBE-32 RISC-V 转码项目（Agent 生成 — 概念验证）

## 项目概述

本项目基于 **CNBE-32 (Chinese Native Binary Encoding)** 仓库的 `v84_riscv_os_full/src/basic/` **basic 编码思路**，将 **Linux 0.01** (1991年发布的第一个 Linux 内核版本) 从 x86 架构转码为 **RISC-V 64 + CNBE-32 中文原生二进制编码** 版本。

## 硬件目标

| 参数 | 规格 |
|------|------|
| 处理器 | RISC-V 1GHz |
| L3 缓存 | 32MB (可完整容纳 81.6KB CNBE-32 Skill 表) |
| 内存 | 1GB RAM |
| 存储 | 1GB Storage |
| 目标平台 | QEMU RISC-V `virt` 机器 |

## 转码核心思路 (来自仓库 basic 编码)

1. **CNBE-32 运行时集成**: `cnhe_map` (Unicode→CNBE) / `cnhe_extract` (位域提取) / `cnhe_cmp` (语义距离)
2. **中文内核消息**: 所有 `printk`/`panic` 字符串使用 UTF-8 中文
3. **中文注释**: 关键代码注释全部转码为中文
4. **RISC-V 自定义指令接口**: 保留 `cnhe.map` / `cnhe.extract` / `cnhe.cmp` 硬件指令扩展点
5. **零标准库**: `-nostdlib -ffreestanding` 独立内核构建

## 项目结构

```
linux-cnbe32-riscv/
├── boot/
│   └── start.S              # RISC-V 启动代码 (QEMU virt)
├── init/
│   └── main.c               # 内核入口 + CNBE-32 初始化
├── kernel/
│   ├── asm.S                # 异常/陷阱处理 (RISC-V)
│   ├── system_call.S        # 系统调用分发 (ecall)
│   ├── rs_io.S              # 串口中断 (MMIO UART)
│   ├── keyboard.S           # 键盘中断处理
│   ├── page.S               # 页面异常 (RISC-V sret)
│   ├── sched.c              # 进程调度器
│   ├── traps.c              # 陷阱/异常处理
│   ├── fork.c               # 进程创建
│   ├── exit.c               # 进程退出
│   ├── panic.c              # 内核恐慌
│   ├── sys.c                # 系统调用实现
│   ├── mktime.c             # 时间计算
│   ├── printk.c             # 内核打印
│   ├── vsprintf.c           # 格式化字符串
│   ├── console.c            # 串行控制台 (替代 VGA)
│   ├── tty_io.c             # TTY 核心层
│   ├── serial.c             # UART 串口驱动
│   └── hd.c                 # 硬盘/块设备驱动
├── mm/
│   ├── memory.c             # 内存管理 (Sv32/Sv39 页表)
│   └── page.S               # 页面异常底层处理
├── fs/
│   ├── buffer.c             # 缓冲区管理
│   ├── inode.c              # inode 管理
│   ├── super.c              # 超级块管理
│   ├── namei.c              # 路径解析 (含 CNBE-32 中文文件名支持)
│   ├── exec.c               # 程序执行
│   ├── open.c               # 文件打开
│   ├── read_write.c         # 读写操作
│   ├── pipe.c               # 管道
│   ├── block_dev.c          # 块设备
│   ├── char_dev.c           # 字符设备
│   ├── file_dev.c           # 文件设备
│   ├── bitmap.c             # 位图管理
│   ├── truncate.c           # 截断
│   ├── stat.c               # 文件状态
│   ├── fcntl.c              # 文件控制
│   ├── ioctl.c              # IO 控制
│   ├── file_table.c         # 文件表
│   └── tty_ioctl.c          # TTY IO 控制
├── lib/
│   ├── string.c             # 字符串操作 (纯 C 实现)
│   ├── ctype.c              # 字符类型
│   ├── _exit.c              # 退出系统调用
│   ├── open.c               # 打开系统调用
│   ├── close.c              # 关闭系统调用
│   ├── read.c               # 读系统调用
│   ├── write.c              # 写系统调用
│   ├── execve.c             # 执行系统调用
│   ├── dup.c                # 复制文件描述符
│   ├── wait.c               # 等待系统调用
│   ├── setsid.c             # 设置会话
│   └── errno.c              # 错误码
├── cnbe/
│   └── cnbe.c               # CNBE-32 运行时 (81.6KB 查表)
├── include/
│   ├── cnbe.h               # CNBE-32 头文件
│   ├── asm/
│   │   ├── riscv.h          # RISC-V CSR/异常/页表常量
│   │   ├── system.h         # 系统指令 (cli/sti/SAVE_CONTEXT)
│   │   ├── io.h             # MMIO 读写
│   │   ├── memory.h         # 内存管理常量
│   │   └── segment.h        # 段寄存器兼容层 (RISC-V 无段式)
│   └── linux/
│       ├── head.h           # 页表/异常向量声明
│       ├── sched.h          # 任务结构/调度器
│       ├── mm.h             # 内存管理接口
│       ├── sys.h            # 系统调用表
│       ├── fs.h             # 文件系统结构
│       ├── tty.h            # TTY 结构
│       ├── kernel.h         # 内核函数原型
│       └── ...              # 其他标准头文件
├── kernel/
│   └── linker.ld            # RISC-V 链接器脚本 (1GB 内存布局)
├── Makefile                 # 构建系统
└── plan.md                  # 转码计划文档
```

## 关键转码变更

### 1. 架构移植: x86 → RISC-V

| x86 特性 | RISC-V 替代 |
|---------|------------|
| `cli`/`sti` | `csrci`/`csrsi mstatus, MSTATUS_MIE` |
| `int 0x80` 系统调用 | `ecall` 指令 |
| `iret` | `mret`/`sret` |
| `inb`/`outb` (I/O 端口) | MMIO `readb`/`writeb` |
| 段寄存器 (`ds`/`es`/`fs`) | 直接虚拟地址访问 |
| VGA 显存 (0xB8000) | UART 串行控制台 (0x10000000) |
| 8259 PIC 中断 | RISC-V PLIC/CLINT |
| x86 2级页表 | RISC-V Sv32/Sv39 |
| `pusha`/`popa` | 显式寄存器 `sd`/`ld` 保存/恢复 |
| `rep movsl` | C 循环/`memcpy` |

### 2. CNBE-32 编码集成

| 组件 | 集成方式 |
|------|---------|
| `cnhe_map()` | UTF-8 汉字 → 32位 CNBE 编码映射 |
| `cnhe_extract()` | 提取部首/笔画/结构位域 |
| `cnhe_cmp()` | 汉字语义距离计算 |
| `cnbe_utf8_decode()` | UTF-8 字符串解码 |
| `cnbe_printk()` | 中文内核消息输出 |
| `cnbe_strcmp()` | 支持 UTF-8 的文件名比较 |

### 3. 中文化

- **内核启动消息**: `"Loading system..."` → `"加载系统中..."`
- **panic 消息**: `"Kernel panic"` → `"【内核恐慌】"`
- **调度器消息**: `"Task 0 cannot sleep"` → `"任务0尝试睡眠，这是不允许的"`
- **文件系统消息**: `"Buffer locked"` → `"缓冲区被重复锁定"`
- **所有关键注释**: 英文 → 中文 UTF-8

## 构建指南

### 环境要求

- riscv64-linux-gnu-gcc (或 riscv64-unknown-elf-gcc)
- QEMU (riscv64-system-gnu)
- Make

### 安装交叉编译器 (Ubuntu/Debian)

```bash
sudo apt-get install gcc-riscv64-linux-gnu qemu-system-misc
```

### 编译

```bash
cd linux-cnbe32-riscv
make all
```

### 在 QEMU 中运行

```bash
make run
```

或手动:

```bash
qemu-system-riscv64 \
    -M virt \
    -m 1024M \
    -smp 1 \
    -bios none \
    -kernel output/kernel.bin \
    -nographic \
    -serial stdio
```

## 内存布局

```
0x0000_0000 - 0x0040_0000: 保留 (QEMU 固件/设备树)
0x1000_0000:               UART0 (16550A MMIO)
0x8000_0000 - 0xBFFF_FFFF: 1GB RAM
0x8020_0000:               内核加载地址
0xBFFFF000:                内核栈顶
```

## CNBE-32 编码位域

```
[31:24] 部首区 (8bit)  |  [23:19] 笔画区 (5bit)  |  [18:15] 结构区 (4bit)
[14:4]  字库区 (11bit) |  [3:0]   扩展区 (4bit)
```

- **部首**: 0-255 (214 康熙部首 + 41 扩展)
- **笔画**: 1-31 画
- **结构**: 0-15 (独体/左右/上下/包围等 9 种)
- **字库索引**: 0-20902 (CJK 基本字)
- **扩展**: 繁简/古今/方言标志

## 性能优化

- **81.6KB Skill 表**: 完全放入 32MB L3 Cache，查表延迟 1-2 周期 @ 1GHz
- **二分查找**: 零额外硬件成本，312x 加速
- **哈希索引**: 131KB 额外存储，4052x 加速
- **FPGA 实现**: 1 周期查表完成 (BRAM)

## 许可证

基于 Linux 0.01 原始许可证和 Mulan PSL v2 (CNBE-32 项目许可证)。

## 致谢

- Linux 0.01 by Linus Torvalds (1991)
- CNBE-32 Chinese Native Binary Encoding Project
- RISC-V 国际基金会开源 ISA 规范

---

**让会中文的人，用母语进入操作系统底层。**
