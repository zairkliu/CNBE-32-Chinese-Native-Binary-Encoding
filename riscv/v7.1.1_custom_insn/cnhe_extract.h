// cnhe_extract.h — cnhe.extract instruction: Extract field from CNBE code
// rd = cnhe_extract(rs1, rs2)
// Input:  rs1 = 32-bit CNBE code, rs2 = field selector (0/1/2)
// Output: rd = extracted field value
// Custom-0 opcode=0x0B, funct3=1
// MATCH=0x0000100B, MASK=0xFE00707F

require_extension("C");

uint32_t code = (uint32_t)RS1;
uint64_t sel = RS2;
uint64_t result = 0;

switch (sel) {
    case 0:  // Radical (bits 31:24, 8-bit radical ID)
        result = (code >> 24) & 0xFF;
        break;
    case 1:  // Stroke count (bits 23:19, 5-bit, 0-31)
        result = (code >> 19) & 0x1F;
        break;
    case 2:  // Structure type (bits 18:15, 4-bit, 0-15)
        result = (code >> 15) & 0x0F;
        break;
    default:
        result = 0;
        break;
}

STATE->cnbe_cycle_counter++;
STATE->cnbe_inst_extract_count++;
WRITE_RD(result);
