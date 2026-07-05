#include <stdint.h>
#include "cnbe_runtime.h"
static uint32_t skill_table[20902] = {0};
uint32_t cnhe_map(uint32_t u) { return (u>=0x4E00&&u<=0x9FA5)?skill_table[u-0x4E00]:0; }
uint32_t cnhe_extract(uint32_t c, uint32_t f) { switch(f) { case 0: return (c>>24)&0xFF; case 1: return (c>>19)&0x1F; case 2: return (c>>15)&0xF; default: return 0; } }
uint32_t cnhe_cmp(uint32_t a, uint32_t b) { uint32_t ra=(a>>24)&0xFF,rb=(b>>24)&0xFF,sa=(a>>19)&0x1F,sb=(b>>19)&0x1F,ta=(a>>15)&0xF,tb=(b>>15)&0xF; return (ra>rb?(ra-rb)*8:(rb-ra)*8)+(sa>sb?(sa-sb)*5:(sb-sa)*5)+(ta>tb?(ta-tb)*4:(tb-ta)*4); }
int cnhe_compare_chars(uint32_t a, uint32_t b) { uint32_t ca=cnhe_map(a),cb=cnhe_map(b); if(!ca||!cb)return -1; return (int)cnhe_cmp(ca,cb); }
