/* Linux 0.01 CNBE-32 版本 —— 初始化入口
 * 基于仓库 basic 编码思路: 中文消息 + CNBE-32 运行时集成
 * 硬件: RISC-V 1GHz | 32MB L3 Cache | 1GB RAM | 1GB Storage
 */

#define __LIBRARY__
#include <unistd.h>
#include <time.h>

#include <linux/tty.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <linux/head.h>
#include <asm/system.h>
#include <asm/io.h>
#include <linux/fs.h>

#include <stddef.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>

#include <stdint.h>

#include <cnbe.h>

/* RISC-V 系统调用内联声明 (现代 GCC 不支持 static 在 extern 之后) */
_syscall0(int,fork)
_syscall0(int,pause)
_syscall0(int,setup)
_syscall0(int,sync)

static char printbuf[1024];

extern int vsprintf(char *buf, const char *fmt, va_list args);
extern void init(void);
extern void hd_init(void);
extern long kernel_mktime(struct tm * tm);
extern long startup_time;


/* 系统初始化时间 —— QEMU/OpenSBI 下 S-mode 无法直读 CLINT mtime，
 * 先使用固定时间源，后续可改为 SBI get_time 调用。 */
static uint64_t read_mtime(void)
{
    return 0;
}

/* 时间初始化 (替换 x86 CMOS RTC) */
static void time_init(void)
{
    struct tm time;
    uint64_t mtime = read_mtime();
    /* QEMU virt 默认 mtime 频率 10MHz */
    uint64_t sec = mtime / 10000000;

    /* 简化为 2024-01-01 00:00:00 + 秒数 */
    time.tm_sec = sec % 60;
    time.tm_min = (sec / 60) % 60;
    time.tm_hour = (sec / 3600) % 24;
    time.tm_mday = 1 + (sec / 86400) % 30;
    time.tm_mon = 0;
    time.tm_year = 124; /* 2024 - 1900 */

    startup_time = kernel_mktime(&time);
}

void main(void)
{
    /* 中断仍被禁用，进行必要设置后启用 */
    cnbe_init();                    /* 初始化 CNBE-32 查表 (81.6KB -> L3 Cache) */
    time_init();
    tty_init();
    trap_init();
    sched_init();
    buffer_init();
    hd_init();
    sti();                          /* 启用中断 */
    init();
    for(;;) __asm__ volatile ("wfi");
}

static void boot_uart_puts(const char *s)
{
    volatile unsigned char *uart = (volatile unsigned char *)0x10000000UL;
    while (*s) {
        while ((uart[5] & 0x20) == 0)
            ;
        uart[0] = (unsigned char)*s++;
    }
}

void init(void)
{
    boot_uart_puts("\r\n=== 中文原生操作系统 ===\r\n");
    boot_uart_puts("CNBE-32 中文编码 | RISC-V 64位架构\r\n");
    boot_uart_puts("部首-笔画-结构 三维语义编码\r\n");
    boot_uart_puts("中文系统> 就绪\r\n");
}
