/*
 * CNBE-32 中文 BASIC 解释器头文件
 * Linux 0.01 RISC-V 内核版本
 * 全中文关键字 — 零英文依赖
 */

#ifndef _CNBE_BASIC_H
#define _CNBE_BASIC_H

/* 解释器接口 */
int cnbe_basic_eval(const char *line);
void cnbe_basic_run(void);

/* Shell 接口 */
void cnbe_shell_run(void);

#endif /* _CNBE_BASIC_H */
