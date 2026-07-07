#ifndef _HEAD_H
#define _HEAD_H

/*
 * RISC-V CNBE-32 头文件
 * 替代 x86 GDT/LDT/IDT 定义
 * RISC-V 无段式内存，使用页表管理地址空间
 */

/* 页目录 (Sv39 根页表) */
extern unsigned long pg_dir[512];

/* RISC-V 无 GDT/LDT/IDT，保留空结构以兼容 */
typedef struct desc_struct {
    unsigned long a, b;
} desc_table[1];

/* 兼容宏 - RISC-V 中为空操作 */
#define GDT_NUL     0
#define GDT_CODE    0
#define GDT_DATA    0
#define GDT_TMP     0

#define LDT_NUL     0
#define LDT_CODE    0
#define LDT_DATA    0

#endif
