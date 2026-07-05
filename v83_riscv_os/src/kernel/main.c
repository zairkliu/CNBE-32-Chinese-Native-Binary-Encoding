#include <stdint.h>
volatile char* const UART = (char*)0x10000000;
void uart_putchar(char c) { *UART = c; }
void uart_puts(const char* s) { while (*s) { if (*s==10) uart_putchar(13); uart_putchar(*s++); } }
char uart_getchar(void) { while(!(((volatile uint32_t*)0x10000000)[5]&1)); return *UART; }
void main() {
    uart_puts("\n\nHello from CNBE-32!\n");
    uart_puts("Type a char: ");
    uart_putchar(uart_getchar());
    uart_puts("\nDone.\n");
    while(1);
}