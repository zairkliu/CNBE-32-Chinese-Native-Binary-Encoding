#!/usr/bin/env python3
import os

code = '''#include <stdint.h>

/* UART registers for QEMU virt ns16550a */
#define UART_BASE ((volatile unsigned char*)0x10000000)

void uart_putchar(char c) {
    UART_BASE[0] = (unsigned char)c;  /* THR at offset 0 */
}

void uart_puts(const char* s) {
    while (*s) {
        if (*s == 10) uart_putchar(13);
        uart_putchar(*s++);
    }
}

char uart_getchar(void) {
    while (!(UART_BASE[5] & 1));  /* LSR bit 0 = data ready */
    return (char)UART_BASE[0];    /* RBR at offset 0 */
}

extern void shell_run(void);

void main(void) {
    UART_BASE[3] = 0x03;  /* LCR: 8N1 */

    uart_puts("\\n\\n");
    uart_puts("========================================\\n");
    uart_puts("  CNBE-32 v8.4.1 Chinese OS for RISC-V\\n");
    uart_puts("  1GHz | 1GB RAM | Text Reader/Editor\\n");
    uart_puts("========================================\\n");
    uart_puts("  Try: help | load-daodejing | display\\n");
    uart_puts("========================================\\n");
    shell_run();
    while (1);
}
'''

path = os.path.expanduser("~/v84_riscv_os_full/src/kernel/main.c")
with open(path, "w", encoding="utf-8") as f:
    f.write(code)
print("Written fixed main.c")
