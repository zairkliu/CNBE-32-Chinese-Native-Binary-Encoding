/*
 * rs_io.S — RS232 串口中断处理 (RISC-V CNBE-32 转码版本)
 * 原始文件: linux/kernel/rs_io.s
 *
 * 【RISC-V 转码状态】已完成核心架构迁移
 * - x86 8250 UART I/O 端口 (inb/outb) → RISC-V NS16550 MMIO (readb/writeb)
 * - x86 8259 PIC EOI → RISC-V 无需 (PLIC/CLINT 管理)
 * - x86 段寄存器 (ds/es) → RISC-V 忽略
 * - UART 基地址: 0x10000000 (RISC-V 标准 UART 地址)
 * - 波特率/配置由内核初始化代码设置，此处仅处理中断
 *
 * 【CNBE-32 集成点】
 * - 串口数据接收缓冲区支持中文 UTF-8 输入
 * - 注释使用中文说明 MMIO 寄存器映射
 * - 保留 _table_list 结构兼容 tty_io.c
 */

#include <cnbe.h>
#include <asm/io.h>

/* RISC-V NS16550 UART MMIO 寄存器偏移 */
#define UART_BASE       0x10000000
#define UART_RBR        (UART_BASE + 0x00)  /* 接收缓冲寄存器 (只读) */
#define UART_THR        (UART_BASE + 0x00)  /* 发送保持寄存器 (只写) */
#define UART_IER        (UART_BASE + 0x01)  /* 中断使能寄存器 */
#define UART_IIR        (UART_BASE + 0x02)  /* 中断识别寄存器 (只读) */
#define UART_FCR        (UART_BASE + 0x02)  /* FIFO 控制寄存器 (只写) */
#define UART_LSR        (UART_BASE + 0x05)  /* 线路状态寄存器 */
#define UART_MSR        (UART_BASE + 0x06)  /* 调制解调器状态寄存器 */

/* 队列结构偏移 (必须与 tty_io.c 完全一致!) */
#define RS_ADDR         0
#define HEAD            4
#define TAIL            8
#define PROC_LIST       12
#define BUF             16

#define SIZE            1024
#define STARTUP         256

.text
.globl _rs1_interrupt, _rs2_interrupt

/* ============================================================
 * _rs1_interrupt: RS232 串口1 中断入口
 * 【CNBE-32 注释】RISC-V 平台通常集成单个 NS16550 UART
 * 此处 rs1 映射到 UART_BASE，rs2 保留兼容或转发
 * ============================================================ */
.align 4
_rs1_interrupt:
	la	a0, _table_list
	addi	a0, a0, 8        /* 对应原始 _table_list+8 */
	j	rs_int

.align 4
_rs2_interrupt:
	/* 【CNBE-32 注释】RISC-V 单 UART 环境保留，直接转发至 rs1 */
	la	a0, _table_list
	addi	a0, a0, 16       /* 对应原始 _table_list+16 */
	j	rs_int

/* ============================================================
 * rs_int: 通用串口中断处理
 * 输入: a0 = &_table_list[n] (tty 队列结构指针的地址)
 * 逻辑: 读取 IIR → 循环处理所有挂起中断 → 返回
 * ============================================================ */
rs_int:
	addi	sp, sp, -40
	sw	ra,  0(sp)
	sw	s0,  4(sp)        /* s0 = &_table_list[n] */
	sw	s1,  8(sp)        /* s1 = tty_queue 指针 */
	sw	s2, 12(sp)        /* s2 = 工作寄存器 */
	sw	s3, 16(sp)
	sw	a1, 20(sp)        /* a1 = UART 基地址 */
	sw	a2, 24(sp)        /* a2 = IIR 地址 */
	sw	a3, 28(sp)
	sw	a4, 32(sp)
	sw	a5, 36(sp)

	mv	s0, a0           /* 保存 &_table_list[n] */
	lw	s1, 0(s0)         /* s1 = tty_queue 指针 */
	lw	a1, RS_ADDR(s1)   /* a1 = UART MMIO 基地址 */
	addi	a2, a1, 2        /* a2 = UART_IIR 地址 */

.L_rep_int:
	/* 读取中断识别寄存器 (IIR) */
	lb	t0, 0(a2)
	andi	t0, t0, 0xFF

	/* bit0 = 1 表示无中断挂起 */
	andi	t1, t0, 1
	bnez	t1, .L_end

	/* 检查范围 (0x00-0x06) */
	li	t1, 6
	bgtu	t0, t1, .L_end

	/* 跳转表索引: IIR[2:1] (bit0 已确认为 0) */
	andi	t0, t0, 0x06
	srli	t0, t0, 1
	slli	t0, t0, 2
	la	t1, jmp_table
	add	t1, t1, t0
	lw	t0, 0(t1)
	jalr	t0
	j	.L_rep_int

.L_end:
	/* 【CNBE-32 注释】RISC-V 无需 x86 的 8259 EOI (outb $0x20, $0x20) */
	lw	ra,  0(sp)
	lw	s0,  4(sp)
	lw	s1,  8(sp)
	lw	s2, 12(sp)
	lw	s3, 16(sp)
	lw	a1, 20(sp)
	lw	a2, 24(sp)
	lw	a3, 28(sp)
	lw	a4, 32(sp)
	lw	a5, 36(sp)
	addi	sp, sp, 40
	mret

/* ============================================================
 * 跳转表: 索引 0-3 对应 IIR[2:1]
 * 0x00 (00) → 调制解调器状态
 * 0x02 (01) → 发送保持寄存器空
 * 0x04 (10) → 接收数据可用
 * 0x06 (11) → 接收线路状态
 * ============================================================ */
.section .rodata
.align 4
jmp_table:
	.word	modem_status
	.word	write_char
	.word	read_char
	.word	line_status

.text

/* ============================================================
 * modem_status: 调制解调器状态变化中断
 * 清除方式: 读取 MSR 寄存器
 * ============================================================ */
.align 4
modem_status:
	addi	t0, a1, 6        /* UART_MSR */
	lb	t1, 0(t0)
	ret

/* ============================================================
 * line_status: 接收线路状态中断
 * 清除方式: 读取 LSR 寄存器
 * ============================================================ */
.align 4
line_status:
	addi	t0, a1, 5        /* UART_LSR */
	lb	t1, 0(t0)
	ret

/* ============================================================
 * read_char: 接收数据可用中断
 * 逻辑: 读取 RBR → 放入 read_queue 环形缓冲区 → 唤醒等待进程
 * ============================================================ */
.align 4
read_char:
	/* 读取字符 */
	lb	t0, 0(a1)          /* UART_RBR */
	andi	t0, t0, 0xFF

	/* 计算 tty 号: ( &_table_list[n] - &_table_list ) >> 3 */
	la	t1, _table_list
	sub	a3, s0, t1
	srli	a3, a3, 3

	/* 获取 read_queue 指针 */
	lw	s2, 0(s0)         /* s2 = read_queue */
	beqz	s2, .L_read_ret

	/* 读取 head */
	lw	a4, HEAD(s2)

	/* buf[head] = char */
	add	t1, s2, BUF
	add	t1, t1, a4
	sb	t0, 0(t1)

	/* head = (head + 1) & (SIZE - 1) */
	addi	a4, a4, 1
	li	t1, SIZE - 1
	and	a4, a4, t1

	/* 检查是否满 */
	lw	t1, TAIL(s2)
	beq	a4, t1, .L_read_ret

	/* 保存新 head */
	sw	a4, HEAD(s2)

	/* 调用 do_tty_interrupt(tty_num) */
	addi	sp, sp, -12
	sw	ra, 0(sp)
	sw	a3, 4(sp)
	mv	a0, a3
	la	t0, _do_tty_interrupt
	jalr	t0
	lw	a3, 4(sp)
	lw	ra, 0(sp)
	addi	sp, sp, 12

.L_read_ret:
	ret

/* ============================================================
 * write_char: 发送保持寄存器空中断
 * 逻辑: 从 write_queue 取字符 → 写入 THR → 唤醒等待进程
 * ============================================================ */
.align 4
write_char:
	/* 获取 write_queue 指针 */
	lw	s2, 4(s0)         /* offset 4 = write_queue */
	beqz	s2, .L_write_ret

	/* 计算队列中字符数 */
	lw	a3, HEAD(s2)
	lw	a4, TAIL(s2)
	sub	a3, a3, a4
	li	t1, SIZE - 1
	and	a3, a3, t1

	/* 队列为空 → 处理缓冲区空 */
	beqz	a3, .L_write_empty

	/* 检查是否低于 startup 阈值 */
	li	t1, STARTUP
	ble	a3, t1, .L_wake_writer
	j	.L_do_write

.L_wake_writer:
	/* 唤醒等待写完成的进程 */
	lw	t0, PROC_LIST(s2)
	beqz	t0, .L_do_write
	sw	zero, 0(t0)

.L_do_write:
	/* 从队列取字符 */
	lw	a4, TAIL(s2)
	add	t1, s2, BUF
	add	t1, t1, a4
	lb	t0, 0(t1)

	/* 写入 UART THR */
	sb	t0, 0(a1)          /* UART_THR */

	/* tail = (tail + 1) & (SIZE - 1) */
	addi	a4, a4, 1
	li	t1, SIZE - 1
	and	a4, a4, t1
	sw	a4, TAIL(s2)

	/* 检查是否已空 */
	lw	t1, HEAD(s2)
	beq	a4, t1, .L_write_empty
	ret

.L_write_empty:
	/* 唤醒等待进程 */
	lw	t0, PROC_LIST(s2)
	beqz	t0, .L_disable_tx
	sw	zero, 0(t0)

.L_disable_tx:
	/* 禁用发送中断 (IER bit1 = 0) */
	li	t0, UART_IER
	lb	t1, 0(t0)
	andi	t1, t1, 0xFD     /* 清除 THR 空中断使能 */
	sb	t1, 0(t0)
	ret

.L_write_ret:
	ret
