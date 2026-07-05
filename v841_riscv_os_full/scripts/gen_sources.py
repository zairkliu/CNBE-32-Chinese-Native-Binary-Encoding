#!/usr/bin/env python3
"""Generate all v8.4.1 source files for CNBE-32 RISC-V OS."""

import os
import sys

ROOT = os.path.expanduser("~/v84_riscv_os_full")


def write_file(relpath, content):
    """Write content to file under ROOT, creating dirs as needed."""
    full = os.path.join(ROOT, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK  {relpath}")


def main():
    print("Generating v8.4.1 sources...")

    # ---- 1. reader.c ----
    write_file(
        "src/editor/reader.c",
        r'''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "reader.h"
#include "daodejing_data.h"

extern void uart_putchar(char);
extern void uart_puts(const char*);
extern char uart_getchar(void);

#define TEXT_BUF_BASE   0x80200000
#define TEXT_BUF_SIZE   (1 * 1024 * 1024)
#define MAX_LINES       1000
#define MAX_LINE_LEN    256

static char *text_buf = (char*)TEXT_BUF_BASE;
static int line_count = 0;
static int total_chars = 0;
static char *line_ptrs[MAX_LINES];
static int line_lens[MAX_LINES];

void reader_init(void) {
    line_count = 0;
    total_chars = 0;
    for (int i = 0; i < MAX_LINES; i++) line_ptrs[i] = 0;
    for (int i = 0; i < TEXT_BUF_SIZE; i++) text_buf[i] = 0;
    line_ptrs[0] = text_buf;
    line_lens[0] = 0;
    line_count = 1;
}

void reader_add_line(const char *line) {
    if (line_count >= MAX_LINES) {
        uart_puts("ERROR: too many lines\n");
        return;
    }
    int len = 0;
    while (line[len]) len++;
    if (len > MAX_LINE_LEN) len = MAX_LINE_LEN;
    char *dest;
    if (line_count == 1 && line_lens[0] == 0) {
        dest = text_buf;
    } else {
        dest = text_buf + total_chars;
    }
    for (int i = 0; i < len; i++) dest[i] = line[i];
    dest[len] = 0;
    line_ptrs[line_count - 1] = dest;
    line_lens[line_count - 1] = len;
    total_chars += len + 1;
    line_count++;
}

void reader_display(void) {
    uart_puts("\n========== TEXT ==========\n");
    for (int i = 0; i < line_count; i++) {
        if (line_ptrs[i] == 0) continue;
        int n = i + 1;
        char num[8];
        int pos = 0;
        int started = 0;
        for (int d = 10000; d != 0; d /= 10) {
            int digit = (n / d) % 10;
            if (digit || started || d == 1) {
                num[pos++] = '0' + digit;
                started = 1;
            }
        }
        num[pos] = 0;
        uart_puts(num);
        uart_puts(": ");
        uart_puts(line_ptrs[i]);
        uart_putchar('\n');
    }
    uart_puts("==========================\n");
    uart_puts("Lines: ");
    uart_putchar('0' + (line_count / 100) % 10);
    uart_putchar('0' + (line_count / 10) % 10);
    uart_putchar('0' + line_count % 10);
    uart_puts("  Chars: ");
    int tc = total_chars;
    uart_putchar('0' + (tc / 10000) % 10);
    uart_putchar('0' + (tc / 1000) % 10);
    uart_putchar('0' + (tc / 100) % 10);
    uart_putchar('0' + (tc / 10) % 10);
    uart_putchar('0' + tc % 10);
    uart_putchar('\n');
}

void reader_add_line_raw(const char *line) {
    if (line_count >= MAX_LINES) return;
    int len = 0;
    while (line[len]) len++;
    if (len > MAX_LINE_LEN) len = MAX_LINE_LEN;
    char *dest = text_buf + total_chars;
    for (int i = 0; i < len; i++) dest[i] = line[i];
    dest[len] = 0;
    line_ptrs[line_count] = dest;
    line_lens[line_count] = len;
    total_chars += len + 1;
    line_count++;
}

void reader_enter(void) {
    char buf[MAX_LINE_LEN + 2];
    int idx;
    uart_puts("\nEnter input mode (empty line to quit):\n");
    while (1) {
        uart_puts("> ");
        idx = 0;
        char c;
        while (1) {
            c = uart_getchar();
            if (c == 13 || c == 10) {
                uart_putchar('\n');
                break;
            }
            if (c == 127 || c == 8) {
                if (idx > 0) {
                    idx--;
                    uart_puts("\b \b");
                }
                continue;
            }
            if (idx < MAX_LINE_LEN) {
                buf[idx++] = c;
                uart_putchar(c);
            }
        }
        buf[idx] = 0;
        if (idx == 0) break;
        reader_add_line_raw(buf);
    }
    uart_puts("Input complete.\n");
}

void reader_stats(void) {
    int chinese_chars = 0;
    int ascii_chars = 0;
    for (int i = 0; i < line_count; i++) {
        if (line_ptrs[i] == 0) continue;
        char *p = line_ptrs[i];
        while (*p) {
            if ((*p & 0x80) == 0) {
                ascii_chars++;
                p++;
            } else if ((*p & 0xE0) == 0xC0) {
                chinese_chars++;
                p += 2;
            } else if ((*p & 0xF0) == 0xE0) {
                chinese_chars++;
                p += 3;
            } else {
                p++;
            }
        }
    }
    uart_puts("\n===== STATS =====\n");
    uart_puts("Lines: ");
    uart_putchar('0' + (line_count / 100) % 10);
    uart_putchar('0' + (line_count / 10) % 10);
    uart_putchar('0' + line_count % 10);
    uart_puts("\nChinese chars: ");
    uart_putchar('0' + (chinese_chars / 100) % 10);
    uart_putchar('0' + (chinese_chars / 10) % 10);
    uart_putchar('0' + chinese_chars % 10);
    uart_puts("\nASCII chars: ");
    uart_putchar('0' + (ascii_chars / 100) % 10);
    uart_putchar('0' + (ascii_chars / 10) % 10);
    uart_putchar('0' + ascii_chars % 10);
    uart_putchar('\n');
    uart_puts("=================\n");
}

void reader_load_daodejing(void) {
    reader_init();
    line_count = 0;
    total_chars = 0;
    for (int i = 0; i < DDJ_LINE_COUNT; i++) {
        reader_add_line_raw(daodejing_text[i]);
    }
    uart_puts("Loaded: Daode Jing (");
    uart_putchar('0' + (DDJ_LINE_COUNT / 100) % 10);
    uart_putchar('0' + (DDJ_LINE_COUNT / 10) % 10);
    uart_putchar('0' + DDJ_LINE_COUNT % 10);
    uart_puts(" lines)\n");
}
''',
    )

    # ---- 2. shell.c ----
    write_file(
        "src/shell/shell.c",
        r'''#include <stdint.h>
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
''',
    )

    # ---- 3. main.c ----
    write_file(
        "src/kernel/main.c",
        r'''#include <stdint.h>

volatile char* const UART = (char*)0x10000000;

void uart_putchar(char c) {
    *UART = c;
}

void uart_puts(const char* s) {
    while (*s) {
        if (*s == 10) uart_putchar(13);
        uart_putchar(*s++);
    }
}

char uart_getchar(void) {
    while (!(((volatile uint32_t*)0x10000000)[5] & 1));
    return *UART;
}

extern void shell_run(void);

void main(void) {
    uart_puts("\n\n");
    uart_puts("========================================\n");
    uart_puts("  CNBE-32 v8.4.1 Chinese OS for RISC-V\n");
    uart_puts("  1GHz | 1GB RAM | Text Reader/Editor\n");
    uart_puts("========================================\n");
    uart_puts("  Try: 帮助  |  预置道德经  |  显示\n");
    uart_puts("========================================\n");
    shell_run();
    while (1);
}
''',
    )

    # ---- 4. basic.c (enhanced with print_hex and all commands) ----
    write_file(
        "src/basic/basic.c",
        r'''#include <stdint.h>
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
''',
    )

    print("All source files generated successfully!")


if __name__ == "__main__":
    main()
