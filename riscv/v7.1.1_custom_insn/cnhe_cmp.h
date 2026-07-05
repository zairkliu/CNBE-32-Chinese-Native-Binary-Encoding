// cnhe_cmp.h — cnhe.cmp instruction: Compare two CNBE codes
// rd = cnhe_cmp(rs1, rs2)
// Input:  rs1, rs2 = 32-bit CNBE codes
// Output: rd = weighted absolute difference distance
// Custom-0 opcode=0x0B, funct3=2
// MATCH=0x0000200B, MASK=0xFE00707F
//
// Distance = |rad1-rad2|*4 + |str1-str2|*2 + |stc1-stc2|*1

require_extension("C");

uint32_t c1 = (uint32_t)RS1;
uint32_t c2 = (uint32_t)RS2;

uint32_t r1 = (c1 >> 24) & 0xFF, r2 = (c2 >> 24) & 0xFF;
uint32_t s1 = (c1 >> 19) & 0x1F, s2 = (c2 >> 19) & 0x1F;
uint32_t t1 = (c1 >> 15) & 0x0F, t2 = (c2 >> 15) & 0x0F;

uint32_t rd = (r1 > r2 ? r1 - r2 : r2 - r1) * 4;
rd += (s1 > s2 ? s1 - s2 : s2 - s1) * 2;
rd += (t1 > t2 ? t1 - t2 : t2 - t1);

STATE->cnbe_cycle_counter += 3;
STATE->cnbe_inst_cmp_count++;
WRITE_RD(rd);
