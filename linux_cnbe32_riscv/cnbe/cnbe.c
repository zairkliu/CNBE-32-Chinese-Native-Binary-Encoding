/* CNBE-32 运行时实现 —— Linux 0.01 RISC-V 版本
 * 基于仓库 v84_riscv_os_full/src/basic/cnbe.c 的基本编码思路扩展
 */

#include <stdint.h>
#include "cnbe.h"
#include "cnbe_table_data.h"  /* 自动生成的 20902 条目 skill 表 */

/* 81.6 KB Skill 表 — 可完全放入 32MB L3 Cache，查表延迟 1-2 周期 @ 1GHz */
static uint32_t cnbe_skill_table[CJK_TABLE_SIZE] __attribute__((aligned(4096)));
static int cnbe_initialized = 0;

/* 简化的 Skill 表加载 (实际系统中从只读段或初始化数据加载) */
void cnbe_init(void)
{
    int i;
    if (cnbe_initialized)
        return;
    /* 从预编译的 skill_table 数据初始化 (tools/gen_cnbe_table.py 生成)。
     * 数据位于 .rodata 段，启动时复制到对齐的运行时表中。 */
    for (i = 0; i < CJK_TABLE_SIZE; i++) {
        cnbe_skill_table[i] = cnbe_skill_table_data[i];
    }
    cnbe_initialized = 1;
}

/* cnhe.map: Unicode -> CNBE-32 */
uint32_t cnhe_map(uint32_t unicode)
{
    if (unicode < CJK_START_UNICODE || unicode > CJK_END_UNICODE)
        return 0;
    return cnbe_skill_table[unicode - CJK_START_UNICODE];
}

/* cnhe.extract: 位域提取 */
uint32_t cnhe_extract(uint32_t code, uint32_t field)
{
    switch (field) {
    case 0: return (code >> CNBE_RADIX_SHIFT) & CNBE_RADIX_MASK;   /* 部首 */
    case 1: return (code >> CNBE_STROKE_SHIFT) & CNBE_STROKE_MASK; /* 笔画 */
    case 2: return (code >> CNBE_STRUCT_SHIFT) & CNBE_STRUCT_MASK; /* 结构 */
    default: return 0;
    }
}

/* cnhe.cmp: 加权语义距离 (部首×8 + 笔画×5 + 结构×4) */
uint32_t cnhe_cmp(uint32_t a, uint32_t b)
{
    uint32_t ra = (a >> CNBE_RADIX_SHIFT) & CNBE_RADIX_MASK;
    uint32_t rb = (b >> CNBE_RADIX_SHIFT) & CNBE_RADIX_MASK;
    uint32_t sa = (a >> CNBE_STROKE_SHIFT) & CNBE_STROKE_MASK;
    uint32_t sb = (b >> CNBE_STROKE_SHIFT) & CNBE_STROKE_MASK;
    uint32_t ta = (a >> CNBE_STRUCT_SHIFT) & CNBE_STRUCT_MASK;
    uint32_t tb = (b >> CNBE_STRUCT_SHIFT) & CNBE_STRUCT_MASK;

    uint32_t dr = (ra > rb) ? (ra - rb) : (rb - ra);
    uint32_t ds = (sa > sb) ? (sa - sb) : (sb - sa);
    uint32_t dt = (ta > tb) ? (ta - tb) : (tb - ta);

    return dr * 8 + ds * 5 + dt * 4;
}

/* UTF-8 解码: 提取第一个汉字 Unicode 码点 */
uint32_t cnbe_utf8_decode(const char *s, int *advance)
{
    unsigned char c0 = (unsigned char)s[0];
    uint32_t code = 0;
    int len = 1;

    if (c0 < 0x80) {
        code = c0;
    } else if ((c0 & 0xE0) == 0xC0) {
        code = ((c0 & 0x1F) << 6) | ((unsigned char)s[1] & 0x3F);
        len = 2;
    } else if ((c0 & 0xF0) == 0xE0) {
        code = ((c0 & 0x0F) << 12)
             | (((unsigned char)s[1] & 0x3F) << 6)
             | ((unsigned char)s[2] & 0x3F);
        len = 3;
    } else if ((c0 & 0xF8) == 0xF0) {
        code = ((c0 & 0x07) << 18)
             | (((unsigned char)s[1] & 0x3F) << 12)
             | (((unsigned char)s[2] & 0x3F) << 6)
             | ((unsigned char)s[3] & 0x3F);
        len = 4;
    }

    if (advance)
        *advance = len;
    return code;
}

/* CNBE-32 反查 (线性搜索，仅用于小数据量显示场景) */
uint32_t cnbe_reverse_lookup(uint32_t cnbe_code)
{
    int i;
    for (i = 0; i < CJK_TABLE_SIZE; i++) {
        if (cnbe_skill_table[i] == cnbe_code)
            return CJK_START_UNICODE + i;
    }
    return 0;
}

/* 中文内核消息输出 (UTF-8 直通 UART) */
void cnbe_printk(const char *cn_msg)
{
    /* 在完整系统中通过 UART 输出 UTF-8 字符串
     * 此处为桩函数，实际由 tty_io.c / console.c 实现 */
    (void)cn_msg;
}

/* 编码字符串比较 (支持 UTF-8 中文) */
int cnbe_strcmp(const char *a, const char *b)
{
    while (*a && (*a == *b)) {
        a++;
        b++;
    }
    return (unsigned char)*a - (unsigned char)*b;
}
