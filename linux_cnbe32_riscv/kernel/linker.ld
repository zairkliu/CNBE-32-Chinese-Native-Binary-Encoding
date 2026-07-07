/* RISC-V Linker Script for Linux 0.01 CNBE-32
 * 硬件目标: 1GHz RISC-V | 1GB RAM | 1GB Storage
 * 内存布局: 内核加载于 0x80200000 (8MB 偏移处，保留低 8MB 给设备/Boot)
 */

ENTRY(_start)

MEMORY
{
    RAM (rwx) : ORIGIN = 0x80200000, LENGTH = 0x3FE00000  /* 1GB - 8MB */
}

SECTIONS
{
    . = 0x80200000;

    /* 代码段 */
    .text : ALIGN(4096)
    {
        *(.text.boot)
        *(.text)
        *(.text.*)
    } > RAM

    /* 只读数据段 */
    .rodata : ALIGN(4096)
    {
        *(.rodata)
        *(.rodata.*)
        /* CNBE-32 Skill 表嵌入此处 (81.6KB) */
        *(.cnbe.skill_table)
    } > RAM

    /* 数据段 */
    .data : ALIGN(4096)
    {
        *(.data)
        *(.data.*)
    } > RAM

    /* BSS 段 */
    .bss : ALIGN(4096)
    {
        __bss_start = .;
        *(.bss)
        *(.bss.*)
        *(COMMON)
        __bss_end = .;
    } > RAM

    /* 内核栈 (每 CPU 16KB，从 1GB 顶端向下生长) */
    __stack_top = 0xBFFFF000;

    /* 丢弃不需要的段 */
    /DISCARD/ :
    {
        *(.comment)
        *(.note)
        *(.eh_frame)
    }
}
