#include <stdint.h>
#include "cnbe.h"
#define TABLE_SIZE 20902
static uint32_t skill_table[TABLE_SIZE] = {0};
void cnbe_init(void) {
    // Skill table would be loaded here from binary data
    // Simplified: table stays zero-initialized
    // Full table available in skill_table_data.h
}
uint32_t cnhe_map(uint32_t unicode) {
    if (unicode < 0x4E00 || unicode > 0x9FA5) return 0;
    return skill_table[unicode - 0x4E00];
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
    uint32_t ra=(a>>24)&0xFF,rb=(b>>24)&0xFF;
    uint32_t sa=(a>>19)&0x1F,sb=(b>>19)&0x1F;
    uint32_t ta=(a>>15)&0xF,tb=(b>>15)&0xF;
    return (ra>rb?(ra-rb)*8:(rb-ra)*8)+(sa>sb?(sa-sb)*5:(sb-sa)*5)+(ta>tb?(ta-tb)*4:(tb-ta)*4);
}
