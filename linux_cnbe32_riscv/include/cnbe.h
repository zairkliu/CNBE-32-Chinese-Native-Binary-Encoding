/*
 * CNBE-32 (Chinese Native Binary Encoding) runtime header
 * RISC-V port, aligned to the v8 ISA semantics.
 *
 * The four operations mirror the v8 custom instructions:
 *   cnbe_map     -> cnbe.map
 *   cnbe_extract -> cnbe.extract
 *   cnbe_cmp     -> cnbe.cmp
 *   cnbe_skill   -> cnbe.skill
 */

#ifndef _CNBE_H
#define _CNBE_H

#include <stdint.h>

/* CNBE-32 bit-field layout (v8) */
/* [31:24] radix (8) | [23:19] stroke (5) | [18:15] struct (4) |
 * [14:4] index (11) | [3:0] ext (4) */

#define CNBE_RADIX_SHIFT    24
#define CNBE_STROKE_SHIFT   19
#define CNBE_STRUCT_SHIFT   15
#define CNBE_INDEX_SHIFT    4

#define CNBE_RADIX_MASK     0xFF
#define CNBE_STROKE_MASK    0x1F
#define CNBE_STRUCT_MASK    0x0F
#define CNBE_INDEX_MASK     0x7FF
#define CNBE_EXT_MASK       0x0F

/* Structure labels follow GF 0017-2013 13-label numbering. */
enum cnbe_structure {
    STRUCT_DUOTI   = 0,  /* 独体 */
    STRUCT_ZUOYOU  = 1,  /* 左右 */
    STRUCT_ZUOZHOYO= 2,  /* 左中右 */
    STRUCT_SHANGXIA= 3,  /* 上下 */
    STRUCT_SHANGZHONGXIA = 4, /* 上中下 */
    STRUCT_ZUOSHANGBAO = 5,   /* 左上包围 */
    STRUCT_YOUSHANGBAO = 6,   /* 右上包围 */
    STRUCT_ZUOXIBAO = 7,      /* 左下包围 */
    STRUCT_SHANGBAO = 8,      /* 上包围 */
    STRUCT_XIABAO   = 9,      /* 下包围 */
    STRUCT_ZUOBAO   = 10,     /* 左包围 */
    STRUCT_QUANBAO  = 11,     /* 全包围 */
    STRUCT_PINZI    = 12,     /* 品字 */
};

/* Initialize the runtime skill table. */
extern void cnbe_init(void);

/* Unicode -> CNBE-32 (cnbe.map). Returns 0 when not found. */
extern uint32_t cnbe_map(uint32_t unicode);

/* Field extraction (cnbe.extract).
 * selector: 0=radix, 1=stroke, 2=struct, 3=index, 4=ext. */
extern uint32_t cnbe_extract(uint32_t code, uint32_t selector);

/* SDK-aligned field-weighted distance (cnbe.cmp):
 * |rad1-rad2|*8 + |stroke1-stroke2|*5 + |struct1-struct2|*4 */
extern uint32_t cnbe_cmp(uint32_t a, uint32_t b);

/* CNBE -> Unicode reverse lookup (cnbe.skill). First match in Unicode order. */
extern uint32_t cnbe_skill(uint32_t code);

/* Decode the first UTF-8 character from a string. */
extern uint32_t cnbe_utf8_decode(const char *s, int *advance);

/* Legacy alias for cnbe_skill. */
extern uint32_t cnbe_reverse_lookup(uint32_t cnbe_code);

/* Chinese kernel message output. */
extern void cnbe_printk(const char *cn_msg);

/* UTF-8 string compare used by the kernel filesystem. */
extern int cnbe_strcmp(const char *a, const char *b);

/* Chinese kernel message macros. */
#define CNBE_MSG_PANIC      "【内核恐慌】"
#define CNBE_MSG_TRAP       "【陷阱处理】"
#define CNBE_MSG_SCHED      "【调度器】"
#define CNBE_MSG_FORK       "【进程创建】"
#define CNBE_MSG_EXIT       "【进程退出】"
#define CNBE_MSG_SYS        "【系统调用】"
#define CNBE_MSG_TIME       "【时间子系统】"
#define CNBE_MSG_WARN       "【警告】"
#define CNBE_MSG_FATAL      "【致命错误】"

#endif
