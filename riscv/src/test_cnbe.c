#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define TABLE_MIN 0x4E00
#define TABLE_MAX 0x9FA5
#define TABLE_SIZE (TABLE_MAX - TABLE_MIN + 1)

uint32_t skill_table[TABLE_SIZE];

int load_table(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror("fopen"); return -1; }
    size_t r = fread(skill_table, 1, TABLE_SIZE * 4, f);
    fclose(f);
    return (r == TABLE_SIZE * 4) ? 0 : -1;
}

uint32_t cnhe_lookup(uint32_t unicode) {
    if (unicode >= TABLE_MIN && unicode <= TABLE_MAX) {
        return skill_table[unicode - TABLE_MIN];
    }
    return 0;
}

void cnhe_decode(uint32_t code, uint32_t *radical, uint32_t *stroke,
                 uint32_t *structure, uint32_t *idx) {
    if (radical)   *radical   = (code >> 24) & 0xFF;
    if (stroke)    *stroke    = (code >> 19) & 0x1F;
    if (structure) *structure = (code >> 15) & 0xF;
    if (idx)       *idx       = (code >> 4)  & 0x7FF;
}

typedef struct {
    uint32_t unicode;
    const char *name;
    uint32_t exp_radical, exp_stroke, exp_structure;
} TestCase;

int main() {
    printf("CNBE-32 Skill Table Test (v7.0)\n");
    printf("================================\n\n");

    if (load_table("skill_table_8105.bin") != 0) {
        printf("FAILED: Cannot load skill_table_8105.bin\n");
        return 1;
    }
    printf("Table: %d entries (%.1f KB)\n", TABLE_SIZE, TABLE_SIZE * 4.0 / 1024);

    TestCase tests[] = {
        {0x570B, "國", 31, 11, 3},
        {0x611B, "愛", 61, 13, 3},
        {0x9F8D, "龍", 212, 16, 1},
        {0x9AD4, "體", 188, 23, 3},
        {0x6C22, "氢", 84, 9, 3},
        {0x9502, "锂", 167, 12, 3},
        {0x78B3, "碳", 112, 14, 3},
        {0x6C27, "氧", 84, 10, 3},
        {0x5B66, "学", 0, 0, 0},
        {0x7535, "电", 0, 0, 0},
        {0x4E2D, "中", 0, 0, 0},
        {0x6C34, "水", 0, 0, 0},
    };
    int n_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0, failed = 0;

    printf("\n--- Verification ---\n");
    for (int i = 0; i < n_tests; i++) {
        uint32_t code = cnhe_lookup(tests[i].unicode);
        uint32_t rad, stk, str, idx;
        cnhe_decode(code, &rad, &stk, &str, &idx);

        if (code == 0) {
            printf("  [%d] %-4s U+%04X: code=0\n", i+1, tests[i].name, tests[i].unicode);
            continue;
        }
        printf("  [%d] %-4s U+%04X: rad=%3u stk=%2u str=%u idx=%4u",
               i+1, tests[i].name, tests[i].unicode, rad, stk, str, idx);

        if (tests[i].exp_radical != 0 || tests[i].exp_stroke != 0) {
            int ok = (rad == tests[i].exp_radical && stk == tests[i].exp_stroke && str == tests[i].exp_structure);
            printf(" %s", ok ? "PASS" : "FAIL");
            if (ok) passed++; else failed++;
        }
        printf("\n");
    }
    printf("\nResults: %d passed, %d failed, %d total\n", passed, failed, n_tests);

    printf("\n--- Performance ---\n");
    clock_t start = clock();
    int iter = 1000000;
    volatile uint32_t dummy = 0;
    for (int i = 0; i < iter; i++) {
        dummy ^= cnhe_lookup(tests[i % n_tests].unicode);
    }
    clock_t end = clock();
    double total_us = (double)(end - start) / CLOCKS_PER_SEC * 1e6;
    printf("Lookups: %d calls\n", iter);
    printf("Total:   %.0f us\n", total_us);
    printf("Per call: %.1f ns\n", total_us / iter * 1000);

    printf("\nDone.\n");
    return (failed > 0) ? 1 : 0;
}
