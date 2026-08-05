// cnbe.extract rd, rs1, rs2 -- extract CNBE field
// Custom-0 opcode=0x0B, funct3=1, MATCH=0x0000100B
#include "cnbe_skill_table.h"
uint32_t code = (uint32_t)RS1;
uint32_t sel = (uint32_t)RS2;
uint32_t result = 0;
switch (sel) {
    case 0: result = (code >> 24) & 0xFF; break;
    case 1: result = (code >> 19) & 0x1F; break;
    case 2: result = (code >> 15) & 0x0F; break;
    case 3: result = (code >> 4) & 0x7FF; break;
    case 4: result = code & 0xF; break;
    default: result = 0; break;
}
WRITE_RD((reg_t)result);
