/* 
 * file_table.c - 文件表定义
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: 无 x86 特定代码，仅添加中文注释
 */
#include <linux/fs.h>
#include <cnbe.h>

struct file file_table[NR_FILE];
