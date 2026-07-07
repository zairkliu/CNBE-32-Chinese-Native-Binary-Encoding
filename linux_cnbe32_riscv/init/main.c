/* Linux 0.01 CNBE-32 版本 —— 初始化入口
 * 基于仓库 basic 编码思路: 中文消息 + CNBE-32 运行时集成
 * 硬件: RISC-V 1GHz | 32MB L3 Cache | 1GB RAM | 1GB Storage
 */

#define __LIBRARY__
#include <unistd.h>
#include <time.h>

#include <linux/tty.h>
#include <linux/sched.h>
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


/* 系统初始化时间 —— 使用 RISC-V mtime 寄存器 */
#define MTIME_BASE      0x0200BFF8UL
static uint64_t read_mtime(void)
{
    return *(volatile uint64_t *)MTIME_BASE;
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
    move_to_user_mode();
    if (!fork()) {
        init();
    }
    for(;;) pause();
}

static int printf(const char *fmt, ...)
{
    va_list args;
    int i;
    va_start(args, fmt);
    write(1, printbuf, i = vsprintf(printbuf, fmt, args));
    va_end(args);
    return i;
}

static char * argv[] = { "-", NULL };
static char * envp[] = { "HOME=/usr/root", NULL };  /* 环境变量路径保留英文 */

void init(void)
{
    int i, j;

    setup();
    if (!fork())
        _exit(execve("/bin/update", NULL, NULL));
    (void) open("/dev/tty0", O_RDWR, 0);
    (void) dup(0);
    (void) dup(0);
    printf("%d 个缓冲区 = %d 字节缓冲空间\r\n", NR_BUFFERS, NR_BUFFERS * BLOCK_SIZE);
    printf(" 就绪\r\n");

    /* CNBE-32 中文内核就绪消息 */
    printf("=== 中文原生操作系统 ===\r\n");
    printf("CNBE-32 中文编码 | RISC-V 64位架构\r\n");
    printf("部首-笔画-结构 三维语义编码\r\n");

    if ((i = fork()) < 0)
        printf("初始化创建进程失败\r\n");
    else if (!i) {
        close(0); close(1); close(2);
        setsid();
        (void) open("/dev/tty0", O_RDWR, 0);
        (void) dup(0);
        (void) dup(0);
        printf("\r\n中文系统> ");
        _exit(execve("/bin/sh", argv, envp));
    }
    j = wait(&i);
    printf("子进程 %d 退出，代码 %04x\n", j, i);
    sync();
    _exit(0);
}
