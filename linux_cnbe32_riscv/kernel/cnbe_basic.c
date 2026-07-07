/* CNBE-32 中文 BASIC 解释器
 * Linux 0.01 RISC-V 内核版本
 * 全中文关键字 — 零英文依赖
 *
 * 关键字表:
 *   输出(PRINT) 变量(LET) 如果(IF) 否则(ELSE) 循环(FOR)
 *   直到(NEXT) 当(WHILE) 函数(DEF) 返回(RETURN) 取编码(CNBE)
 *   取部首(RADICAL) 比较(CMP) 阅读(READ) 帮助(HELP)
 *   退出(EXIT) 注释(REM)
 *
 * 变量系统: 支持中文变量名与英文单字母变量 A-Z
 * 表达式: 整数四则运算 + 括号 + 变量引用 + 函数调用
 * 程序模式: 行号支持, 输出 "运行" 执行已存储程序
 * 字符串: 输出 "中文字符串" 及字符串拼接
 */

#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/tty.h>
#include <asm/io.h>
#include <asm/segment.h>
#include <cnbe.h>
#include <stdarg.h>
#include <stdint.h>
#include <linux/cnbe_basic.h>

/* ========== 常量定义 ========== */

#define MAX_VARS        64      /* 最大变量数 */
#define MAX_VAR_NAME    8       /* 变量名最大字节 (UTF-8 中文最多3字) */
#define MAX_PROG_LINES  128     /* 最大程序行数 */
#define MAX_LINE_LEN    256     /* 单行最大长度 */
#define MAX_FUNC_DEFS   16      /* 最大函数定义数 */
#define MAX_FUNC_PARAMS 4       /* 函数最大参数数 */
#define MAX_STACK       32      /* 调用栈深度 */
#define MAX_STRING_LEN  256     /* 字符串最大长度 */

/* 值类型 */
#define VAL_INT     0   /* 整数 */
#define VAL_STR     1   /* 字符串 */
#define VAL_NONE    2   /* 无值 */

/* ========== 数据结构 ========== */

/* 变量: 支持中文变量名 */
struct cnbe_var {
    char name[MAX_VAR_NAME];   /* 变量名 (UTF-8) */
    int  type;                 /* 整数类型或字符串类型 */
    long ival;                 /* 整数值 */
    char sval[MAX_STRING_LEN]; /* 字符串值 */
    int  defined;              /* 是否已定义 */
};

/* 程序行 */
struct cnbe_prog_line {
    int lineno;                /* 行号 */
    char text[MAX_LINE_LEN];   /* 行内容 */
    int  active;               /* 是否有效 */
};

/* 函数定义 */
struct cnbe_func {
    char name[MAX_VAR_NAME];          /* 函数名 */
    int  nparams;                      /* 参数个数 */
    char params[MAX_FUNC_PARAMS][MAX_VAR_NAME]; /* 参数名 */
    char body[MAX_LINE_LEN];           /* 函数体 (单行表达式) */
    int  defined;                      /* 是否已定义 */
};

/* 值栈 (表达式求值用) */
struct cnbe_value {
    int type;        /* 整数、字符串或空类型 */
    long ival;       /* 整数值 */
    char sval[MAX_STRING_LEN]; /* 字符串值 */
};

/* ========== 全局状态 ========== */

static struct cnbe_var    vars[MAX_VARS];
static struct cnbe_prog_line prog_lines[MAX_PROG_LINES];
static struct cnbe_func   funcs[MAX_FUNC_DEFS];
static int prog_count = 0;
static int var_count = 0;
static int func_count = 0;

/* 临时变量存储 (用于函数参数传递) */
static struct cnbe_var    temp_vars[MAX_VARS];
static int temp_var_count = 0;

/* ========== 内核输出辅助函数 ========== */

/* 直接通过 UART 输出字符 (RISC-V QEMU virt 平台) */
#define UART0_BASE  0x10000000UL
#define UART_THR    0x00    /* 发送保持寄存器 */
#define UART_LSR    0x05    /* 线路状态寄存器 */
#define UART_LSR_THRE 0x20  /* 发送保持寄存器空 */

static void cnbe_uart_putc(char c)
{
    volatile unsigned char *uart = (volatile unsigned char *)UART0_BASE;
    while ((uart[UART_LSR] & UART_LSR_THRE) == 0)
        ;
    uart[UART_THR] = c;
}

static void cnbe_puts(const char *s)
{
    while (*s) {
        cnbe_uart_putc(*s);
        s++;
    }
}

static void cnbe_putc(char c)
{
    cnbe_uart_putc(c);
}

/* 输出整数 */
static void cnbe_putint(long val)
{
    char buf[24];
    int i = 0;
    int neg = 0;

    if (val < 0) {
        neg = 1;
        val = -val;
    }

    if (val == 0) {
        cnbe_putc('0');
        return;
    }

    while (val > 0) {
        buf[i++] = '0' + (val % 10);
        val /= 10;
    }

    if (neg)
        cnbe_putc('-');

    while (i > 0)
        cnbe_putc(buf[--i]);
}

/* 输出十六进制 */
static void cnbe_puthex(unsigned long val)
{
    char hex[] = "0123456789ABCDEF";
    int i;
    cnbe_puts("0x");
    for (i = 28; i >= 0; i -= 4) {
        unsigned long nib = (val >> i) & 0xF;
        if (nib || i < 28)
            cnbe_putc(hex[nib]);
    }
}

/* ========== 字符串辅助函数 ========== */

static int cnbe_strlen(const char *s)
{
    int n = 0;
    while (s[n]) n++;
    return n;
}

static void cnbe_strcpy(char *dst, const char *src)
{
    while ((*dst++ = *src++))
        ;
}

static void cnbe_strncpy(char *dst, const char *src, int n)
{
    int i;
    for (i = 0; i < n && src[i]; i++)
        dst[i] = src[i];
    dst[i] = '\0';
}

static int cnbe_strcmp_impl(const char *a, const char *b)
{
    while (*a && (*a == *b)) {
        a++;
        b++;
    }
    return (unsigned char)*a - (unsigned char)*b;
}

static int cnbe_strncmp_impl(const char *a, const char *b, int n)
{
    int i;
    for (i = 0; i < n; i++) {
        if (a[i] != b[i])
            return (unsigned char)a[i] - (unsigned char)b[i];
        if (a[i] == '\0')
            return 0;
    }
    return 0;
}

static char *cnbe_strchr_impl(const char *s, char c)
{
    while (*s) {
        if (*s == c)
            return (char *)s;
        s++;
    }
    return (c == '\0') ? (char *)s : 0;
}

/* 跳过空白 */
static const char *skip_ws(const char *p)
{
    while (*p == ' ' || *p == '\t')
        p++;
    return p;
}

/* 判断是否为数字字符 */
static int is_digit(char c)
{
    return (c >= '0' && c <= '9');
}

/* 判断是否为 ASCII 字母 */
static int is_alpha(char c)
{
    return ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'));
}

/* ========== UTF-8 辅助 ========== */

/* 获取 UTF-8 字符字节长度 */
static int utf8_len(unsigned char c)
{
    if (c < 0x80) return 1;
    if ((c & 0xE0) == 0xC0) return 2;
    if ((c & 0xF0) == 0xE0) return 3;
    if ((c & 0xF8) == 0xF0) return 4;
    return 1;
}

/* 比较字符串开头的 UTF-8 关键字
 * 返回: 匹配成功返回关键字长度, 否则返回 0 */
static int match_kw(const char *p, const char *kw)
{
    int len = cnbe_strlen(kw);
    if (cnbe_strncmp_impl(p, kw, len) == 0)
        return len;
    return 0;
}

/* ========== 道德经摘录 ========== */

static const char *daodejing[] = {
    "道可道，非常道。名可名，非常名。",
    "无名天地之始，有名万物之母。",
    "故常无欲以观其妙，常有欲以观其徼。",
    "此两者同出而异名，同谓之玄。",
    "玄之又玄，众妙之门。",
    "上善若水。水善利万物而不争。",
    "处众人之所恶，故几于道。",
    "居善地，心善渊，与善仁，言善信。",
    "正善治，事善能，动善时。",
    "夫唯不争，故无尤。",
    "致虚极，守静笃。万物并作，吾以观复。",
    "夫物芸芸，各复归其根。",
    "归根曰静，静曰复命。复命曰常，知常曰明。",
    "知人者智，自知者明。胜人者有力，自胜者强。",
    "知足者富。强行者有志。",
    "不失其所者久。死而不亡者寿。",
    "大方无隅，大器晚成，大音希声，大象无形。",
    "道生一，一生二，二生三，三生万物。",
    "万物负阴而抱阳，冲气以为和。",
    "上士闻道勤而行之。中士闻道若存若亡。",
    "下士闻道大笑之。不笑不足以为道。",
    NULL
};

/* ========== 变量系统 ========== */

/* 查找变量, 返回索引, 不存在返回 -1 */
static int find_var(const char *name)
{
    int i;
    for (i = 0; i < var_count; i++) {
        if (cnbe_strcmp_impl(vars[i].name, name) == 0)
            return i;
    }
    /* 查找临时变量 (函数参数) */
    for (i = 0; i < temp_var_count; i++) {
        if (cnbe_strcmp_impl(temp_vars[i].name, name) == 0)
            return MAX_VARS + i;
    }
    return -1;
}

/* 创建或获取变量, 返回索引 */
static int get_or_create_var(const char *name)
{
    int idx = find_var(name);
    if (idx >= 0)
        return idx;

    if (var_count < MAX_VARS) {
        cnbe_strncpy(vars[var_count].name, name, MAX_VAR_NAME - 1);
        vars[var_count].name[MAX_VAR_NAME - 1] = '\0';
        vars[var_count].defined = 0;
        vars[var_count].type = VAL_INT;
        vars[var_count].ival = 0;
        vars[var_count].sval[0] = '\0';
        return var_count++;
    }
    return -1;
}

/* 获取变量值 (整数) */
static long get_var_int(const char *name, int *ok)
{
    int idx = find_var(name);
    if (ok) *ok = 1;

    if (idx < 0) {
        if (ok) *ok = 0;
        return 0;
    }

    if (idx >= MAX_VARS) {
        idx -= MAX_VARS;
        if (temp_vars[idx].type != VAL_INT || !temp_vars[idx].defined) {
            if (ok) *ok = 0;
            return 0;
        }
        return temp_vars[idx].ival;
    }

    if (vars[idx].type != VAL_INT || !vars[idx].defined) {
        if (ok) *ok = 0;
        return 0;
    }
    return vars[idx].ival;
}

/* 设置整数变量 */
static void set_var_int(const char *name, long val)
{
    int idx = get_or_create_var(name);
    if (idx < 0) return;
    vars[idx].type = VAL_INT;
    vars[idx].ival = val;
    vars[idx].defined = 1;
    vars[idx].sval[0] = '\0';
}

/* 获取字符串变量 */
static const char *get_var_str(const char *name, int *ok)
{
    int idx = find_var(name);
    if (ok) *ok = 1;

    if (idx < 0) {
        if (ok) *ok = 0;
        return "";
    }

    if (idx >= MAX_VARS) {
        idx -= MAX_VARS;
        if (temp_vars[idx].type != VAL_STR || !temp_vars[idx].defined) {
            if (ok) *ok = 0;
            return "";
        }
        return temp_vars[idx].sval;
    }

    if (vars[idx].type != VAL_STR || !vars[idx].defined) {
        if (ok) *ok = 0;
        return "";
    }
    return vars[idx].sval;
}

/* 设置字符串变量 */
static void set_var_str(const char *name, const char *val)
{
    int idx = get_or_create_var(name);
    if (idx < 0) return;
    vars[idx].type = VAL_STR;
    vars[idx].ival = 0;
    cnbe_strncpy(vars[idx].sval, val, MAX_STRING_LEN - 1);
    vars[idx].sval[MAX_STRING_LEN - 1] = '\0';
    vars[idx].defined = 1;
}

/* 清空临时变量 (函数调用时使用) */
static void clear_temp_vars(void)
{
    temp_var_count = 0;
}

/* ========== 表达式求值器 ========== */

/* 表达式解析上下文 */
struct expr_ctx {
    const char *p;     /* 当前位置 */
    int error;         /* 错误标志 */
    char errmsg[64];   /* 错误信息 */
};

static void expr_error(struct expr_ctx *ctx, const char *msg)
{
    ctx->error = 1;
    cnbe_strncpy(ctx->errmsg, msg, 63);
    ctx->errmsg[63] = '\0';
}

/* 前向声明 */
static struct cnbe_value eval_expr(struct expr_ctx *ctx);
static struct cnbe_value eval_comparison(struct expr_ctx *ctx);
static struct cnbe_value eval_addsub(struct expr_ctx *ctx);
static struct cnbe_value eval_muldiv(struct expr_ctx *ctx);
static struct cnbe_value eval_primary(struct expr_ctx *ctx);
static struct cnbe_value eval_func_call(struct expr_ctx *ctx, const char *name, int namelen);

/* 初始化值 */
static void val_set_int(struct cnbe_value *v, long val)
{
    v->type = VAL_INT;
    v->ival = val;
    v->sval[0] = '\0';
}

static void val_set_str(struct cnbe_value *v, const char *s)
{
    v->type = VAL_STR;
    v->ival = 0;
    cnbe_strncpy(v->sval, s, MAX_STRING_LEN - 1);
    v->sval[MAX_STRING_LEN - 1] = '\0';
}

/* 值转整数 */
static long val_to_int(struct cnbe_value *v, int *ok)
{
    if (ok) *ok = 1;
    if (v->type == VAL_INT)
        return v->ival;
    if (v->type == VAL_STR) {
        /* 尝试解析字符串为数字 */
        const char *s = v->sval;
        long val = 0;
        int neg = 0;
        if (*s == '-') { neg = 1; s++; }
        if (!is_digit(*s)) {
            if (ok) *ok = 0;
            return 0;
        }
        while (is_digit(*s)) {
            val = val * 10 + (*s - '0');
            s++;
        }
        return neg ? -val : val;
    }
    if (ok) *ok = 0;
    return 0;
}

/* 跳过空白 */
static void expr_skip_ws(struct expr_ctx *ctx)
{
    while (*ctx->p == ' ' || *ctx->p == '\t')
        ctx->p++;
}

/* 解析整数 */
static struct cnbe_value parse_number(struct expr_ctx *ctx)
{
    long val = 0;
    int has_digit = 0;

    while (is_digit(*ctx->p)) {
        val = val * 10 + (*ctx->p - '0');
        ctx->p++;
        has_digit = 1;
    }

    if (!has_digit) {
        expr_error(ctx, "语法错误: 期望数字");
        struct cnbe_value v;
        val_set_int(&v, 0);
        return v;
    }

    struct cnbe_value v;
    val_set_int(&v, val);
    return v;
}

/* 解析字符串字面量 "..." */
static struct cnbe_value parse_string(struct expr_ctx *ctx)
{
    struct cnbe_value v;
    char buf[MAX_STRING_LEN];
    int i = 0;

    ctx->p++; /* 跳过开头的 " */

    while (*ctx->p && *ctx->p != '"' && i < MAX_STRING_LEN - 1) {
        buf[i++] = *ctx->p++;
    }

    if (*ctx->p == '"')
        ctx->p++; /* 跳过结尾的 " */
    else
        expr_error(ctx, "语法错误: 字符串未闭合");

    buf[i] = '\0';
    val_set_str(&v, buf);
    return v;
}

/* 读取标识符 (中文或英文)
 * 中文标识符: 连续的 UTF-8 多字节字符
 * 英文标识符: 单个字母 A-Z, a-z
 * 返回标识符长度 */
static int read_identifier(const char *p, char *buf, int bufsize)
{
    int i = 0;
    unsigned char c = (unsigned char)*p;

    /* 英文单字母变量 */
    if (is_alpha(c)) {
        if (i < bufsize - 1)
            buf[i++] = *p++;
        /* 英文变量只取一个字母 */
        buf[i] = '\0';
        return i;
    }

    /* 中文标识符: 连续的 UTF-8 3字节字符 */
    while (*p && (unsigned char)*p >= 0x80) {
        int len = utf8_len((unsigned char)*p);
        int j;
        for (j = 0; j < len && i < bufsize - 1; j++) {
            buf[i++] = *p++;
        }
    }

    buf[i] = '\0';
    return i;
}

/* 判断字符是否可作为标识符的一部分 */
static int is_ident_char(char c)
{
    return is_alpha(c) || ((unsigned char)c >= 0x80);
}

/* 解析基本元素: 数字、字符串、变量、括号、函数调用 */
static struct cnbe_value eval_primary(struct expr_ctx *ctx)
{
    struct cnbe_value v;
    expr_skip_ws(ctx);

    char c = *ctx->p;

    /* 数字 */
    if (is_digit(c)) {
        return parse_number(ctx);
    }

    /* 负号 (一元负) */
    if (c == '-') {
        ctx->p++;
        struct cnbe_value inner = eval_primary(ctx);
        long val = val_to_int(&inner, 0);
        val_set_int(&v, -val);
        return v;
    }

    /* 括号 */
    if (c == '(') {
        ctx->p++; /* 跳过 ( */
        v = eval_expr(ctx);
        expr_skip_ws(ctx);
        if (*ctx->p == ')')
            ctx->p++;
        else
            expr_error(ctx, "语法错误: 缺少右括号");
        return v;
    }

    /* 字符串 */
    if (c == '"') {
        return parse_string(ctx);
    }

    /* 变量或函数调用 */
    if (is_ident_char(c)) {
        char name[MAX_VAR_NAME];
        int namelen = read_identifier(ctx->p, name, MAX_VAR_NAME);
        if (namelen == 0) {
            expr_error(ctx, "语法错误: 无效标识符");
            val_set_int(&v, 0);
            return v;
        }
        ctx->p += namelen;

        expr_skip_ws(ctx);

        /* 检查是否是函数调用 */
        if (*ctx->p == '(') {
            ctx->p++; /* 跳过 ( */
            return eval_func_call(ctx, name, namelen);
        }

        /* 变量引用 */
        int idx = find_var(name);
        if (idx < 0) {
            /* 未定义变量, 默认为 0 */
            val_set_int(&v, 0);
            return v;
        }

        if (idx >= MAX_VARS) {
            idx -= MAX_VARS;
            if (temp_vars[idx].type == VAL_INT)
                val_set_int(&v, temp_vars[idx].ival);
            else if (temp_vars[idx].type == VAL_STR)
                val_set_str(&v, temp_vars[idx].sval);
            else
                val_set_int(&v, 0);
        } else {
            if (vars[idx].type == VAL_INT)
                val_set_int(&v, vars[idx].ival);
            else if (vars[idx].type == VAL_STR)
                val_set_str(&v, vars[idx].sval);
            else
                val_set_int(&v, 0);
        }
        return v;
    }

    expr_error(ctx, "语法错误: 意外字符");
    val_set_int(&v, 0);
    return v;
}

/* 函数调用求值 */
static struct cnbe_value eval_func_call(struct expr_ctx *ctx, const char *name, int namelen)
{
    struct cnbe_value v;
    struct cnbe_value args[MAX_FUNC_PARAMS];
    int nargs = 0;
    int i;

    /* 解析参数列表 */
    expr_skip_ws(ctx);
    while (*ctx->p && *ctx->p != ')' && nargs < MAX_FUNC_PARAMS) {
        args[nargs] = eval_expr(ctx);
        nargs++;
        expr_skip_ws(ctx);
        if (*ctx->p == ',') {
            ctx->p++;
            expr_skip_ws(ctx);
        }
    }

    if (*ctx->p == ')')
        ctx->p++;
    else
        expr_error(ctx, "语法错误: 缺少右括号");

    /* 查找用户定义函数 */
    for (i = 0; i < func_count; i++) {
        if (cnbe_strcmp_impl(funcs[i].name, name) == 0 && funcs[i].defined) {
            /* 保存当前临时变量区 */
            int saved_temp = temp_var_count;
            int saved_vars[MAX_FUNC_PARAMS];
            int j;

            /* 设置参数变量 */
            for (j = 0; j < funcs[i].nparams && j < nargs; j++) {
                if (temp_var_count < MAX_VARS) {
                    cnbe_strncpy(temp_vars[temp_var_count].name,
                                 funcs[i].params[j], MAX_VAR_NAME - 1);
                    temp_vars[temp_var_count].name[MAX_VAR_NAME - 1] = '\0';
                    if (args[j].type == VAL_INT) {
                        temp_vars[temp_var_count].type = VAL_INT;
                        temp_vars[temp_var_count].ival = args[j].ival;
                    } else {
                        temp_vars[temp_var_count].type = VAL_STR;
                        cnbe_strncpy(temp_vars[temp_var_count].sval,
                                     args[j].sval, MAX_STRING_LEN - 1);
                    }
                    temp_vars[temp_var_count].defined = 1;
                    saved_vars[j] = temp_var_count;
                    temp_var_count++;
                }
            }

            /* 求值函数体 */
            struct expr_ctx fctx;
            fctx.p = funcs[i].body;
            fctx.error = 0;
            v = eval_expr(&fctx);

            /* 恢复临时变量区 */
            temp_var_count = saved_temp;
            return v;
        }
    }

    /* 内建函数: 取编码 (CNBE编码) */
    if (cnbe_strcmp_impl(name, "取编码") == 0 && nargs >= 1) {
        int advance = 0;
        uint32_t uni = cnbe_utf8_decode(args[0].sval, &advance);
        uint32_t code = cnhe_map(uni);
        val_set_int(&v, (long)code);
        return v;
    }

    /* 内建函数: 取部首 */
    if (cnbe_strcmp_impl(name, "取部首") == 0 && nargs >= 1) {
        int advance = 0;
        uint32_t uni = cnbe_utf8_decode(args[0].sval, &advance);
        uint32_t code = cnhe_map(uni);
        uint32_t radical = cnhe_extract(code, 0);
        val_set_int(&v, (long)radical);
        return v;
    }

    /* 内建函数: 比较 */
    if (cnbe_strcmp_impl(name, "比较") == 0 && nargs >= 2) {
        int advance1 = 0, advance2 = 0;
        uint32_t uni1 = cnbe_utf8_decode(args[0].sval, &advance1);
        uint32_t uni2 = cnbe_utf8_decode(args[1].sval, &advance2);
        uint32_t code1 = cnhe_map(uni1);
        uint32_t code2 = cnhe_map(uni2);
        uint32_t dist = cnhe_cmp(code1, code2);
        val_set_int(&v, (long)dist);
        return v;
    }

    /* 内建函数: 绝对值 */
    if (cnbe_strcmp_impl(name, "绝对值") == 0 && nargs >= 1) {
        long val = val_to_int(&args[0], 0);
        val_set_int(&v, val < 0 ? -val : val);
        return v;
    }

    /* 内建函数: 最大值 */
    if (cnbe_strcmp_impl(name, "最大") == 0 && nargs >= 2) {
        long a = val_to_int(&args[0], 0);
        long b = val_to_int(&args[1], 0);
        val_set_int(&v, a > b ? a : b);
        return v;
    }

    /* 内建函数: 最小值 */
    if (cnbe_strcmp_impl(name, "最小") == 0 && nargs >= 2) {
        long a = val_to_int(&args[0], 0);
        long b = val_to_int(&args[1], 0);
        val_set_int(&v, a < b ? a : b);
        return v;
    }

    expr_error(ctx, "未定义函数");
    val_set_int(&v, 0);
    return v;
}

/* 乘除法 */
static struct cnbe_value eval_muldiv(struct expr_ctx *ctx)
{
    struct cnbe_value left = eval_primary(ctx);

    for (;;) {
        expr_skip_ws(ctx);
        char c = *ctx->p;

        if (c == '*') {
            ctx->p++;
            struct cnbe_value right = eval_primary(ctx);
            long a = val_to_int(&left, 0);
            long b = val_to_int(&right, 0);
            val_set_int(&left, a * b);
        } else if (c == '/') {
            ctx->p++;
            struct cnbe_value right = eval_primary(ctx);
            long a = val_to_int(&left, 0);
            long b = val_to_int(&right, 0);
            if (b == 0) {
                expr_error(ctx, "运行时错误: 除数为零");
                val_set_int(&left, 0);
            } else {
                val_set_int(&left, a / b);
            }
        } else if (c == '%') {
            ctx->p++;
            struct cnbe_value right = eval_primary(ctx);
            long a = val_to_int(&left, 0);
            long b = val_to_int(&right, 0);
            if (b == 0) {
                expr_error(ctx, "运行时错误: 模数为零");
                val_set_int(&left, 0);
            } else {
                val_set_int(&left, a % b);
            }
        } else {
            break;
        }
    }

    return left;
}

/* 加减法与字符串拼接 */
static struct cnbe_value eval_addsub(struct expr_ctx *ctx)
{
    struct cnbe_value left = eval_muldiv(ctx);

    for (;;) {
        expr_skip_ws(ctx);
        char c = *ctx->p;

        if (c == '+') {
            ctx->p++;
            struct cnbe_value right = eval_muldiv(ctx);

            /* 字符串拼接 */
            if (left.type == VAL_STR || right.type == VAL_STR) {
                char buf[MAX_STRING_LEN * 2];
                int pl = 0;
                int i;

                if (left.type == VAL_STR) {
                    int sl = cnbe_strlen(left.sval);
                    for (i = 0; i < sl && pl < MAX_STRING_LEN * 2 - 1; i++)
                        buf[pl++] = left.sval[i];
                } else {
                    /* 整数转字符串 */
                    long val = left.ival;
                    char numbuf[24];
                    int nlen = 0;
                    int neg = 0;
                    if (val < 0) { neg = 1; val = -val; }
                    if (val == 0) {
                        numbuf[nlen++] = '0';
                    } else {
                        while (val > 0) {
                            numbuf[nlen++] = '0' + (val % 10);
                            val /= 10;
                        }
                    }
                    if (neg) buf[pl++] = '-';
                    for (i = nlen - 1; i >= 0 && pl < MAX_STRING_LEN * 2 - 1; i--)
                        buf[pl++] = numbuf[i];
                }

                if (right.type == VAL_STR) {
                    int sl = cnbe_strlen(right.sval);
                    for (i = 0; i < sl && pl < MAX_STRING_LEN * 2 - 1; i++)
                        buf[pl++] = right.sval[i];
                } else {
                    long val = right.ival;
                    char numbuf[24];
                    int nlen = 0;
                    int neg = 0;
                    if (val < 0) { neg = 1; val = -val; }
                    if (val == 0) {
                        numbuf[nlen++] = '0';
                    } else {
                        while (val > 0) {
                            numbuf[nlen++] = '0' + (val % 10);
                            val /= 10;
                        }
                    }
                    if (neg) buf[pl++] = '-';
                    for (i = nlen - 1; i >= 0 && pl < MAX_STRING_LEN * 2 - 1; i--)
                        buf[pl++] = numbuf[i];
                }

                buf[pl] = '\0';
                val_set_str(&left, buf);
            } else {
                /* 整数加法 */
                long a = val_to_int(&left, 0);
                long b = val_to_int(&right, 0);
                val_set_int(&left, a + b);
            }
        } else if (c == '-') {
            ctx->p++;
            struct cnbe_value right = eval_muldiv(ctx);
            long a = val_to_int(&left, 0);
            long b = val_to_int(&right, 0);
            val_set_int(&left, a - b);
        } else {
            break;
        }
    }

    return left;
}

/* 比较运算: = != < > <= >= */
static struct cnbe_value eval_comparison(struct expr_ctx *ctx)
{
    struct cnbe_value left = eval_addsub(ctx);

    expr_skip_ws(ctx);

    /* 等于 */
    if (*ctx->p == '=' && ctx->p[1] != '=') {
        ctx->p++;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a == b ? 1 : 0);
        return left;
    }

    /* 不等于 */
    if (*ctx->p == '#' || (*ctx->p == '!' && ctx->p[1] == '=')) {
        if (*ctx->p == '!')
            ctx->p += 2;
        else
            ctx->p++;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a != b ? 1 : 0);
        return left;
    }

    /* 小于等于 */
    if (*ctx->p == '<' && ctx->p[1] == '=') {
        ctx->p += 2;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a <= b ? 1 : 0);
        return left;
    }

    /* 大于等于 */
    if (*ctx->p == '>' && ctx->p[1] == '=') {
        ctx->p += 2;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a >= b ? 1 : 0);
        return left;
    }

    /* 小于 */
    if (*ctx->p == '<') {
        ctx->p++;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a < b ? 1 : 0);
        return left;
    }

    /* 大于 */
    if (*ctx->p == '>') {
        ctx->p++;
        struct cnbe_value right = eval_addsub(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, a > b ? 1 : 0);
        return left;
    }

    return left;
}

/* 逻辑运算: 与 或 非 */
static struct cnbe_value eval_expr(struct expr_ctx *ctx)
{
    struct cnbe_value left = eval_comparison(ctx);

    expr_skip_ws(ctx);

    /* 逻辑与: 中文 "与" 或英文 & */
    int kwlen;
    if ((kwlen = match_kw(ctx->p, "与")) || *ctx->p == '&') {
        if (kwlen) ctx->p += kwlen; else ctx->p++;
        struct cnbe_value right = eval_expr(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, (a && b) ? 1 : 0);
        return left;
    }

    /* 逻辑或: 中文 "或" 或英文 | */
    if ((kwlen = match_kw(ctx->p, "或")) || *ctx->p == '|') {
        if (kwlen) ctx->p += kwlen; else ctx->p++;
        struct cnbe_value right = eval_expr(ctx);
        long a = val_to_int(&left, 0);
        long b = val_to_int(&right, 0);
        val_set_int(&left, (a || b) ? 1 : 0);
        return left;
    }

    return left;
}

/* ========== 语句解析器 ========== */

/* 输出值 */
static void print_value(struct cnbe_value *v)
{
    if (v->type == VAL_INT) {
        cnbe_putint(v->ival);
    } else if (v->type == VAL_STR) {
        cnbe_puts(v->sval);
    }
}

/* 输出命令: 输出 <表达式>
 * 输出 "字符串"
 * 输出 表达式1, 表达式2, ... */
static void cmd_print(const char *p)
{
    struct cnbe_value v;
    int first = 1;

    p = skip_ws(p);

    if (*p == '\0' || *p == '\n' || *p == '\r') {
        cnbe_putc('\n');
        return;
    }

    while (*p && *p != '\n' && *p != '\r') {
        p = skip_ws(p);

        /* 检查结尾的 注释 */
        if (match_kw(p, "注释") || *p == '\'') {
            break;
        }

        if (!first) {
            /* 逗号分隔 -> 输出制表符 */
            cnbe_putc('\t');
        }
        first = 0;

        struct expr_ctx ctx;
        ctx.p = p;
        ctx.error = 0;
        v = eval_expr(&ctx);

        if (ctx.error) {
            cnbe_puts("语法错误");
            cnbe_putc('\n');
            return;
        }

        print_value(&v);
        p = ctx.p;
        p = skip_ws(p);

        if (*p == ',') {
            p++;
            continue;
        } else if (*p == ';') {
            p++;
            /* 分号不换行, 继续 */
            continue;
        } else {
            break;
        }
    }
    cnbe_putc('\n');
}

/* 变量赋值: 变量 名 = 表达式 */
static void cmd_let(const char *p)
{
    char name[MAX_VAR_NAME];
    int namelen;

    p = skip_ws(p);
    namelen = read_identifier(p, name, MAX_VAR_NAME);
    if (namelen == 0) {
        cnbe_puts("语法错误: 缺少变量名\n");
        return;
    }
    p += namelen;
    p = skip_ws(p);

    if (*p != '=') {
        cnbe_puts("语法错误: 缺少赋值号 =\n");
        return;
    }
    p++;
    p = skip_ws(p);

    /* 检查是否是字符串赋值 */
    if (*p == '"') {
        /* 字符串赋值 */
        char buf[MAX_STRING_LEN];
        int i = 0;
        p++; /* 跳过 " */
        while (*p && *p != '"' && i < MAX_STRING_LEN - 1) {
            buf[i++] = *p++;
        }
        buf[i] = '\0';
        if (*p == '"') p++;

        /* 检查是否有拼接 */
        p = skip_ws(p);
        if (*p == '+') {
            /* 字符串拼接 */
            char result[MAX_STRING_LEN];
            cnbe_strcpy(result, buf);
            while (*p == '+') {
                p++;
                p = skip_ws(p);
                if (*p == '"') {
                    char buf2[MAX_STRING_LEN];
                    int j = 0;
                    p++;
                    while (*p && *p != '"' && j < MAX_STRING_LEN - 1) {
                        buf2[j++] = *p++;
                    }
                    buf2[j] = '\0';
                    if (*p == '"') p++;

                    /* 拼接到 result */
                    int rl = cnbe_strlen(result);
                    int bl = cnbe_strlen(buf2);
                    if (rl + bl < MAX_STRING_LEN) {
                        int k;
                        for (k = 0; k < bl; k++)
                            result[rl + k] = buf2[k];
                        result[rl + bl] = '\0';
                    }
                } else {
                    /* 变量引用拼接 */
                    char vname[MAX_VAR_NAME];
                    int vl = read_identifier(p, vname, MAX_VAR_NAME);
                    if (vl > 0) {
                        p += vl;
                        int ok;
                        const char *sval = get_var_str(vname, &ok);
                        if (ok) {
                            int rl = cnbe_strlen(result);
                            int sl = cnbe_strlen(sval);
                            if (rl + sl < MAX_STRING_LEN) {
                                int k;
                                for (k = 0; k < sl; k++)
                                    result[rl + k] = sval[k];
                                result[rl + sl] = '\0';
                            }
                        }
                    }
                }
                p = skip_ws(p);
            }
            set_var_str(name, result);
        } else {
            set_var_str(name, buf);
        }
    } else {
        /* 数值表达式赋值 */
        struct expr_ctx ctx;
        ctx.p = p;
        ctx.error = 0;
        struct cnbe_value v = eval_expr(&ctx);

        if (ctx.error) {
            cnbe_puts(ctx.errmsg);
            cnbe_putc('\n');
            return;
        }

        if (v.type == VAL_STR) {
            set_var_str(name, v.sval);
        } else {
            set_var_int(name, v.ival);
        }
    }
}

/* 如果语句: 如果 条件 语句 [否则 语句] */
static int cmd_if(const char *p)
{
    struct expr_ctx ctx;
    ctx.p = p;
    ctx.error = 0;

    struct cnbe_value cond = eval_expr(&ctx);

    if (ctx.error) {
        cnbe_puts("语法错误: 条件表达式错误\n");
        return 0;
    }

    long result = val_to_int(&cond, 0);
    p = ctx.p;
    p = skip_ws(p);

    /* 查找 "则" 或 "就" 或 "then" 关键字 (可选) */
    int kwlen;
    if ((kwlen = match_kw(p, "则")))
        p += kwlen;
    else if ((kwlen = match_kw(p, "就")))
        p += kwlen;

    p = skip_ws(p);

    if (result) {
        /* 条件为真, 执行 then 分支 */
        /* 检查是否有 "否则" 分支 */
        const char *else_pos = p;
        while (*else_pos) {
            if ((kwlen = match_kw(else_pos, "否则"))) {
                /* 找到否则, 截断 then 分支 */
                break;
            }
            else_pos++;
        }

        /* 递归求值 then 分支 */
        char then_buf[MAX_LINE_LEN];
        int then_len = 0;
        const char *src = p;
        while (*src && !(match_kw(src, "否则"))) {
            if (then_len < MAX_LINE_LEN - 1)
                then_buf[then_len++] = *src;
            src++;
        }
        then_buf[then_len] = '\0';

        /* 求值 then 分支 */
        if (then_len > 0) {
            cnbe_basic_eval(then_buf);
        }
        return 1;
    } else {
        /* 条件为假, 查找否则分支 */
        while (*p) {
            if ((kwlen = match_kw(p, "否则"))) {
                p += kwlen;
                p = skip_ws(p);
                cnbe_basic_eval(p);
                return 1;
            }
            p++;
        }
        /* 没有否则分支, 不做任何事 */
        return 1;
    }
}

/* 循环语句: 循环 变量 = 起 到 终 [步长 步] */
static void cmd_for(const char *p, int *loop_active, int *loop_var_idx,
                    long *loop_start, long *loop_end, long *loop_step,
                    const char **loop_body, int *loop_body_lineno)
{
    /* 此为简化版: 循环 甲 = 1 到 10 ... 直到 */
    /* 在程序模式下, FOR/NEXT 需要跨行配对 */
    /* 此处仅记录循环状态, 由运行器处理跳转 */
    (void)p;
    (void)loop_active;
    (void)loop_var_idx;
    (void)loop_start;
    (void)loop_end;
    (void)loop_step;
    (void)loop_body;
    (void)loop_body_lineno;

    /* 简化实现: 在 cnbe_basic_run 中处理 */
}

/* 函数定义: 函数 名(参数1, 参数2) = 表达式 */
static void cmd_def(const char *p)
{
    char fname[MAX_VAR_NAME];
    int fnamelen;

    p = skip_ws(p);
    fnamelen = read_identifier(p, fname, MAX_VAR_NAME);
    if (fnamelen == 0) {
        cnbe_puts("语法错误: 缺少函数名\n");
        return;
    }
    p += fnamelen;
    p = skip_ws(p);

    if (*p != '(') {
        cnbe_puts("语法错误: 缺少左括号\n");
        return;
    }
    p++;

    /* 解析参数列表 */
    int nparams = 0;
    while (*p && *p != ')') {
        p = skip_ws(p);
        if (*p == ')') break;

        char pname[MAX_VAR_NAME];
        int pnamelen = read_identifier(p, pname, MAX_VAR_NAME);
        if (pnamelen == 0) {
            cnbe_puts("语法错误: 参数名无效\n");
            return;
        }
        p += pnamelen;

        if (nparams < MAX_FUNC_PARAMS) {
            cnbe_strncpy(funcs[func_count].params[nparams], pname, MAX_VAR_NAME - 1);
            funcs[func_count].params[nparams][MAX_VAR_NAME - 1] = '\0';
            nparams++;
        }

        p = skip_ws(p);
        if (*p == ',') {
            p++;
            continue;
        }
    }

    if (*p == ')')
        p++;

    p = skip_ws(p);

    if (*p != '=') {
        cnbe_puts("语法错误: 缺少等号\n");
        return;
    }
    p++;

    p = skip_ws(p);

    /* 存储函数体 */
    if (func_count < MAX_FUNC_DEFS) {
        cnbe_strncpy(funcs[func_count].name, fname, MAX_VAR_NAME - 1);
        funcs[func_count].name[MAX_VAR_NAME - 1] = '\0';
        funcs[func_count].nparams = nparams;
        cnbe_strncpy(funcs[func_count].body, p, MAX_LINE_LEN - 1);
        funcs[func_count].body[MAX_LINE_LEN - 1] = '\0';
        funcs[func_count].defined = 1;
        func_count++;
    }
}

/* 取编码命令: 取编码 "字" */
static void cmd_cnbe(const char *p)
{
    p = skip_ws(p);
    struct expr_ctx ctx;
    ctx.p = p;
    ctx.error = 0;
    struct cnbe_value v = eval_expr(&ctx);

    if (ctx.error) {
        cnbe_puts("语法错误\n");
        return;
    }

    int advance = 0;
    uint32_t uni;

    if (v.type == VAL_STR) {
        uni = cnbe_utf8_decode(v.sval, &advance);
    } else {
        uni = (uint32_t)v.ival;
    }

    uint32_t code = cnhe_map(uni);
    cnbe_puts("CNBE-32编码: ");
    cnbe_puthex((unsigned long)code);
    cnbe_putc('\n');

    cnbe_puts("  部首: ");
    cnbe_putint((long)cnhe_extract(code, 0));
    cnbe_puts("  笔画: ");
    cnbe_putint((long)cnhe_extract(code, 1));
    cnbe_puts("  结构: ");
    cnbe_putint((long)cnhe_extract(code, 2));
    cnbe_putc('\n');
}

/* 取部首命令: 取部首 "字" */
static void cmd_radical(const char *p)
{
    p = skip_ws(p);
    struct expr_ctx ctx;
    ctx.p = p;
    ctx.error = 0;
    struct cnbe_value v = eval_expr(&ctx);

    if (ctx.error) {
        cnbe_puts("语法错误\n");
        return;
    }

    int advance = 0;
    uint32_t uni;

    if (v.type == VAL_STR) {
        uni = cnbe_utf8_decode(v.sval, &advance);
    } else {
        uni = (uint32_t)v.ival;
    }

    uint32_t code = cnhe_map(uni);
    uint32_t radical = cnhe_extract(code, 0);

    cnbe_puts("部首码: ");
    cnbe_putint((long)radical);
    cnbe_putc('\n');
}

/* 比较命令: 比较 "字1" "字2" */
static void cmd_cmp(const char *p)
{
    p = skip_ws(p);
    struct expr_ctx ctx;
    ctx.p = p;
    ctx.error = 0;
    struct cnbe_value v1 = eval_expr(&ctx);

    p = ctx.p;
    p = skip_ws(p);

    /* 支持逗号分隔或空格分隔 */
    if (*p == ',') {
        p++;
        p = skip_ws(p);
    }

    struct expr_ctx ctx2;
    ctx2.p = p;
    ctx2.error = 0;
    struct cnbe_value v2 = eval_expr(&ctx2);

    if (ctx.error || ctx2.error) {
        cnbe_puts("语法错误\n");
        return;
    }

    int adv1, adv2;
    uint32_t uni1, uni2;

    if (v1.type == VAL_STR)
        uni1 = cnbe_utf8_decode(v1.sval, &adv1);
    else
        uni1 = (uint32_t)v1.ival;

    if (v2.type == VAL_STR)
        uni2 = cnbe_utf8_decode(v2.sval, &adv2);
    else
        uni2 = (uint32_t)v2.ival;

    uint32_t code1 = cnhe_map(uni1);
    uint32_t code2 = cnhe_map(uni2);
    uint32_t dist = cnhe_cmp(code1, code2);

    cnbe_puts("语义距离: ");
    cnbe_putint((long)dist);
    cnbe_putc('\n');

    cnbe_puts("  字1 部首: ");
    cnbe_putint((long)cnhe_extract(code1, 0));
    cnbe_puts(" 笔画: ");
    cnbe_putint((long)cnhe_extract(code1, 1));
    cnbe_puts(" 结构: ");
    cnbe_putint((long)cnhe_extract(code1, 2));
    cnbe_putc('\n');

    cnbe_puts("  字2 部首: ");
    cnbe_putint((long)cnhe_extract(code2, 0));
    cnbe_puts(" 笔画: ");
    cnbe_putint((long)cnhe_extract(code2, 1));
    cnbe_puts(" 结构: ");
    cnbe_putint((long)cnhe_extract(code2, 2));
    cnbe_putc('\n');
}

/* 阅读命令: 阅读 [章节号] */
static void cmd_read(const char *p)
{
    p = skip_ws(p);

    int chapter = -1; /* 默认随机输出 */
    if (is_digit(*p)) {
        chapter = 0;
        while (is_digit(*p)) {
            chapter = chapter * 10 + (*p - '0');
            p++;
        }
    }

    cnbe_puts("=== 道德经 ===\n");

    if (chapter >= 0) {
        /* 输出指定章节 (循环) */
        int count = 0;
        const char **ptr = daodejing;
        while (*ptr) {
            if (count == chapter) {
                cnbe_puts(*ptr);
                cnbe_putc('\n');
                return;
            }
            ptr++;
            count++;
        }
        cnbe_puts("章节号超出范围\n");
    } else {
        /* 输出全部 */
        const char **ptr = daodejing;
        int line = 1;
        while (*ptr) {
            cnbe_putint(line);
            cnbe_puts(". ");
            cnbe_puts(*ptr);
            cnbe_putc('\n');
            ptr++;
            line++;
        }
    }
}

/* 帮助命令 */
static void cmd_help(void)
{
    cnbe_puts("=== 中文 BASIC 帮助 ===\n");
    cnbe_puts("关键字:\n");
    cnbe_puts("  输出 <表达式>       输出值或字符串\n");
    cnbe_puts("  变量 <名> = <值>    赋值变量\n");
    cnbe_puts("  如果 <条件> 语句    条件判断\n");
    cnbe_puts("  否则 <语句>         否则分支\n");
    cnbe_puts("  循环 <名> = <起> 到 <终> 循环体 直到\n");
    cnbe_puts("  当 <条件> 语句      当循环\n");
    cnbe_puts("  函数 <名>(参数) = <表达式>  定义函数\n");
    cnbe_puts("  返回 <表达式>       从函数返回\n");
    cnbe_puts("  取编码 \"字\"         获取CNBE-32编码\n");
    cnbe_puts("  取部首 \"字\"         取部首码\n");
    cnbe_puts("  比较 \"字1\" \"字2\"   比较两字语义距离\n");
    cnbe_puts("  阅读 [章节号]       阅读道德经\n");
    cnbe_puts("  帮助                显示此帮助\n");
    cnbe_puts("  退出                退出解释器\n");
    cnbe_puts("  注释...             注释行\n");
    cnbe_puts("\n");
    cnbe_puts("程序模式:\n");
    cnbe_puts("  10 输出 \"你好\"      带行号的程序行\n");
    cnbe_puts("  运行                 执行已存储的程序\n");
    cnbe_puts("  列表                 列出程序\n");
    cnbe_puts("\n");
    cnbe_puts("变量: 支持中文变量名(甲乙丙...)和英文(A-Z)\n");
    cnbe_puts("表达式: + - * / % ( ) 及比较运算\n");
    cnbe_puts("字符串: \"...\" 可用 + 拼接\n");
}

/* 列出程序 */
static void cmd_list(void)
{
    int i;
    for (i = 0; i < prog_count; i++) {
        if (prog_lines[i].active) {
            cnbe_putint(prog_lines[i].lineno);
            cnbe_putc(' ');
            cnbe_puts(prog_lines[i].text);
            cnbe_putc('\n');
        }
    }
}

/* 添加/替换程序行 */
static void add_prog_line(int lineno, const char *text)
{
    int i;
    /* 查找是否已有此行号 */
    for (i = 0; i < prog_count; i++) {
        if (prog_lines[i].active && prog_lines[i].lineno == lineno) {
            /* 替换 */
            cnbe_strncpy(prog_lines[i].text, text, MAX_LINE_LEN - 1);
            prog_lines[i].text[MAX_LINE_LEN - 1] = '\0';
            return;
        }
    }

    /* 新增 */
    if (prog_count < MAX_PROG_LINES) {
        prog_lines[prog_count].lineno = lineno;
        prog_lines[prog_count].active = 1;
        cnbe_strncpy(prog_lines[prog_count].text, text, MAX_LINE_LEN - 1);
        prog_lines[prog_count].text[MAX_LINE_LEN - 1] = '\0';
        prog_count++;
    }
}

/* 程序排序 (按行号) */
static void sort_prog_lines(void)
{
    int i, j;
    for (i = 0; i < prog_count - 1; i++) {
        for (j = 0; j < prog_count - i - 1; j++) {
            if (prog_lines[j].lineno > prog_lines[j + 1].lineno) {
                struct cnbe_prog_line tmp;
                tmp = prog_lines[j];
                prog_lines[j] = prog_lines[j + 1];
                prog_lines[j + 1] = tmp;
            }
        }
    }
}

/* 执行单行程序语句 */
static int exec_prog_line(const char *text)
{
    /* 直接调用 eval, 返回是否有返回语句 */
    cnbe_basic_eval(text);
    return 0;
}

/* 运行已存储的程序 */
static void cmd_run(void)
{
    int i;
    sort_prog_lines();

    /* 循环状态 */
    int loop_stack_depth = 0;
    struct {
        int var_idx;
        long start, end, step;
        int body_lineno;
    } loop_stack[16];
    int loop_sp = 0;

    i = 0;
    while (i < prog_count) {
        if (!prog_lines[i].active) {
            i++;
            continue;
        }

        const char *text = prog_lines[i].text;
        const char *p = skip_ws(text);

        /* 检查循环结束关键字 "直到" */
        int kwlen;
        if ((kwlen = match_kw(p, "直到"))) {
            if (loop_sp > 0) {
                /* 增加循环变量 */
                int vidx = loop_stack[loop_sp - 1].var_idx;
                if (vidx >= 0 && vidx < var_count) {
                    vars[vidx].ival += loop_stack[loop_sp - 1].step;
                    long cur = vars[vidx].ival;
                    long end = loop_stack[loop_sp - 1].end;
                    long step = loop_stack[loop_sp - 1].step;

                    int continue_loop = 0;
                    if (step > 0 && cur <= end) continue_loop = 1;
                    if (step < 0 && cur >= end) continue_loop = 1;

                    if (continue_loop) {
                        /* 跳回循环体开始 */
                        i = loop_stack[loop_sp - 1].body_lineno;
                        continue;
                    } else {
                        /* 循环结束 */
                        loop_sp--;
                    }
                }
            }
            i++;
            continue;
        }

        /* 检查循环关键字 "循环" */
        if ((kwlen = match_kw(p, "循环"))) {
            p += kwlen;
            p = skip_ws(p);

            /* 解析: 变量 = 起 到 终 [步长 N] */
            char vname[MAX_VAR_NAME];
            int vnamelen = read_identifier(p, vname, MAX_VAR_NAME);
            if (vnamelen == 0) {
                cnbe_puts("语法错误: 循环缺少变量名\n");
                return;
            }
            p += vnamelen;
            p = skip_ws(p);

            if (*p != '=') {
                cnbe_puts("语法错误: 循环缺少等号\n");
                return;
            }
            p++;

            /* 起始值 */
            struct expr_ctx ctx;
            ctx.p = p;
            ctx.error = 0;
            struct cnbe_value v = eval_expr(&ctx);
            long start = val_to_int(&v, 0);
            p = ctx.p;
            p = skip_ws(p);

            /* 期望 "到" */
            if (!(kwlen = match_kw(p, "到"))) {
                cnbe_puts("语法错误: 循环缺少'到'\n");
                return;
            }
            p += kwlen;

            /* 终止值 */
            ctx.p = p;
            ctx.error = 0;
            v = eval_expr(&ctx);
            long end = val_to_int(&v, 0);
            p = ctx.p;
            p = skip_ws(p);

            /* 可选步长 */
            long step = 1;
            if ((kwlen = match_kw(p, "步长"))) {
                p += kwlen;
                ctx.p = p;
                ctx.error = 0;
                v = eval_expr(&ctx);
                step = val_to_int(&v, 0);
                p = ctx.p;
            }

            /* 设置循环变量 */
            set_var_int(vname, start);

            /* 压入循环栈 */
            if (loop_sp < 16) {
                int vidx = find_var(vname);
                loop_stack[loop_sp].var_idx = vidx;
                loop_stack[loop_sp].start = start;
                loop_stack[loop_sp].end = end;
                loop_stack[loop_sp].step = step;
                loop_stack[loop_sp].body_lineno = i + 1; /* 下一条语句 */
                loop_sp++;
            }

            i++;
            continue;
        }

        /* 当循环: 当 条件 ... 直到 */
        if ((kwlen = match_kw(p, "当"))) {
            /* 简化: 记录条件位置和循环体起始 */
            /* 在简化版中, 只支持单行当循环 */
            p += kwlen;
            struct expr_ctx ctx;
            ctx.p = p;
            ctx.error = 0;
            struct cnbe_value cond = eval_expr(&ctx);
            long result = val_to_int(&cond, 0);

            if (ctx.error) {
                cnbe_puts("语法错误: 当循环条件错误\n");
                return;
            }

            if (result) {
                /* 执行循环体 */
                p = ctx.p;
                p = skip_ws(p);
                int kwlen2;
                if ((kwlen2 = match_kw(p, "执行")))
                    p += kwlen2;
                p = skip_ws(p);
                cnbe_basic_eval(p);
                /* 重新执行此行 (简化版, 可能死循环) */
                continue;
            }
            i++;
            continue;
        }

        /* 普通语句 */
        exec_prog_line(text);
        i++;
    }
}

/* ========== 主接口 ========== */

/* 评估一行输入 */
int cnbe_basic_eval(const char *line)
{
    const char *p;
    int kwlen;
    int lineno = 0;

    if (!line)
        return 0;

    p = skip_ws(line);

    /* 空行 */
    if (*p == '\0' || *p == '\n' || *p == '\r')
        return 0;

    /* 注释: 注 或 ' 开头 */
    if ((kwlen = match_kw(p, "注释")) || *p == '\'') {
        return 0;
    }

    /* 检查行号: 如果以数字开头, 存为程序行 */
    if (is_digit(*p)) {
        lineno = 0;
        while (is_digit(*p)) {
            lineno = lineno * 10 + (*p - '0');
            p++;
        }
        p = skip_ws(p);

        if (*p == '\0' || *p == '\n' || *p == '\r') {
            /* 只有行号, 删除该行 */
            int i;
            for (i = 0; i < prog_count; i++) {
                if (prog_lines[i].active && prog_lines[i].lineno == lineno) {
                    prog_lines[i].active = 0;
                    break;
                }
            }
            return 0;
        }

        /* 存储程序行 */
        add_prog_line(lineno, p);
        return 0;
    }

    /* 运行命令 */
    if ((kwlen = match_kw(p, "运行"))) {
        cmd_run();
        return 0;
    }

    /* 列表命令 */
    if ((kwlen = match_kw(p, "列表"))) {
        cmd_list();
        return 0;
    }

    /* 清除命令 */
    if ((kwlen = match_kw(p, "清除"))) {
        prog_count = 0;
        var_count = 0;
        func_count = 0;
        cnbe_puts("已清除所有程序和变量\n");
        return 0;
    }

    /* 输出命令 */
    if ((kwlen = match_kw(p, "输出"))) {
        cmd_print(p + kwlen);
        return 0;
    }

    /* 变量赋值命令 */
    if ((kwlen = match_kw(p, "变量"))) {
        cmd_let(p + kwlen);
        return 0;
    }

    /* 如果命令 */
    if ((kwlen = match_kw(p, "如果"))) {
        cmd_if(p + kwlen);
        return 0;
    }

    /* 否则命令 (单独行, 通常在程序模式中) */
    if ((kwlen = match_kw(p, "否则"))) {
        return 0;
    }

    /* 循环命令 */
    if ((kwlen = match_kw(p, "循环"))) {
        /* 在程序模式下由 cmd_run 处理 */
        /* 在直接模式下, 不支持 */
        cnbe_puts("提示: 循环需在程序模式中使用\n");
        return 0;
    }

    /* 直到命令 */
    if ((kwlen = match_kw(p, "直到"))) {
        /* 在程序模式下由 cmd_run 处理 */
        return 0;
    }

    /* 当命令 */
    if ((kwlen = match_kw(p, "当"))) {
        /* 简化: 直接模式也可用单行当循环 */
        p += kwlen;
        struct expr_ctx ctx;
        ctx.p = p;
        ctx.error = 0;
        struct cnbe_value cond = eval_expr(&ctx);
        long result = val_to_int(&cond, 0);

        if (ctx.error) {
            cnbe_puts("语法错误: 当循环条件错误\n");
            return 1;
        }

        p = ctx.p;
        p = skip_ws(p);
        int kwlen2;
        if ((kwlen2 = match_kw(p, "执行")))
            p += kwlen2;
        p = skip_ws(p);

        if (result) {
            cnbe_basic_eval(p);
        }
        return 0;
    }

    /* 函数定义命令 */
    if ((kwlen = match_kw(p, "函数"))) {
        cmd_def(p + kwlen);
        return 0;
    }

    /* 返回命令 */
    if ((kwlen = match_kw(p, "返回"))) {
        /* 在直接模式下, 返回就是退出当前表达式 */
        return 1;
    }

    /* 取编码命令 */
    if ((kwlen = match_kw(p, "取编码"))) {
        cmd_cnbe(p + kwlen);
        return 0;
    }

    /* 取部首命令 */
    if ((kwlen = match_kw(p, "取部首"))) {
        cmd_radical(p + kwlen);
        return 0;
    }

    /* 比较命令 */
    if ((kwlen = match_kw(p, "比较"))) {
        cmd_cmp(p + kwlen);
        return 0;
    }

    /* 阅读命令 */
    if ((kwlen = match_kw(p, "阅读"))) {
        cmd_read(p + kwlen);
        return 0;
    }

    /* 帮助命令 */
    if ((kwlen = match_kw(p, "帮助"))) {
        cmd_help();
        return 0;
    }

    /* 退出命令 */
    if ((kwlen = match_kw(p, "退出"))) {
        return -1;
    }

    /* 尝试作为隐式赋值 (甲 = 42, 不需要 变量 前缀) */
    {
        char name[MAX_VAR_NAME];
        const char *save_p = p;
        int namelen = read_identifier(p, name, MAX_VAR_NAME);
        if (namelen > 0) {
            const char *p2 = p + namelen;
            p2 = skip_ws(p2);
            if (*p2 == '=') {
                /* 隐式赋值 */
                cmd_let(save_p);
                return 0;
            }
        }
    }

    /* 未知命令 */
    cnbe_puts("语法错误: 未知命令 \"");
    cnbe_puts(line);
    cnbe_puts("\"\n");
    cnbe_puts("输入 \"帮助\" 查看可用命令\n");

    return 0;
}

/* 运行交互式解释器 (非 shell 入口, 供内核调用) */
void cnbe_basic_run(void)
{
    cnbe_puts("\n");
    cnbe_puts("=== 中文 BASIC 解释器 ===\n");
    cnbe_puts("输入 \"帮助\" 查看命令列表, \"退出\" 退出\n");
    cnbe_puts("\n");
}
