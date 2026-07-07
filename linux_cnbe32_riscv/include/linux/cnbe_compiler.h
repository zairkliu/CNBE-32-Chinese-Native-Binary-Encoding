/*
 * CNBE-32 中文编译器头文件
 * 将中文源代码编译为字节码并执行
 * 全中文关键字 — 零英文依赖
 */

#ifndef _CNBE_COMPILER_H
#define _CNBE_COMPILER_H

/* 编译并执行中文源代码 */
int cnbe_compile_and_run(const char *source);

/* 仅编译，返回字节码长度 */
int cnbe_compile(const char *source, unsigned char *bytecode, int max_size);

/* 执行字节码 */
int cnbe_execute(unsigned char *bytecode, int size);

/* 交互式编译器外壳 */
void cnbe_compiler_shell(void);

#endif /* _CNBE_COMPILER_H */
