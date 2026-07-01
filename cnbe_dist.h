// cnbe_dist.h — Compute weighted semantic distance between two CNBE-32 codes
// Distance = 4*popcount(rad^rad2) + 2*popcount(strk^strk2) + 1*popcount(struct^struct2)
// Format: cnbe.dist rd, rs1, rs2
// Uses Custom-0 (opcode=0x0b, funct3=5, MATCH=0x0050000b)
require_extension('C');
uint32_t c1 = (uint32_t)RS1;
uint32_t c2 = (uint32_t)RS2;
uint32_t rad1  = (c1 >> 24) & 0xFF, rad2  = (c2 >> 24) & 0xFF;
uint32_t str1  = (c1 >> 19) & 0x1F, str2  = (c2 >> 19) & 0x1F;
uint32_t sgt1  = (c1 >> 15) & 0xF,  sgt2  = (c2 >> 15) & 0xF;
uint32_t dist  = 4 * __builtin_popcount(rad1 ^ rad2);
dist += 2 * __builtin_popcount(str1 ^ str2);
dist += 1 * __builtin_popcount(sgt1 ^ sgt2);
WRITE_RD((reg_t)dist);
