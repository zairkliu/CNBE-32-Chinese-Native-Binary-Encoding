/*
 * RISC-V system.h - 系统级宏与门设置
 * CNBE-32 移植版本
 * 
 * 原 x86 特权级切换、门描述符等概念在 RISC-V 中不存在，
 * 本文件提供等效的 RISC-V 异常处理与系统调用设置。
 */

#ifndef _SYSTEM_H
#define _SYSTEM_H

#include <asm/riscv.h>

/* move_to_user_mode: RISC-V 简化版 — 仅清除 MPP 位 */
/* 完整的用户模式切换需要设置 mepc 并 mret，此处为简化实现 */
#define move_to_user_mode() \
    __asm__ __volatile__ ( \
        "li t0, 0x1800\n\t"        /* MSTATUS_MPP */ \
        "csrc mstatus, t0\n\t"     /* 清除 MPP, 设为 U-mode */ \
        ::: "t0", "memory")

/* 中断使能/禁用 (x86 sti/cli 的 RISC-V 替代) */
#define sti()   local_irq_enable()
#define cli()   local_irq_disable()
#define nop()   __asm__ volatile ("nop" :::)

/* RISC-V 使用 sret/mret 返回，替代 x86 的 iret */
#define sret()  __asm__ volatile ("sret" :::)
#define mret()  __asm__ volatile ("mret" :::)

#ifdef __ASSEMBLY__

/* RISC-V 没有门描述符，使用 mtvec/stvec 寄存器设置异常入口 */
/* 这些宏为兼容旧代码保留，但功能已不同 */

#define set_trap_gate(n, addr)        /* assembly stub */
#define set_intr_gate(n, addr)        /* assembly stub */
#define set_system_gate(n, addr)      /* assembly stub */

#else

/* C code below */

#define set_trap_gate(n, addr)        riscv_set_trap_handler(n, addr)
#define set_intr_gate(n, addr)        riscv_set_intr_handler(n, addr)
#define set_system_gate(n, addr)      riscv_set_syscall_handler(n, addr)

/* 异常处理函数声明 */
extern void riscv_set_trap_handler(int n, void *addr);
extern void riscv_set_intr_handler(int n, void *addr);
extern void riscv_set_syscall_handler(int n, void *addr);

#endif

/* RISC-V 没有 x86 的 TSS/LDT 描述符 */
/* 以下宏保留以保持代码兼容性，但为空操作 */
#define set_tss_desc(n, addr)         do { (void)(n); (void)(addr); } while(0)
#define set_ldt_desc(n, addr)         do { (void)(n); (void)(addr); } while(0)
#define ltr(n)                        do { (void)(n); } while(0)
#define lldt(n)                       do { (void)(n); } while(0)
#define str(n)                        do { (void)(n); } while(0)

/* RISC-V 上下文保存/恢复宏 (替代 x86 pusha/popa) */
#define SAVE_CONTEXT()  do { \
    __asm__ volatile ( \
        "addi sp, sp, -120\n\t" \
        "sw ra, 116(sp)\n\t" \
        "sw t0, 112(sp)\n\t" \
        "sw t1, 108(sp)\n\t" \
        "sw t2, 104(sp)\n\t" \
        "sw s0, 100(sp)\n\t" \
        "sw s1, 96(sp)\n\t" \
        "sw a0, 92(sp)\n\t" \
        "sw a1, 88(sp)\n\t" \
        "sw a2, 84(sp)\n\t" \
        "sw a3, 80(sp)\n\t" \
        "sw a4, 76(sp)\n\t" \
        "sw a5, 72(sp)\n\t" \
        "sw a6, 68(sp)\n\t" \
        "sw a7, 64(sp)\n\t" \
        "sw s2, 60(sp)\n\t" \
        "sw s3, 56(sp)\n\t" \
        "sw s4, 52(sp)\n\t" \
        "sw s5, 48(sp)\n\t" \
        "sw s6, 44(sp)\n\t" \
        "sw s7, 40(sp)\n\t" \
        "sw s8, 36(sp)\n\t" \
        "sw s9, 32(sp)\n\t" \
        "sw s10, 28(sp)\n\t" \
        "sw s11, 24(sp)\n\t" \
        "sw t3, 20(sp)\n\t" \
        "sw t4, 16(sp)\n\t" \
        "sw t5, 12(sp)\n\t" \
        "sw t6, 8(sp)\n\t" \
        ::: "memory"); \
} while(0)

#define RESTORE_CONTEXT() do { \
    __asm__ volatile ( \
        "lw t6, 8(sp)\n\t" \
        "lw t5, 12(sp)\n\t" \
        "lw t4, 16(sp)\n\t" \
        "lw t3, 20(sp)\n\t" \
        "lw s11, 24(sp)\n\t" \
        "lw s10, 28(sp)\n\t" \
        "lw s9, 32(sp)\n\t" \
        "lw s8, 36(sp)\n\t" \
        "lw s7, 40(sp)\n\t" \
        "lw s6, 44(sp)\n\t" \
        "lw s5, 48(sp)\n\t" \
        "lw s4, 52(sp)\n\t" \
        "lw s3, 56(sp)\n\t" \
        "lw s2, 60(sp)\n\t" \
        "lw a7, 64(sp)\n\t" \
        "lw a6, 68(sp)\n\t" \
        "lw a5, 72(sp)\n\t" \
        "lw a4, 76(sp)\n\t" \
        "lw a3, 80(sp)\n\t" \
        "lw a2, 84(sp)\n\t" \
        "lw a1, 88(sp)\n\t" \
        "lw a0, 92(sp)\n\t" \
        "lw s1, 96(sp)\n\t" \
        "lw s0, 100(sp)\n\t" \
        "lw t2, 104(sp)\n\t" \
        "lw t1, 108(sp)\n\t" \
        "lw t0, 112(sp)\n\t" \
        "lw ra, 116(sp)\n\t" \
        "addi sp, sp, 120\n\t" \
        ::: "memory"); \
} while(0)

#endif
