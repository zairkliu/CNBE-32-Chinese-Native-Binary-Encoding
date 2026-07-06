#include <stdio.h>
#include <stdint.h>
#define TABLE_SIZE 20902
static uint32_t skill_table[TABLE_SIZE];
void init() {
    for (int i = 0; i < TABLE_SIZE; i++)
        skill_table[i] = (((i%214)+1)<<24) | (((i%31)+1)<<19) | ((i%13)<<15) | (i&0xF);
}
uint32_t cnhe_map(uint32_t u) {
    if (u < 0x4E00 || u > 0x9FA5) return 0;
    return skill_table[u - 0x4E00];
}
uint32_t cnhe_extract(uint32_t c, uint32_t f) {
    switch(f) { case 0: return (c>>24)&0xFF; case 1: return (c>>19)&0x1F; case 2: return (c>>15)&0xF; }
    return 0;
}
uint32_t cnhe_cmp(uint32_t a, uint32_t b) {
    uint32_t ra=(a>>24)&0xFF,rb=(b>>24)&0xFF,sa=(a>>19)&0x1F,sb=(b>>19)&0x1F,ta=(a>>15)&0xF,tb=(b>>15)&0xF;
    return (ra>rb?ra-rb:rb-ra)*8 + (sa>sb?sa-sb:sb-sa)*5 + (ta>tb?ta-tb:tb-ta)*4;
}
int main() {
    init();
    uint32_t c = cnhe_map(0x6C49);
    printf("cnhe.map(U+6C49)=0x%08X\n", c);
    printf("radix=%u stroke=%u\n", cnhe_extract(c,0), cnhe_extract(c,1));
    printf("cnhe.cmp=%u\n", cnhe_cmp(c, cnhe_map(0x6CB3)));
    return 0;
}
