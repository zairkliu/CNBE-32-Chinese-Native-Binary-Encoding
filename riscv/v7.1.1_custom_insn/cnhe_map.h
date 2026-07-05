// cnhe_map.h — cnhe.map instruction: Map Unicode to CNBE encoding
// rd = cnhe_map(rs1)
// Input:  rs1 = Unicode code point (U+4E00~U+9FA5)
// Output: rd = 32-bit CNBE encoding code
// Custom-0 opcode=0x0B, funct3=0
// MATCH=0x0000000B, MASK=0xFE00707F

require_extension("C");

uint64_t unicode = RS1;
uint32_t cnbe_code = 0;

if (unicode >= 0x4E00 && unicode <= 0x9FA5) {
    uint32_t index = unicode - 0x4E00;
    if (index < CNBE_TABLE_SIZE) {
        cnbe_code = cnbe_skill_table[index];
    }
}

STATE->cnbe_cycle_counter += 2;
STATE->cnbe_inst_map_count++;
WRITE_RD(cnbe_code);
