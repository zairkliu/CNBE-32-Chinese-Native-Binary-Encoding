#include <stdint.h>
#include "basic.h"
#include "cnbe.h"

extern void uart_puts(const char*);
extern void uart_putchar(char);

static int vars[26];

static void skip_space(const char** p) {
    while (**p == 32 || **p == 9 || **p == 10 || **p == 13) (*p)++;
}

static void print_hex(uint32_t v) {
    const char* hex = "0123456789ABCDEF";
    uart_puts("0x");
    int started = 0;
    for (int i = 28; i >= 0; i -= 4) {
        int d = (v >> i) & 0xF;
        if (d || started || i == 0) { started = 1; uart_putchar(hex[d]); }
    }
}

static void print_int(int v) {
    char buf[12]; int pos = 10; buf[11] = 0;
    int neg = 0;
    if (v < 0) { neg = 1; v = -v; }
    do { buf[--pos] = (v % 10) + 48; v /= 10; } while (v);
    if (neg) buf[--pos] = 45;
    uart_puts(buf + pos);
}

static int parse_int(const char** p) {
    skip_space(p);
    int val = 0, neg = 0;
    if (**p == 45) { neg = 1; (*p)++; skip_space(p); }
    while (**p >= 48 && **p <= 57) { val = val * 10 + (**p - 48); (*p)++; }
    return neg ? -val : val;
}

static int eval_expr(const char** p) {
    skip_space(p);
    int val = parse_int(p);
    skip_space(p);
    if (**p == 43) { (*p)++; val += eval_expr(p); }
    else if (**p == 45) { (*p)++; val -= eval_expr(p); }
    return val;
}

static int match_utf8(const char** p, const char* pat, int plen) {
    for (int i = 0; i < plen; i++) {
        if ((unsigned char)(*p)[i] != (unsigned char)pat[i]) return 0;
    }
    *p += plen;
    return 1;
}

int basic_eval(const char* line) {
    const char* p = line;
    skip_space(&p);
    if (*p == 0) return 0;

    // Output: E8 BE 93 E5 87 BA
    if (match_utf8(&p, "\xE8\xBE\x93\xE5\x87\xBA", 6)) {
        skip_space(&p);
        if (*p == 40) p++;
        int val = eval_expr(&p);
        print_int(val);
        uart_putchar(10);
        return 0;
    }

    // Return: E8 BF 94 E5 9B 9E
    if (match_utf8(&p, "\xE8\xBF\x94\xE5\x9B\x9E", 6)) {
        return 0;
    }

    // Get code: E5 8F 96 E7 BC 96 E7 A0 81
    if (match_utf8(&p, "\xE5\x8F\x96\xE7\xBC\x96\xE7\xA0\x81", 9)) {
        skip_space(&p);
        if (*p == 40) p++;
        int val = eval_expr(&p);
        if (val >= 0x4E00 && val <= 0x9FA5) {
            uint32_t code = cnhe_map((uint32_t)val);
            if (code) {
                uart_puts("CNBE: "); print_hex(code); uart_putchar(10);
                uart_puts("Radical: "); print_int(cnhe_extract(code, 0)); uart_putchar(10);
                uart_puts("Stroke: "); print_int(cnhe_extract(code, 1)); uart_putchar(10);
                uart_puts("Struct: "); print_int(cnhe_extract(code, 2)); uart_putchar(10);
            } else {
                uart_puts("Not encoded\n");
            }
        } else {
            uart_puts("Invalid\n");
        }
        return 0;
    }

    // Compare: E6 AF 94 E8 BE 83
    if (match_utf8(&p, "\xE6\xAF\x94\xE8\xBE\x83", 6)) {
        skip_space(&p);
        if (*p == 40) p++;
        int a = eval_expr(&p);
        skip_space(&p);
        if (*p == 44) p++;
        int b = eval_expr(&p);
        uint32_t dist = cnhe_cmp((uint32_t)a, (uint32_t)b);
        uart_puts("Dist: "); print_int(dist); uart_putchar(10);
        return 0;
    }

    // Help: E5 B8 AE E5 8A A9
    if (match_utf8(&p, "\xE5\xB8\xAE\xE5\x8A\xA9", 6)) {
        uart_puts("BASIC commands:\n");
        uart_puts("  output(num)\n");
        uart_puts("  return\n");
        uart_puts("  getcode(Unicode)\n");
        uart_puts("  compare(code1,code2)\n");
        return 0;
    }

    uart_puts(" ?\n");
    return 0;
}
