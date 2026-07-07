/*
 * RISC-V MMIO I/O 操作
 * CNBE-32 移植版本
 * 替代 x86 inb/outb 端口 I/O，使用内存映射 I/O
 */

#ifndef _ASM_IO_H
#define _ASM_IO_H

#include <asm/riscv.h>

/* MMIO 读写 (替代 x86 inb/outb) */
static inline void writeb(unsigned char val, volatile void *addr)
{
    *(volatile unsigned char *)addr = val;
}

static inline void writew(unsigned short val, volatile void *addr)
{
    *(volatile unsigned short *)addr = val;
}

static inline void writel(unsigned long val, volatile void *addr)
{
    *(volatile unsigned long *)addr = val;
}

static inline unsigned char readb(volatile void *addr)
{
    return *(volatile unsigned char *)addr;
}

static inline unsigned short readw(volatile void *addr)
{
    return *(volatile unsigned short *)addr;
}

static inline unsigned long readl(volatile void *addr)
{
    return *(volatile unsigned long *)addr;
}

/* x86 兼容宏: outb/inb 映射到 MMIO 写/读 */
#define outb(value, port)      writeb((value), (void *)(port))
#define inb(port)               readb((void *)(port))
#define outb_p(value, port)     writeb((value), (void *)(port))
#define inb_p(port)             readb((void *)(port))

/* I/O 内存映射延迟 (RISC-V 使用 fence 替代 x86 jmp 延迟) */
#define io_delay()              __asm__ volatile ("fence io, io" ::: "memory")

#endif
