/*
 * asm.S — 低级硬件异常处理入口 (RISC-V CNBE-32 转码版本)
 * 原始文件: linux/kernel/asm.s
 * 
 * 【RISC-V 转码状态】已完成核心架构迁移
 * - x86 IDT 多硬件入口 → RISC-V mtvec 统一入口 + 软件向量表分发
 * - x86 push/pop 寄存器 → RISC-V sw/lw 保存/恢复
 * - x86 iret → RISC-V mret
 * - x86 段寄存器 (ds/es/fs) → RISC-V 已移除 (无段式内存管理)
 * - x86 CR0/TS/EM 浮点管理 → RISC-V mstatus.FS 字段
 * - 页异常由 mm 子系统处理，不在此处定义
 * 
 * 【CNBE-32 集成点】
 * - 异常消息通过 cnbe_printk 输出中文诊断信息
 * - 保留核心函数命名以保证跨文件 ABI 兼容
 */

#include <cnbe.h>

/* RISC-V CSR 数值 (避免依赖未安装的 csr.h) */
#define CSR_MSTATUS   0x300
#define CSR_MEPC      0x341
#define CSR_MCAUSE    0x342
#define CSR_MTVAL     0x343
#define CSR_MTVEC     0x305

#define MSTATUS_MIE   0x00000008
#define MSTATUS_MPP   0x00001800
#define MSTATUS_FS    0x00006000

/* 导出符号：供 traps.c 设置 mtvec 和向量表引用 */
.globl _trap_entry
.globl _trap_vector_table

/* 异常处理函数入口 (供向量表和 traps.c 链接) */
.globl _divide_error, _debug, _nmi, _int3, _overflow, _bounds, _invalid_op
.globl _device_not_available, _double_fault, _coprocessor_segment_overrun
.globl _invalid_TSS, _segment_not_present, _stack_segment
.globl _general_protection, _coprocessor_error, _reserved

.text
.align 4

/* ============================================================
 * _trap_entry: RISC-V 统一异常/中断入口
 * 硬件触发: 所有同步异常和外部中断均跳转至此
 * 软件行为: 保存完整上下文 → 读取 mcause → 向量表分发
 * ============================================================ */
_trap_entry:
	/* 保存所有通用寄存器 (构建 trap frame) */
	addi	sp, sp, -144
	sw	x1,   0(sp)       /* ra */
	sw	x3,   8(sp)       /* gp */
	sw	x4,  12(sp)       /* tp */
	sw	x5,  16(sp)       /* t0 */
	sw	x6,  20(sp)       /* t1 */
	sw	x7,  24(sp)       /* t2 */
	sw	x8,  28(sp)       /* s0/fp (对应 x86 ebp) */
	sw	x9,  32(sp)       /* s1 */
	sw	x10, 36(sp)       /* a0 (对应 x86 eax) */
	sw	x11, 40(sp)       /* a1 (对应 x86 ebx) */
	sw	x12, 44(sp)       /* a2 (对应 x86 ecx) */
	sw	x13, 48(sp)       /* a3 (对应 x86 edx) */
	sw	x14, 52(sp)       /* a4 */
	sw	x15, 56(sp)       /* a5 */
	sw	x16, 60(sp)       /* a6 */
	sw	x17, 64(sp)       /* a7 (系统调用号) */
	sw	x18, 68(sp)       /* s2 (对应 x86 esi) */
	sw	x19, 72(sp)       /* s3 (对应 x86 edi) */
	sw	x20, 76(sp)       /* s4 */
	sw	x21, 80(sp)       /* s5 */
	sw	x22, 84(sp)       /* s6 */
	sw	x23, 88(sp)       /* s7 */
	sw	x24, 92(sp)       /* s8 */
	sw	x25, 96(sp)       /* s9 */
	sw	x26, 100(sp)      /* s10 */
	sw	x27, 104(sp)      /* s11 */
	sw	x28, 108(sp)      /* t3 */
	sw	x29, 112(sp)      /* t4 */
	sw	x30, 116(sp)      /* t5 */
	sw	x31, 120(sp)      /* t6 */

	/* 保存原始 sp (用户态或内核态) */
	addi	t0, sp, 144
	sw	t0, 4(sp)

	/* 保存 CSR (关键上下文) */
	csrr	t0, CSR_MEPC
	sw	t0, 124(sp)      /* mepc (对应 x86 eip) */
	csrr	t0, CSR_MSTATUS
	sw	t0, 128(sp)      /* mstatus (对应 x86 eflags/特权级) */
	csrr	t0, CSR_MCAUSE
	sw	t0, 132(sp)      /* mcause (异常原因) */
	csrr	t0, CSR_MTVAL
	sw	t0, 136(sp)      /* mtval (异常值/地址) */

	/* 保存 trap frame 基址到 s0 (供各处理函数访问) */
	mv	s0, sp

	/* 根据 mcause 分派 (同步异常码 0-15) */
	csrr	a0, CSR_MCAUSE
	li	t1, 0x7FFFFFFF
	and	a0, a0, t1       /* 屏蔽中断位，获取异常码 */
	li	t1, 16
	bgeu	a0, t1, .L_reserved_dispatch  /* >= 16 → 保留异常 */

	/* 查向量表 */
	la	t1, trap_vector_table
	slli	t0, a0, 2
	add	t1, t1, t0
	lw	t0, 0(t1)
	jalr	t0               /* 跳转到 _divide_error 等处理函数 */
	/* 各处理函数返回后继续执行统一恢复路径 */

.L_restore_and_mret:
	/* 恢复 CSR */
	lw	t0, 124(sp)
	csrw	CSR_MEPC, t0
	lw	t0, 128(sp)
	csrw	CSR_MSTATUS, t0

	/* 恢复所有通用寄存器 */
	lw	x1,   0(sp)
	lw	x3,   8(sp)
	lw	x4,  12(sp)
	lw	x5,  16(sp)
	lw	x6,  20(sp)
	lw	x7,  24(sp)
	lw	x8,  28(sp)
	lw	x9,  32(sp)
	lw	x10, 36(sp)
	lw	x11, 40(sp)
	lw	x12, 44(sp)
	lw	x13, 48(sp)
	lw	x14, 52(sp)
	lw	x15, 56(sp)
	lw	x16, 60(sp)
	lw	x17, 64(sp)
	lw	x18, 68(sp)
	lw	x19, 72(sp)
	lw	x20, 76(sp)
	lw	x21, 80(sp)
	lw	x22, 84(sp)
	lw	x23, 88(sp)
	lw	x24, 92(sp)
	lw	x25, 96(sp)
	lw	x26, 100(sp)
	lw	x27, 104(sp)
	lw	x28, 108(sp)
	lw	x29, 112(sp)
	lw	x30, 116(sp)
	lw	x31, 120(sp)
	lw	x2,   4(sp)       /* 恢复原始 sp */
	addi	sp, sp, 144
	mret

.L_reserved_dispatch:
	la	t0, _reserved
	jalr	t0
	j	.L_restore_and_mret

/* ============================================================
 * 异常向量表 (mcause 索引 0-15)
 * 对应 x86 IDT 0-15 项，供 _trap_entry 查询
 * ============================================================ */
.section .rodata
.align 4
trap_vector_table:
	.word	_divide_error              /* 0:  除零错误 (Instruction address misaligned) */
	.word	_debug                     /* 1:  调试异常 / 访问故障 */
	.word	_nmi                       /* 2:  NMI (RISC-V 中通常映射为保留) */
	.word	_int3                      /* 3:  断点 / 加载地址错位 */
	.word	_overflow                   /* 4:  溢出 / 加载访问故障 */
	.word	_bounds                     /* 5:  边界检查 / 存储地址错位 */
	.word	_invalid_op                 /* 6:  非法指令 */
	.word	_device_not_available       /* 7:  设备不可用 / 断点 */
	.word	_double_fault               /* 8:  双重故障 / 用户环境调用 */
	.word	_coprocessor_segment_overrun /* 9: 协处理器段溢出 */
	.word	_invalid_TSS                /* 10: 无效 TSS */
	.word	_segment_not_present       /* 11: 段不存在 */
	.word	_stack_segment              /* 12: 栈段错误 / 指令访问故障 */
	.word	_general_protection         /* 13: 通用保护 / 加载页面故障 */
	.word	_page_fault                 /* 14: 页故障 (由 mm/page.s 处理) */
	.word	_reserved                   /* 15: 保留 */

.text

/* ============================================================
 * 无错误码异常处理入口 (no_error_code 类型)
 * 原始 x86 中由 IDT 直接跳入，RISC-V 中由 _trap_entry 统一分发调用
 * 参数约定: s0 = trap frame 基址
 * ============================================================ */

.align 4
_divide_error:
	/* 【CNBE-32 注释】除零错误：算术运算异常，需终止进程 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_divide_error
	jalr	t0
	ret

.align 4
_debug:
	/* 【CNBE-32 注释】调试异常：RISC-V 通过 dcsr 管理，此处兼容保留 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_int3          /* 原始 x86 debug 映射到 do_int3 */
	jalr	t0
	ret

.align 4
_nmi:
	/* 【CNBE-32 注释】NMI：RISC-V 无独立 NMI，通常映射为高优先级中断 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_nmi
	jalr	t0
	ret

.align 4
_int3:
	/* 【CNBE-32 注释】断点异常：RISC-V 使用 ebreak 指令触发 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_int3
	jalr	t0
	ret

.align 4
_overflow:
	mv	a0, s0
	li	a1, 0
	la	t0, _do_overflow
	jalr	t0
	ret

.align 4
_bounds:
	mv	a0, s0
	li	a1, 0
	la	t0, _do_bounds
	jalr	t0
	ret

.align 4
_invalid_op:
	/* 【CNBE-32 注释】非法指令：RISC-V 中 mcause=2 或 mcause=6 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_invalid_op
	jalr	t0
	ret

.align 4
_device_not_available:
	/* 【CNBE-32 注释】RISC-V 浮点单元通过 mstatus.FS 位管理状态 */
	/* 原始 x86 检查 CR0.EM/TS，此处映射为 mstatus.FS 检查 */
	csrr	t0, CSR_MSTATUS
	li	t1, MSTATUS_FS
	and	t0, t0, t1
	li	t1, 0x2000            /* FS = Initial (01) */
	ble	t0, t1, .L_math_emulate

	/* 浮点可用：清除 TS (设置 FS = Dirty) */
	csrr	t0, CSR_MSTATUS
	li	t1, MSTATUS_FS
	or	t0, t0, t1           /* FS = 3 (Dirty) */
	csrw	CSR_MSTATUS, t0

	/* 检查是否需要恢复浮点状态 */
	la	t0, _current
	lw	t0, 0(t0)
	la	t1, _last_task_used_math
	lw	t1, 0(t1)
	beq	t0, t1, 1f

	addi	sp, sp, -16
	sw	ra, 0(sp)
	la	t0, _math_state_restore
	jalr	t0
	lw	ra, 0(sp)
	addi	sp, sp, 16
1:
	ret

.L_math_emulate:
	/* 数学仿真路径 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_device_not_available
	jalr	t0
	ret

.align 4
_coprocessor_segment_overrun:
	mv	a0, s0
	li	a1, 0
	la	t0, _do_coprocessor_segment_overrun
	jalr	t0
	ret

.align 4
_reserved:
	mv	a0, s0
	li	a1, 0
	la	t0, _do_reserved
	jalr	t0
	ret

.align 4
_coprocessor_error:
	mv	a0, s0
	li	a1, 0
	la	t0, _do_coprocessor_error
	jalr	t0
	ret

/* ============================================================
 * 有错误码异常处理入口 (error_code 类型)
 * 原始 x86 中 IDT 提供错误码，RISC-V 无硬件错误码，软件模拟为 0
 * ============================================================ */

.align 4
_double_fault:
	mv	a0, s0
	li	a1, 0                   /* RISC-V 无硬件错误码 */
	la	t0, _do_double_fault
	jalr	t0
	ret

.align 4
_invalid_TSS:
	/* 【CNBE-32 注释】RISC-V 无 TSS 概念，保留兼容符号 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_invalid_TSS
	jalr	t0
	ret

.align 4
_segment_not_present:
	/* 【CNBE-32 注释】RISC-V 无段式，此异常保留为兼容 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_segment_not_present
	jalr	t0
	ret

.align 4
_stack_segment:
	/* 【CNBE-32 注释】RISC-V 无栈段寄存器，栈错误映射为访问故障 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_stack_segment
	jalr	t0
	ret

.align 4
_general_protection:
	/* 【CNBE-32 注释】RISC-V 无保护环/段检查，GPF 映射为权限故障 */
	mv	a0, s0
	li	a1, 0
	la	t0, _do_general_protection
	jalr	t0
	ret

/* 页异常入口符号 (由 mm/page.s 实际定义) */
.globl _page_fault

/* ============================================================ */
