#include <stdarg.h>

void verify_area(void * addr,int count);
volatile void panic(const char * str);
int printf(const char * fmt, ...);
int printk(const char * fmt, ...);
int tty_write(unsigned ch,char * buf,int count);
int vsprintf(char *buf, const char *fmt, va_list args);
