/* CNBE-32 中文交互式 Shell
 * Linux 0.01 RISC-V 内核版本
 * 
 * 提供 中文> 提示符的交互式中文 Shell
 * 读取用户输入, 传递给 cnbe_basic_eval 求值
 * 直到用户输入 "退出" 命令
 */

#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/tty.h>
#include <asm/io.h>
#include <asm/segment.h>
#include <cnbe.h>
#include <stdarg.h>
#include <stdint.h>
#include <linux/cnbe_basic.h>

/* UART 基地址 (QEMU virt 平台 16550) */
#define UART0_BASE  0x10000000UL
#define UART_THR    0x00
#define UART_RBR    0x00    /* 接收缓冲寄存器 */
#define UART_LSR    0x05
#define UART_LSR_DR   0x01  /* 数据就绪 */
#define UART_LSR_THRE 0x20  /* 发送保持寄存器空 */

/* 从 UART 读取一个字符 (阻塞) */
static char shell_getc(void)
{
    volatile unsigned char *uart = (volatile unsigned char *)UART0_BASE;
    while ((uart[UART_LSR] & UART_LSR_DR) == 0)
        ;
    return (char)uart[UART_RBR];
}

/* 向 UART 输出一个字符 */
static void shell_putc(char c)
{
    volatile unsigned char *uart = (volatile unsigned char *)UART0_BASE;
    while ((uart[UART_LSR] & UART_LSR_THRE) == 0)
        ;
    uart[UART_THR] = (unsigned char)c;
}

/* 输出字符串 */
static void shell_puts(const char *s)
{
    while (*s) {
        if (*s == '\n')
            shell_putc('\r');
        shell_putc(*s);
        s++;
    }
}

/* 读取一行输入 */
static int shell_getline(char *buf, int maxlen)
{
    int i = 0;
    char c;

    while (i < maxlen - 1) {
        c = shell_getc();

        /* 回车 */
        if (c == '\r' || c == '\n') {
            shell_putc('\r');
            shell_putc('\n');
            buf[i] = '\0';
            return i;
        }

        /* 退格 (BS 或 DEL) */
        if (c == 0x08 || c == 0x7F) {
            if (i > 0) {
                i--;
                shell_putc('\b');
                shell_putc(' ');
                shell_putc('\b');
            }
            continue;
        }

        /* 可打印字符 */
        if ((unsigned char)c >= 0x20 || (unsigned char)c >= 0x80) {
            buf[i++] = c;
            shell_putc(c);
        }
    }

    buf[i] = '\0';
    shell_putc('\r');
    shell_putc('\n');
    return i;
}

/* 交互式中文 Shell 主循环 */
void cnbe_shell_run(void)
{
    char buf[256];

    /* 初始化 CNBE-32 运行时 */
    cnbe_init();

    /* 输出欢迎信息 */
    shell_puts("\n");
    shell_puts("╔══════════════════════════════════════╗\n");
    shell_puts("║    CNBE-32 中文 BASIC 解释器        ║\n");
    shell_puts("║    Linux 0.01 RISC-V 内核版本       ║\n");
    shell_puts("║    全中文关键字 — 零英文依赖        ║\n");
    shell_puts("╚══════════════════════════════════════╝\n");
    shell_puts("\n");
    shell_puts("输入 \"帮助\" 查看命令列表\n");
    shell_puts("输入 \"阅读\" 阅读道德经\n");
    shell_puts("输入 \"退出\" 退出解释器\n");
    shell_puts("\n");

    /* 主循环 */
    for (;;) {
        /* 显示提示符 */
        shell_puts("中文> ");

        /* 读取一行 */
        int len = shell_getline(buf, sizeof(buf));

        if (len == 0)
            continue;

        /* 评估输入 */
        int result = cnbe_basic_eval(buf);

        /* 退出命令 */
        if (result < 0) {
            shell_puts("再见！\n");
            break;
        }
    }
}
