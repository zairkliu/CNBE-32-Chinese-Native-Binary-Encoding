/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/wait.c
 * 变更说明:
 *   - 原 _syscall3 宏生成 x86 `int $0x80` 汇编
 *   - 替换为直接 RISC-V `ecall` 内联汇编
 *   - 寄存器: a7 = __NR_waitpid, a0 = pid, a1 = wait_stat, a2 = options
 * CNBE-32: 保留核心函数命名
 */

#define __LIBRARY__
#include <unistd.h>
#include <sys/wait.h>

pid_t waitpid(pid_t pid, int * wait_stat, int options)
{
	pid_t __res;
	register long a7 __asm__("a7") = __NR_waitpid;
	register long a0 __asm__("a0") = pid;
	register long a1 __asm__("a1") = (long)wait_stat;
	register long a2 __asm__("a2") = options;

	__asm__ volatile (
		"ecall"
		: "+r" (a0)
		: "r" (a7), "r" (a1), "r" (a2)
		: "memory"
	);

	__res = a0;
	if (__res < 0) {
		errno = -__res;
		return -1;
	}
	return __res;
}

pid_t wait(int * wait_stat)
{
	return waitpid(-1, wait_stat, 0);
}
