// cnbe_enc.h v2 — CNBE-32 Encode with binary search (O(log n), ~13 cycles)
// Also supports hash-based O(1) lookup via cnbe_hash_index table
// Format: cnbe.enc rd, rs1 (Custom-0, funct3=0, MATCH=0x0000000b)
require_extension('C');
uint32_t ucp = (uint32_t)RS1;
uint32_t result = 0;
#ifdef CNBE_USE_HASH
// Method A: O(1) hash lookup (max 2 comparisons)
int h = ucp & 0x7FFF;
int idx;
idx = cnbe_hash_index[h][0];
if (idx >= 0 && unicode_table[idx] == ucp) { result = cnbe_table[idx]; }
else {
    idx = cnbe_hash_index[h][1];
    if (idx >= 0 && unicode_table[idx] == ucp) { result = cnbe_table[idx]; }
}
STATE->cnbe_cycle_counter += 2;  // hash(1) + 1-2比较(1)
#else
// Method B: O(log n) binary search (13 comparisons max)
int lo = 0, hi = 8104;
while (lo <= hi) {
    int mid = (lo + hi) >> 1;
    if (unicode_table[mid] == ucp) { result = cnbe_table[mid]; break; }
    if (unicode_table[mid] < ucp) lo = mid + 1;
    else hi = mid - 1;
}
STATE->cnbe_cycle_counter += 14;  // ~13次循环+1次判断
#endif
STATE->cnbe_inst_enc_count++;
WRITE_RD((reg_t)result);
