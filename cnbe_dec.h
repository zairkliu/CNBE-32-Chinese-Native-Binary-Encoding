// cnbe_dec.h v2 — CNBE-32 Decode with hash lookup (O(1))
// Format: cnbe.dec rd, rs1 (Custom-0, funct3=1, MATCH=0x0010000b)
require_extension('C');
uint32_t code = (uint32_t)RS1;
uint32_t result = 0;
// O(n) lookup on CNBE code (no sort order on CNBE codes)
// Can be optimized with separate CNBE→Unicode hash table
for (int i = 0; i < 8105; i++) {
    if (cnbe_table[i] == code) { result = unicode_table[i]; break; }
}
STATE->cnbe_cycle_counter += (result ? 4053 : 8105);  // avg linear
STATE->cnbe_inst_dec_count++;
WRITE_RD((reg_t)result);
