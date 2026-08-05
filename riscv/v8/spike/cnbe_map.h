// cnbe.map rd, rs1 -- Unicode -> CNBE skill table lookup
// Custom-0 opcode=0x0B, funct3=0, MATCH=0x0000000B
#include "cnbe_skill_table.h"
uint32_t ucp = (uint32_t)RS1;
uint32_t result = 0;
int lo = 0, hi = (int)CNBE_TABLE_SIZE - 1;
while (lo <= hi) {
    int mid = (lo + hi) / 2;
    uint32_t value = cnbe_unicode_table[mid];
    if (value == ucp) {
        result = cnbe_skill_table[mid];
        break;
    }
    if (value < ucp) {
        lo = mid + 1;
    } else {
        hi = mid - 1;
    }
}
WRITE_RD((reg_t)result);
