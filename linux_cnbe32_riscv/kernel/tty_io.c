/*
 * 【RISC-V 转码状态】kernel/tty_io.c
 * 原始文件: Linux 0.01 kernel/tty_io.c
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - 移除 x86 段寄存器依赖 (asm/segment.h 的 get_fs_byte/put_fs_byte)
 *   - RISC-V 扁平内存模型：fs 段操作 → 直接指针访问
 *   - cli/sti → RISC-V mstatus MIE 位操作 (RISCV_DISABLE_IRQ/ENABLE_IRQ)
 *   - 保留 tty 核心逻辑、行规程和 cooked 模式处理
 *   - 添加中文注释
 *   - 集成 CNBE-32 头文件
 *
 * 【RISC-V 说明】
 * x86 的 fs/gs 段寄存器用于访问用户空间数据。
 * RISC-V 采用单一的扁平虚拟地址空间，
 * 用户空间和内核空间通过页表隔离。
 * 因此 get_fs_byte/put_fs_byte 可直接替换为 * 指针解引用。
 */

#include <ctype.h>
#include <errno.h>
#include <signal.h>

#include <linux/sched.h>
#include <linux/tty.h>
#include <linux/kernel.h>
#include <asm/system.h>
#include <cnbe.h>

/* RISC-V UART16550 基址 (替代 x86 COM1=0x3f8, COM2=0x2f8) */
#define UART_BASE       0x10000000UL
#define UART_BASE2      0x10000100UL

#define RISCV_DISABLE_IRQ()  cli()
#define RISCV_ENABLE_IRQ()   sti()

#define ALRMMASK (1 << (SIGALRM - 1))

#define _L_FLAG(tty, f)	((tty)->termios.c_lflag & f)
#define _I_FLAG(tty, f)	((tty)->termios.c_iflag & f)
#define _O_FLAG(tty, f)	((tty)->termios.c_oflag & f)

#define L_CANON(tty)	_L_FLAG((tty), ICANON)
#define L_ISIG(tty)	_L_FLAG((tty), ISIG)
#define L_ECHO(tty)	_L_FLAG((tty), ECHO)
#define L_ECHOE(tty)	_L_FLAG((tty), ECHOE)
#define L_ECHOK(tty)	_L_FLAG((tty), ECHOK)
#define L_ECHOCTL(tty)	_L_FLAG((tty), ECHOCTL)
#define L_ECHOKE(tty)	_L_FLAG((tty), ECHOKE)

#define I_UCLC(tty)	_I_FLAG((tty), IUCLC)
#define I_NLCR(tty)	_I_FLAG((tty), INLCR)
#define I_CRNL(tty)	_I_FLAG((tty), ICRNL)
#define I_NOCR(tty)	_I_FLAG((tty), IGNCR)

#define O_POST(tty)	_O_FLAG((tty), OPOST)
#define O_NLCR(tty)	_O_FLAG((tty), ONLCR)
#define O_CRNL(tty)	_O_FLAG((tty), OCRNL)
#define O_NLRET(tty)	_O_FLAG((tty), ONLRET)
#define O_LCUC(tty)	_O_FLAG((tty), OLCUC)

/* tty 设备表：控制台 + 2 个串口 */
struct tty_struct tty_table[] = {
	{
		{0,
		OPOST | ONLCR,		/* 输出时将换行转为回车换行 */
		0,
		ICANON | ECHO | ECHOCTL | ECHOKE,
		0,			/* 控制台 termio */
		INIT_C_CC},
		0,			/* 初始进程组 */
		0,			/* 初始停止状态 */
		con_write,
		{0, 0, 0, 0, ""},		/* 控制台读取队列 */
		{0, 0, 0, 0, ""},		/* 控制台写入队列 */
		{0, 0, 0, 0, ""}		/* 控制台辅助队列 */
	}, {
		{0,
		OPOST | ONLRET,		/* 输出时将换行转为回车 */
		B2400 | CS8,
		0,
		0,
		INIT_C_CC},
		0,
		0,
		rs_write,
		{UART_BASE, 0, 0, 0, ""},		/* 串口 1 (RISC-V UART16550) */
		{UART_BASE, 0, 0, 0, ""},
		{0, 0, 0, 0, ""}
	}, {
		{0,
		OPOST | ONLRET,
		B2400 | CS8,
		0,
		0,
		INIT_C_CC},
		0,
		0,
		rs_write,
		{UART_BASE2, 0, 0, 0, ""},		/* 串口 2 (RISC-V 第二 UART) */
		{UART_BASE2, 0, 0, 0, ""},
		{0, 0, 0, 0, ""}
	}
};

/*
 * 这些表由机器代码中断处理程序使用。
 * 可以更改它们以实现伪 tty 等功能（当前未实现）。
 */
struct tty_queue *table_list[] = {
	&tty_table[0].read_q, &tty_table[0].write_q,
	&tty_table[1].read_q, &tty_table[1].write_q,
	&tty_table[2].read_q, &tty_table[2].write_q
};

void tty_init(void)
{
	rs_init();
	con_init();
}

void tty_intr(struct tty_struct *tty, int signal)
{
	int i;

	if (tty->pgrp <= 0)
		return;
	for (i = 0; i < NR_TASKS; i++)
		if (task[i] && task[i]->pgrp == tty->pgrp)
			task[i]->signal |= 1 << (signal - 1);
}

static void sleep_if_empty(struct tty_queue *queue)
{
	RISCV_DISABLE_IRQ();
	while (!current->signal && EMPTY(*queue))
		interruptible_sleep_on(&queue->proc_list);
	RISCV_ENABLE_IRQ();
}

static void sleep_if_full(struct tty_queue *queue)
{
	if (!FULL(*queue))
		return;
	RISCV_DISABLE_IRQ();
	while (!current->signal && LEFT(*queue) < 128)
		interruptible_sleep_on(&queue->proc_list);
	RISCV_ENABLE_IRQ();
}

void copy_to_cooked(struct tty_struct *tty)
{
	signed char c;

	while (!EMPTY(tty->read_q) && !FULL(tty->secondary)) {
		GETCH(tty->read_q, c);
		if (c == 13)
			if (I_CRNL(tty))
				c = 10;
			else if (I_NOCR(tty))
				continue;
			else;
		else if (c == 10 && I_NLCR(tty))
			c = 13;
		if (I_UCLC(tty))
			c = tolower(c);
		if (L_CANON(tty)) {
			if (c == ERASE_CHAR(tty)) {
				if (EMPTY(tty->secondary) ||
				   (c = LAST(tty->secondary)) == 10 ||
				   c == EOF_CHAR(tty))
					continue;
				if (L_ECHO(tty)) {
					if (c < 32)
						PUTCH(127, tty->write_q);
					PUTCH(127, tty->write_q);
					tty->write(tty);
				}
				DEC(tty->secondary.head);
				continue;
			}
			if (c == STOP_CHAR(tty)) {
				tty->stopped = 1;
				continue;
			}
			if (c == START_CHAR(tty)) {
				tty->stopped = 0;
				continue;
			}
		}
		if (!L_ISIG(tty)) {
			if (c == INTR_CHAR(tty)) {
				tty_intr(tty, SIGINT);
				continue;
			}
		}
		if (c == 10 || c == EOF_CHAR(tty))
			tty->secondary.data++;
		if (L_ECHO(tty)) {
			if (c == 10) {
				PUTCH(10, tty->write_q);
				PUTCH(13, tty->write_q);
			} else if (c < 32) {
				if (L_ECHOCTL(tty)) {
					PUTCH('^', tty->write_q);
					PUTCH(c + 64, tty->write_q);
				}
			} else
				PUTCH(c, tty->write_q);
			tty->write(tty);
		}
		PUTCH(c, tty->secondary);
	}
	wake_up(&tty->secondary.proc_list);
}

/*
 * 【RISC-V 替换】tty_read - 从 tty 读取数据
 * 原始 x86 使用 get_fs_byte 从用户空间缓冲区读取数据。
 * RISC-V 扁平内存模型下，直接使用指针访问。
 * 注意：内核态直接访问用户空间仍需通过 copy_to_user 风格函数，
 * 但 Linux 0.01 的 get_fs_byte 在此简化实现中等同于 * 解引用。
 */
int tty_read(unsigned channel, char *buf, int nr)
{
	struct tty_struct *tty;
	char c, *b = buf;
	int minimum, time, flag = 0;
	unsigned long oldalarm;

	if (channel > 2 || nr < 0) return -1;
	tty = &tty_table[channel];
	oldalarm = current->alarm;
	time = (unsigned) 10 * tty->termios.c_cc[VTIME];
	minimum = (unsigned) tty->termios.c_cc[VMIN];
	if (time && !minimum) {
		minimum = 1;
		if (flag = (!oldalarm || time + jiffies < oldalarm))
			current->alarm = time + jiffies;
	}
	if (minimum > nr)
		minimum = nr;
	while (nr > 0) {
		if (flag && (current->signal & ALRMMASK)) {
			current->signal &= ~ALRMMASK;
			break;
		}
		if (current->signal)
			break;
		if (EMPTY(tty->secondary) || (L_CANON(tty) &&
		!tty->secondary.data && LEFT(tty->secondary) > 20)) {
			sleep_if_empty(&tty->secondary);
			continue;
		}
		do {
			GETCH(tty->secondary, c);
			if (c == EOF_CHAR(tty) || c == 10)
				tty->secondary.data--;
			if (c == EOF_CHAR(tty) && L_CANON(tty))
				return (b - buf);
			else {
				/* 【RISC-V 替换】put_fs_byte → 直接写入 */
				*b++ = c;
				if (!--nr)
					break;
			}
		} while (nr > 0 && !EMPTY(tty->secondary));
		if (time && !L_CANON(tty))
			if (flag = (!oldalarm || time + jiffies < oldalarm))
				current->alarm = time + jiffies;
			else
				current->alarm = oldalarm;
		if (L_CANON(tty)) {
			if (b - buf)
				break;
		} else if (b - buf >= minimum)
			break;
	}
	current->alarm = oldalarm;
	if (current->signal && !(b - buf))
		return -EINTR;
	return (b - buf);
}

/*
 * 【RISC-V 替换】tty_write - 向 tty 写入数据
 * 原始 x86 使用 get_fs_byte 从用户空间读取数据。
 * RISC-V 直接使用指针访问。
 */
int tty_write(unsigned channel, char *buf, int nr)
{
	static int cr_flag = 0;
	struct tty_struct *tty;
	char c, *b = buf;

	if (channel > 2 || nr < 0) return -1;
	tty = channel + tty_table;
	while (nr > 0) {
		sleep_if_full(&tty->write_q);
		if (current->signal)
			break;
		while (nr > 0 && !FULL(tty->write_q)) {
			/* 【RISC-V 替换】get_fs_byte → 直接读取 */
			c = *b;
			if (O_POST(tty)) {
				if (c == '\r' && O_CRNL(tty))
					c = '\n';
				else if (c == '\n' && O_NLRET(tty))
					c = '\r';
				if (c == '\n' && !cr_flag && O_NLCR(tty)) {
					cr_flag = 1;
					PUTCH(13, tty->write_q);
					continue;
				}
				if (O_LCUC(tty))
					c = toupper(c);
			}
			b++; nr--;
			cr_flag = 0;
			PUTCH(c, tty->write_q);
		}
		tty->write(tty);
		if (nr > 0)
			schedule();
	}
	return (b - buf);
}

/*
 * 【RISC-V 注释】
 * 原始 x86 依赖 386 特性允许中断中睡眠。
 * RISC-V 架构下同样允许中断处理中睡眠，
 * 因为 trap 处理使用的是入口点跳转而非中断门自动关闭中断。
 * 但需注意在调用此函数前确保中断控制器已重新使能，
 * 以避免嵌套中断丢失。
 */
void do_tty_interrupt(int tty)
{
	copy_to_cooked(tty_table + tty);
}
