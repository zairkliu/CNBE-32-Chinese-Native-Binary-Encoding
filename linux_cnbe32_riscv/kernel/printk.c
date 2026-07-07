/*
 * 【RISC-V 转码状态】kernel/printk.c
 * 原始文件: Linux 0.01 kernel/printk.c
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - 移除 x86 段寄存器操作 (push %%fs, push %%ds, pop %%fs)
 *   - 移除 x86 内联汇编调用 tty_write
 *   - 替换为直接 C 函数调用 tty_write
 *   - RISC-V 无段式内存，无需 fs/ds 段切换
 *   - 添加中文注释和内核消息
 *   - 集成 CNBE-32 运行时头文件
 */

#include <stdarg.h>
#include <stddef.h>

#include <linux/kernel.h>
#include <linux/tty.h>
#include <cnbe.h>

/* 内核打印缓冲区 */
static char buf[1024];

/*
 * printk - 内核打印函数
 * 这是内核态的 printf 等价物。
 * 在 x86 中，由于 fs 寄存器可能指向用户空间，需要通过汇编保存/恢复 fs，
 * 然后调用 tty_write。RISC-V 采用扁平内存模型，无段寄存器，
 * 因此直接通过 C 调用即可。
 */
int printk(const char *fmt, ...)
{
	va_list args;
	int i;

	va_start(args, fmt);
	i = vsprintf(buf, fmt, args);
	va_end(args);

	/*
	 * RISC-V 注释: 以下 x86 汇编块在 RISC-V 中被替换为直接函数调用。
	 * 原始 x86 代码:
	 *   push %%fs
	 *   push %%ds
	 *   pop %%fs
	 *   pushl %0
	 *   pushl $_buf
	 *   pushl $0
	 *   call _tty_write
	 *   addl $8,%%esp
	 *   popl %0
	 *   pop %%fs
	 * RISC-V 无段寄存器，buf 在内核数据段，直接调用即可。
	 */
	(void)tty_write(0, buf, i);
	return i;
}
