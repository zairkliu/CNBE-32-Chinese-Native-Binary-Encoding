/*
 * RISC-V 内存操作
 * CNBE-32 移植版本
 * 替代 x86 内联汇编 memcpy (cld;rep;movsb)
 */

#ifndef _ASM_MEMORY_H
#define _ASM_MEMORY_H

/* 纯 C 实现 memcpy (替代 x86 cld;rep;movsb) */
static inline void *memcpy(void *dest, const void *src, unsigned long n)
{
    char *d = (char *)dest;
    const char *s = (const char *)src;
    while (n--)
        *d++ = *s++;
    return dest;
}

#endif
