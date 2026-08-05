/* CNBE-32 runtime implementation - Linux 0.01 RISC-V port.
 * Aligned to the v8 ISA semantics and generated from data/cnbe32.db. */

#include <stdint.h>
#include "cnbe.h"
#include "cnbe_table_data.h"

static int cnbe_initialized = 0;

void cnbe_init(void)
{
    cnbe_initialized = 1;
}

/* cnbe.map: Unicode -> CNBE-32 via binary search. */
uint32_t cnbe_map(uint32_t unicode)
{
    int lo = 0, hi = (int)CNBE_KERNEL_TABLE_SIZE - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        uint32_t value = cnbe_kernel_unicode_table[mid];
        if (value == unicode)
            return cnbe_kernel_skill_table[mid];
        if (value < unicode)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    return 0;
}

/* cnbe.extract: field selector 0..4. */
uint32_t cnbe_extract(uint32_t code, uint32_t selector)
{
    switch (selector) {
    case 0: return (code >> CNBE_RADIX_SHIFT) & CNBE_RADIX_MASK;
    case 1: return (code >> CNBE_STROKE_SHIFT) & CNBE_STROKE_MASK;
    case 2: return (code >> CNBE_STRUCT_SHIFT) & CNBE_STRUCT_MASK;
    case 3: return (code >> CNBE_INDEX_SHIFT) & CNBE_INDEX_MASK;
    case 4: return code & CNBE_EXT_MASK;
    default: return 0;
    }
}

/* cnbe.cmp: SDK weights 8/5/4. */
uint32_t cnbe_cmp(uint32_t a, uint32_t b)
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

/* cnbe.skill: reverse lookup, first match in Unicode order. */
uint32_t cnbe_skill(uint32_t code)
{
    unsigned int i;
    for (i = 0; i < CNBE_KERNEL_TABLE_SIZE; i++) {
        if (cnbe_kernel_skill_table[i] == code)
            return cnbe_kernel_unicode_table[i];
    }
    return 0;
}

/* Decode the first UTF-8 character. */
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

/* Legacy alias for cnbe_skill. */
uint32_t cnbe_reverse_lookup(uint32_t cnbe_code)
{
    return cnbe_skill(cnbe_code);
}

/* Chinese kernel message output. */
void cnbe_printk(const char *cn_msg)
{
    (void)cn_msg;
}

/* UTF-8 string compare. */
int cnbe_strcmp(const char *a, const char *b)
{
    while (*a && (*a == *b)) {
        a++;
        b++;
    }
    return (unsigned char)*a - (unsigned char)*b;
}
