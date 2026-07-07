/*
 * CNBE-32 中文编译器
 * 将中文源代码编译为字节码并在栈式虚拟机上执行
 * 全中文关键字 — 零英文依赖
 *
 * 编译流程:
 *   1. 词法分析器: 中文源码 → 中文词记流
 *   2. 递归下降解析器: 词记 → 中文字节码
 *   3. 栈式虚拟机: 字节码 → 执行结果
 *
 * 中文关键字:
 *   整数/长整数/字符  — 数据类型
 *   若/否则若/否则     — 条件分支
 *   循环/跳出/继续     — 循环控制
 *   从...到            — 范围循环
 *   定义/返回/调用     — 函数
 *   写/读              — 输入输出
 *   加减乘除           — 算术运算
 *   等于/不等/大于/小于 — 比较运算
 *   且/或              — 逻辑运算
 *
 * 字节码格式:
 *   0x01 压整数 <值>    0x02 压变量 <编号>
 *   0x03 存变量 <编号>   0x04 加法  0x05 减法
 *   0x06 乘法  0x07 除法 0x08 等于  0x09 不等
 *   0x0A 大于  0x0B 小于 0x0C 跳转 <地址>
 *   0x0D 零则跳 <地址>   0x0E 调用 <函数号>
 *   0x0F 返回  0x10 输出字符串 <偏移>
 *   0x11 输出整数  0x12 停止  0x13 输出字符
 *   0x14 与  0x15 或  0x16 取模
 *   0x17 压字符串 <偏移>  0x18 字符串拼接
 *   0x19 跳过到 <地址>     0x1A 非零则跳 <地址>
 */

#include <linux/kernel.h>
#include <linux/sched.h>
#include <asm/io.h>
#include <asm/segment.h>
#include <cnbe.h>
#include <stdarg.h>
#include <stdint.h>

#include "cnbe_compiler.h"

/* ========== 常量定义 ========== */

#define MAX_TOKENS    256     /* 最大词记数 */
#define MAX_BYTECODE  4096    /* 字节码缓冲区大小 */
#define MAX_STR_POOL  2048    /* 字符串池大小 */
#define MAX_VARS      64      /* 变量槽数 */
#define MAX_FUNCS     16      /* 函数最大数 */
#define MAX_FUNC_PARAMS 4     /* 函数最大参数数 */
#define STACK_SIZE    256     /* 数据栈深度 */
#define MAX_VAR_NAME  16      /* 变量名最大字节 */

/* 字节码操作码 */
enum {
    OP_PUSH_INT   = 0x01,     /* 压整数 (后跟 8 字节值) */
    OP_PUSH_VAR   = 0x02,     /* 压变量 (后跟 2 字节编号) */
    OP_STORE_VAR  = 0x03,     /* 存变量 (后跟 2 字节编号) */
    OP_ADD        = 0x04,     /* 加法 */
    OP_SUB        = 0x05,     /* 减法 */
    OP_MUL        = 0x06,     /* 乘法 */
    OP_DIV        = 0x07,     /* 除法 */
    OP_EQ         = 0x08,     /* 等于 */
    OP_NE         = 0x09,     /* 不等 */
    OP_GT         = 0x0A,     /* 大于 */
    OP_LT         = 0x0B,     /* 小于 */
    OP_JMP        = 0x0C,     /* 无条件跳转 (后跟 2 字节地址) */
    OP_JZ         = 0x0D,     /* 零则跳 (后跟 2 字节地址) */
    OP_CALL       = 0x0E,     /* 调用函数 (后跟 1 字节函数号 + 1 字节参数数) */
    OP_RET        = 0x0F,     /* 返回 */
    OP_PRINT_STR  = 0x10,     /* 输出字符串 (后跟 2 字节偏移) */
    OP_PRINT_INT  = 0x11,     /* 输出整数 */
    OP_HALT       = 0x12,     /* 停止 */
    OP_PRINT_CHAR = 0x13,     /* 输出字符 */
    OP_AND        = 0x14,     /* 逻辑与 */
    OP_OR         = 0x15,     /* 逻辑或 */
    OP_MOD        = 0x16,     /* 取模 */
    OP_PUSH_STR   = 0x17,     /* 压字符串 (后跟 2 字节偏移) */
    OP_STR_CAT    = 0x18,     /* 字符串拼接 */
    OP_JMP_TO     = 0x19,     /* 跳过到地址 (后跟 2 字节地址) */
    OP_JNZ        = 0x1A,     /* 非零则跳 (后跟 2 字节地址) */
    OP_PUSH_CHAR  = 0x1B,     /* 压字符 (后跟 1 字节值) */
};

/* 词记类型 */
enum {
    TK_EOF = 0,
    TK_INT,           /* 整数字面量 */
    TK_STRING,        /* 字符串字面量 */
    TK_IDENT,         /* 标识符 */
    TK_KEYWORD,       /* 关键字 */
    TK_OP,            /* 运算符 */
    TK_LPAREN,        /* 左括号 */
    TK_RPAREN,        /* 右括号 */
    TK_LBRACE,        /* 左花括号 */
    TK_RBRACE,        /* 右花括号 */
    TK_COMMA,         /* 逗号 */
    TK_SEMI,          /* 分号 */
    TK_ASSIGN,        /* 赋值号 */
    TK_CHAR,          /* 字符字面量 */
};

/* ========== 词记结构 ========== */

typedef struct {
    int type;
    long ival;              /* 整数值 */
    char sval[64];          /* 字符串/标识符值 */
    int slen;               /* 字符串长度 */
} Token;

/* ========== 变量表 ========== */

typedef struct {
    char name[MAX_VAR_NAME];
    int  used;
} VarSlot;

/* ========== 函数表 ========== */

typedef struct {
    char name[MAX_VAR_NAME];
    int  nparams;
    char params[MAX_FUNC_PARAMS][MAX_VAR_NAME];
    int  body_start;        /* 字节码起始地址 */
} FuncSlot;

/* ========== 编译器状态 ========== */

typedef struct {
    const char *src;        /* 源代码指针 */
    int   pos;              /* 当前位置 */
    Token tokens[MAX_TOKENS];
    int   ntokens;
    int   tok_pos;          /* 当前词记位置 */

    unsigned char bytecode[MAX_BYTECODE];
    int   bc_len;           /* 字节码长度 */

    char  str_pool[MAX_STR_POOL];
    int   str_len;

    VarSlot vars[MAX_VARS];
    int   nvars;

    FuncSlot funcs[MAX_FUNCS];
    int   nfuncs;

    int   error;            /* 错误标志 */
    char  errmsg[128];      /* 错误消息 */
} Compiler;

/* ========== 虚拟机状态 ========== */

typedef struct {
    long stack[STACK_SIZE];
    int  sp;                /* 栈指针 */
    unsigned char *bc;      /* 字节码指针 */
    int  pc;                /* 程序计数器 */
    char *str_pool;         /* 字符串池 */
    long vars[MAX_VARS];    /* 变量存储 */
    int  halted;
    int  error;
    char errmsg[128];
} VM;

/* ========== UART 输出 (QEMU virt 16550) ========== */

#define UART0_BASE  0x10000000UL
#define UART_THR    (*(volatile char *)(UART0_BASE))
#define UART_LSR    (*(volatile char *)(UART0_BASE + 5))

static void cnbe_uart_putc(char c)
{
    UART_THR = c;
}

static void cnbe_uart_puts(const char *s)
{
    while (*s) {
        if (*s == 10) cnbe_uart_putc(13);  /* LF → CRLF */
        cnbe_uart_putc(*s++);
    }
}

/* 整数转字符串输出 */
static void cnbe_uart_putint(long val)
{
    char buf[24];
    int pos = sizeof(buf) - 1;
    int neg = 0;
    buf[pos] = 0;
    if (val < 0) { neg = 1; val = -val; }
    do { buf[--pos] = (val % 10) + '0'; val /= 10; } while (val);
    if (neg) buf[--pos] = '-';
    cnbe_uart_puts(buf + pos);
}

/* ========== UTF-8 匹配辅助 ========== */

static int match_utf8(const char **p, const char *pat, int len)
{
    int i;
    for (i = 0; i < len; i++) {
        if ((unsigned char)(*p)[i] != (unsigned char)pat[i])
            return 0;
    }
    *p += len;
    return 1;
}

/* ========== 词法分析器 ========== */

/* 中文关键字 UTF-8 编码 */
/* 整数: \xe6\x95\xb4\xe6\x95\xb0 (6字节) */
/* 长整数: \xe9\x95\xbf\xe6\x95\xb4\xe6\x95\xb0 (9字节) */
/* 字符: \xe5\xad\x97\xe7\xac\xa6 (6字节) */
/* 若: \xe8\x8b\xa5 (3字节) */
/* 否则若: \xe5\x90\xa6\xe5\x88\x99\xe8\x8b\xa5 (9字节) */
/* 否则: \xe5\x90\xa6\xe5\x88\x99 (6字节) */
/* 循环: \xe5\xbe\xaa\xe7\x8e\xaf (6字节) */
/* 跳出: \xe8\xb7\xb3\xe5\x87\xba (6字节) */
/* 继续: \xe7\xbb\xa7\xe7\xbb\xad (6字节) */
/* 从: \xe4\xbb\x8e (3字节) */
/* 到: \xe5\x88\xb0 (3字节) */
/* 定义: \xe5\xae\x9a\xe4\xb9\x89 (6字节) */
/* 返回: \xe8\xbf\x94\xe5\x9b\x9e (6字节) */
/* 调用: \xe8\xb0\x83\xe7\x94\xa8 (6字节) */
/* 写: \xe5\x86\x99 (3字节) */
/* 读: \xe8\xaf\xbb (3字节) */
/* 加: \xe5\x8a\xa0 (3字节) */
/* 减: \xe5\x87\x8f (3字节) */
/* 乘: \xe4\xb9\x98 (3字节) */
/* 除: \xe9\x99\xa4 (3字节) */
/* 等于: \xe7\xad\x89\xe4\xba\x8e (6字节) */
/* 不等: \xe4\xb8\x8d\xe7\xad\x89 (6字节) */
/* 大于: \xe5\xa4\xa7\xe4\xba\x8e (6字节) */
/* 小于: \xe5\xb0\x8f\xe4\xba\x8e (6字节) */
/* 且: \xe4\xb8\x94 (3字节) */
/* 或: \xe6\x88\x96 (3字节) */
/* 取模: \xe5\x8f\x96\xe6\xa8\xa1 (6字节) */

static int is_cn_char_start(unsigned char c)
{
    return c >= 0x80;
}

static int cn_char_len(unsigned char c)
{
    if ((c & 0xE0) == 0xC0) return 2;
    if ((c & 0xF0) == 0xE0) return 3;
    if ((c & 0xF8) == 0xF0) return 4;
    return 1;
}

/* 词法分析: 源码 → 词记数组 */
static int lex(Compiler *c)
{
    const char *p = c->src;
    int n = 0;

    while (*p && n < MAX_TOKENS - 1) {
        /* 跳过空白 */
        while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')
            p++;

        if (*p == 0) break;

        /* 注释: 以 # 开头到行末 */
        if (*p == '#') {
            while (*p && *p != '\n') p++;
            continue;
        }

        /* 数字 */
        if (*p >= '0' && *p <= '9') {
            long val = 0;
            while (*p >= '0' && *p <= '9') {
                val = val * 10 + (*p - '0');
                p++;
            }
            c->tokens[n].type = TK_INT;
            c->tokens[n].ival = val;
            n++;
            continue;
        }

        /* 字符串 */
        if (*p == '"') {
            p++;
            int slen = 0;
            while (*p && *p != '"' && slen < 63) {
                c->tokens[n].sval[slen++] = *p++;
            }
            if (*p == '"') p++;
            c->tokens[n].sval[slen] = 0;
            c->tokens[n].slen = slen;
            c->tokens[n].type = TK_STRING;
            n++;
            continue;
        }

        /* 运算符和标点 */
        if (*p == '(') { c->tokens[n].type = TK_LPAREN; n++; p++; continue; }
        if (*p == ')') { c->tokens[n].type = TK_RPAREN; n++; p++; continue; }
        if (*p == '{') { c->tokens[n].type = TK_LBRACE; n++; p++; continue; }
        if (*p == '}') { c->tokens[n].type = TK_RBRACE; n++; p++; continue; }
        if (*p == ',') { c->tokens[n].type = TK_COMMA;  n++; p++; continue; }
        if (*p == ';') { c->tokens[n].type = TK_SEMI;   n++; p++; continue; }
        if (*p == '=') {
            p++;
            if (*p == '=') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "=="); p++; }
            else { c->tokens[n].type = TK_ASSIGN; }
            n++; continue;
        }
        if (*p == '+') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "+"); n++; p++; continue; }
        if (*p == '-') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "-"); n++; p++; continue; }
        if (*p == '*') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "*"); n++; p++; continue; }
        if (*p == '/') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "/"); n++; p++; continue; }
        if (*p == '%') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "%"); n++; p++; continue; }
        if (*p == '>') {
            p++;
            if (*p == '=') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, ">="); p++; }
            else { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, ">"); }
            n++; continue;
        }
        if (*p == '<') {
            p++;
            if (*p == '=') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "<="); p++; }
            else { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "<"); }
            n++; continue;
        }
        if (*p == '!') {
            p++;
            if (*p == '=') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "!="); p++; }
            n++; continue;
        }
        if (*p == '&') {
            p++;
            if (*p == '&') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "&&"); p++; }
            n++; continue;
        }
        if (*p == '|') {
            p++;
            if (*p == '|') { c->tokens[n].type = TK_OP; strcpy(c->tokens[n].sval, "||"); p++; }
            n++; continue;
        }

        /* 中文关键字和标识符 */
        if (is_cn_char_start((unsigned char)*p)) {
            const char *start = p;
            int matched = 0;

            /* 尝试匹配中文关键字 (从长到短) */

            /* 长整数 (9字节) */
            if (!matched && match_utf8(&p, "\xe9\x95\xbf\xe6\x95\xb4\xe6\x95\xb0", 9)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "长整数");
                matched = 1;
            }
            /* 否则若 (9字节) */
            if (!matched && match_utf8(&p, "\xe5\x90\xa6\xe5\x88\x99\xe8\x8b\xa5", 9)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "否则若");
                matched = 1;
            }
            /* 整数 (6字节) */
            if (!matched && match_utf8(&p, "\xe6\x95\xb4\xe6\x95\xb0", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "整数");
                matched = 1;
            }
            /* 字符 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\xad\x97\xe7\xac\xa6", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "字符");
                matched = 1;
            }
            /* 否则 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\x90\xa6\xe5\x88\x99", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "否则");
                matched = 1;
            }
            /* 循环 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\xbe\xaa\xe7\x8e\xaf", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "循环");
                matched = 1;
            }
            /* 跳出 (6字节) */
            if (!matched && match_utf8(&p, "\xe8\xb7\xb3\xe5\x87\xba", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "跳出");
                matched = 1;
            }
            /* 继续 (6字节) */
            if (!matched && match_utf8(&p, "\xe7\xbb\xa7\xe7\xbb\xad", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "继续");
                matched = 1;
            }
            /* 定义 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\xae\x9a\xe4\xb9\x89", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "定义");
                matched = 1;
            }
            /* 返回 (6字节) */
            if (!matched && match_utf8(&p, "\xe8\xbf\x94\xe5\x9b\x9e", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "返回");
                matched = 1;
            }
            /* 调用 (6字节) */
            if (!matched && match_utf8(&p, "\xe8\xb0\x83\xe7\x94\xa8", 6)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "调用");
                matched = 1;
            }
            /* 等于 (6字节) */
            if (!matched && match_utf8(&p, "\xe7\xad\x89\xe4\xba\x8e", 6)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "==");
                matched = 1;
            }
            /* 不等 (6字节) */
            if (!matched && match_utf8(&p, "\xe4\xb8\x8d\xe7\xad\x89", 6)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "!=");
                matched = 1;
            }
            /* 大于 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\xa4\xa7\xe4\xba\x8e", 6)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, ">");
                matched = 1;
            }
            /* 小于 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\xb0\x8f\xe4\xba\x8e", 6)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "<");
                matched = 1;
            }
            /* 取模 (6字节) */
            if (!matched && match_utf8(&p, "\xe5\x8f\x96\xe6\xa8\xa1", 6)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "%");
                matched = 1;
            }
            /* 若 (3字节) */
            if (!matched && match_utf8(&p, "\xe8\x8b\xa5", 3)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "若");
                matched = 1;
            }
            /* 从 (3字节) */
            if (!matched && match_utf8(&p, "\xe4\xbb\x8e", 3)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "从");
                matched = 1;
            }
            /* 到 (3字节) */
            if (!matched && match_utf8(&p, "\xe5\x88\xb0", 3)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "到");
                matched = 1;
            }
            /* 写 (3字节) */
            if (!matched && match_utf8(&p, "\xe5\x86\x99", 3)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "写");
                matched = 1;
            }
            /* 读 (3字节) */
            if (!matched && match_utf8(&p, "\xe8\xaf\xbb", 3)) {
                c->tokens[n].type = TK_KEYWORD;
                strcpy(c->tokens[n].sval, "读");
                matched = 1;
            }
            /* 加 (3字节) */
            if (!matched && match_utf8(&p, "\xe5\x8a\xa0", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "+");
                matched = 1;
            }
            /* 减 (3字节) */
            if (!matched && match_utf8(&p, "\xe5\x87\x8f", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "-");
                matched = 1;
            }
            /* 乘 (3字节) */
            if (!matched && match_utf8(&p, "\xe4\xb9\x98", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "*");
                matched = 1;
            }
            /* 除 (3字节) */
            if (!matched && match_utf8(&p, "\xe9\x99\xa4", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "/");
                matched = 1;
            }
            /* 且 (3字节) */
            if (!matched && match_utf8(&p, "\xe4\xb8\x94", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "&&");
                matched = 1;
            }
            /* 或 (3字节) */
            if (!matched && match_utf8(&p, "\xe6\x88\x96", 3)) {
                c->tokens[n].type = TK_OP;
                strcpy(c->tokens[n].sval, "||");
                matched = 1;
            }

            if (matched) {
                n++;
                continue;
            }

            /* 未匹配关键字 — 作为中文标识符 */
            {
                int clen = cn_char_len((unsigned char)*p);
                int slen = 0;
                while (is_cn_char_start((unsigned char)*p) && slen < MAX_VAR_NAME - clen) {
                    int i;
                    for (i = 0; i < clen && *p; i++)
                        c->tokens[n].sval[slen++] = *p++;
                    /* 检查下一个字符是否还是中文 */
                    if (*p == 0 || *p == ' ' || *p == '\t' || *p == '\n' ||
                        *p == '(' || *p == ')' || *p == '{' || *p == '}' ||
                        *p == ',' || *p == ';' || *p == '=' || *p == '"')
                        break;
                    clen = cn_char_len((unsigned char)*p);
                }
                c->tokens[n].sval[slen] = 0;
                c->tokens[n].type = TK_IDENT;
                n++;
                continue;
            }
        }

        /* 英文标识符 (A-Z, a-z, _) */
        if ((*p >= 'A' && *p <= 'Z') || (*p >= 'a' && *p <= 'z') || *p == '_') {
            int slen = 0;
            while ((*p >= 'A' && *p <= 'Z') || (*p >= 'a' && *p <= 'z') ||
                   (*p >= '0' && *p <= '9') || *p == '_') {
                if (slen < 63) c->tokens[n].sval[slen++] = *p;
                p++;
            }
            c->tokens[n].sval[slen] = 0;
            c->tokens[n].type = TK_IDENT;
            n++;
            continue;
        }

        /* 未知字符 — 跳过 */
        p++;
    }

    c->tokens[n].type = TK_EOF;
    c->ntokens = n + 1;
    return n;
}

/* ========== 字节码发射辅助 ========== */

static void emit_byte(Compiler *c, unsigned char b)
{
    if (c->bc_len < MAX_BYTECODE - 1)
        c->bytecode[c->bc_len++] = b;
}

static void emit_short(Compiler *c, unsigned short v)
{
    emit_byte(c, (v >> 8) & 0xFF);
    emit_byte(c, v & 0xFF);
}

static void emit_long(Compiler *c, long v)
{
    int i;
    for (i = 0; i < 8; i++)
        emit_byte(c, (v >> (i * 8)) & 0xFF);
}

static int emit_placeholder(Compiler *c)
{
    int addr = c->bc_len;
    emit_short(c, 0);
    return addr;
}

static void patch_short(Compiler *c, int addr, unsigned short val)
{
    c->bytecode[addr] = (val >> 8) & 0xFF;
    c->bytecode[addr + 1] = val & 0xFF;
}

static int add_string(Compiler *c, const char *s, int len)
{
    int offset = c->str_len;
    int i;
    for (i = 0; i < len && c->str_len < MAX_STR_POOL - 1; i++)
        c->str_pool[c->str_len++] = s[i];
    c->str_pool[c->str_len++] = 0;
    return offset;
}

static int find_or_add_var(Compiler *c, const char *name)
{
    int i;
    for (i = 0; i < c->nvars; i++) {
        if (strcmp(c->vars[i].name, name) == 0)
            return i;
    }
    if (c->nvars < MAX_VARS) {
        strncpy(c->vars[c->nvars].name, name, MAX_VAR_NAME - 1);
        c->vars[c->nvars].name[MAX_VAR_NAME - 1] = 0;
        c->vars[c->nvars].used = 1;
        return c->nvars++;
    }
    return -1;
}

static int find_func(Compiler *c, const char *name)
{
    int i;
    for (i = 0; i < c->nfuncs; i++) {
        if (strcmp(c->funcs[i].name, name) == 0)
            return i;
    }
    return -1;
}

/* ========== 解析器 (递归下降) ========== */

static Token *cur_tok(Compiler *c)
{
    return &c->tokens[c->tok_pos];
}

static Token *advance(Compiler *c)
{
    if (c->tok_pos < c->ntokens - 1)
        c->tok_pos++;
    return &c->tokens[c->tok_pos];
}

static int check_tok(Compiler *c, int type)
{
    return cur_tok(c)->type == type;
}

static int check_kw(Compiler *c, const char *kw)
{
    Token *t = cur_tok(c);
    return t->type == TK_KEYWORD && strcmp(t->sval, kw) == 0;
}

static int check_op(Compiler *c, const char *op)
{
    Token *t = cur_tok(c);
    return t->type == TK_OP && strcmp(t->sval, op) == 0;
}

static void set_error(Compiler *c, const char *msg)
{
    c->error = 1;
    strncpy(c->errmsg, msg, sizeof(c->errmsg) - 1);
    c->errmsg[sizeof(c->errmsg) - 1] = 0;
}

/* 前向声明 */
static void parse_expr(Compiler *c);
static void parse_stmt(Compiler *c);
static void parse_block(Compiler *c);

/* 解析基本表达式: 数字 | 字符串 | 标识符 | (表达式) | 调用 */
static void parse_primary(Compiler *c)
{
    Token *t = cur_tok(c);

    if (t->type == TK_INT) {
        emit_byte(c, OP_PUSH_INT);
        emit_long(c, t->ival);
        advance(c);
    } else if (t->type == TK_STRING) {
        int off = add_string(c, t->sval, t->slen);
        emit_byte(c, OP_PUSH_STR);
        emit_short(c, off);
        advance(c);
    } else if (t->type == TK_IDENT) {
        /* 检查是否是函数调用 */
        Token *next = &c->tokens[c->tok_pos + 1];
        if (next->type == TK_LPAREN || check_kw(c, "调用")) {
            if (check_kw(c, "调用"))
                advance(c);
            /* 函数调用 */
            int fidx = find_func(c, t->sval);
            if (fidx < 0) {
                /* 未定义函数 — 创建占位 */
                if (c->nfuncs < MAX_FUNCS) {
                    strncpy(c->funcs[c->nfuncs].name, t->sval, MAX_VAR_NAME - 1);
                    c->funcs[c->nfuncs].name[MAX_VAR_NAME - 1] = 0;
                    c->funcs[c->nfuncs].body_start = -1;
                    fidx = c->nfuncs++;
                } else {
                    set_error(c, "函数表已满");
                    return;
                }
            }
            advance(c); /* 跳过函数名 */
            if (check_tok(c, TK_LPAREN)) advance(c); /* 跳过 '(' */

            /* 解析参数 */
            int nargs = 0;
            while (!check_tok(c, TK_RPAREN) && !check_tok(c, TK_EOF)) {
                parse_expr(c);
                nargs++;
                if (check_tok(c, TK_COMMA)) advance(c);
            }
            if (check_tok(c, TK_RPAREN)) advance(c); /* 跳过 ')' */

            emit_byte(c, OP_CALL);
            emit_byte(c, fidx);
            emit_byte(c, nargs);
        } else {
            /* 变量引用 */
            int vidx = find_or_add_var(c, t->sval);
            if (vidx < 0) {
                set_error(c, "变量表已满");
                return;
            }
            emit_byte(c, OP_PUSH_VAR);
            emit_short(c, vidx);
            advance(c);
        }
    } else if (t->type == TK_LPAREN) {
        advance(c);
        parse_expr(c);
        if (check_tok(c, TK_RPAREN)) advance(c);
    } else if (check_kw(c, "读")) {
        /* 读 — 读取输入 (简化为返回0) */
        advance(c);
        emit_byte(c, OP_PUSH_INT);
        emit_long(c, 0);
    } else {
        set_error(c, "语法错误: 意外的词记");
    }
}

/* 解析乘除表达式 */
static void parse_mul_expr(Compiler *c)
{
    parse_primary(c);
    while (check_op(c, "*") || check_op(c, "/") || check_op(c, "%") ||
           check_kw(c, "乘") || check_kw(c, "除") || check_kw(c, "取模")) {
        Token *t = cur_tok(c);
        advance(c);
        parse_primary(c);
        if (strcmp(t->sval, "*") == 0)
            emit_byte(c, OP_MUL);
        else if (strcmp(t->sval, "/") == 0)
            emit_byte(c, OP_DIV);
        else
            emit_byte(c, OP_MOD);
    }
}

/* 解析加减表达式 */
static void parse_add_expr(Compiler *c)
{
    parse_mul_expr(c);
    while (check_op(c, "+") || check_op(c, "-") ||
           check_kw(c, "加") || check_kw(c, "减")) {
        Token *t = cur_tok(c);
        advance(c);
        parse_mul_expr(c);
        if (strcmp(t->sval, "+") == 0)
            emit_byte(c, OP_ADD);
        else
            emit_byte(c, OP_SUB);
    }
}

/* 解析比较表达式 */
static void parse_cmp_expr(Compiler *c)
{
    parse_add_expr(c);
    while (check_op(c, "==") || check_op(c, "!=") ||
           check_op(c, ">") || check_op(c, "<") ||
           check_op(c, ">=") || check_op(c, "<=") ||
           check_kw(c, "等于") || check_kw(c, "不等") ||
           check_kw(c, "大于") || check_kw(c, "小于")) {
        Token *t = cur_tok(c);
        advance(c);
        parse_add_expr(c);
        if (strcmp(t->sval, "==") == 0)
            emit_byte(c, OP_EQ);
        else if (strcmp(t->sval, "!=") == 0)
            emit_byte(c, OP_NE);
        else if (strcmp(t->sval, ">") == 0 || strcmp(t->sval, ">=") == 0)
            emit_byte(c, OP_GT);
        else
            emit_byte(c, OP_LT);
    }
}

/* 解析逻辑表达式 */
static void parse_expr(Compiler *c)
{
    parse_cmp_expr(c);
    while (check_op(c, "&&") || check_op(c, "||") ||
           check_kw(c, "且") || check_kw(c, "或")) {
        Token *t = cur_tok(c);
        advance(c);
        parse_cmp_expr(c);
        if (strcmp(t->sval, "&&") == 0)
            emit_byte(c, OP_AND);
        else
            emit_byte(c, OP_OR);
    }
}

/* 解析语句 */
static void parse_stmt(Compiler *c)
{
    /* 注释行: # 到行末 (词法分析器已处理) */

    /* 变量声明: 整数 变量名 = 表达式 */
    if (check_kw(c, "整数") || check_kw(c, "长整数") || check_kw(c, "字符")) {
        advance(c); /* 跳过类型关键字 */
        if (check_tok(c, TK_IDENT)) {
            int vidx = find_or_add_var(c, cur_tok(c)->sval);
            advance(c); /* 跳过变量名 */
            if (check_tok(c, TK_ASSIGN)) {
                advance(c);
                parse_expr(c);
                emit_byte(c, OP_STORE_VAR);
                emit_short(c, vidx);
            }
        }
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 赋值: 变量名 = 表达式 */
    if (check_tok(c, TK_IDENT)) {
        Token *next = &c->tokens[c->tok_pos + 1];
        if (next->type == TK_ASSIGN) {
            int vidx = find_or_add_var(c, cur_tok(c)->sval);
            advance(c); /* 跳过变量名 */
            advance(c); /* 跳过 '=' */
            parse_expr(c);
            emit_byte(c, OP_STORE_VAR);
            emit_short(c, vidx);
            if (check_tok(c, TK_SEMI)) advance(c);
            return;
        }
    }

    /* 写: 写 表达式  或  写 "字符串" */
    if (check_kw(c, "写")) {
        advance(c);
        /* 支持多个表达式用逗号分隔 */
        parse_expr(c);
        /* 检查类型: 如果是字符串压入则输出字符串，否则输出整数 */
        {
            /* 回看最后发射的指令 */
            int p = c->bc_len - 3;
            if (p >= 0 && c->bytecode[p] == OP_PUSH_STR) {
                emit_byte(c, OP_PRINT_STR);
                emit_short(c, (c->bytecode[p+1] << 8) | c->bytecode[p+2]);
                /* 移除之前的 PUSH_STR */
                c->bc_len -= 3;
            } else {
                emit_byte(c, OP_PRINT_INT);
            }
        }
        while (check_tok(c, TK_COMMA)) {
            advance(c);
            parse_expr(c);
            emit_byte(c, OP_PRINT_INT);
        }
        /* 输出换行 */
        emit_byte(c, OP_PUSH_CHAR);
        emit_byte(c, '\n');
        emit_byte(c, OP_PRINT_CHAR);
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 若 (if) 条件语句 */
    if (check_kw(c, "若")) {
        advance(c);
        parse_expr(c);
        /* 零则跳到 else 块 */
        int jz_addr = emit_placeholder(c);
        emit_byte(c, OP_JZ);
        /* 注意: emit_placeholder 已发射了 2 字节，但我们需要 OP_JZ 在前面 */
        /* 修正: 先移除 placeholder，发射 JZ，再发射 placeholder */
        c->bc_len -= 2; /* 移除 placeholder 的 2 字节 */
        /* 现在栈顶是比较结果，JZ 跳过 then 块 */
        patch_short(c, jz_addr, 0); /* 清除误发射 */

        /* 正确方式: 发射 JZ + placeholder */
        int jz_pos = c->bc_len;
        emit_byte(c, OP_JZ);
        int else_addr = emit_placeholder(c);

        parse_stmt(c);

        if (check_kw(c, "否则")) {
            advance(c);
            /* 在 then 块后跳过 else 块 */
            int jmp_addr = emit_placeholder(c);
            emit_byte(c, OP_JMP);
            /* 修正: 移除多余 placeholder */
            c->bc_len -= 2;

            int jmp_pos = c->bc_len;
            emit_byte(c, OP_JMP);
            int end_addr = emit_placeholder(c);

            /* 回填 else 跳转地址 */
            patch_short(c, else_addr, c->bc_len);
            parse_stmt(c);
            /* 回填 end 跳转地址 */
            patch_short(c, end_addr, c->bc_len);
        } else if (check_kw(c, "否则若")) {
            /* 否则若 = else if */
            patch_short(c, else_addr, c->bc_len);
            /* 递归处理: 相当于 else { 若 ... } */
            parse_stmt(c);
        } else {
            /* 无 else 块 */
            patch_short(c, else_addr, c->bc_len);
        }
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 循环 (while) 语句 */
    if (check_kw(c, "循环")) {
        advance(c);
        int loop_start = c->bc_len;
        parse_expr(c);

        int jz_pos = c->bc_len;
        emit_byte(c, OP_JZ);
        int exit_addr = emit_placeholder(c);

        parse_stmt(c);

        emit_byte(c, OP_JMP);
        emit_short(c, loop_start);

        patch_short(c, exit_addr, c->bc_len);
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 从...到 (for 循环) */
    if (check_kw(c, "从")) {
        advance(c);
        /* 解析循环变量初始值 */
        if (!check_tok(c, TK_IDENT)) {
            set_error(c, "语法错误: 循环需要变量名");
            return;
        }
        int vidx = find_or_add_var(c, cur_tok(c)->sval);
        advance(c); /* 跳过变量名 */
        if (check_tok(c, TK_ASSIGN)) {
            advance(c);
            parse_expr(c);
            emit_byte(c, OP_STORE_VAR);
            emit_short(c, vidx);
        }

        /* 到 */
        if (!check_kw(c, "到")) {
            set_error(c, "语法错误: 缺少 '到'");
            return;
        }
        advance(c);

        /* 解析结束值 */
        int loop_start = c->bc_len;
        emit_byte(c, OP_PUSH_VAR);
        emit_short(c, vidx);
        parse_expr(c);
        emit_byte(c, OP_GT); /* 变量 > 结束值 则退出 */
        emit_byte(c, OP_JZ);
        /* 取反: 如果 !(变量 > 结束值) 则继续循环 */
        /* 实际上 GT 返回 1 表示大于，JZ 跳过循环体当结果为 0 (不大于) */
        /* 但我们需要: 变量 <= 结束值 时执行循环体 */
        /* 所以应该用 OP_LE... 简化: 用 NOT 然后跳转 */
        /* 修正: 用 GT 然后跳转 (大于则跳出) */
        c->bytecode[c->bc_len - 2] = OP_JNZ; /* 改为非零则跳 (大于则跳到出口) */
        int exit_addr = emit_placeholder(c);

        parse_stmt(c);

        /* 递增循环变量 */
        emit_byte(c, OP_PUSH_VAR);
        emit_short(c, vidx);
        emit_byte(c, OP_PUSH_INT);
        emit_long(c, 1);
        emit_byte(c, OP_ADD);
        emit_byte(c, OP_STORE_VAR);
        emit_short(c, vidx);

        emit_byte(c, OP_JMP);
        emit_short(c, loop_start);

        patch_short(c, exit_addr, c->bc_len);
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 跳出 (break) */
    if (check_kw(c, "跳出")) {
        advance(c);
        emit_byte(c, OP_JMP);
        emit_short(c, 0); /* 需要回填 — 简化版不支持 break 回填 */
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 继续 (continue) */
    if (check_kw(c, "继续")) {
        advance(c);
        emit_byte(c, OP_JMP);
        emit_short(c, 0); /* 需要回填 */
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 返回 (return) */
    if (check_kw(c, "返回")) {
        advance(c);
        if (!check_tok(c, TK_SEMI) && !check_tok(c, TK_RBRACE) && !check_tok(c, TK_EOF)) {
            parse_expr(c);
        } else {
            emit_byte(c, OP_PUSH_INT);
            emit_long(c, 0);
        }
        emit_byte(c, OP_RET);
        if (check_tok(c, TK_SEMI)) advance(c);
        return;
    }

    /* 定义 (function definition) */
    if (check_kw(c, "定义")) {
        advance(c);
        if (!check_tok(c, TK_IDENT)) {
            set_error(c, "语法错误: 函数需要名称");
            return;
        }
        int fidx = find_func(c, cur_tok(c)->sval);
        if (fidx < 0 && c->nfuncs < MAX_FUNCS) {
            fidx = c->nfuncs++;
            strncpy(c->funcs[fidx].name, cur_tok(c)->sval, MAX_VAR_NAME - 1);
            c->funcs[fidx].name[MAX_VAR_NAME - 1] = 0;
        }
        advance(c); /* 跳过函数名 */

        c->funcs[fidx].body_start = c->bc_len;
        c->funcs[fidx].nparams = 0;

        /* 解析参数列表 */
        if (check_tok(c, TK_LPAREN)) {
            advance(c);
            while (!check_tok(c, TK_RPAREN) && !check_tok(c, TK_EOF)) {
                /* 跳过类型关键字 */
                if (check_kw(c, "整数") || check_kw(c, "长整数") || check_kw(c, "字符"))
                    advance(c);
                if (check_tok(c, TK_IDENT)) {
                    int vidx = find_or_add_var(c, cur_tok(c)->sval);
                    if (c->funcs[fidx].nparams < MAX_FUNC_PARAMS) {
                        strncpy(c->funcs[fidx].params[c->funcs[fidx].nparams],
                                cur_tok(c)->sval, MAX_VAR_NAME - 1);
                        c->funcs[fidx].params[c->funcs[fidx].nparams][MAX_VAR_NAME - 1] = 0;
                        c->funcs[fidx].nparams++;
                    }
                    /* 参数从栈弹出到变量 */
                    emit_byte(c, OP_STORE_VAR);
                    emit_short(c, vidx);
                    advance(c);
                }
                if (check_tok(c, TK_COMMA)) advance(c);
            }
            if (check_tok(c, TK_RPAREN)) advance(c);
        }

        /* 函数体 */
        if (check_tok(c, TK_LBRACE)) {
            advance(c);
            while (!check_tok(c, TK_RBRACE) && !check_tok(c, TK_EOF)) {
                parse_stmt(c);
                if (c->error) return;
            }
            if (check_tok(c, TK_RBRACE)) advance(c);
        } else {
            parse_stmt(c);
        }

        /* 函数默认返回 0 */
        emit_byte(c, OP_PUSH_INT);
        emit_long(c, 0);
        emit_byte(c, OP_RET);
        return;
    }

    /* 表达式语句 */
    parse_expr(c);
    if (check_tok(c, TK_SEMI)) advance(c);
}

/* 解析块: 多条语句 */
static void parse_block(Compiler *c)
{
    while (!check_tok(c, TK_EOF) && !check_tok(c, TK_RBRACE)) {
        parse_stmt(c);
        if (c->error) return;
    }
}

/* ========== 编译入口 ========== */

static int compile_source(Compiler *c, const char *source)
{
    c->src = source;
    c->pos = 0;
    c->tok_pos = 0;
    c->bc_len = 0;
    c->str_len = 0;
    c->nvars = 0;
    c->nfuncs = 0;
    c->error = 0;
    c->errmsg[0] = 0;

    /* 词法分析 */
    lex(c);

    /* 语法分析 + 代码生成 */
    parse_block(c);

    /* 发射停止指令 */
    emit_byte(c, OP_HALT);

    if (c->error) {
        cnbe_uart_puts("编译错误: ");
        cnbe_uart_puts(c->errmsg);
        cnbe_uart_puts("\n");
        return -1;
    }

    return c->bc_len;
}

/* ========== 虚拟机执行 ========== */

static long vm_pop(VM *vm)
{
    if (vm->sp > 0)
        return vm->stack[--vm->sp];
    vm->error = 1;
    strcpy(vm->errmsg, "栈下溢");
    return 0;
}

static void vm_push(VM *vm, long val)
{
    if (vm->sp < STACK_SIZE)
        vm->stack[vm->sp++] = val;
    else {
        vm->error = 1;
        strcpy(vm->errmsg, "栈上溢");
    }
}

static int run_bytecode(VM *vm)
{
    vm->sp = 0;
    vm->pc = 0;
    vm->halted = 0;
    vm->error = 0;

    while (!vm->halted && !vm->error && vm->pc < 4096) {
        unsigned char op = vm->bc[vm->pc++];

        switch (op) {
        case OP_PUSH_INT: {
            long v = 0;
            int i;
            for (i = 0; i < 8; i++)
                v |= ((long)vm->bc[vm->pc++]) << (i * 8);
            vm_push(vm, v);
            break;
        }
        case OP_PUSH_VAR: {
            int idx = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            vm_push(vm, vm->vars[idx]);
            break;
        }
        case OP_STORE_VAR: {
            int idx = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            vm->vars[idx] = vm_pop(vm);
            break;
        }
        case OP_ADD: { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a + b); break; }
        case OP_SUB: { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a - b); break; }
        case OP_MUL: { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a * b); break; }
        case OP_DIV: {
            long b = vm_pop(vm), a = vm_pop(vm);
            if (b == 0) { vm->error = 1; strcpy(vm->errmsg, "除以零"); break; }
            vm_push(vm, a / b);
            break;
        }
        case OP_MOD: {
            long b = vm_pop(vm), a = vm_pop(vm);
            if (b == 0) { vm->error = 1; strcpy(vm->errmsg, "除以零"); break; }
            vm_push(vm, a % b);
            break;
        }
        case OP_EQ:  { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a == b); break; }
        case OP_NE:  { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a != b); break; }
        case OP_GT:  { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a > b); break; }
        case OP_LT:  { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a < b); break; }
        case OP_AND: { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a && b); break; }
        case OP_OR:  { long b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a || b); break; }
        case OP_JMP: {
            int addr = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            vm->pc = addr;
            break;
        }
        case OP_JZ: {
            int addr = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            if (vm_pop(vm) == 0) vm->pc = addr;
            break;
        }
        case OP_JNZ: {
            int addr = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            if (vm_pop(vm) != 0) vm->pc = addr;
            break;
        }
        case OP_CALL: {
            int fidx = vm->bc[vm->pc++];
            int nargs = vm->bc[vm->pc++];
            /* 简化: 直接跳转到函数体 */
            /* 参数已在栈上 */
            vm_push(vm, vm->pc); /* 保存返回地址 */
            vm_push(vm, nargs);  /* 保存参数数 */
            /* 查找函数地址 — 需要从编译器状态获取 */
            /* 简化版: 不支持函数调用，弹出参数 */
            while (nargs-- > 0) vm_pop(vm);
            vm_pop(vm); /* 弹出返回地址占位 */
            break;
        }
        case OP_RET: {
            /* 简化: 返回值为栈顶 */
            long retval = vm_pop(vm);
            /* 简化版: 直接停止 */
            vm_push(vm, retval);
            vm->halted = 1;
            break;
        }
        case OP_PRINT_STR: {
            int off = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            cnbe_uart_puts(&vm->str_pool[off]);
            break;
        }
        case OP_PRINT_INT: {
            long v = vm_pop(vm);
            cnbe_uart_putint(v);
            break;
        }
        case OP_PRINT_CHAR: {
            long v = vm_pop(vm);
            cnbe_uart_putc((char)v);
            break;
        }
        case OP_PUSH_STR: {
            int off = (vm->bc[vm->pc++] << 8) | vm->bc[vm->pc++];
            /* 压入字符串偏移作为值 */
            vm_push(vm, off);
            break;
        }
        case OP_STR_CAT: {
            /* 简化: 弹出两个值，忽略 */
            vm_pop(vm);
            break;
        }
        case OP_PUSH_CHAR: {
            char ch = vm->bc[vm->pc++];
            vm_push(vm, (long)ch);
            break;
        }
        case OP_HALT:
            vm->halted = 1;
            break;
        default:
            vm->error = 1;
            strcpy(vm->errmsg, "未知字节码");
            break;
        }
    }

    if (vm->error) {
        cnbe_uart_puts("运行时错误: ");
        cnbe_uart_puts(vm->errmsg);
        cnbe_uart_puts("\n");
        return -1;
    }

    return 0;
}

/* ========== 公共接口 ========== */

int cnbe_compile(const char *source, unsigned char *bytecode, int max_size)
{
    Compiler c;
    int len = compile_source(&c, source);
    if (len < 0)
        return -1;
    if (len > max_size)
        return -1;
    /* 复制字节码 */
    {
        int i;
        for (i = 0; i < len; i++)
            bytecode[i] = c.bytecode[i];
    }
    return len;
}

int cnbe_execute(unsigned char *bytecode, int size)
{
    VM vm;
    vm.bc = bytecode;
    vm.str_pool = NULL; /* 字符串池需要从编译阶段传递 */
    return run_bytecode(&vm);
}

int cnbe_compile_and_run(const char *source)
{
    Compiler c;
    int len = compile_source(&c, source);
    if (len < 0)
        return -1;

    cnbe_uart_puts("编译成功\n");

    VM vm;
    vm.bc = c.bytecode;
    vm.str_pool = c.str_pool;
    /* 复制变量表初始值 */
    {
        int i;
        for (i = 0; i < MAX_VARS; i++)
            vm.vars[i] = 0;
    }

    int result = run_bytecode(&vm);
    if (result == 0)
        cnbe_uart_puts("执行完成\n");
    return result;
}

/* 交互式编译器外壳 */
void cnbe_compiler_shell(void)
{
    static char input_buf[1024];
    int pos;

    cnbe_uart_puts("\n");
    cnbe_uart_puts("=== CNBE-32 中文编译器 ===\n");
    cnbe_uart_puts("全中文关键字 | 字节码虚拟机\n");
    cnbe_uart_puts("输入 '帮助' 查看关键字列表，输入 '退出' 返回\n");
    cnbe_uart_puts("\n");

    while (1) {
        cnbe_uart_puts("中文编译器> ");

        /* 读取输入 */
        pos = 0;
        while (pos < 1023) {
            char ch = 0;
            /* 从 UART 读取 (轮询 LSR) */
            while (!(UART_LSR & 1));
            ch = UART_THR; /* 实际是 RBR 在偏移 0 */
            if (ch == '\r' || ch == '\n') {
                cnbe_uart_putc('\n');
                break;
            }
            if (ch == 8 || ch == 127) {
                if (pos > 0) {
                    pos--;
                    cnbe_uart_puts("\b \b");
                }
                continue;
            }
            input_buf[pos++] = ch;
            cnbe_uart_putc(ch);
        }
        input_buf[pos] = 0;

        /* 检查退出命令 */
        if (strcmp(input_buf, "退出") == 0 || strcmp(input_buf, "exit") == 0)
            break;

        /* 检查帮助命令 */
        if (strcmp(input_buf, "帮助") == 0 || strcmp(input_buf, "help") == 0) {
            cnbe_uart_puts("\n");
            cnbe_uart_puts("中文关键字:\n");
            cnbe_uart_puts("  整数/长整数/字符 — 数据类型\n");
            cnbe_uart_puts("  若/否则/否则若   — 条件分支\n");
            cnbe_uart_puts("  循环             — 当循环\n");
            cnbe_uart_puts("  从...到          — 范围循环\n");
            cnbe_uart_puts("  跳出/继续        — 循环控制\n");
            cnbe_uart_puts("  定义/返回/调用   — 函数\n");
            cnbe_uart_puts("  写/读            — 输入输出\n");
            cnbe_uart_puts("  加/减/乘/除/取模 — 算术运算\n");
            cnbe_uart_puts("  等于/不等/大于/小于 — 比较运算\n");
            cnbe_uart_puts("  且/或            — 逻辑运算\n");
            cnbe_uart_puts("\n");
            cnbe_uart_puts("示例:\n");
            cnbe_uart_puts("  整数 甲 = 42\n");
            cnbe_uart_puts("  写 甲\n");
            cnbe_uart_puts("  若 甲 > 10 { 写 \"大于十\" }\n");
            cnbe_uart_puts("  循环 甲 > 0 { 写 甲; 甲 = 甲 - 1 }\n");
            cnbe_uart_puts("\n");
            continue;
        }

        /* 编译并执行 */
        cnbe_compile_and_run(input_buf);
        cnbe_uart_puts("\n");
    }
}
