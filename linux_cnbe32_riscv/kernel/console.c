/*
 * 【RISC-V 转码状态】kernel/console.c
 * 原始文件: Linux 0.01 kernel/console.c
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - x86 VGA 文本模式 (0xB8000) → RISC-V UART 串行控制台
 *   - 移除所有 VGA 显存操作和 CRTC 寄存器操作 (outb_p/inb_p 0x3d4/0x3d5)
 *   - 移除 x86 字符串操作内联汇编 (rep movsl, rep stosw, cld, std)
 *   - cli/sti → RISC-V mstatus MIE 位操作
 *   - x86 段寄存器操作 → 忽略（RISC-V 无段式）
 *   - 添加 UART 输出函数替代显存写入
 *   - 保留 VT102 转义序列处理逻辑
 *   - 添加中文注释
 *   - 集成 CNBE-32 头文件
 *
 * 【RISC-V 说明】
 * 在 RISC-V 平台上，通常使用 UART 串口作为早期控制台输出设备。
 * 目标平台 virt 使用 UART16550 兼容控制器，基址 0x10000000。
 * 由于无 VGA 显示，终端模拟在主机端完成（如 QEMU 的串口终端）。
 * 25x80 字符网格的概念保留，但数据存储在内核缓冲区而非显存。
 */

#include <linux/sched.h>
#include <linux/tty.h>
#include <linux/kernel.h>
#include <asm/io.h>
#include <asm/system.h>
#include <cnbe.h>

/* RISC-V virt UART16550 定义 */
#define UART_BASE       0x10000000UL
#define UART_RBR        (UART_BASE + 0x00)
#define UART_THR        (UART_BASE + 0x00)
#define UART_IER        (UART_BASE + 0x01)
#define UART_IIR        (UART_BASE + 0x02)
#define UART_FCR        (UART_BASE + 0x02)
#define UART_LCR        (UART_BASE + 0x03)
#define UART_MCR        (UART_BASE + 0x04)
#define UART_LSR        (UART_BASE + 0x05)
#define UART_MSR        (UART_BASE + 0x06)
#define UART_SCR        (UART_BASE + 0x07)
#define UART_LSR_DR     0x01
#define UART_LSR_THRE   0x20
#define UART_LSR_TEMT   0x40
#define UART_DLL        (UART_BASE + 0x00)
#define UART_DLM        (UART_BASE + 0x01)

/* RISC-V IRQ 宏映射到标准 cli/sti */
#define RISCV_DISABLE_IRQ()  cli()
#define RISCV_ENABLE_IRQ()   sti()

/* MMIO 读写宏 */
#define MMIO_READB(addr)        (*(volatile unsigned char *)(addr))
#define MMIO_WRITEB(addr, val)  (*(volatile unsigned char *)(addr) = (val))

/* 控制台尺寸定义（保留 VT102 的 25x80 逻辑） */
#define LINES	25
#define COLUMNS	80
#define NPAR	16

/* 串行控制台缓冲区大小 */
#define CONSOLE_BUFSIZE	(LINES * COLUMNS * 2)

/* 外部函数声明 */
extern void keyboard_interrupt(void);

/* 控制台状态变量 */
static unsigned long origin = 0;		/* 缓冲区起始偏移（保留兼容性） */
static unsigned long scr_end = (LINES * COLUMNS * 2);  /* 缓冲区结束偏移 */
static unsigned long pos;          /* 当前光标位置（在缓冲区中的偏移） */
static unsigned long x, y;         /* 当前光标坐标 */
static unsigned long top = 0, bottom = LINES;
static unsigned long lines = LINES, columns = COLUMNS;
static unsigned long state = 0;    /* 转义序列处理状态 */
static unsigned long npar, par[NPAR];
static unsigned long ques = 0;
static unsigned char attr = 0x07;  /* 属性字节（保留，但 UART 输出时忽略） */

/* 字符缓冲区（替代 VGA 显存） */
static unsigned short console_buf[CONSOLE_BUFSIZE / 2];

/* 保存的光标位置 */
static int saved_x = 0;
static int saved_y = 0;

/*
 * 终端响应字符串（VT102 查询响应）
 */
#define RESPONSE	"\033[?1;2c"

/*
 * 【RISC-V 新增】uart_putc - 通过 UART 发送单个字符
 * 替代 x86 显存直接写入，使用 MMIO 访问 UART16550。
 * 轮询 LSR 的 THRE 位确保发送寄存器可用。
 */
static inline void uart_putc(unsigned char c)
{
	/* 等待发送保持寄存器为空 */
	while (!(MMIO_READB(UART_LSR) & UART_LSR_THRE))
		;
	MMIO_WRITEB(UART_THR, c);
}

/*
 * 【RISC-V 新增】uart_puts - 通过 UART 发送字符串
 */
static void uart_puts(const char *s)
{
	while (*s)
		uart_putc(*s++);
}

/*
 * 【RISC-V 替换】set_cursor - 设置光标位置
 * 原始 x86 代码通过 CRTC 寄存器 (0x3d4/0x3d5) 设置硬件光标。
 * RISC-V 无硬件光标，通过发送 ANSI 转义序列到终端模拟器来定位光标。
 */
static inline void set_cursor(void)
{
	/* 发送 ANSI 光标定位序列: ESC [ y;x H */
	char buf[16];
	char *p = buf;
	*p++ = '\033';
	*p++ = '[';
	/* 简单整数转字符串（避免递归调用 printk） */
	if (y + 1 >= 10) *p++ = '0' + (y + 1) / 10;
	*p++ = '0' + (y + 1) % 10;
	*p++ = ';';
	if (x + 1 >= 10) *p++ = '0' + (x + 1) / 10;
	*p++ = '0' + (x + 1) % 10;
	*p++ = 'H';
	*p = '\0';
	uart_puts(buf);
}

/*
 * 【RISC-V 替换】con_putchar_at - 在指定位置写入字符
 * 替代 x86 的显存写入操作 *(unsigned short *)pos = 0x0720。
 */
static inline void con_putchar_at(int cx, int cy, unsigned char c, unsigned char a)
{
	if (cx < columns && cy < lines)
		console_buf[cy * columns + cx] = ((unsigned short)a << 8) | c;
}

static inline void con_getchar_at(int cx, int cy, unsigned char *c, unsigned char *a)
{
	unsigned short val = console_buf[cy * columns + cx];
	if (c) *c = val & 0xFF;
	if (a) *a = (val >> 8) & 0xFF;
}

/*
 * gotoxy - 移动光标到指定位置
 */
static inline void gotoxy(unsigned int new_x, unsigned int new_y)
{
	if (new_x >= columns || new_y >= lines)
		return;
	x = new_x;
	y = new_y;
	pos = (y * columns + x) * 2;
}

/*
 * 【RISC-V 替换】scrup - 屏幕内容上滚
 * 原始 x86 使用 rep movsl / rep stosw 进行显存块移动。
 * RISC-V 使用 C 循环操作内存缓冲区，然后重新输出到 UART。
 * 注意：对于串行控制台，每次修改后都需要重新发送内容，
 * 因此此操作效率较低。实际 RISC-V 实现中通常使用简单的
 * 换行而非完整的滚屏。
 */
static void scrup(void)
{
	int i, j;

	if (!top && bottom == lines) {
		/* 整屏滚动 */
		for (i = top; i < bottom - 1; i++) {
			for (j = 0; j < columns; j++)
				console_buf[i * columns + j] =
					console_buf[(i + 1) * columns + j];
		}
		/* 清除最后一行 */
		for (j = 0; j < columns; j++)
			console_buf[(bottom - 1) * columns + j] = 0x0720;
	} else {
		/* 部分滚动 */
		for (i = top; i < bottom - 1; i++) {
			for (j = 0; j < columns; j++)
				console_buf[i * columns + j] =
					console_buf[(i + 1) * columns + j];
		}
		for (j = 0; j < columns; j++)
			console_buf[(bottom - 1) * columns + j] = 0x0720;
	}
	/* 光标上移一行 */
	if (y > top)
		y--;
	gotoxy(x, y);
	/* 发送滚屏后重新绘制提示 */
	uart_puts("\033[S");  /* ANSI 滚屏序列 */
}

/*
 * 【RISC-V 替换】scrdown - 屏幕内容下滚
 */
static void scrdown(void)
{
	int i, j;

	for (i = bottom - 1; i > top; i--) {
		for (j = 0; j < columns; j++)
			console_buf[i * columns + j] =
				console_buf[(i - 1) * columns + j];
	}
	for (j = 0; j < columns; j++)
		console_buf[top * columns + j] = 0x0720;
	gotoxy(x, y);
}

static void lf(void)
{
	if (y + 1 < bottom) {
		y++;
		pos += columns * 2;
		return;
	}
	scrup();
}

static void ri(void)
{
	if (y > top) {
		y--;
		pos -= columns * 2;
		return;
	}
	scrdown();
}

static void cr(void)
{
	pos -= x * 2;
	x = 0;
}

static void del(void)
{
	if (x) {
		pos -= 2;
		x--;
		con_putchar_at(x, y, ' ', 0x07);
	}
}

/*
 * 【RISC-V 替换】csi_J - 擦除显示
 * 使用 ANSI 转义序列替代 x86 显存操作。
 */
static void csi_J(int par)
{
	switch (par) {
	case 0:	/* 从光标擦除到显示末尾 */
		uart_puts("\033[0J");
		for (int i = pos >> 1; i < (scr_end - origin) >> 1; i++)
			console_buf[i] = 0x0720;
		break;
	case 1:	/* 从显示开头擦除到光标 */
		uart_puts("\033[1J");
		for (int i = 0; i <= (pos >> 1); i++)
			console_buf[i] = 0x0720;
		break;
	case 2:	/* 擦除整个显示 */
		uart_puts("\033[2J\033[H");
		for (int i = 0; i < (lines * columns); i++)
			console_buf[i] = 0x0720;
		gotoxy(0, 0);
		break;
	default:
		return;
	}
}

/*
 * 【RISC-V 替换】csi_K - 擦除行
 */
static void csi_K(int par)
{
	int i, start, count;

	switch (par) {
	case 0:	/* 从光标擦除到行尾 */
		if (x >= columns)
			return;
		count = columns - x;
		start = pos >> 1;
		break;
	case 1:	/* 从行首擦除到光标 */
		start = (pos >> 1) - x;
		count = (x < columns) ? x : columns;
		break;
	case 2:	/* 擦除整行 */
		start = (pos >> 1) - x;
		count = columns;
		break;
	default:
		return;
	}
	for (i = 0; i < count; i++)
		console_buf[start + i] = 0x0720;
	/* 发送 ANSI 序列 */
	if (par == 0)
		uart_puts("\033[0K");
	else if (par == 1)
		uart_puts("\033[1K");
	else
		uart_puts("\033[2K");
}

void csi_m(void)
{
	int i;

	for (i = 0; i <= npar; i++)
		switch (par[i]) {
		case 0: attr = 0x07; uart_puts("\033[0m"); break;
		case 1: attr = 0x0f; uart_puts("\033[1m"); break;
		case 4: attr = 0x0f; uart_puts("\033[4m"); break;
		case 7: attr = 0x70; uart_puts("\033[7m"); break;
		case 27: attr = 0x07; uart_puts("\033[0m"); break;
		}
}

/*
 * 【RISC-V 替换】respond - 发送终端响应
 * 替代 x86 的 cli/sti 和直接队列操作，使用 RISC-V 中断控制。
 */
static void respond(struct tty_struct *tty)
{
	char *p = RESPONSE;

	RISCV_DISABLE_IRQ();
	while (*p) {
		PUTCH(*p, tty->read_q);
		p++;
	}
	RISCV_ENABLE_IRQ();
	copy_to_cooked(tty);
}

static void insert_char(void)
{
	int i = x;
	unsigned short tmp, old = 0x0720;
	unsigned short *p = &console_buf[y * columns + x];

	while (i++ < columns) {
		tmp = *p;
		*p = old;
		old = tmp;
		p++;
	}
}

static void insert_line(void)
{
	int oldtop, oldbottom;

	oldtop = top;
	oldbottom = bottom;
	top = y;
	bottom = lines;
	scrdown();
	top = oldtop;
	bottom = oldbottom;
}

static void delete_char(void)
{
	int i;
	unsigned short *p = &console_buf[y * columns + x];

	if (x >= columns)
		return;
	i = x;
	while (++i < columns) {
		*p = *(p + 1);
		p++;
	}
	*p = 0x0720;
}

static void delete_line(void)
{
	int oldtop, oldbottom;

	oldtop = top;
	oldbottom = bottom;
	top = y;
	bottom = lines;
	scrup();
	top = oldtop;
	bottom = oldbottom;
}

static void csi_at(int nr)
{
	if (nr > columns)
		nr = columns;
	else if (!nr)
		nr = 1;
	while (nr--)
		insert_char();
}

static void csi_L(int nr)
{
	if (nr > lines)
		nr = lines;
	else if (!nr)
		nr = 1;
	while (nr--)
		insert_line();
}

static void csi_P(int nr)
{
	if (nr > columns)
		nr = columns;
	else if (!nr)
		nr = 1;
	while (nr--)
		delete_char();
}

static void csi_M(int nr)
{
	if (nr > lines)
		nr = lines;
	else if (!nr)
		nr = 1;
	while (nr--)
		delete_line();
}

static void save_cur(void)
{
	saved_x = x;
	saved_y = y;
}

static void restore_cur(void)
{
	x = saved_x;
	y = saved_y;
	gotoxy(x, y);
}

/*
 * 【RISC-V 替换】con_write - 控制台写函数
 * 这是 VT102 终端处理的核心函数。
 * 原始 x86 版本直接写入 VGA 显存 (0xB8000)。
 * RISC-V 版本通过 UART 发送字符，同时维护内部缓冲区。
 * 注意：此实现为兼容层，完整的串行控制台应直接在驱动层处理。
 */
void con_write(struct tty_struct *tty)
{
	int nr;
	char c;

	nr = CHARS(tty->write_q);
	while (nr--) {
		GETCH(tty->write_q, c);
		switch (state) {
		case 0:
			if (c > 31 && c < 127) {
				if (x >= columns) {
					x -= columns;
					pos -= columns * 2;
					lf();
				}
				/* 【RISC-V 替换】显存写入 → UART 输出 + 缓冲区更新 */
				con_putchar_at(x, y, c, attr);
				uart_putc(c);
				pos += 2;
				x++;
			} else if (c == 27)
				state = 1;
			else if (c == 10 || c == 11 || c == 12)
				lf();
			else if (c == 13)
				cr();
			else if (c == ERASE_CHAR(tty))
				del();
			else if (c == 8) {
				if (x) {
					x--;
					pos -= 2;
				}
			} else if (c == 9) {
				c = 8 - (x & 7);
				x += c;
				pos += c * 2;
				if (x > columns) {
					x -= columns;
					pos -= columns * 2;
					lf();
				}
				c = 9;
			}
			break;
		case 1:
			state = 0;
			if (c == '[')
				state = 2;
			else if (c == 'E')
				gotoxy(0, y + 1);
			else if (c == 'M')
				ri();
			else if (c == 'D')
				lf();
			else if (c == 'Z')
				respond(tty);
			else if (c == '7')
				save_cur();
			else if (c == '8')
				restore_cur();
			break;
		case 2:
			for (npar = 0; npar < NPAR; npar++)
				par[npar] = 0;
			npar = 0;
			state = 3;
			if ((ques = (c == '?')))
				break;
		case 3:
			if (c == ';' && npar < NPAR - 1) {
				npar++;
				break;
			} else if (c >= '0' && c <= '9') {
				par[npar] = 10 * par[npar] + c - '0';
				break;
			} else
				state = 4;
		case 4:
			state = 0;
			switch (c) {
			case 'G': case '`':
				if (par[0]) par[0]--;
				gotoxy(par[0], y);
				break;
			case 'A':
				if (!par[0]) par[0]++;
				gotoxy(x, y - par[0]);
				break;
			case 'B': case 'e':
				if (!par[0]) par[0]++;
				gotoxy(x, y + par[0]);
				break;
			case 'C': case 'a':
				if (!par[0]) par[0]++;
				gotoxy(x + par[0], y);
				break;
			case 'D':
				if (!par[0]) par[0]++;
				gotoxy(x - par[0], y);
				break;
			case 'E':
				if (!par[0]) par[0]++;
				gotoxy(0, y + par[0]);
				break;
			case 'F':
				if (!par[0]) par[0]++;
				gotoxy(0, y - par[0]);
				break;
			case 'd':
				if (par[0]) par[0]--;
				gotoxy(x, par[0]);
				break;
			case 'H': case 'f':
				if (par[0]) par[0]--;
				if (par[1]) par[1]--;
				gotoxy(par[1], par[0]);
				break;
			case 'J':
				csi_J(par[0]);
				break;
			case 'K':
				csi_K(par[0]);
				break;
			case 'L':
				csi_L(par[0]);
				break;
			case 'M':
				csi_M(par[0]);
				break;
			case 'P':
				csi_P(par[0]);
				break;
			case '@':
				csi_at(par[0]);
				break;
			case 'm':
				csi_m();
				break;
			case 'r':
				if (par[0]) par[0]--;
				if (!par[1]) par[1] = lines;
				if (par[0] < par[1] && par[1] <= lines) {
					top = par[0];
					bottom = par[1];
				}
				break;
			case 's':
				save_cur();
				break;
			case 'u':
				restore_cur();
				break;
			}
		}
	}
	set_cursor();
}

/*
 * 【RISC-V 替换】con_init - 控制台初始化
 * 原始 x86 代码:
 *   - 从 BIOS 数据区 (0x90000) 读取光标位置
 *   - 设置键盘中断门 (set_trap_gate 0x21)
 *   - 配置 8259A 中断控制器 (0x21, 0x61)
 * RISC-V 版本:
 *   - 初始化 UART 串口 (波特率 9600, 8N1)
 *   - 设置 PLIC/CLINT 中断路由（具体由架构代码完成）
 *   - 初始化内部缓冲区
 * 注意: 键盘中断由独立的 RISC-V 中断控制器管理，
 * 此处仅初始化 UART 和清屏。
 */
void con_init(void)
{
	unsigned int i;

	/* 初始化 UART 为 9600 bps, 8N1 */
	MMIO_WRITEB(UART_LCR, 0x80);		/* 设置 DLAB */
	MMIO_WRITEB(UART_DLL, 0x0C);		/* 除数低位 (12 对应 9600 @ 1.8432MHz) */
	MMIO_WRITEB(UART_DLM, 0x00);		/* 除数高位 */
	MMIO_WRITEB(UART_LCR, 0x03);		/*  8 bits, no parity, 1 stop bit */
	MMIO_WRITEB(UART_FCR, 0x01);		/*  Enable FIFO */
	MMIO_WRITEB(UART_IER, 0x01);		/*  Enable receive interrupts */

	/* 清屏并发送 ANSI 清屏序列 */
	for (i = 0; i < (lines * columns); i++)
		console_buf[i] = 0x0720;
	uart_puts("\033[2J\033[H");
	gotoxy(0, 0);

	/* 【RISC-V 说明】
	 * 原始 x86 的 set_trap_gate(0x21, &keyboard_interrupt) 被移除。
	 * RISC-V 的中断向量表在 trap_entry.S 中设置，
	 * 外部中断（包括键盘/UART）通过 PLIC 路由。
	 * 键盘中断初始化应由 keyboard.S 或架构代码完成。
	 */
}
