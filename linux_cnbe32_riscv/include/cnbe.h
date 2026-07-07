/*
 * CNBE-32 (Chinese Native Binary Encoding) 运行时头文件
 * RISC-V 架构移植版本
 * 基于仓库 v84_riscv_os_full/src/basic/cnbe.c 编码思路
 */

#ifndef _CNBE_H
#define _CNBE_H

#include <stdint.h>

/* CNBE-32 位域布局 (CJK 汉字规范 v6.0) */
/* [31:24] 部首区 (8bit) | [23:19] 笔画区 (5bit) | [18:15] 结构区 (4bit) |
 * [14:4] 字库区 (11bit) | [3:0] 扩展区 (4bit) */

#define CNBE_RADIX_SHIFT    24
#define CNBE_STROKE_SHIFT   19
#define CNBE_STRUCT_SHIFT   15
#define CNBE_INDEX_SHIFT    4

#define CNBE_RADIX_MASK     0xFF
#define CNBE_STROKE_MASK    0x1F
#define CNBE_STRUCT_MASK    0x0F
#define CNBE_INDEX_MASK     0x7FF
#define CNBE_EXT_MASK       0x0F

#define CJK_START_UNICODE   0x4E00
#define CJK_END_UNICODE     0x9FA5
#define CJK_TABLE_SIZE      20902

/* 结构类型枚举 */
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

/* 初始化 CNBE-32 查表缓存 (81.6KB 表，可放入 32MB L3 Cache) */
extern void cnbe_init(void);

/* Unicode -> CNBE-32 编码映射 (对应 cnhe.map 指令) */
extern uint32_t cnhe_map(uint32_t unicode);

/* 位域提取 (对应 cnhe.extract 指令)
 * field: 0=部首, 1=笔画, 2=结构 */
extern uint32_t cnhe_extract(uint32_t code, uint32_t field);

/* 加权语义距离 (对应 cnhe.cmp 指令) */
extern uint32_t cnhe_cmp(uint32_t a, uint32_t b);

/* 从 UTF-8 字符串提取第一个汉字的 Unicode 码点 */
extern uint32_t cnbe_utf8_decode(const char *s, int *advance);

/* 将 CNBE-32 编码反查为 Unicode (用于显示) */
extern uint32_t cnbe_reverse_lookup(uint32_t cnbe_code);

/* 中文内核消息输出 (替换 printk 的字符串处理) */
extern void cnbe_printk(const char *cn_msg);

/* 编码字符串比较 (用于中文路径名/文件名) */
extern int cnbe_strcmp(const char *a, const char *b);

/* 中文内核消息宏 */
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
