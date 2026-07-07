/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/write.c
 * 变更说明:
 *   - 原 _syscall3 宏生成 x86 `int $0x80` 汇编
 *   - 替换为直接 RISC-V `ecall` 内联汇编
 *   - 寄存器: a7 = __NR_write, a0 = fd, a1 = buf, a2 = count
 * CNBE-32: 支持写入中文 UTF-8 字符串，保留核心函数命名
 */

#define __LIBRARY__
#include <unistd.h>

int write(int fd, const char * buf, off_t count)
{
	int __res;
	register long a7 __asm__("a7") = __NR_write;
	register long a0 __asm__("a0") = fd;
	register long a1 __asm__("a1") = (long)buf;
	register long a2 __asm__("a2") = count;

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
