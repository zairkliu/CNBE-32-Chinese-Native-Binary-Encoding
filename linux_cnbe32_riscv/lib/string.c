/* 转码状态: RISC-V CNBE-32 已转码
 * 原始文件: Linux 0.01 lib/string.c
 * 变更说明:
 *   - 原始 string.c 包含 x86 汇编优化的 string.h
 *   - 已替换为所有字符串函数的 C 语言实现
 *   - 所有函数保持原始语义，兼容 RISC-V
 *   - 不使用 x86 特有的段寄存器假设 (ds=es=data space)
 * CNBE-32: 字符串操作支持 UTF-8 安全（按字节操作）
 *          集成点: 可使用 cnhe_cmp 进行中文语义比较
 */

#ifndef __GNUC__
#error 需要 GCC 编译器
#endif

#define __LIBRARY__
#include <stddef.h>

/* 外部链接的 strtok 状态变量 */
char * ___strtok = NULL;

char * strcpy(char * dest, const char *src)
{
	char *tmp = dest;
	while ((*dest++ = *src++) != '\0')
		;
	return tmp;
}

char * strncpy(char * dest, const char *src, int count)
{
	char *tmp = dest;
	while (count && (*dest++ = *src++) != '\0')
		count--;
	while (count--)
		*dest++ = '\0';
	return tmp;
}

char * strcat(char * dest, const char * src)
{
	char *tmp = dest;
	while (*dest)
		dest++;
	while ((*dest++ = *src++) != '\0')
		;
	return tmp;
}

char * strncat(char * dest, const char * src, int count)
{
	char *tmp = dest;
	while (*dest)
		dest++;
	while (count-- && (*dest++ = *src++) != '\0')
		;
	*dest = '\0';
	return tmp;
}

int strcmp(const char * cs, const char * ct)
{
	while (*cs == *ct) {
		if (*cs == '\0')
			return 0;
		cs++;
		ct++;
	}
	return (*cs < *ct) ? -1 : 1;
}

int strncmp(const char * cs, const char * ct, int count)
{
	while (count--) {
		if (*cs != *ct)
			return (*cs < *ct) ? -1 : 1;
		if (*cs == '\0')
			return 0;
		cs++;
		ct++;
	}
	return 0;
}

char * strchr(const char * s, char c)
{
	while (*s != c) {
		if (*s == '\0')
			return NULL;
		s++;
	}
	return (char *)s;
}

char * strrchr(const char * s, char c)
{
	const char *res = NULL;
	do {
		if (*s == c)
			res = s;
	} while (*s++);
	return (char *)res;
}

int strspn(const char * cs, const char * ct)
{
	const char *p;
	int count = 0;
	while (*cs) {
		for (p = ct; *p; p++) {
			if (*cs == *p)
				break;
		}
		if (*p == '\0')
			break;
		cs++;
		count++;
	}
	return count;
}

int strcspn(const char * cs, const char * ct)
{
	const char *p;
	int count = 0;
	while (*cs) {
		for (p = ct; *p; p++) {
			if (*cs == *p)
				return count;
		}
		count++;
		cs++;
	}
	return count;
}

char * strpbrk(const char * cs, const char * ct)
{
	const char *p;
	while (*cs) {
		for (p = ct; *p; p++) {
			if (*cs == *p)
				return (char *)cs;
		}
		cs++;
	}
	return NULL;
}

char * strstr(const char * cs, const char * ct)
{
	const char *p, *q;
	if (!*ct)
		return (char *)cs;
	while (*cs) {
		p = cs;
		q = ct;
		while (*p && *q && (*p == *q)) {
			p++;
			q++;
		}
		if (!*q)
			return (char *)cs;
		cs++;
	}
	return NULL;
}

int strlen(const char * s)
{
	int len = 0;
	while (*s++)
		len++;
	return len;
}

char * strtok(char * s, const char * ct)
{
	char *token;
	if (!s)
		s = ___strtok;
	if (!s)
		return NULL;
	/* 跳过前导分隔符 */
	while (*s) {
		const char *q = ct;
		while (*q) {
			if (*s == *q)
				break;
			q++;
		}
		if (!*q)
			break;
		s++;
	}
	if (!*s)
		return NULL;
	token = s;
	/* 查找下一个分隔符 */
	while (*s) {
		const char *q = ct;
		while (*q) {
			if (*s == *q) {
				*s = '\0';
				___strtok = s + 1;
				return token;
			}
			q++;
		}
		s++;
	}
	___strtok = NULL;
	return token;
}

void * memcpy(void * dest, const void * src, int n)
{
	char *d = dest;
	const char *s = src;
	while (n--)
		*d++ = *s++;
	return dest;
}

void * memmove(void * dest, const void * src, int n)
{
	char *d = dest;
	const char *s = src;
	if (d < s) {
		while (n--)
			*d++ = *s++;
	} else {
		d += n;
		s += n;
		while (n--)
			*--d = *--s;
	}
	return dest;
}

int memcmp(const void * cs, const void * ct, int count)
{
	const char *s1 = cs;
	const char *s2 = ct;
	while (count--) {
		if (*s1 != *s2)
			return (*s1 < *s2) ? -1 : 1;
		s1++;
		s2++;
	}
	return 0;
}

void * memchr(const void * cs, char c, int count)
{
	const char *p = cs;
	while (count--) {
		if (*p == c)
			return (void *)p;
		p++;
	}
	return NULL;
}

void * memset(void * s, char c, int count)
{
	char *p = s;
	while (count--)
		*p++ = c;
	return s;
}
