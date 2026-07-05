#include "cnhe_skill_table.h"

// Pre-initialized skill table (83.6KB = 20902 x 4 bytes)
// Full binary data: see riscv/skill_table/skill_table.hex
const uint32_t cnbe_skill_table[CNBE_TABLE_SIZE] = {0};

__attribute__((constructor))
void cnbe_skill_table_init(void) {
    // For standalone compilation, load from .hex or .bin file.
    // When embedded via xxd -i, table is statically initialized.
}
