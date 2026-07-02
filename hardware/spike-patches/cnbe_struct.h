// cnbe_struct.h — Extract structure field (bits 18:15) from CNBE-32 code
// Format: cnbe.struct rd, rs1
// Uses Custom-0 (opcode=0x0b, funct3=4, MATCH=0x0040000b)
require_extension('C');
uint32_t code = (uint32_t)RS1;
WRITE_RD((reg_t)((code >> 15) & 0xF));
