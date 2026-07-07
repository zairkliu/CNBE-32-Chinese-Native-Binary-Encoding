/*
 * 【RISC-V 转码状态】kernel/vsprintf.c
 * 原始文件: Linux 0.01 kernel/vsprintf.c
 * 原作者: Lars Wirzenius & Linus Torvalds
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - 将 x86 divl 内联汇编替换为 C 语言除法运算
 *   - RISC-V 编译器可高效生成 div/rem 指令
 *   - 保留原有格式控制逻辑，确保输出兼容
 *   - 添加中文注释
 *   - 集成 CNBE-32 头文件
 */

#include <stdarg.h>
#include <string.h>
#include <cnbe.h>

/* 无需 ctype 库，使用简单数字判断宏 */
#define is_digit(c)	((c) >= '0' && (c) <= '9')

static int skip_atoi(const char **s)
{
	int i = 0;

	while (is_digit(**s))
		i = i * 10 + *((*s)++) - '0';
	return i;
}

#define ZEROPAD	1		/* 用零填充 */
#define SIGN	2		/* 有符号/无符号长整型 */
#define PLUS	4		/* 显示正号 */
#define SPACE	8		/* 正数前加空格 */
#define LEFT	16		/* 左对齐 */
#define SPECIAL	32		/* 显示前缀 0x */
#define SMALL	64		/* 使用小写 'abcdef' */

/*
 * 【RISC-V 替换】do_div 宏
 * 原始 x86 代码使用 divl 内联汇编:
 *   __asm__("divl %4":"=a" (n),"=d" (__res):"0" (n),"1" (0),"r" (base));
 * RISC-V 使用 C 语言除法/取模，编译器将生成 div/rem 指令。
 * 注意：RISC-V 32位使用 div/rem 指令，64位使用 divw/remw。
 */
#define do_div(n, base) ({ \
	int __res = (n) % (base); \
	(n) = (n) / (base); \
	__res; \
})

static char * number(char *str, int num, int base, int size, int precision,
			int type)
{
	char c, sign, tmp[36];
	const char *digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
	int i;

	if (type & SMALL)
		digits = "0123456789abcdefghijklmnopqrstuvwxyz";
	if (type & LEFT)
		type &= ~ZEROPAD;
	if (base < 2 || base > 36)
		return 0;
	c = (type & ZEROPAD) ? '0' : ' ';
	if (type & SIGN && num < 0) {
		sign = '-';
		num = -num;
	} else
		sign = (type & PLUS) ? '+' : ((type & SPACE) ? ' ' : 0);
	if (sign)
		size--;
	if (type & SPECIAL)
		if (base == 16)
			size -= 2;
		else if (base == 8)
			size--;
	i = 0;
	if (num == 0)
		tmp[i++] = '0';
	else while (num != 0)
		tmp[i++] = digits[do_div(num, base)];
	if (i > precision)
		precision = i;
	size -= precision;
	if (!(type & (ZEROPAD + LEFT)))
		while (size-- > 0)
			*str++ = ' ';
	if (sign)
		*str++ = sign;
	if (type & SPECIAL)
		if (base == 8)
			*str++ = '0';
		else if (base == 16) {
			*str++ = '0';
			*str++ = digits[33];
		}
	if (!(type & LEFT))
		while (size-- > 0)
			*str++ = c;
	while (i < precision--)
		*str++ = '0';
	while (i-- > 0)
		*str++ = tmp[i];
	while (size-- > 0)
		*str++ = ' ';
	return str;
}

int vsprintf(char *buf, const char *fmt, va_list args)
{
	int len;
	int i;
	char *str;
	char *s;
	int *ip;

	int flags;		/* 传递给 number() 的格式标志 */
	int field_width;	/* 输出字段宽度 */
	int precision;		/* 整数最小位数；字符串最大字符数 */
	int qualifier;		/* 整数字段的 'h', 'l', 或 'L' */

	for (str = buf; *fmt; ++fmt) {
		if (*fmt != '%') {
			*str++ = *fmt;
			continue;
		}

		/* 处理格式标志 */
		flags = 0;
	repeat:
		++fmt;		/* 跳过第一个 '%' */
		switch (*fmt) {
		case '-': flags |= LEFT; goto repeat;
		case '+': flags |= PLUS; goto repeat;
		case ' ': flags |= SPACE; goto repeat;
		case '#': flags |= SPECIAL; goto repeat;
		case '0': flags |= ZEROPAD; goto repeat;
		}

		/* 获取字段宽度 */
		field_width = -1;
		if (is_digit(*fmt))
			field_width = skip_atoi(&fmt);
		else if (*fmt == '*') {
			/* 字段宽度来自下一个参数 */
			field_width = va_arg(args, int);
			if (field_width < 0) {
				field_width = -field_width;
				flags |= LEFT;
			}
		}

		/* 获取精度 */
		precision = -1;
		if (*fmt == '.') {
			++fmt;
			if (is_digit(*fmt))
				precision = skip_atoi(&fmt);
			else if (*fmt == '*') {
				/* 精度来自下一个参数 */
				precision = va_arg(args, int);
			}
			if (precision < 0)
				precision = 0;
		}

		/* 获取转换限定符 */
		qualifier = -1;
		if (*fmt == 'h' || *fmt == 'l' || *fmt == 'L') {
			qualifier = *fmt;
			++fmt;
		}

		switch (*fmt) {
		case 'c':
			if (!(flags & LEFT))
				while (--field_width > 0)
					*str++ = ' ';
			*str++ = (unsigned char) va_arg(args, int);
			while (--field_width > 0)
				*str++ = ' ';
			break;

		case 's':
			s = va_arg(args, char *);
			len = strlen(s);
			if (precision < 0)
				precision = len;
			else if (len > precision)
				len = precision;

			if (!(flags & LEFT))
				while (len < field_width--)
					*str++ = ' ';
			for (i = 0; i < len; ++i)
				*str++ = *s++;
			while (len < field_width--)
				*str++ = ' ';
			break;

		case 'o':
			str = number(str, va_arg(args, unsigned long), 8,
				field_width, precision, flags);
			break;

		case 'p':
			if (field_width == -1) {
				field_width = 8;
				flags |= ZEROPAD;
			}
			str = number(str,
				(unsigned long) va_arg(args, void *), 16,
				field_width, precision, flags);
			break;

		case 'x':
			flags |= SMALL;
		case 'X':
			str = number(str, va_arg(args, unsigned long), 16,
				field_width, precision, flags);
			break;

		case 'd':
		case 'i':
			flags |= SIGN;
		case 'u':
			str = number(str, va_arg(args, unsigned long), 10,
				field_width, precision, flags);
			break;

		case 'n':
			ip = va_arg(args, int *);
			*ip = (str - buf);
			break;

		default:
			if (*fmt != '%')
				*str++ = '%';
			if (*fmt)
				*str++ = *fmt;
			else
				--fmt;
			break;
		}
	}
	*str = '\0';
	return str - buf;
}
