// cnbe_str.h — Extract strokes field (bits 23:19) from CNBE-32 code
// Format: cnbe.str rd, rs1
// Uses Custom-0 (opcode=0x0b, funct3=3, MATCH=0x0030000b)
require_extension('C');
uint32_t code = (uint32_t)RS1;
WRITE_RD((reg_t)((code >> 19) & 0x1F));
