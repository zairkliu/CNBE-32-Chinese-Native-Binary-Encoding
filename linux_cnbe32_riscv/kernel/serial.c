/*
 * 【RISC-V 转码状态】kernel/serial.c
 * 原始文件: Linux 0.01 kernel/serial.c
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - x86 I/O 端口 (0x3f8, 0x2f8) → MMIO UART16550 (0x10000000)
 *   - 移除 set_intr_gate 调用 (x86 特定中断门设置)
 *   - cli/sti → RISC-V mstatus MIE 位操作
 *   - 保留串口初始化和中断处理逻辑框架
 *   - 添加中文注释
 *   - 集成 CNBE-32 头文件
 *
 * 【RISC-V 说明】
 * RISC-V virt 平台使用 UART16550 兼容控制器，基址 0x10000000。
 * 中断通过 PLIC 路由，而非 x86 的 8259A PIC。
 * 串口初始化在中断控制器初始化之后完成。
 */

#include <linux/tty.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <asm/system.h>
#include <cnbe.h>

#define RISCV_DISABLE_IRQ()  cli()
#define RISCV_ENABLE_IRQ()   sti()

/* UART16550 MMIO 定义 */
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
#define UART_DLL        (UART_BASE + 0x00)
#define UART_DLM        (UART_BASE + 0x01)
#define UART_LSR_DR     0x01
#define UART_LSR_THRE   0x20
#define UART_LSR_TEMT   0x40

#define MMIO_READB(addr)        (*(volatile unsigned char *)(addr))
#define MMIO_WRITEB(addr, val)  (*(volatile unsigned char *)(addr) = (val))

/* 唤醒阈值 */
#define WAKEUP_CHARS (TTY_BUF_SIZE / 4)

extern void rs1_interrupt(void);
extern void rs2_interrupt(void);

/*
 * 【RISC-V 替换】init - 初始化 UART
 * 原始 x86 使用 outb_p 配置 8250/16550 UART 的 I/O 端口。
 * RISC-V 使用 MMIO 访问 UART 寄存器。
 * 注意: 目标波特率 9600，假设 UART 时钟为 1.8432MHz。
 */
static void init(unsigned long port_base)
{
	MMIO_WRITEB(port_base + 3, 0x80);		/* 设置 DLAB */
	MMIO_WRITEB(port_base + 0, 0x0C);		/* 除数低字节 (9600 bps) */
	MMIO_WRITEB(port_base + 1, 0x00);		/* 除数高字节 */
	MMIO_WRITEB(port_base + 3, 0x03);		/* 8位数据, 无校验, 1位停止 */
	MMIO_WRITEB(port_base + 4, 0x0B);		/* 设置 DTR, RTS, OUT_2 */
	MMIO_WRITEB(port_base + 1, 0x0D);		/* 使能除发送外的所有中断 */
	(void) MMIO_READB(port_base + 0);		/* 读数据端口以复位状态 */
}

/*
 * 【RISC-V 替换】rs_init - 初始化串口
 * 原始 x86 代码设置 8259A 中断门 (0x24, 0x23)。
 * RISC-V 中断由 PLIC/CLINT 管理，中断向量在 trap_entry.S 中统一设置。
 * 此处仅初始化 UART 硬件，中断注册由架构代码完成。
 */
void rs_init(void)
{
	/* 初始化串口 1 和串口 2 */
	init(tty_table[1].read_q.data);
	init(tty_table[2].read_q.data);

	/*
	 * 【RISC-V 说明】以下 x86 代码被移除:
	 *   set_intr_gate(0x24, rs1_interrupt);
	 *   set_intr_gate(0x23, rs2_interrupt);
	 *   outb(inb_p(0x21) & 0xE7, 0x21);
	 * RISC-V 使用 plic_init() 或 clint_init() 配置外部中断，
	 * 串口中断在设备树中指定 IRQ 号，通过 request_irq() 注册。
	 */
}

/*
 * 【RISC-V 替换】rs_write - 串口写函数
 * 当 tty_write 将数据放入 write_queue 时调用。
 * 检查队列是否为空，并设置中断使能寄存器。
 */
void rs_write(struct tty_struct *tty)
{
	unsigned long port;

	RISCV_DISABLE_IRQ();
	if (!EMPTY(tty->write_q)) {
		port = tty->write_q.data;
		MMIO_WRITEB(port + 1,
			MMIO_READB(port + 1) | 0x02);
	}
	RISCV_ENABLE_IRQ();
}
