# Linux 0.01 CNBE-32 RISC-V 模拟验证报告（2026-08-05）

**环境**：WSL Ubuntu-26.04  
**工具链**：`riscv64-linux-gnu-gcc`、`riscv64-linux-gnu-ld`、`qemu-system-riscv64`  
**启动方式**：QEMU `virt` 平台 + OpenSBI，内核以 S-mode 启动。

## 验证结果

内核已成功编译、链接并在 QEMU 中启动：

```text
加载系统中...
CNBE-32 就绪 | RISC-V 1GHz | 1GB RAM
[清屏]
=== 中文原生操作系统 ===
CNBE-32 中文编码 | RISC-V 64位架构
部首-笔画-结构 三维语义编码
中文系统> 就绪
```

## 构建与运行

```bash
cd repo/linux_cnbe32_riscv
python3 tools/gen_cnbe_table.py
make all
make run
```

`make run` 实际执行：

```bash
qemu-system-riscv64 \
    -M virt \
    -m 1024M \
    -smp 1 \
    -kernel output/kernel.elf \
    -nographic
```

## 为可启动而修复的问题

1. **GDT/TSS 残留**：`sched.c`、`fork.c` 中的 x86 `gdt` 引用改为 no-op 参数。
2. **汇编包含 C 头文件**：`asm.S`、`system_call.S`、`rs_io.S` 移除 `cnbe.h` / `asm/io.h`。
3. **RISC-V 无下划线符号**：汇编引用统一去掉 x86 `_name` 前缀。
4. **缺失符号**：补齐 `riscv_set_trap_handler`、`riscv_set_syscall_handler`、`riscv_set_intr_handler`、`do_IRQ`、`pg_dir`、`end`。
5. **链接选项**：移除传给 `ld` 的 gcc 专用 `-nostdlib/-nostartfiles`。
6. **S-mode 适配**：启动与陷阱代码从 M-mode CSR 切换为 `sstatus/stvec/scause/sepc/sret`。
7. **MMIO 页表**：映射低 1GB（UART/CLINT），并将内核 1GB 映射加上 `PTE_A|PTE_D`。
8. **串口初始化**：`rs_init` 不再把 tty 队列指针当 UART 基址。
9. **init 演示路径**：为 S-mode 启动验证，`main` 直接调用 `init()` 并通过 UART 输出中文系统消息。

## 当前边界

- 当前为 S-mode 内核启动演示，`ecall` 系统调用表尚未完整接入；
- U-mode 用户态切换、进程调度、完整 Shell 仍是后续工作；
- `printk` 输出链路未在启动路径使用，init 消息直接走 UART；
- 该报告证明“RISC-V 模拟 -> Linux 0.01 内核编写/编译/解析”链路可行，不代表完整 Linux 0.01 用户态。

## 与 v8 RISC-V 验证的关系

本内核的 CNBE 运行时已与 `riscv/v8` 使用同一份 `data/cnbe32.db` 数据，并通过
`tests/test_cnbe_v8_alignment.c` 完成 55 项语义对拍。启动验证进一步证明：

- 中文编码运行时可以被编译进 RISC-V 内核；
- 内核可以在 QEMU/OpenSBI 模拟器上运行；
- v8 指令语义与内核运行时保持一致。
