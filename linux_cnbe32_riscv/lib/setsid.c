/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/setsid.c
 * 变更说明:
 *   - 原 _syscall0 宏生成 x86 `int $0x80` 汇编
 *   - 替换为直接 RISC-V `ecall` 内联汇编
 *   - 寄存器: a7 = __NR_setsid, a0 = 返回值
 * CNBE-32: 保留核心函数命名
 */

#define __LIBRARY__
#include <unistd.h>

pid_t setsid(void)
{
	pid_t __res;
	register long a7 __asm__("a7") = __NR_setsid;
	register long a0 __asm__("a0");

	__asm__ volatile (
		"ecall"
		: "=r" (a0)
		: "r" (a7)
		: "memory"
	);

	__res = a0;
	if (__res >= 0)
		return __res;
	errno = -__res;
	return -1;
}
