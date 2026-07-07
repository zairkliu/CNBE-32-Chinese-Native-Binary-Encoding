/* 
 * tty_ioctl.c - TTY 设备控制
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: x86 cli/sti 替换为 RISC-V CSR 中断控制，fs 段访问替换为直接内存访问
 */
#include <errno.h>
#include <termios.h>

#include <linux/sched.h>
#include <linux/kernel.h>
#include <linux/tty.h>
#include <cnbe.h>

/* RISC-V 替代 x86 cli/sti */
#define cli_riscv() __asm__ __volatile__ ("csrci mstatus, 8" ::: "memory")
#define sti_riscv() __asm__ __volatile__ ("csrsi mstatus, 8" ::: "memory")

/* RISC-V 替代 x86 fs 段访问 */
static inline unsigned char get_fs_byte_riscv(const char *addr)
{
	return *(volatile unsigned char *)addr;
}
static inline void put_fs_byte_riscv(char val, char *addr)
{
	*(volatile unsigned char *)addr = val;
}
static inline void put_fs_long_riscv(unsigned long val, unsigned long *addr)
{
	*(volatile unsigned long *)addr = val;
}
static inline unsigned long get_fs_long_riscv(const unsigned long *addr)
{
	return *(volatile unsigned long *)addr;
}

static void flush(struct tty_queue * queue)
{
	cli_riscv();
	queue->head = queue->tail;
	sti_riscv();
}

static void wait_until_sent(struct tty_struct * tty)
{
	/* 什么都不做 - 未实现 */
}

static void send_break(struct tty_struct * tty)
{
	/* 什么都不做 - 未实现 */
}

static int get_termios(struct tty_struct * tty, struct termios * termios)
{
	int i;

	verify_area(termios, sizeof (*termios));
	for (i=0 ; i< (sizeof (*termios)) ; i++)
		put_fs_byte_riscv( ((char *)&tty->termios)[i] , i+(char *)termios );
	return 0;
}

static int set_termios(struct tty_struct * tty, struct termios * termios)
{
	int i;

	for (i=0 ; i< (sizeof (*termios)) ; i++)
		((char *)&tty->termios)[i]=get_fs_byte_riscv(i+(char *)termios);
	return 0;
}

static int get_termio(struct tty_struct * tty, struct termio * termio)
{
	int i;
	struct termio tmp_termio;

	verify_area(termio, sizeof (*termio));
	tmp_termio.c_iflag = tty->termios.c_iflag;
	tmp_termio.c_oflag = tty->termios.c_oflag;
	tmp_termio.c_cflag = tty->termios.c_cflag;
	tmp_termio.c_lflag = tty->termios.c_lflag;
	tmp_termio.c_line = tty->termios.c_line;
	for(i=0 ; i < NCC ; i++)
		tmp_termio.c_cc[i] = tty->termios.c_cc[i];
	for (i=0 ; i< (sizeof (*termio)) ; i++)
		put_fs_byte_riscv( ((char *)&tmp_termio)[i] , i+(char *)termio );
	return 0;
}

static int set_termio(struct tty_struct * tty, struct termio * termio)
{
	int i;
	struct termio tmp_termio;

	for (i=0 ; i< (sizeof (*termio)) ; i++)
		((char *)&tmp_termio)[i]=get_fs_byte_riscv(i+(char *)termio);
	*(unsigned short *)&tty->termios.c_iflag = tmp_termio.c_iflag;
	*(unsigned short *)&tty->termios.c_oflag = tmp_termio.c_oflag;
	*(unsigned short *)&tty->termios.c_cflag = tmp_termio.c_cflag;
	*(unsigned short *)&tty->termios.c_lflag = tmp_termio.c_lflag;
	tty->termios.c_line = tmp_termio.c_line;
	for(i=0 ; i < NCC ; i++)
		tty->termios.c_cc[i] = tmp_termio.c_cc[i];
	return 0;
}

int tty_ioctl(int dev, int cmd, int arg)
{
	struct tty_struct * tty;
	if (MAJOR(dev) == 5) {
		dev=current->tty;
		if (dev<0)
			panic("tty_ioctl: dev<0");
	} else
		dev=MINOR(dev);
	tty = dev + tty_table;
	switch (cmd) {
		case TCGETS:
			return get_termios(tty,(struct termios *) arg);
		case TCSETSF:
			flush(&tty->read_q); /* fallthrough */
		case TCSETSW:
			wait_until_sent(tty); /* fallthrough */
		case TCSETS:
			return set_termios(tty,(struct termios *) arg);
		case TCGETA:
			return get_termio(tty,(struct termio *) arg);
		case TCSETAF:
			flush(&tty->read_q); /* fallthrough */
		case TCSETAW:
			wait_until_sent(tty); /* fallthrough */
		case TCSETA:
			return set_termio(tty,(struct termio *) arg);
		case TCSBRK:
			if (!arg) {
				wait_until_sent(tty);
				send_break(tty);
			}
			return 0;
		case TCXONC:
			return -EINVAL; /* 未实现 */
		case TCFLSH:
			if (arg==0)
				flush(&tty->read_q);
			else if (arg==1)
				flush(&tty->write_q);
			else if (arg==2) {
				flush(&tty->read_q);
				flush(&tty->write_q);
			} else
				return -EINVAL;
			return 0;
		case TIOCEXCL:
			return -EINVAL; /* 未实现 */
		case TIOCNXCL:
			return -EINVAL; /* 未实现 */
		case TIOCSCTTY:
			return -EINVAL; /* 设置控制终端未实现 */
		case TIOCGPGRP:
			verify_area((void *) arg,4);
			put_fs_long_riscv(tty->pgrp,(unsigned long *) arg);
			return 0;
		case TIOCSPGRP:
			tty->pgrp=get_fs_long_riscv((unsigned long *) arg);
			return 0;
		case TIOCOUTQ:
			verify_area((void *) arg,4);
			put_fs_long_riscv(CHARS(tty->write_q),(unsigned long *) arg);
			return 0;
		case TIOCSTI:
			return -EINVAL; /* 未实现 */
		case TIOCGWINSZ:
			return -EINVAL; /* 未实现 */
		case TIOCSWINSZ:
			return -EINVAL; /* 未实现 */
		case TIOCMGET:
			return -EINVAL; /* 未实现 */
		case TIOCMBIS:
			return -EINVAL; /* 未实现 */
		case TIOCMBIC:
			return -EINVAL; /* 未实现 */
		case TIOCMSET:
			return -EINVAL; /* 未实现 */
		case TIOCGSOFTCAR:
			return -EINVAL; /* 未实现 */
		case TIOCSSOFTCAR:
			return -EINVAL; /* 未实现 */
		default:
			return -EINVAL;
	}
}
