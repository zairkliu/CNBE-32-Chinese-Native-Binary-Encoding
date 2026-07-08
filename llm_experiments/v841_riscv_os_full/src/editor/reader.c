#include <stdint.h>
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
