/* RISC-V 启动代码 —— Linux 0.01 CNBE-32 版本
 * 基于仓库 v84_riscv_os_full 启动逻辑扩展
 * 目标: QEMU virt 平台 (RISC-V 64)
 * 硬件: 1GHz | 32MB L3 Cache | 1GB RAM | 1GB Storage
 */

.section .text.boot
.global _start

/* QEMU virt 内存映射:
 * 0x0000_0000 - 0x0040_0000: QEMU 固件/设备树 (保留)
 * 0x1000_0000: UART0 (16550A)
 * 0x8000_0000 - 0xBFFF_FFFF: 1GB RAM
 */

#define UART_BASE       0x10000000
#define UART_THR        (UART_BASE + 0x00)  /* 发送保持寄存器 */
#define UART_LSR        (UART_BASE + 0x05)  /* 线状态寄存器 */
#define UART_LSR_THRE   0x20                /* 发送保持寄存器空 */

/* PLIC 地址 */
#define PLIC_BASE       0x0C000000

#include <asm/riscv.h>

/* 内核栈大小: 16KB */
#define STACK_SIZE      0x4000

_start:
    /* 关闭所有中断 (机器模式) */
    csrrci  x0, mstatus, 0x8    /* 清除 MIE */
    csrw    mie, x0             /* 关闭所有中断使能 */

    /* 仅在 Hart 0 上启动 (QEMU virt 多核) */
    csrr    t0, mhartid
    bnez    t0, _hang           /* 非主核进入循环 */

    /* 初始化栈指针 (1GB 顶端 - 16KB) */
    li      sp, 0xBFFFF000

    /* 清零 BSS 段 */
    la      t0, __bss_start
    la      t1, __bss_end
_bss_clear:
    bge     t0, t1, _bss_done
    sd      x0, 0(t0)
    addi    t0, t0, 8
    j       _bss_clear
_bss_done:

    /* 设置陷阱向量表 (机器模式) */
    la      t0, _trap_vector
    csrw    mtvec, t0

    /* 初始化 UART (输出 "加载系统中...") */
    call    _uart_init
    la      a0, msg_boot
    call    _uart_puts

    /* 初始化 CNBE-32 运行时 (81.6KB 表加载到 L3 Cache) */
    call    cnbe_init

    /* 输出 CNBE-32 就绪消息 */
    la      a0, msg_cnbe_ready
    call    _uart_puts

    /* 设置 Sv39 页表 (内核映射) */
    call    _setup_mmu

    /* 启用 MMU (Sv39) */
    la      t0, swapper_pg_dir
    srli    t0, t0, 12          /* PPN */
    li      t1, (8UL << 60)     /* MODE = Sv39 */
    or      t0, t0, t1
    csrw    satp, t0
    sfence.vma

    /* 进入内核主函数 */
    call    main

    /* main 不应返回，如果返回则挂起 */
_hang:
    wfi
    j       _hang

/* UART 初始化 (设置 115200 8N1) */
_uart_init:
    /* QEMU 默认已初始化 UART，无需额外配置 */
    ret

/* 输出单个字符 (a0 = char) */
_uart_putchar:
    li      t0, UART_BASE
_uart_wait:
    lbu     t1, 5(t0)           /* 读 LSR */
    andi    t1, t1, UART_LSR_THRE
    beqz    t1, _uart_wait
    sb      a0, 0(t0)           /* 写 THR */
    ret

/* 输出字符串 (a0 = 字符串地址) */
_uart_puts:
    addi    sp, sp, -8
    sd      ra, 0(sp)
    mv      t2, a0
_puts_loop:
    lbu     a0, 0(t2)
    beqz    a0, _puts_done
    call    _uart_putchar
    addi    t2, t2, 1
    j       _puts_loop
_puts_done:
    ld      ra, 0(sp)
    addi    sp, sp, 8
    ret

/* 设置 Sv39 页表: 恒等映射 0x80000000 - 0xBFFFFFFF */
_setup_mmu:
    /* 使用静态页表 (编译时分配) */
    la      t0, swapper_pg_dir  /* 根页表 (4KB) */

    /* 映射 0x80000000 - 0xBFFFFFFF (1GB) 使用 1GB 超大页 */
    /* VPN[2] = 0x2 (0x80000000 >> 30 = 2) */
    li      t1, 0x80000000
    li      t2, (PTE_V | PTE_R | PTE_W | PTE_X | PTE_G)
    srli    t1, t1, 2           /* 转为 PPN 格式 */
    or      t1, t1, t2
    sd      t1, 16(t0)          /* 根页表[2] = 映射 */

    ret

/* 陷阱向量表 (机器模式) */
.align 4
_trap_vector:
    /* 保存上下文 */
    addi    sp, sp, -256
    sd      ra, 0(sp)
    sd      t0, 8(sp)
    sd      t1, 16(sp)
    sd      t2, 24(sp)
    sd      a0, 32(sp)
    sd      a1, 40(sp)
    sd      a2, 48(sp)
    sd      a3, 56(sp)
    sd      a4, 64(sp)
    sd      a5, 72(sp)
    sd      a6, 80(sp)
    sd      a7, 88(sp)

    csrr    t0, mcause
    bgez    t0, _trap_exception

    /* 中断处理 */
    andi    t0, t0, 0x7FF
    li      t1, IRQ_M_EXTERNAL
    beq     t0, t1, _trap_external_irq
    j       _trap_done

_trap_exception:
    /* 异常处理: 检查是否为系统调用 (ecall) */
    li      t1, 8               /* ecall 异常码 */
    beq     t0, t1, _trap_syscall
    li      t1, 9               /* ecall from S-mode */
    beq     t0, t1, _trap_syscall
    li      t1, 11              /* ecall from M-mode */
    beq     t0, t1, _trap_syscall
    j       _trap_done

_trap_syscall:
    /* 系统调用处理: a7 = 系统调用号, a0-a6 = 参数 */
    call    system_call
    j       _trap_done

_trap_external_irq:
    /* 外部中断 (PLIC) */
    call    do_IRQ
    j       _trap_done

_trap_done:
    /* 恢复上下文 */
    ld      ra, 0(sp)
    ld      t0, 8(sp)
    ld      t1, 16(sp)
    ld      t2, 24(sp)
    ld      a0, 32(sp)
    ld      a1, 40(sp)
    ld      a2, 48(sp)
    ld      a3, 56(sp)
    ld      a4, 64(sp)
    ld      a5, 72(sp)
    ld      a6, 80(sp)
    ld      a7, 88(sp)
    addi    sp, sp, 256
    mret

/* 数据段 */
.section .rodata
msg_boot:
    .string "\r\n加载系统中...\r\n"
msg_cnbe_ready:
    .string "CNBE-32 就绪 | RISC-V 1GHz | 1GB RAM\r\n"

/* BSS 段: 页表 (必须在 4KB 对齐) */
.section .bss
.align 12

.global __bss_start
__bss_start:

.global swapper_pg_dir
swapper_pg_dir:
    .space 4096                 /* 根页表 (512 * 8) */

.global __bss_end
__bss_end:
