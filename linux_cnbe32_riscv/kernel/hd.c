/*
 * 【RISC-V 转码状态】kernel/hd.c
 * 原始文件: Linux 0.01 kernel/hd.c
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - x86 IDE 控制器 (I/O 端口 0x1f0-0x1f7) → RISC-V virtio-blk 或 MMIO 块设备
 *   - 移除 x86 内联汇编 (divl, rep insw, rep outsw)
 *   - port_read/port_write → MMIO 读取/写入循环
 *   - cli/sti → RISC-V mstatus MIE 位操作
 *   - 保留请求队列、电梯算法和分区表逻辑
 *   - 添加中文注释和错误消息
 *   - 集成 CNBE-32 头文件
 *
 * 【RISC-V 说明】
 * x86 的 IDE 控制器通过 I/O 端口访问。
 * RISC-V 平台通常使用 virtio-blk (PCIe MMIO) 或 SPI 控制器访问存储。
 * 本文件保留块请求层和分区表解析，但将底层硬件访问抽象为 MMIO 操作。
 * 实际硬件驱动需根据具体平台适配（virtio-blk, NVMe, 或 SD 卡）。
 */

#include <linux/config.h>
#include <linux/sched.h>
#include <linux/fs.h>
#include <linux/kernel.h>
#include <linux/hdreg.h>
#include <asm/system.h>
#include <cnbe.h>

#define RISCV_DISABLE_IRQ()  cli()
#define RISCV_ENABLE_IRQ()   sti()

/* MMIO 读写宏 */
#define MMIO_READB(addr)        (*(volatile unsigned char *)(addr))
#define MMIO_WRITEB(addr, val)  (*(volatile unsigned char *)(addr) = (val))
#define MMIO_READW(addr)        (*(volatile unsigned short *)(addr))
#define MMIO_WRITEW(addr, val)  (*(volatile unsigned short *)(addr) = (val))


/*
 * 本代码处理所有硬盘中断和读写请求。
 * 中断处理相对直接（也许不明显，但中断永远不会明显），
 * 同时保持高效，且从不禁用中断（除非为了克服可能的竞态条件）。
 * 电梯块寻道算法由于巧妙的编程，不需要禁用中断。
 */

/* 每扇区最大读写错误次数 */
#define MAX_ERRORS	5
#define MAX_HD		2
#define NR_REQUEST	32

/*
 * 硬盘类型定义。
 * 当前为 CP3044 定义，即修改后的 type 17。
 */
static struct hd_i_struct {
	int head, sect, cyl, wpcom, lzone, ctl;
} hd_info[] = { HD_TYPE };

#define NR_HD ((sizeof(hd_info)) / (sizeof(struct hd_i_struct)))

static struct hd_struct {
	long start_sect;
	long nr_sects;
} hd[5 * MAX_HD] = {{0, 0}, };

static struct hd_request {
	int hd;		/* -1 表示无请求 */
	int nsector;
	int sector;
	int head;
	int cyl;
	int cmd;
	int errors;
	struct buffer_head *bh;
	struct hd_request *next;
} request[NR_REQUEST];

#define IN_ORDER(s1, s2) \
((s1)->hd < (s2)->hd || (s1)->hd == (s2)->hd && \
((s1)->cyl < (s2)->cyl || (s1)->cyl == (s2)->cyl && \
((s1)->head < (s2)->head || (s1)->head == (s2)->head && \
((s1)->sector < (s2)->sector))))

static struct hd_request *this_request = NULL;

static int sorting = 0;

static void do_request(void);
static void reset_controller(void);
static void rw_abs_hd(int rw, unsigned int nr, unsigned int sec,
		unsigned int head, unsigned int cyl, struct buffer_head *bh);
void hd_init(void);

/*
 * 【RISC-V 替换】port_read - 从端口读取数据到缓冲区
 * 原始 x86 使用 rep insw (字符串输入指令)。
 * RISC-V 使用 MMIO 读取循环。
 *
 * 参数:
 *   port - MMIO 数据端口地址
 *   buf  - 目标缓冲区
 *   nr   - 读取的字数 (16位)
 */
#define port_read(port, buf, nr) do { \
	unsigned short *__p = (unsigned short *)(buf); \
	unsigned long __port = (port); \
	int __i; \
	for (__i = 0; __i < (nr); __i++) \
		__p[__i] = MMIO_READW(__port); \
} while(0)

/*
 * 【RISC-V 替换】port_write - 从缓冲区写入数据到端口
 * 原始 x86 使用 rep outsw (字符串输出指令)。
 * RISC-V 使用 MMIO 写入循环。
 */
#define port_write(port, buf, nr) do { \
	unsigned short *__p = (unsigned short *)(buf); \
	unsigned long __port = (port); \
	int __i; \
	for (__i = 0; __i < (nr); __i++) \
		MMIO_WRITEW(__port, __p[__i]); \
} while(0)

extern void hd_interrupt(void);

static struct task_struct *wait_for_request = NULL;

static inline void lock_buffer(struct buffer_head *bh)
{
	if (bh->b_lock)
		printk("硬盘驱动: 缓冲区被重复锁定\n");
	bh->b_lock = 1;
}

static inline void unlock_buffer(struct buffer_head *bh)
{
	if (!bh->b_lock)
		printk("硬盘驱动: 释放未锁定的缓冲区\n");
	bh->b_lock = 0;
	wake_up(&bh->b_wait);
}

static inline void wait_on_buffer(struct buffer_head *bh)
{
	RISCV_DISABLE_IRQ();
	while (bh->b_lock)
		sleep_on(&bh->b_wait);
	RISCV_ENABLE_IRQ();
}

/*
 * 【RISC-V 替换】rw_hd - 块设备读写请求
 * 原始 x86 使用 divl 内联汇编计算扇区/磁头/柱面。
 * RISC-V 使用 C 语言除法/取模运算。
 */
void rw_hd(int rw, struct buffer_head *bh)
{
	unsigned int block, dev;
	unsigned int sec, head, cyl;
	unsigned int tmp;

	block = bh->b_blocknr << 1;
	dev = MINOR(bh->b_dev);
	if (dev >= 5 * NR_HD || block + 2 > hd[dev].nr_sects)
		return;
	block += hd[dev].start_sect;
	dev /= 5;

	/* 【RISC-V 替换】divl 汇编 → C 除法运算 */
	tmp = block;
	sec = tmp % hd_info[dev].sect;
	block = tmp / hd_info[dev].sect;
	sec++;

	tmp = block;
	head = tmp % hd_info[dev].head;
	cyl = tmp / hd_info[dev].head;

	rw_abs_hd(rw, dev, sec + 1, head, cyl, bh);
}

/* 此函数只能使用一次，由 static int callable 强制执行 */
int sys_setup(void)
{
	static int callable = 1;
	int i, drive;
	struct partition *p;

	if (!callable)
		return -1;
	callable = 0;
	for (drive = 0; drive < NR_HD; drive++) {
		rw_abs_hd(READ, drive, 1, 0, 0, (struct buffer_head *)start_buffer);
		if (!start_buffer->b_uptodate) {
			printk("无法读取驱动器 %d 的分区表\n\r", drive);
			panic("");
		}
		if (start_buffer->b_data[510] != 0x55 ||
		    (unsigned char)start_buffer->b_data[511] != 0xAA) {
			printk("驱动器 %d 的分区表损坏\n\r", drive);
			panic("");
		}
		p = 0x1BE + (void *)start_buffer->b_data;
		for (i = 1; i < 5; i++, p++) {
			hd[i + 5 * drive].start_sect = p->start_sect;
			hd[i + 5 * drive].nr_sects = p->nr_sects;
		}
	}
	printk("分区表正常。\n\r");
	mount_root();
	return (0);
}

/*
 * 这是每次硬盘中断时执行的函数指针。
 * 有趣的实现方式，但应该相当实用。
 */
void (*do_hd)(void) = NULL;

/*
 * 【RISC-V 替换】controller_ready - 检查控制器是否就绪
 * 原始 x86 使用 inb(HD_STATUS) 读取 IDE 状态寄存器。
 * RISC-V 使用 MMIO 读取状态寄存器。
 * 注意：以下地址为占位符，实际地址由平台设备树定义。
 */
#define HD_STATUS_MMIO	0x40000000UL	/* 占位符：硬盘状态 MMIO 地址 */
#define HD_STATUS_READY	0x40
#define HD_STATUS_BUSY	0x80

static int controller_ready(void)
{
	int retries = 1000;

	while (--retries &&
	       (MMIO_READB(HD_STATUS_MMIO) & 0xC0) != HD_STATUS_READY)
		;
	return retries;
}

static int win_result(void)
{
	int i = MMIO_READB(HD_STATUS_MMIO);

	if ((i & (BUSY_STAT | READY_STAT | WRERR_STAT | SEEK_STAT | ERR_STAT))
	    == (READY_STAT | SEEK_STAT))
		return 0; /* 正常 */
	if (i & 1)
		i = MMIO_READB(HD_STATUS_MMIO + 1); /* 读取错误寄存器 */
	return 1;
}

/*
 * 【RISC-V 替换】hd_out - 向硬盘控制器发送命令
 * 原始 x86 使用 dx 寄存器存储 I/O 端口，逐步递增。
 * RISC-V 使用 MMIO 地址直接访问。
 * 注意：以下实现为兼容层，实际 RISC-V 平台应使用 virtio-blk 驱动。
 */
#define HD_DATA_MMIO	0x40000010UL	/* 占位符：数据寄存器 MMIO */
#define HD_CMD_MMIO	0x40000020UL	/* 占位符：命令寄存器 MMIO */

static void hd_out(unsigned int drive, unsigned int nsect,
		   unsigned int sect, unsigned int head,
		   unsigned int cyl, unsigned int cmd,
		   void (*intr_addr)(void))
{
	if (drive > 1 || head > 15)
		panic("尝试写入坏扇区");
	if (!controller_ready())
		panic("硬盘控制器未就绪");
	do_hd = intr_addr;
	MMIO_WRITEB(HD_CMD_MMIO, _CTL);
	MMIO_WRITEB(HD_DATA_MMIO + 0, _WPCOM);
	MMIO_WRITEB(HD_DATA_MMIO + 1, nsect);
	MMIO_WRITEB(HD_DATA_MMIO + 2, sect);
	MMIO_WRITEB(HD_DATA_MMIO + 3, cyl);
	MMIO_WRITEB(HD_DATA_MMIO + 4, cyl >> 8);
	MMIO_WRITEB(HD_DATA_MMIO + 5, 0xA0 | (drive << 4) | head);
	MMIO_WRITEB(HD_DATA_MMIO + 6, cmd);
}

static int drive_busy(void)
{
	unsigned int i;
	unsigned int status;

	for (i = 0; i < 100000; i++) {
		status = MMIO_READB(HD_STATUS_MMIO);
		if ((status & (BUSY_STAT | READY_STAT)) == READY_STAT)
			break;
	}
	status = MMIO_READB(HD_STATUS_MMIO);
	status &= BUSY_STAT | READY_STAT | SEEK_STAT;
	if (status == (READY_STAT | SEEK_STAT))
		return 0;
	printk("硬盘控制器超时\n\r");
	return 1;
}

static void reset_controller(void)
{
	int i;

	MMIO_WRITEB(HD_CMD_MMIO, 4);
	for (i = 0; i < 1000; i++)
		nop();
	MMIO_WRITEB(HD_CMD_MMIO, 0);
	for (i = 0; i < 10000 && drive_busy(); i++)
		;
	if (drive_busy())
		printk("硬盘控制器仍忙\n\r");
	if ((i = MMIO_READB(HD_STATUS_MMIO + 1)) != 1)
		printk("硬盘控制器复位失败: %02x\n\r", i);
}

static void reset_hd(int nr)
{
	reset_controller();
	hd_out(nr, _SECT, _SECT, _HEAD - 1, _CYL, WIN_SPECIFY, &do_request);
}

void unexpected_hd_interrupt(void)
{
	panic("意外的硬盘中断\n\r");
}

static void bad_rw_intr(void)
{
	int i = this_request->hd;

	if (this_request->errors++ >= MAX_ERRORS) {
		this_request->bh->b_uptodate = 0;
		unlock_buffer(this_request->bh);
		wake_up(&wait_for_request);
		this_request->hd = -1;
		this_request = this_request->next;
	}
	reset_hd(i);
}

static void read_intr(void)
{
	if (win_result()) {
		bad_rw_intr();
		return;
	}
	port_read(HD_DATA_MMIO,
		this_request->bh->b_data +
		512 * (this_request->nsector & 1), 256);
	this_request->errors = 0;
	if (--this_request->nsector)
		return;
	this_request->bh->b_uptodate = 1;
	this_request->bh->b_dirt = 0;
	wake_up(&wait_for_request);
	unlock_buffer(this_request->bh);
	this_request->hd = -1;
	this_request = this_request->next;
	do_request();
}

static void write_intr(void)
{
	if (win_result()) {
		bad_rw_intr();
		return;
	}
	if (--this_request->nsector) {
		port_write(HD_DATA_MMIO,
			this_request->bh->b_data + 512, 256);
		return;
	}
	this_request->bh->b_uptodate = 1;
	this_request->bh->b_dirt = 0;
	wake_up(&wait_for_request);
	unlock_buffer(this_request->bh);
	this_request->hd = -1;
	this_request = this_request->next;
	do_request();
}

static void do_request(void)
{
	int i, r;

	if (sorting)
		return;
	if (!this_request) {
		do_hd = NULL;
		return;
	}
	if (this_request->cmd == WIN_WRITE) {
		hd_out(this_request->hd, this_request->nsector,
			this_request->sector, this_request->head,
			this_request->cyl, this_request->cmd, &write_intr);
		for (i = 0; i < 3000 && !(r = MMIO_READB(HD_STATUS_MMIO) & DRQ_STAT); i++)
			;
		if (!r) {
			reset_hd(this_request->hd);
			return;
		}
		port_write(HD_DATA_MMIO,
			this_request->bh->b_data +
			512 * (this_request->nsector & 1), 256);
	} else if (this_request->cmd == WIN_READ) {
		hd_out(this_request->hd, this_request->nsector,
			this_request->sector, this_request->head,
			this_request->cyl, this_request->cmd, &read_intr);
	} else
		panic("未知的硬盘命令");
}

/*
 * add_request 将请求添加到链表中。
 * 当执行可能受中断影响的操作时，设置 sorting 变量。
 */
static void add_request(struct hd_request *req)
{
	struct hd_request *tmp;

	if (req->nsector != 2)
		panic("nsector != 2 未实现");

	/*
	 * 为了不搞乱链表，我们从不触碰前两个条目
	 * （不是 this_request，因为它被当前中断使用，
	 * 也不是 this_request->next，因为它可能被赋给 this_request）。
	 * 这是为不禁用中断的能力付出的不高代价。
	 */
	sorting = 1;
	if (!(tmp = this_request))
		this_request = req;
	else {
		if (!(tmp->next))
			tmp->next = req;
		else {
			tmp = tmp->next;
			for (; tmp->next; tmp = tmp->next)
				if ((IN_ORDER(tmp, req) ||
				    !IN_ORDER(tmp, tmp->next)) &&
				    IN_ORDER(req, tmp->next))
					break;
			req->next = tmp->next;
			tmp->next = req;
		}
	}
	sorting = 0;

	/*
	 * 注意！由于排序，中断可能已停止，
	 * 因为中断不重新执行（sorting=1 锁定）。
	 * 如果这是队列中的第一个请求，中断可能也从未开始，
	 * 因此如有必要我们重新启动。
	 */
	if (!do_hd)
		do_request();
}

void rw_abs_hd(int rw, unsigned int nr, unsigned int sec,
		unsigned int head, unsigned int cyl,
		struct buffer_head *bh)
{
	struct hd_request *req;

	if (rw != READ && rw != WRITE)
		panic("错误的硬盘命令，必须是读/写");
	lock_buffer(bh);
repeat:
	for (req = 0 + request; req < NR_REQUEST + request; req++)
		if (req->hd < 0)
			break;
	if (req == NR_REQUEST + request) {
		sleep_on(&wait_for_request);
		goto repeat;
	}
	req->hd = nr;
	req->nsector = 2;
	req->sector = sec;
	req->head = head;
	req->cyl = cyl;
	req->cmd = ((rw == READ) ? WIN_READ : WIN_WRITE);
	req->bh = bh;
	req->errors = 0;
	req->next = NULL;
	add_request(req);
	wait_on_buffer(bh);
}

/*
 * 【RISC-V 替换】hd_init - 硬盘初始化
 * 原始 x86 设置 8259A 中断门和 IMR 寄存器。
 * RISC-V 中断由 PLIC 管理，中断向量在架构层设置。
 */
void hd_init(void)
{
	int i;

	for (i = 0; i < NR_REQUEST; i++) {
		request[i].hd = -1;
		request[i].next = NULL;
	}
	for (i = 0; i < NR_HD; i++) {
		hd[i * 5].start_sect = 0;
		hd[i * 5].nr_sects = hd_info[i].head *
				hd_info[i].sect * hd_info[i].cyl;
	}

	/*
	 * 【RISC-V 说明】以下 x86 代码被移除:
	 *   set_trap_gate(0x2E, &hd_interrupt);
	 *   outb_p(inb_p(0x21) & 0xfb, 0x21);
	 *   outb(inb_p(0xA1) & 0xbf, 0xA1);
	 * RISC-V 硬盘中断通过 plic 注册，中断号由设备树指定。
	 * 硬盘控制器初始化由平台代码完成。
	 */
}
