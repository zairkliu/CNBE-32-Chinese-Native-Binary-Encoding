/*
 * RISC-V sched.h - 进程调度与任务结构
 * CNBE-32 移植版本
 * 
 * 原 x86 的 TSS/LDT/GDT 在 RISC-V 中不存在。
 * 任务切换通过保存/恢复通用寄存器实现。
 * 地址空间由 Sv39 页表管理。
 */

#ifndef _SCHED_H
#define _SCHED_H

#define NR_TASKS 64
#define HZ 100

#define FIRST_TASK task[0]
#define LAST_TASK task[NR_TASKS-1]

#include <linux/head.h>
#include <linux/fs.h>
#include <linux/mm.h>

#if (NR_OPEN > 32)
#error "Currently the close-on-exec-flags are in one word, max 32 files/proc"
#endif

#define TASK_RUNNING		0
#define TASK_INTERRUPTIBLE	1
#define TASK_UNINTERRUPTIBLE	2
#define TASK_ZOMBIE		3
#define TASK_STOPPED		4

#ifndef NULL
#define NULL ((void *) 0)
#endif

extern int copy_page_tables(unsigned long from, unsigned long to, long size);
extern int free_page_tables(unsigned long from, long size);

extern void sched_init(void);
extern void schedule(void);
extern void trap_init(void);
extern void panic(const char * str);
extern int tty_write(unsigned minor,char * buf,int count);

/* 函数指针类型 */
typedef int (*fn_ptr)();

/* RISC-V 浮点状态结构 - 保留以兼容旧代码，RISC-V 使用浮点寄存器 */
struct i387_struct {
	long	cwd;
	long	swd;
	long	twd;
	long	fip;
	long	fcs;
	long	foo;
	long	fos;
	long	st_space[20];	/* 8*10 bytes for each FP-reg = 80 bytes */
};

/* RISC-V 任务状态结构 - 替代 x86 的 TSS */
/* RISC-V 32 位通用寄存器保存区 */
struct tss_struct {
	/* RISC-V 没有 back_link/ss0/esp0 等概念，保留字段以兼容 */
	long	back_link;	/* 16 high bits zero */
	long	esp0;
	long	ss0;
	/* RISC-V 上下文：x1-x31 寄存器 */
	long	ra;		/* x1: 返回地址 (替代 eip) */
	long	sp;		/* x2: 栈指针 (替代 esp) */
	long	gp;		/* x3: 全局指针 */
	long	tp;		/* x4: 线程指针 */
	long	t0, t1, t2;	/* x5-x7: 临时寄存器 */
	long	s0, s1;		/* x8-x9: 保存寄存器 */
	long	a0, a1, a2, a3, a4, a5, a6, a7; /* x10-x17: 参数/返回值 */
	long	s2, s3, s4, s5, s6, s7, s8, s9, s10, s11; /* x18-x27 */
	long	t3, t4, t5, t6;	/* x28-x31: 临时寄存器 */
	long	epc;		/* mepc/sepc: 异常 PC (替代 eip) */
	long	status;		/* mstatus/sstatus: 状态寄存器 (替代 eflags) */
	long	cause;		/* mcause/scause: 异常原因 */
	long	badaddr;	/* mtval/stval: 错误地址 */
	/* 以下字段为 x86 兼容保留，RISC-V 中不使用段寄存器 */
	long	es;
	long	cs;
	long	ss;
	long	ds;
	long	fs;
	long	gs;
	long	ldt;
	long	trace_bitmap;
	struct i387_struct i387;
};

struct task_struct {
/* 状态字段 - 不可修改 */
	long state;	/* -1 不可运行, 0 可运行, >0 停止 */
	long counter;
	long priority;
	long signal;
	fn_ptr sig_restorer;
	fn_ptr sig_fn[32];
	long blocked;
/* 通用字段 */
	int exit_code;
	unsigned long end_code,end_data,brk,start_stack;
	long pid,father,pgrp,session,leader;
	unsigned short uid,euid,suid;
	unsigned short gid,egid,sgid;
	long alarm;
	long utime,stime,cutime,cstime,start_time;
	unsigned short used_math;
/* 文件系统信息 */
	int tty;		/* -1 表示无终端 */
	unsigned short umask;
	struct m_inode * pwd;
	struct m_inode * root;
	unsigned long close_on_exec;
	struct file * filp[NR_OPEN];
/* LDT - RISC-V 保留用于兼容，实际使用页表管理地址空间 */
	struct desc_struct ldt[3];
/* TSS - RISC-V 任务上下文 */
	struct tss_struct tss;
};

/*
 * INIT_TASK 设置第一个任务表
 * RISC-V 版本：页表基址指向 pg_dir，栈指针初始化
 */
#define INIT_TASK \
/* 状态等 */ { 0,15,15, \
/* 信号 */ 0,0,{(fn_ptr) 0,},0, \
/* ec,brk... */ 0,0,0,0,0, \
/* pid 等 */ 0,-1,0,0,0, \
/* uid 等 */ 0,0,0,0,0,0, \
/* alarm */ 0,0,0,0,0,0, \
/* math */ 0, \
/* fs 信息 */ -1,0133,NULL,NULL,0, \
/* filp */ {NULL,}, \
	{ \
		{0,0}, \
/* ldt - 保留以兼容，RISC-V 不使用 */ \
		{0x9f,0xc0fa00}, \
		{0x9f,0xc0f200}, \
	}, \
/* tss - RISC-V 上下文初始化 */ \
	{0,PAGE_SIZE+(long)&init_task,0x10, \
	 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, \
	 0,0,0,0,0,0,0,0,0,0x17,0x17,0x17,0x17,0x17,0x17, \
	 _LDT(0),0x80000000, \
	 {} \
	}, \
}

extern struct task_struct *task[NR_TASKS];
extern struct task_struct *last_task_used_math;
extern struct task_struct *current;
extern long volatile jiffies;
extern long startup_time;

#define CURRENT_TIME (startup_time+jiffies/HZ)

extern void sleep_on(struct task_struct ** p);
extern void interruptible_sleep_on(struct task_struct ** p);
extern void wake_up(struct task_struct ** p);

/*
 * RISC-V 没有 GDT/TSS/LDT 选择子概念。
 * 以下宏保留以保持代码兼容性，但功能已简化。
 */
#define FIRST_TSS_ENTRY 4
#define FIRST_LDT_ENTRY (FIRST_TSS_ENTRY+1)
#define _TSS(n) ((((unsigned long) n)<<4)+(FIRST_TSS_ENTRY<<3))
#define _LDT(n) ((((unsigned long) n)<<4)+(FIRST_LDT_ENTRY<<3))

/* ltr/lldt/str - RISC-V 无段加载指令，为空操作 */
#define ltr(n) do { (void)(n); } while(0)
#define lldt(n) do { (void)(n); } while(0)
#define str(n) do { (void)(n); } while(0)

/*
 * switch_to(n) - RISC-V 任务切换
 * 保存当前任务的通用寄存器，恢复目标任务寄存器。
 * RISC-V 使用 sret/mret 返回，不使用 x86 的 ljmp。
 */
#define switch_to(n) { \
    if (current != task[n]) { \
        struct task_struct *__prev = current; \
        struct task_struct *__next = task[n]; \
        __asm__ volatile ( \
            /* 保存当前上下文 */ \
            "sw ra, %c[ra](%[prev])\n\t" \
            "sw sp, %c[sp](%[prev])\n\t" \
            "sw s0, %c[s0](%[prev])\n\t" \
            "sw s1, %c[s1](%[prev])\n\t" \
            "sw s2, %c[s2](%[prev])\n\t" \
            "sw s3, %c[s3](%[prev])\n\t" \
            "sw s4, %c[s4](%[prev])\n\t" \
            "sw s5, %c[s5](%[prev])\n\t" \
            "sw s6, %c[s6](%[prev])\n\t" \
            "sw s7, %c[s7](%[prev])\n\t" \
            "sw s8, %c[s8](%[prev])\n\t" \
            "sw s9, %c[s9](%[prev])\n\t" \
            "sw s10, %c[s10](%[prev])\n\t" \
            "sw s11, %c[s11](%[prev])\n\t" \
            /* 恢复目标上下文 */ \
            "lw ra, %c[ra](%[next])\n\t" \
            "lw sp, %c[sp](%[next])\n\t" \
            "lw s0, %c[s0](%[next])\n\t" \
            "lw s1, %c[s1](%[next])\n\t" \
            "lw s2, %c[s2](%[next])\n\t" \
            "lw s3, %c[s3](%[next])\n\t" \
            "lw s4, %c[s4](%[next])\n\t" \
            "lw s5, %c[s5](%[next])\n\t" \
            "lw s6, %c[s6](%[next])\n\t" \
            "lw s7, %c[s7](%[next])\n\t" \
            "lw s8, %c[s8](%[next])\n\t" \
            "lw s9, %c[s9](%[next])\n\t" \
            "lw s10, %c[s10](%[next])\n\t" \
            "lw s11, %c[s11](%[next])\n\t" \
            : \
            : [prev] "r" (&__prev->tss), [next] "r" (&__next->tss), \
              [ra] "i" (__builtin_offsetof(struct tss_struct, ra)), \
              [sp] "i" (__builtin_offsetof(struct tss_struct, sp)), \
              [s0] "i" (__builtin_offsetof(struct tss_struct, s0)), \
              [s1] "i" (__builtin_offsetof(struct tss_struct, s1)), \
              [s2] "i" (__builtin_offsetof(struct tss_struct, s2)), \
              [s3] "i" (__builtin_offsetof(struct tss_struct, s3)), \
              [s4] "i" (__builtin_offsetof(struct tss_struct, s4)), \
              [s5] "i" (__builtin_offsetof(struct tss_struct, s5)), \
              [s6] "i" (__builtin_offsetof(struct tss_struct, s6)), \
              [s7] "i" (__builtin_offsetof(struct tss_struct, s7)), \
              [s8] "i" (__builtin_offsetof(struct tss_struct, s8)), \
              [s9] "i" (__builtin_offsetof(struct tss_struct, s9)), \
              [s10] "i" (__builtin_offsetof(struct tss_struct, s10)), \
              [s11] "i" (__builtin_offsetof(struct tss_struct, s11)) \
            : "memory"); \
        current = __next; \
        if (last_task_used_math == __prev) \
            last_task_used_math = NULL; \
    } \
}

/*
 * set_base/get_base - RISC-V 中地址空间由页表管理
 * 这些宏保留以保持代码兼容性，但功能已简化
 */
#define set_base(ldt, base) do { (ldt).a = (base); } while(0)
#define get_base(ldt) ((unsigned long)(ldt).a)

/*
 * get_limit - RISC-V 中地址空间大小由页表决定
 * 为兼容保留，返回一个较大值
 */
#define get_limit(segment) (0xFFFFFFFFUL)

#define PAGE_ALIGN(n) (((n)+0xfff)&0xfffff000)

#endif
