 > ⚠️ **声明：此计划文档由 AI Agent 在转译前生成，描述了预期的工作分解。实际代码与计划可能存在偏差。** 详见 [WHITEPAPER.md](WHITEPAPER.md)。
 
 # Linux 0.01 CNBE-32 RISC-V 转码计划（Agent 生成 — 概念验证）

## 项目目标
基于仓库 `v84_riscv_os_full/src/basic/` 的 basic 编码思路，将 Linux 0.01 源码转码为 CNBE-32 编码的 RISC-V 版本，运行于 1GHz / 32MB L3 / 1GB RAM / 1GB Storage 环境。

## 核心编码思路 (来自仓库 basic)
1. **CNBE-32 运行时集成**: `cnhe_map` / `cnhe_extract` / `cnhe_cmp`
2. **中文消息输出**: 内核关键消息使用 UTF-8 中文
3. **RISC-V 自定义指令接口**: `cnhe.map` (查表) / `cnhe.extract` (位域) / `cnhe.cmp` (距离)
4. **零标准库**: `-nostdlib -ffreestanding` 构建
5. **内存布局**: 内核加载于 0x80200000，栈顶 0xBFFFF000

## 工作分解

### Stage 1: 共享基础设施 (已完成)
- `include/cnbe.h` — CNBE-32 头文件
- `cnbe/cnbe.c` — CNBE-32 运行时实现
- `kernel/linker.ld` — RISC-V 链接器脚本
- `Makefile` — 构建系统

### Stage 2: 并行子系统转码 (AgentSwarm)
每个子代理负责一个子系统，将原始 Linux 0.01 x86 代码转码为 RISC-V + CNBE-32:

1. **Boot_启动** — `boot/start.S` (RISC-V 启动汇编)
2. **Init_初始化** — `init/main.c` (系统初始化 + 中文消息)
3. **Kernel_核心** — `kernel/sched.c`, `kernel/traps.c`, `kernel/fork.c`, `kernel/exit.c`, `kernel/panic.c`, `kernel/sys.c`, `kernel/mktime.c`
4. **Kernel_汇编** — `kernel/asm.S`, `kernel/system_call.S`, `kernel/rs_io.S` (RISC-V 中断/系统调用/串口)
5. **Kernel_打印** — `kernel/printk.c`, `kernel/vsprintf.c`, `kernel/console.c`, `kernel/tty_io.c`, `kernel/keyboard.c`, `kernel/serial.c`, `kernel/hd.c`
6. **MM_内存管理** — `mm/memory.c`, `mm/page.S` (RISC-V Sv39 页表)
7. **FS_文件系统** — `fs/` 全部 16 个 C 文件
8. **LIB_库** — `lib/` 全部 11 个 C 文件
9. **Headers_头文件** — `include/asm/` (RISC-V 版本), `include/linux/` (更新结构体)

### Stage 3: 集成验证
- 合并所有子系统输出
- 检查符号依赖
- 尝试编译
- 修复错误

## 关键转码规则

### 1. 注释转码
- 原始英文注释 → 中文注释（保留技术含义）
- 添加 CNBE-32 相关注释说明

### 2. 字符串转码
- 内核启动消息 → 中文 UTF-8
- 错误提示 → 中文 UTF-8
- 示例: `"Loading system..."` → `"加载系统中..."`

### 3. 函数/变量命名
- 保持核心 C 代码命名（与内核 ABI 兼容）
- 在关键函数旁添加中文注释说明
- CNBE-32 相关函数使用 `cnhe_` / `cnbe_` 前缀

### 4. RISC-V 移植规则
- x86 `outb`/`inb` → RISC-V MMIO (UART 0x10000000)
- x86 `cli`/`sti` → RISC-V `csrc/csrw` (mstatus MIE)
- x86 段寄存器 → RISC-V 无段式，忽略
- x86 中断 0x20-0x2F → RISC-V 外部中断 (PLIC)
- x86 系统调用 `int 0x80` → RISC-V `ecall`
- x86 页表 (2-level) → RISC-V Sv39 (3-level)

### 5. 硬件适配
- 1GB RAM: 页表覆盖 0x80200000 - 0xBFFFF000
- 32MB L3 Cache: 81.6KB CNBE 表常驻缓存
- UART 输出: `0x10000000` (QEMU virt 平台)
- 存储: 无硬盘/软盘模拟，简化 block 层
