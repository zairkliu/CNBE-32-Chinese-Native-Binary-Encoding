/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/panic.c
 * 状态: 已完成转码
 * 变更:
 *   - 英文内核消息 → 中文 UTF-8 消息
 *   - 添加 CNBE-32 注释
 *   - 添加死循环保护说明
 * 
 * 【内核恐慌】此函数在整个内核中被调用(包括 mm 和 fs 子系统)
 * 用于指示严重问题。
 */

#include <linux/kernel.h>
#include <cnbe.h>
#include <asm/system.h>

volatile void panic(const char * s)
{
	/*
	 * RISC-V 注：panic 时首先禁用中断，防止进一步破坏。
	 * 原 x86 的 cli 映射为 csr_clear(mstatus, MSTATUS_MIE)。
	 */
	cli();
	/* 使用中文 UTF-8 输出内核恐慌信息 */
	printk("【内核恐慌】%s\n\r",s);
	
	/*
	 * CNBE-32 集成点：此处可调用 cnhe_map 记录恐慌消息到 CNBE-32 编码日志。
	 * 示例: cnhe_map((const unsigned char *)s, strlen(s));
	 * 但由于 panic 后系统不再运行，实际意义有限。
	 */
	
	/* 进入无限循环，停止系统运行 */
	for(;;)
		;
}
