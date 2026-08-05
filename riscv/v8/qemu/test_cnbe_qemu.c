#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../sim/c/cnbe_ref.h"

static int read_u32(FILE *fp, uint32_t *out) {
    char line[256];
    if (!fgets(line, sizeof(line), fp)) {
        return 0;
    }
    char name[64];
    unsigned long u, c, rev;
    unsigned int r, s, t, idx, e, dist;
    if (sscanf(line, "%63s %lx %lx %u %u %u %u %u %lx %u", name, &u, &c, &r,
               &s, &t, &idx, &e, &rev, &dist) != 10) {
        fprintf(stderr, "bad line: %s", line);
        return -1;
    }
    out[0] = (uint32_t)u;   // unicode
    out[1] = (uint32_t)c;   // code
    out[2] = (uint32_t)r;   // radix
    out[3] = (uint32_t)s;   // stroke
    out[4] = (uint32_t)t;   // struct
    out[5] = (uint32_t)idx; // idx
    out[6] = (uint32_t)e;   // ext
    out[7] = (uint32_t)rev; // reverse unicode
    out[8] = (uint32_t)dist; // distance to previous row
    return 1;
}

int main(int argc, char **argv) {
    const char *table_path = argc > 1 ? argv[1] : "generated/skill_table.bin";
    const char *expect_path = argc > 2 ? argv[2] : "golden/qemu_expected.txt";

    CnbeSkillTable table;
    if (cnbe_table_load(&table, table_path) != 0) {
        fprintf(stderr, "FAIL: cannot load skill table\n");
        return 1;
    }

    FILE *fp = fopen(expect_path, "r");
    if (!fp) {
        fprintf(stderr, "FAIL: cannot open %s\n", expect_path);
        return 1;
    }

    int pass = 0, fail = 0;
    uint32_t row9[9];
    uint32_t prev_code = 0;
    int have_prev = 0;
    while (read_u32(fp, row9) == 1) {
        uint32_t unicode = row9[0], code = row9[1];
        uint32_t ok = 1;
        uint32_t look = cnbe_lookup(&table, unicode);

        if (look != code) {
            printf("  map mismatch: got 0x%08X expected 0x%08X U+%04X\n", look, code, unicode);
            ok = 0;
        }
        uint32_t sel_expected[5] = {row9[2], row9[3], row9[4], row9[5], row9[6]};
        for (uint32_t sel = 0; sel < 5; sel++) {
            uint32_t got = cnbe_extract(code, sel);
            if (got != sel_expected[sel]) {
                printf("  extract sel=%u mismatch: got %u expected %u\n", sel, got,
                       sel_expected[sel]);
                ok = 0;
            }
        }
        uint32_t rev = cnbe_skill(&table, code);
        if (rev != row9[7]) {
            printf("  skill mismatch: got 0x%04X expected 0x%04X\n", rev, row9[7]);
            ok = 0;
        }
        if (have_prev) {
            uint32_t dist = cnbe_cmp(prev_code, code);
            if (dist != row9[8]) {
                printf("  cmp mismatch: got %u expected %lu\n", dist,
                       (unsigned long)row9[8]);
                ok = 0;
            }
        }
        prev_code = code;
        have_prev = 1;

        if (ok) {
            pass++;
        } else {
            fail++;
            printf("FAIL row: U+%04X code=0x%08X\n", unicode, code);
        }
    }
    fclose(fp);

    printf("CNBE-32 v8 QEMU test: %d passed, %d failed\n", pass, fail);
    cnbe_table_free(&table);
    return fail == 0 ? 0 : 1;
}
