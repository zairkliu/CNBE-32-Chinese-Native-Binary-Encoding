#include <stdint.h>
#include "basic.h"
#include "cnbe.h"

extern void uart_puts(const char*);
extern void uart_putchar(char);

static void skip_space(const char** p) {
    while (**p == 32 || **p == 9 || **p == 10 || **p == 13) (*p)++;
}

static int parse_int(const char** p) {
    skip_space(p);
    int val = 0, neg = 0;
    if (**p == 45) { neg = 1; (*p)++; skip_space(p); }
    while (**p >= 48 && **p <= 57) { val = val * 10 + (**p - 48); (*p)++; }
    return neg ? -val : val;
}

static void print_int(int v) {
    char buf[12]; int pos = 10; buf[11] = 0;
    int neg = 0;
    if (v < 0) { neg = 1; v = -v; }
    do { buf[--pos] = (v % 10) + 48; v /= 10; } while (v);
    if (neg) buf[--pos] = 45;
    uart_puts(buf + pos);
}

static int eval_expr(const char** p) {
    skip_space(p);
    int val = parse_int(p);
    skip_space(p);
    if (**p == 43) { (*p)++; val += eval_expr(p); }
    else if (**p == 45) { (*p)++; val -= eval_expr(p); }
    else if (**p == 42) { (*p)++; val *= eval_expr(p); }
    return val;
}

static int match_utf8(const char** p, const char* pat, int len) {
    for (int i = 0; i < len; i++) { if ((unsigned char)(*p)[i] != (unsigned char)pat[i]) return 0; }
    *p += len; return 1;
}

// Daodejing text
#include "daodejing_text.h"
// Daodejing text from header

int basic_eval(const char* line) {
    const char* p = line;
    skip_space(&p);
    if (*p == 0) return 0;

    if (match_utf8(&p, "\xE8\xBE\x93\xE5\x87\xBA", 6)) { // 输出
        skip_space(&p); if (*p == 40) p++;
        print_int(eval_expr(&p)); uart_putchar(10); return 0;
    }

    if (match_utf8(&p, "\xE8\xBF\x94\xE5\x9B\x9E", 6)) { // 返回
        return 0;
    }

    if (match_utf8(&p, "\xE5\x8F\x96\xE7\xBC\x96\xE7\xA0\x81", 9)) { // 取编码
        skip_space(&p); if (*p == 40) p++;
        uint32_t code = cnhe_map(eval_expr(&p));
        uart_puts("0x");
        for (int i = 7; i >= 0; i--) {
            int nib = (code >> (i * 4)) & 0xF;
            uart_putchar(nib < 10 ? nib + 48 : nib + 55);
        }
        uart_putchar(10); return 0;
    }

    if (match_utf8(&p, "\xE5\x8F\x96\xE9\x83\xA8\xE9\xA6\x96", 9)) { // 取部首
        skip_space(&p); if (*p == 40) p++;
        print_int(cnhe_extract(eval_expr(&p), 0));
        uart_putchar(10); return 0;
    }

    if (match_utf8(&p, "\xE6\xAF\x94\xE8\xBE\x83", 6)) { // 比较
        skip_space(&p); if (*p == 40) p++;
        int a = eval_expr(&p);
        skip_space(&p); if (*p == 44) p++;
        int b = eval_expr(&p);
        print_int(cnhe_cmp(a, b)); uart_putchar(10); return 0;
    }

    if (match_utf8(&p, "\xE9\x98\x85\xE8\xAF\xBB", 6)) { // 阅读
        uart_puts(ddj_text); return 0;
    }

    if (match_utf8(&p, "\xE5\xB8\xAE\xE5\x8A\xA9", 6)) { // 帮助
        uart_puts("\n  Commands:\n");
        uart_puts("  输出(N) - print\n");
        uart_puts("  返回(N) - exit\n");
        uart_puts("  取编码(U) - CNBE code\n");
        uart_puts("  取部首(C) - radical field\n");
        uart_puts("  比较(A,B) - distance\n");
        uart_puts("  阅读() - Dao De Jing\n");
        uart_puts("  帮助() - this help\n");
        return 0;
    }

    uart_puts(" ?\n");
    return 0;
}