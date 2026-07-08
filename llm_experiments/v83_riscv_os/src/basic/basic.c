#include <stdint.h>
#include "basic.h"

extern void uart_puts(const char*);
extern void uart_putchar(char);

static int vars[26];

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
    return val;
}

static int match_utf8(const char** p, const char* pattern, int plen) {
    for (int i = 0; i < plen; i++) {
        if ((*p)[i] != pattern[i]) return 0;
    }
    *p += plen;
    return 1;
}

int basic_eval(const char* line) {
    const char* p = line;
    skip_space(&p);
    if (*p == 0) return 0;

    // 输出 = E8 BE 93 E5 87 BA (6 bytes)
    if (match_utf8(&p, "\xE8\xBE\x93\xE5\x87\xBA", 6)) {
        skip_space(&p);
        if (*p == 40) p++;
        int val = eval_expr(&p);
        print_int(val);
        uart_putchar(10);
        return 0;
    }

    // 返回 = E8 BF 94 E5 9B 9E (6 bytes)
    if (match_utf8(&p, "\xE8\xBF\x94\xE5\x9B\x9E", 6)) {
        return 0;
    }

    uart_puts(" ?\n");
    return 0;
}