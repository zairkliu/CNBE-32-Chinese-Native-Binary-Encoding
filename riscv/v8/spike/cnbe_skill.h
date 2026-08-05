// cnbe.skill rd, rs1 -- CNBE -> Unicode reverse lookup (first match)
// Custom-0 opcode=0x0B, funct3=3, MATCH=0x0000300B
#include "cnbe_skill_table.h"
uint32_t code = (uint32_t)RS1;
uint32_t result = 0;
for (size_t i = 0; i < CNBE_TABLE_SIZE; i++) {
    if (cnbe_skill_table[i] == code) {
        result = cnbe_unicode_table[i];
        break;
    }
}
WRITE_RD((reg_t)result);
