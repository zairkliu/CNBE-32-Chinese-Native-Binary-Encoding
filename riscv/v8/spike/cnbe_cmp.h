// cnbe.cmp rd, rs1, rs2 -- SDK-aligned field-weighted distance
// Custom-0 opcode=0x0B, funct3=2, MATCH=0x0000200B
#include "cnbe_skill_table.h"
uint32_t c1 = (uint32_t)RS1;
uint32_t c2 = (uint32_t)RS2;
uint32_t r1 = (c1 >> 24) & 0xFF, r2 = (c2 >> 24) & 0xFF;
uint32_t s1 = (c1 >> 19) & 0x1F, s2 = (c2 >> 19) & 0x1F;
uint32_t t1 = (c1 >> 15) & 0x0F, t2 = (c2 >> 15) & 0x0F;
uint32_t dr = r1 > r2 ? r1 - r2 : r2 - r1;
uint32_t ds = s1 > s2 ? s1 - s2 : s2 - s1;
uint32_t dt = t1 > t2 ? t1 - t2 : t2 - t1;
WRITE_RD((reg_t)(dr * 8 + ds * 5 + dt * 4));
