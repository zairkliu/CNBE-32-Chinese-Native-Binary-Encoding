/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/close.c
 * 变更说明:
 *   - 原 _syscall1 宏生成 x86 `int $0x80` 汇编
 *   - 替换为直接 RISC-V `ecall` 内联汇编
 *   - 寄存器: a7 = 调用号(__NR_close), a0 = fd
 * CNBE-32: 保留核心函数命名，关键注释已转码为中文
 */

#define __LIBRARY__
#include <unistd.h>

int close(int fd)
{
	int __res;
	register long a7 __asm__("a7") = __NR_close;
	register long a0 __asm__("a0") = fd;

	__asm__ volatile (
		"ecall"
		: "+r" (a0)
		: "r" (a7)
		: "memory"
	);

	__res = a0;
	if (__res >= 0)
		return __res;
	errno = -__res;
	return -1;
}
