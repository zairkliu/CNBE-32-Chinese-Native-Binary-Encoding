/*
 * RISC-V CSR 操作与基础宏定义
 * CNBE-32 移植版本
 */

#ifndef _RISCV_H
#define _RISCV_H

/* RISC-V MSTATUS 位域 */
#define MSTATUS_MIE     0x00000008
#define MSTATUS_MPIE    0x00000080
#define MSTATUS_MPP     0x00001800
#define MSTATUS_SIE     0x00000002
#define MSTATUS_SPIE    0x00000020
#define MSTATUS_SPP     0x00000100

/* RISC-V 中断原因 */
#define MCAUSE_INTR     0x8000000000000000UL
#define MCAUSE_CODE_MASK 0x7FFFFFFFFFFFFFFFUL

/* RISC-V 异常代码 */
#define CAUSE_MISALIGNED_FETCH      0
#define CAUSE_FETCH_ACCESS          1
#define CAUSE_ILLEGAL_INSTRUCTION   2
#define CAUSE_BREAKPOINT            3
#define CAUSE_MISALIGNED_LOAD       4
#define CAUSE_LOAD_ACCESS           5
#define CAUSE_MISALIGNED_STORE      6
#define CAUSE_STORE_ACCESS          7
#define CAUSE_USER_ECALL            8
#define CAUSE_SUPERVISOR_ECALL      9
#define CAUSE_MACHINE_ECALL         11
#define CAUSE_INSTRUCTION_PAGE_FAULT 12
#define CAUSE_LOAD_PAGE_FAULT       13
#define CAUSE_STORE_PAGE_FAULT      15

#define IRQ_M_EXTERNAL          11
#define IRQ_M_TIMER             7
#define IRQ_M_SOFT              3

/* 内核虚拟地址基址 */
#define KERNEL_BASE_ADDR    0x80200000UL

/* 页表相关常量 */
#ifndef PAGE_SHIFT
#define PAGE_SHIFT          12
#endif

#ifndef PAGE_SIZE
#define PAGE_SIZE           (1UL << PAGE_SHIFT)
#endif

#ifndef PAGE_MASK
#define PAGE_MASK           (~(PAGE_SIZE - 1))
#endif

/* Sv39 页表 */
#define SATP_MODE_SV39      (8UL << 60)
#define PTE_V               0x001
#define PTE_R               0x002
#define PTE_W               0x004
#define PTE_X               0x008
#define PTE_U               0x010
#define PTE_G               0x020
#define PTE_A               0x040
#define PTE_D               0x080

/* RISC-V 内联汇编 CSR 操作 - 保持与 x86 cli/sti 语义一致 */
#define csr_read(csr) ({ \
    unsigned long __v; \
    __asm__ volatile ("csrr %0, " #csr : "=r" (__v)); \
    __v; \
})

#define csr_write(csr, val) ({ \
    unsigned long __v = (unsigned long)(val); \
    __asm__ volatile ("csrw " #csr ", %0" : : "rK" (__v)); \
})

#define csr_set(csr, val) ({ \
    unsigned long __v = (unsigned long)(val); \
    __asm__ volatile ("csrs " #csr ", %0" : : "rK" (__v)); \
})

#define csr_clear(csr, val) ({ \
    unsigned long __v = (unsigned long)(val); \
    __asm__ volatile ("csrc " #csr ", %0" : : "rK" (__v)); \
})

/* 中断使能/禁用宏 (x86 cli/sti 的 RISC-V 替代) */
#define local_irq_disable()     csr_clear(mstatus, MSTATUS_MIE)
#define local_irq_enable()      csr_set(mstatus, MSTATUS_MIE)
#define local_irq_save(flags)   do { flags = csr_read(mstatus); csr_clear(mstatus, MSTATUS_MIE); } while(0)
#define local_irq_restore(flags) csr_write(mstatus, flags)

/* 内存屏障 */
#define mb()    __asm__ volatile ("fence" ::: "memory")
#define rmb()   __asm__ volatile ("fence ir, ir" ::: "memory")
#define wmb()   __asm__ volatile ("fence ow, ow" ::: "memory")

/* I/O 内存屏障 */
#define iob()   __asm__ volatile ("fence io, io" ::: "memory")

#endif
