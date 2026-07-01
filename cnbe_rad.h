// cnbe_rad.h — Extract radical field (bits 31:24) from CNBE-32 code
// Format: cnbe.rad rd, rs1
// Uses Custom-0 (opcode=0x0b, funct3=2, MATCH=0x0020000b)
require_extension('C');
uint32_t code = (uint32_t)RS1;
WRITE_RD((reg_t)((code >> 24) & 0xFF));
