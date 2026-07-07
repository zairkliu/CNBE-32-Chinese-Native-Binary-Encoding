/*
 * system_call.S — 系统调用与中断处理 (RISC-V CNBE-32 转码版本)
 * 原始文件: linux/kernel/system_call.s
 *
 * 【RISC-V 转码状态】已完成核心架构迁移
 * - x86 int 0x80 → RISC-V ecall (环境调用)
 * - x86 系统调用号(eax) → RISC-V a7
 * - x86 参数(ebx,ecx,edx) → RISC-V a0,a1,a2
 * - x86 栈布局 → RISC-V trap frame 布局
 * - x86 iret → RISC-V mret
 * - x86 段寄存器 (ds/es/fs) → RISC-V 忽略 (无段式)
 * - x86 信号处理用户栈操作 → RISC-V 简化适配 (需完整信号帧实现)
 * - x86 8259 PIC EOI → RISC-V 无需 (使用 CLINT/PLIC)
 *
 * 【CNBE-32 集成点】
 * - 系统调用错误消息使用中文 UTF-8
 * - 关键路径注释使用中文
 * - 保留 _sys_call_table 符号供 C 代码填充
 */

#include <cnbe.h>

/* RISC-V CSR 定义 */
#define CSR_MSTATUS   0x300
#define CSR_MEPC      0x341

#define MSTATUS_MIE   0x00000008
#define MSTATUS_MPP   0x00001800

/* 任务结构偏移 (与 include/linux/sched.h 兼容) */
#define TASK_STATE      0
#define TASK_COUNTER    4
#define TASK_PRIORITY   8
#define TASK_SIGNAL     12
#define TASK_RESTORER   16
#define TASK_SIG_FN     20

#define SIG_CHLD        17
#define NR_SYSCALLS     67

/* 导出符号 */
.globl _system_call, _sys_fork, _timer_interrupt, _hd_interrupt, _sys_execve

.text

/* ============================================================
 * 系统调用入口 _system_call
 * 触发方式: 用户态执行 ecall 指令
 * 寄存器约定:
 *   a7 = 系统调用号 (对应 x86 eax)
 *   a0 = 参数1 (对应 x86 ebx)
 *   a1 = 参数2 (对应 x86 ecx)
 *   a2 = 参数3 (对应 x86 edx)
 *   a3-a5 = 参数4-6
 * 返回值: a0
 * ============================================================ */
.align 4
_system_call:
	/* 保存完整上下文 (构建 trap frame) */
	addi	sp, sp, -128
	sw	ra,   0(sp)
	sw	gp,   4(sp)
	sw	tp,   8(sp)
	sw	t0,  12(sp)
	sw	t1,  16(sp)
	sw	t2,  20(sp)
	sw	s0,  24(sp)
	sw	s1,  28(sp)
	sw	a0,  32(sp)       /* 保存原始参数1 (x86 ebx) */
	sw	a1,  36(sp)       /* 保存原始参数2 (x86 ecx) */
	sw	a2,  40(sp)       /* 保存原始参数3 (x86 edx) */
	sw	a3,  44(sp)
	sw	a4,  48(sp)
	sw	a5,  52(sp)
	sw	a6,  56(sp)
	sw	a7,  60(sp)       /* 保存系统调用号 */
	sw	s2,  64(sp)
	sw	s3,  68(sp)
	sw	s4,  72(sp)
	sw	s5,  76(sp)
	sw	s6,  80(sp)
	sw	s7,  84(sp)
	sw	s8,  88(sp)
	sw	s9,  92(sp)
	sw	s10, 96(sp)
	sw	s11, 100(sp)
	sw	t3, 104(sp)
	sw	t4, 108(sp)
	sw	t5, 112(sp)
	sw	t6, 116(sp)

	/* 保存 CSR */
	csrr	t0, CSR_MEPC
	sw	t0, 120(sp)      /* mepc (返回地址) */
	csrr	t0, CSR_MSTATUS
	sw	t0, 124(sp)      /* mstatus (特权级/中断状态) */

	/* 检查系统调用号 */
	li	t0, NR_SYSCALLS
	bgeu	a7, t0, _bad_syscall

	/* 调用 sys_call_table[a7] */
	la	t0, _sys_call_table
	slli	t1, a7, 2
	add	t0, t0, t1
	lw	t0, 0(t0)
	jalr	t0             /* 调用具体系统调用函数 */

	/* 保存返回值到 trap frame a0 */
	sw	a0, 32(sp)

_ret_from_syscall:
	/* 检查是否需要调度 */
	la	t0, _current
	lw	t0, 0(t0)
	lw	t1, TASK_STATE(t0)
	bnez	t1, _reschedule
	lw	t1, TASK_COUNTER(t0)
	beqz	t1, _reschedule

	/* =========================================================
	 * 信号处理 (简化适配)
	 * 原始 x86 代码在每个系统调用/定时器中断后扫描信号位图
	 * RISC-V 中保持相同逻辑，但用户栈帧构造需适配新 ABI
	 * ========================================================= */
	la	t0, _current
	lw	t0, 0(t0)
	la	t1, _task
	lw	t1, 0(t1)
	beq	t0, t1, .L_syscall_done    /* task[0] 不能有信号 */

	/* 检查是否来自用户态 (mstatus.MPP == 00, U-mode) */
	lw	t2, 124(sp)
	li	t3, MSTATUS_MPP
	and	t2, t2, t3
	bnez	t2, .L_syscall_done       /* MPP != 0 表示内核态，不处理信号 */

.L_signal_check:
	la	t0, _current
	lw	t0, 0(t0)
	lw	t1, TASK_SIGNAL(t0)
	beqz	t1, .L_syscall_done

	/* 找到第一个置位的信号 (RISC-V 无 bsf 指令，软件实现) */
	li	t2, 0
.L_find_sig:
	li	t3, 1
	sll	t3, t3, t2
	and	t3, t3, t1
	bnez	t3, .L_found_sig
	addi	t2, t2, 1
	li	t3, 32
	blt	t2, t3, .L_find_sig
	j	.L_syscall_done

.L_found_sig:
	/* 清除该信号位 */
	li	t3, 1
	sll	t3, t3, t2
	not	t3, t3
	and	t1, t1, t3
	sw	t1, TASK_SIGNAL(t0)

	/* 获取信号处理函数 */
	la	t3, TASK_SIG_FN(t0)
	slli	t4, t2, 2
	add	t3, t3, t4
	lw	t3, 0(t3)

	beqz	t3, .L_default_signal      /* 0 = 默认处理 (退出) */
	li	t4, 1
	beq	t3, t4, .L_signal_check     /* 1 = 忽略 */

	/* 重置信号处理函数地址 */
	sw	zero, 0(t3)

	/* 信号号转为 1-based */
	addi	t2, t2, 1

	/* 【CNBE-32 注释】用户栈信号帧构造
	 * 原始 x86 代码通过 fs 段在用户栈上构造信号恢复帧
	 * RISC-V 无段寄存器，需直接操作用户态 sp (trap frame offset 4)
	 * 此处为简化框架，实际生产环境需完整实现 RISC-V 信号帧布局
	 * 包括保存 mepc, a0-a7, 及信号恢复器地址 (restorer)
	 */
	/* TODO: 完整的 RISC-V 信号帧压栈实现 */

	j	.L_signal_check

.L_default_signal:
	addi	t2, t2, 1
	li	t3, SIG_CHLD
	beq	t2, t3, .L_signal_check

	addi	sp, sp, -8
	sw	ra, 0(sp)
	sw	t2, 4(sp)
	mv	a0, t2
	la	t0, _do_exit
	jalr	t0
	lw	ra, 0(sp)
	lw	t2, 4(sp)
	addi	sp, sp, 8
	j	.L_signal_check

.L_syscall_done:
	/* 恢复 CSR */
	lw	t0, 120(sp)
	csrw	CSR_MEPC, t0
	lw	t0, 124(sp)
	csrw	CSR_MSTATUS, t0

	/* 恢复寄存器 */
	lw	ra,   0(sp)
	lw	gp,   4(sp)
	lw	tp,   8(sp)
	lw	t0,  12(sp)
	lw	t1,  16(sp)
	lw	t2,  20(sp)
	lw	s0,  24(sp)
	lw	s1,  28(sp)
	lw	a0,  32(sp)
	lw	a1,  36(sp)
	lw	a2,  40(sp)
	lw	a3,  44(sp)
	lw	a4,  48(sp)
	lw	a5,  52(sp)
	lw	a6,  56(sp)
	lw	a7,  60(sp)
	lw	s2,  64(sp)
	lw	s3,  68(sp)
	lw	s4,  72(sp)
	lw	s5,  76(sp)
	lw	s6,  80(sp)
	lw	s7,  84(sp)
	lw	s8,  88(sp)
	lw	s9,  92(sp)
	lw	s10, 96(sp)
	lw	s11, 100(sp)
	lw	t3, 104(sp)
	lw	t4, 108(sp)
	lw	t5, 112(sp)
	lw	t6, 116(sp)
	addi	sp, sp, 128
	mret

/* ============================================================ */
_bad_syscall:
	li	a0, -1
	sw	a0, 32(sp)
	j	.L_syscall_done

_reschedule:
	addi	sp, sp, -4
	sw	ra, 0(sp)
	la	t0, _schedule
	jalr	t0
	lw	ra, 0(sp)
	addi	sp, sp, 4
	j	_ret_from_syscall

/* ============================================================
 * _timer_interrupt: 定时器中断处理
 * 原始 x86 使用 8253 PIT + 8259 PIC
 * RISC-V 使用 CLINT (Core Local Interruptor) 或 PLIC 定时器
 * ============================================================ */
.align 4
_timer_interrupt:
	addi	sp, sp, -48
	sw	ra,  0(sp)
	sw	t0,  4(sp)
	sw	t1,  8(sp)
	sw	a0, 12(sp)
	sw	a1, 16(sp)
	sw	a2, 20(sp)
	sw	a3, 24(sp)
	sw	a4, 28(sp)
	sw	a5, 32(sp)
	sw	a6, 36(sp)
	sw	a7, 40(sp)
	sw	s0, 44(sp)

	/* 增加 jiffies */
	la	t0, _jiffies
	lw	t1, 0(t0)
	addi	t1, t1, 1
	sw	t1, 0(t0)

	/* 【CNBE-32 注释】RISC-V 定时器中断无需 x86 8259 PIC EOI
	 * 原始 x86: outb $0x20, $0x20 (主片 EOI)
	 * RISC-V 替代: CLINT 定时器中断由 mtimecmp 自动管理
	 * 需在内核 C 代码中设置下次定时器中断值
	 */

	/* 提取特权级作为 do_timer 参数 (CPL) */
	csrr	a0, CSR_MSTATUS
	li	t0, MSTATUS_MPP
	and	a0, a0, t0
	srli	a0, a0, 11

	/* 调用 do_timer(CPL) */
	la	t0, _do_timer
	jalr	t0

	/* 恢复并进入系统调用返回路径 */
	lw	ra,  0(sp)
	lw	t0,  4(sp)
	lw	t1,  8(sp)
	lw	a0, 12(sp)
	lw	a1, 16(sp)
	lw	a2, 20(sp)
	lw	a3, 24(sp)
	lw	a4, 28(sp)
	lw	a5, 32(sp)
	lw	a6, 36(sp)
	lw	a7, 40(sp)
	lw	s0, 44(sp)
	addi	sp, sp, 48
	j	_ret_from_syscall

/* ============================================================
 * _sys_execve: execve 系统调用包装
 * 原始 x86: lea EIP(%esp),%eax; pushl %eax; call _do_execve
 * RISC-V: 传递 mepc 地址作为参数 (指向用户返回地址)
 * ============================================================ */
.align 4
_sys_execve:
	/* 此时 sp 仍指向 _system_call 的 trap frame */
	mv	a0, sp
	addi	a0, a0, 120      /* &mepc (对应 x86 &eip) */
	la	t0, _do_execve
	jalr	t0
	ret

/* ============================================================
 * _sys_fork: fork 系统调用包装
 * 原始 x86 通过栈传递 copy_process 的 17 个参数
 * RISC-V 通过寄存器 + 栈传递，从 trap frame 提取寄存器值
 * ============================================================ */
.align 4
_sys_fork:
	mv	s0, sp              /* s0 = trap frame 基址 */
	addi	sp, sp, -40      /* 为 copy_process 的 9 个栈参数分配空间 */
	sw	ra, 36(sp)

	/* 调用 find_empty_process()，返回值 nr 在 a0 */
	la	t0, _find_empty_process
	jalr	t0
	bltz	a0, .L_fork_done

	mv	t0, a0              /* t0 = nr */

	/* 前 8 个参数通过寄存器 a0-a7 */
	mv	a0, t0              /* nr */
	lw	a1, 28(s0)          /* ebp (x86 ebp = s0) */
	lw	a2, 72(s0)          /* edi (x86 edi = s3) */
	lw	a3, 68(s0)          /* esi (x86 esi = s2) */
	li	a4, 0               /* gs (RISC-V 无段寄存器) */
	li	a5, 0               /* none */
	lw	a6, 32(s0)          /* ebx (x86 ebx = a0) */
	lw	a7, 36(s0)          /* ecx (x86 ecx = a1) */

	/* 剩余 9 个参数通过栈传递 */
	lw	t0, 40(s0)          /* edx (x86 edx = a2) */
	sw	t0, 0(sp)
	li	t0, 0               /* fs (RISC-V 无) */
	sw	t0, 4(sp)
	li	t0, 0               /* es (RISC-V 无) */
	sw	t0, 8(sp)
	li	t0, 0               /* ds (RISC-V 无) */
	sw	t0, 12(sp)
	lw	t0, 120(s0)         /* eip (mepc) */
	sw	t0, 16(sp)
	li	t0, 0               /* cs (RISC-V 无) */
	sw	t0, 20(sp)
	lw	t0, 124(s0)         /* eflags (mstatus) */
	sw	t0, 24(sp)
	lw	t0, 4(s0)           /* esp (原始 sp) */
	sw	t0, 28(sp)
	li	t0, 0               /* ss (RISC-V 无) */
	sw	t0, 32(sp)

	la	t0, _copy_process
	jalr	t0

.L_fork_done:
	lw	ra, 36(sp)
	addi	sp, sp, 40
	ret

/* ============================================================
 * _hd_interrupt: 硬盘中断处理
 * 原始 x86 使用 8259 PIC 级联中断
 * RISC-V 使用 PLIC (Platform Level Interrupt Controller)
 * ============================================================ */
.align 4
_hd_interrupt:
	addi	sp, sp, -28
	sw	ra,  0(sp)
	sw	t0,  4(sp)
	sw	t1,  8(sp)
	sw	a0, 12(sp)
	sw	a1, 16(sp)
	sw	a2, 20(sp)
	sw	a3, 24(sp)

	/* 【CNBE-32 注释】RISC-V 硬盘中断无需 x86 8259 EOI 序列
	 * 原始 x86: outb $0x20, $0x20 (主片) + outb $0x20, $0xA0 (从片)
	 * RISC-V 替代: PLIC 通过内存映射完成通知，由驱动处理
	 */

	/* 调用 do_hd 或 unexpected_hd_interrupt */
	la	t0, _do_hd
	lw	t0, 0(t0)
	beqz	t0, .L_unexpected_hd
	jalr	t0
	j	.L_hd_done

.L_unexpected_hd:
	la	t0, _unexpected_hd_interrupt
	jalr	t0

.L_hd_done:
	lw	ra,  0(sp)
	lw	t0,  4(sp)
	lw	t1,  8(sp)
	lw	a0, 12(sp)
	lw	a1, 16(sp)
	lw	a2, 20(sp)
	lw	a3, 24(sp)
	addi	sp, sp, 28
	mret
