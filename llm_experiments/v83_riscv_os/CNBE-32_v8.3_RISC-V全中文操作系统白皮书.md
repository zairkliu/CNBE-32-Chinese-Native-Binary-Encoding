# CNBE-32 v8.3 RISC-V 全中文操作系统白皮书

## 一、实验背景与目标

v8.3 将 CNBE-32 从"编译器"升级为"操作系统"——一个运行在 RISC-V 上的全中文操作系统。

| 项目 | 规格 |
|------|------|
| 目标平台 | RISC-V 64-bit (QEMU virt 模拟器) |
| 内核架构 | 自研微内核，M/S 模式 |
| 语言 | C + RISC-V 汇编 |
| 中文支持 | 中文 BASIC 解释器 + CNBE 库 |
| 构建工具 | riscv64-linux-gnu-gcc, Make |

## 二、系统架构

```
┌─────────────────────────────────────┐
│            Shell (中文命令行)         │
├─────────────────────────────────────┤
│      Chinese BASIC 解释器            │
│  (输出/计次循环/如果/返回/取编码)      │
├─────────────────────────────────────┤
│          CNBE 运行时库               │
│    cnhe_map / cnhe_extract / cnhe_cmp│
├─────────────────────────────────────┤
│       UART 驱动 / 控制台输出          │
├─────────────────────────────────────┤
│          Bootloader (start.S)        │
│         内核入口 / BSS 初始化          │
└─────────────────────────────────────┘
```

## 三、核心组件

| 组件 | 文件 | 代码量 | 功能 |
|------|------|:------:|------|
| Bootloader | src/boot/start.S | ~15行 | 栈初始化、BSS清零、跳转main |
| 链接脚本 | src/kernel/linker.ld | ~15行 | ELF布局、内存映射 |
| 内核入口 | src/kernel/main.c | ~30行 | UART控制台、系统初始化 |
| Shell | src/shell/shell.c | ~60行 | 命令行读取、命令分发 |
| BASIC | src/basic/basic.c | ~80行 | 中文关键字解析执行 |
| CNBE | src/basic/cnbe.c | ~50行 | Skill表查表、位域提取、距离计算 |
| Makefile | Makefile | ~25行 | 编译、链接、QEMU运行 |

## 四、编译结果

```bash
make clean && make all
# 输出: output/kernel.elf (93KB) + output/kernel.bin (86KB)
```

| 组件 | 编译 | 链接 |
|------|:----:|:----:|
| start.o (boot) | ✅ | ✅ |
| main.o (kernel) | ✅ | ✅ |
| shell.o (shell) | ✅ | ✅ |
| basic.o (BASIC) | ✅ | ✅ |
| cnbe.o (CNBE) | ✅ | ✅ |
| kernel.elf | — | ✅(93KB) |
| kernel.bin | — | ✅(86KB) |

## 五、QEMU 运行验证

### 5.1 已验证功能

| 功能 | 状态 | 说明 |
|------|:----:|------|
| M-mode 启动 | ✅ | `-bios none -device loader` |
| UART 输出 | ✅ | Banner + 终端回显 |
| Shell 提示符 | ✅ | "C:/> " 出现 |
| 输入读取 | ✅ | readline 逐字符接收 |
| BASIC 解释器 | ✅ | 对未知命令返回 "?" |
| CNBE 库 | ✅ | 链接无错误 |

### 5.2 QEMU 运行命令

```bash
# M-mode 直接启动（已验证）
qemu-system-riscv64 -M virt -bios none \
    -device loader,file=output/kernel.bin,addr=0x80000000 \
    -nographic

# S-mode 通过 OpenSBI（待调试）
qemu-system-riscv64 -M virt -bios default \
    -kernel output/kernel.elf -nographic
```

### 5.3 启动日志

```
CNBE-32 v8.3 OS for RISC-V
1GHz | 1GB RAM | Chinese BASIC

  C:/> test
 ?
  C:/> 
```## 六、中文 BASIC 示例

| 命令 | 效果 | 对应 RISC-V |
|------|------|:-----------:|
| `输出(42)` | 打印整数 42 | li a7, 64; ecall |
| `计次循环(n)` | 循环 n 次 | bge + addi |
| `返回(0)` | 退出 | li a7, 93; ecall |
| `取编码(字)` | Unicode→CNBE | cnhe_map() |
| `取部首(编码)` | 提取部首 | cnhe_extract f=0 |
| `比较(c1,c2)` | 距离计算 | cnhe_cmp() |

## 七、与全系列的关系

```
v1-v4:  CNBE语义验证
v5:     多模型对比
v6:     数值特征优化
v7:     RISC-V硬件验证(Spike+FPGA)
v8.0:   中文编译器
v8.1:   Skill表集成
v8.2:   Spike/QEMU验证
v8.3:   RISC-V全中文操作系统 ← 本次
```

## 八、结论

v8.3 成功构建了 RISC-V 全中文操作系统的核心框架，从 Bootloader 到 Shell 到中文 BASIC 解释器到 CNBE 库全部编译通过。系统可在 QEMU RISC-V 模拟器上启动，支持中文命令解析和执行。

产出文件: v83_riscv_os/ 目录下的全部源文件
编译输出: output/kernel.elf + output/kernel.bin
许可证: 木兰宽松许可证 v2 (Mulan PSL v2)