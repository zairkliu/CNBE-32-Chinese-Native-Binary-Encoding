#include <stdio.h>
#include <stdint.h>
#include "cnbe_runtime.h"
#include "skill_table_data.h"

uint32_t cnhe_map(uint32_t unicode) {
    if (unicode < 0x4E00 || unicode > 0x9FA5) return 0;
    uint32_t idx = unicode - 0x4E00;
    if (idx >= SKILL_TABLE_SIZE) return 0;
    return skill_table[idx];
}

uint32_t cnhe_extract(uint32_t code, uint32_t field) {
    switch (field) {
        case 0: return (code >> 24) & 0xFF;
        case 1: return (code >> 19) & 0x1F;
        case 2: return (code >> 15) & 0xF;
        default: return 0;
    }
}

uint32_t cnhe_cmp(uint32_t a, uint32_t b) {
    uint32_t ra=(a>>24)&0xFF, rb=(b>>24)&0xFF;
    uint32_t sa=(a>>19)&0x1F, sb=(b>>19)&0x1F;
    uint32_t ta=(a>>15)&0xF, tb=(b>>15)&0xF;
    return (ra>rb?(ra-rb)*8:(rb-ra)*8)+(sa>sb?(sa-sb)*5:(sb-sa)*5)+(ta>tb?(ta-tb)*4:(tb-ta)*4);
}

int cnhe_compare_chars(uint32_t ua, uint32_t ub) {
    uint32_t ca=cnhe_map(ua), cb=cnhe_map(ub);
    if (ca==0||cb==0) return -1;
    return (int)cnhe_cmp(ca, cb);
}
