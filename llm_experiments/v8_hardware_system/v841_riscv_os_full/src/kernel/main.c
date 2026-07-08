#include <stdint.h>

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
