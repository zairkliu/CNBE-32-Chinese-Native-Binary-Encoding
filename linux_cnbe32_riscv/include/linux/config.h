#ifndef _CONFIG_H
#define _CONFIG_H

/*
 * RISC-V CNBE-32 内核配置
 * 目标平台: QEMU virt (RISC-V 64)
 * 硬件: 1GHz | 32MB L3 Cache | 1GB RAM | 1GB Storage
 */

/* 内存配置: 1GB RAM */
#define HIGH_MEMORY     (0x40000000UL)     /* 1GB */

/* 缓冲区结束地址 */
#define BUFFER_END      (0x10000000UL)     /* 256MB 处 */

/* 根设备: 无物理硬盘，使用 virtio-blk 或 ramdisk */
#define ROOT_DEV        0x0100             /* /dev/ram0 */

/* 无物理硬盘类型定义 (RISC-V 使用 virtio) */
#define HD_TYPE         { 0,0,0,0,0,0 }

#endif
