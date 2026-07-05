#include <stdint.h>
#include "shell.h"
#include "basic.h"
extern void uart_putchar(char);
extern void uart_puts(const char*);
extern char uart_getchar(void);
static char sbuf[256];
void readline(char* buf, int n) {
    int p = 0;
    while (p < n-1) {
        char c = uart_getchar();
        if (c == 13 || c == 10) { uart_putchar(10); buf[p]=0; return; }
        if (c == 8 || c == 127) { if(p>0){p--; uart_puts("\b \b");} continue; }
        buf[p++] = c; uart_putchar(c);
    }
    buf[p] = 0;
}
void shell_run(void) {
    while (1) {
        uart_puts("\n  C:/> ");
        readline(sbuf, 256);
        if (sbuf[0]==0) continue;
        basic_eval(sbuf);
    }
}