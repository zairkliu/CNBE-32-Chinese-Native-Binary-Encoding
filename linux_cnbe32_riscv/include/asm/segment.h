/*
 * RISC-V segment.h - 段操作与地址空间访问
 * CNBE-32 移植版本
 * 
 * 重要说明：RISC-V 架构不使用 x86 风格的段式内存管理，
 * 没有 FS/GS/DS/ES/CS/SS 段寄存器。本文件提供等效的
 * 用户空间地址访问功能，通过虚拟地址映射实现。
 */

#ifndef _SEGMENT_H
#define _SEGMENT_H

/* RISC-V 没有段寄存器，get_fs/put_fs 操作通过直接内存访问实现 */
/* 用户空间基址在 RISC-V 中由页表映射，不需要段基址 */

static inline unsigned char get_fs_byte(const char *addr)
{
	return *(volatile unsigned char *)addr;
}

static inline unsigned short get_fs_word(const unsigned short *addr)
{
	return *(volatile unsigned short *)addr;
}

static inline unsigned long get_fs_long(const unsigned long *addr)
{
	return *(volatile unsigned long *)addr;
}

static inline void put_fs_byte(char val, char *addr)
{
	*(volatile char *)addr = val;
}

static inline void put_fs_word(short val, short *addr)
{
	*(volatile short *)addr = val;
}

static inline void put_fs_long(unsigned long val, unsigned long *addr)
{
	*(volatile unsigned long *)addr = val;
}

/* 段寄存器宏 - RISC-V 无段寄存器，为空操作 */
#define get_seg_byte(seg, addr)     get_fs_byte((char *)(addr))
#define get_seg_long(seg, addr)     get_fs_long((unsigned long *)(addr))
#define _fs()                       0

#endif
