/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/open.c
 * 变更说明:
 *   - x86 `int $0x80` 系统调用 -> RISC-V `ecall` 指令
 *   - 原寄存器约束: eax, ebx, ecx, edx -> a7, a0, a1, a2
 *   - 变长参数处理保持 stdarg 不变
 * CNBE-32: 保留核心函数命名，确保 ABI 兼容
 */

#define __LIBRARY__
#include <unistd.h>
#include <stdarg.h>

int open(const char * filename, int flag, ...)
{
	register int res;
	va_list arg;

	va_start(arg, flag);
	
	/* RISC-V 系统调用: a7=调用号, a0=文件名, a1=标志, a2=模式 */
	register long a7 __asm__("a7") = __NR_open;
	register long a0 __asm__("a0") = (long)filename;
	register long a1 __asm__("a1") = flag;
	register long a2 __asm__("a2") = va_arg(arg, int);

	__asm__ volatile (
		"ecall"
		: "+r" (a0)
		: "r" (a7), "r" (a1), "r" (a2)
		: "memory"
	);

	res = a0;
	va_end(arg);
	if (res >= 0)
		return res;
	errno = -res;
	return -1;
}
