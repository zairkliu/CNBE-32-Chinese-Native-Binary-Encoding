#include <stdint.h>
#include "cnbe.h"
#include "shell.h"
#define UART_BASE 0x10000000
#define UART_THR (*(volatile char*)(UART_BASE))
#define UART_LSR (*(volatile char*)(UART_BASE + 5))
void uart_putchar(char c) { UART_THR = c; }
void uart_puts(const char* s) { while (*s) { if (*s==10) uart_putchar(13); uart_putchar(*s++); } }
char uart_getchar(void) { while(!(UART_LSR & 1)); return UART_THR; }

void main() {
    cnbe_init();
    uart_puts("\n\nCNBE-32 v8.3 OS for RISC-V\n1GHz | 1GB RAM | Chinese BASIC\n");
    shell_run();
    while(1) {}
}