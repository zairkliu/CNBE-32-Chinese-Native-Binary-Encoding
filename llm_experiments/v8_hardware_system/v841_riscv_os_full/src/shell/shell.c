#include <stdint.h>
#include "shell.h"
#include "basic.h"
#include "reader.h"

extern void uart_putchar(char);
extern void uart_puts(const char*);
extern char uart_getchar(void);

static char sbuf[256];

static void readline(char* buf, int n) {
    int p = 0;
    while (p < n - 1) {
        char c = uart_getchar();
        if (c == 13 || c == 10) {
            uart_putchar(10);
            buf[p] = 0;
            return;
        }
        if (c == 8 || c == 127) {
            if (p > 0) { p--; uart_puts("\b \b"); }
            continue;
        }
        buf[p++] = c;
        uart_putchar(c);
    }
    buf[p] = 0;
}

static int match_str(const char** p, const char* s, int len) {
    for (int i = 0; i < len; i++) {
        if ((unsigned char)(*p)[i] != (unsigned char)s[i]) return 0;
    }
    *p += len;
    return 1;
}

void shell_run(void) {
    reader_init();
    while (1) {
        uart_puts("\n 中文系统 > ");
        readline(sbuf, 256);
        if (sbuf[0] == 0) continue;

        const char* p = sbuf;

        // "录入" = E5 BD 95 E5 85 A5 (6 bytes)
        if (match_str(&p, "\xE5\xBD\x95\xE5\x85\xA5", 6)) {
            reader_enter();
            continue;
        }
        // "显示" = E6 98 BE E7 A4 BA (6 bytes)
        if (match_str(&p, "\xE6\x98\xBE\xE7\xA4\xBA", 6)) {
            reader_display();
            continue;
        }
        // "统计" = E7 BB 9F E8 AE A1 (6 bytes)
        if (match_str(&p, "\xE7\xBB\x9F\xE8\xAE\xA1", 6)) {
            reader_stats();
            continue;
        }
        // "预置道德经" = E9 A2 84 E7 BD AE E9 81 93 E5 BE B7 E7 BB 8F (15 bytes)
        if (match_str(&p, "\xE9\xA2\x84\xE7\xBD\xAE\xE9\x81\x93\xE5\xBE\xB7\xE7\xBB\x8F", 15)) {
            reader_load_daodejing();
            continue;
        }
        // "帮助" = E5 B8 AE E5 8A A9 (6 bytes)
        if (match_str(&p, "\xE5\xB8\xAE\xE5\x8A\xA9", 6)) {
            uart_puts("Available commands:\n");
            uart_puts("  输出(数字) - print number\n");
            uart_puts("  返回 - return\n");
            uart_puts("  取编码(Unicode) - CNBE lookup\n");
            uart_puts("  比较(code1,code2) - CNBE distance\n");
            uart_puts("  录入 - text input\n");
            uart_puts("  显示 - display text\n");
            uart_puts("  统计 - text statistics\n");
            uart_puts("  预置道德经 - load Daode Jing\n");
            continue;
        }

        // Default: try BASIC eval
        basic_eval(sbuf);
    }
}
