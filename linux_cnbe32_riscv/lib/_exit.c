/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/_exit.c
 * 变更说明:
 *   - x86 `int $0x80` 系统调用 -> RISC-V `ecall` 指令
 *   - 寄存器约束: eax/ebx -> a7/a0
 *   - 保留 _exit 函数签名，确保 ABI 兼容
 * CNBE-32: 保留核心函数命名，关键注释已转码为中文
 */

#define __LIBRARY__
#include <unistd.h>

volatile void _exit(int exit_code)
{
	/* RISC-V 系统调用 ABI: a7 = 调用号, a0 = 参数/返回值 */
	register long a7 __asm__("a7") = __NR_exit;
	register long a0 __asm__("a0") = exit_code;

	__asm__ volatile (
		"ecall"
		:
		: "r" (a7), "r" (a0)
		: "memory"
	);
}
