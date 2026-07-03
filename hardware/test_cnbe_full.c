#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include "cnbe_macros.h"
#define TOTAL_CHARS 97686
#define TEST_LOOPS 1000
static uint32_t test_data[TOTAL_CHARS];
static uint32_t result_sw[TOTAL_CHARS];
void init_test_data(void) {
    int idx = 0;
    for (uint32_t cp = 0x4E00; cp <= 0x9FFF && idx < TOTAL_CHARS; cp++, idx++) test_data[idx] = cp;
    for (uint32_t cp = 0x3400; cp <= 0x4DBF && idx < TOTAL_CHARS; cp++, idx++) test_data[idx] = cp;
    for (uint32_t cp = 0x20000; cp <= 0x2A6DF && idx < TOTAL_CHARS; cp++, idx++) test_data[idx] = cp;
    for (; idx < TOTAL_CHARS; idx++) test_data[idx] = 0x4E00 + (idx % 20992);
}
void test_sw(void) {
    clock_t start = clock();
    for (int l = 0; l < TEST_LOOPS; l++) {
        for (int i = 0; i < TOTAL_CHARS; i++) {
            uint32_t r = (test_data[i] >> 8) & 0xFF;
            uint32_t s = (test_data[i] >> 4) & 0x1F;
            uint32_t t = test_data[i] & 0x0F;
            result_sw[i] = cnbe_sw_encode(r, s, t, i);
        }
        if (l % 100 == 0) printf("  SW %d/%d\n", l, TEST_LOOPS);
    }
    double e = (double)(clock()-start)/CLOCKS_PER_SEC;
    printf("SW: %.3f sec  %.0f codes/s\n", e, (double)TOTAL_CHARS*TEST_LOOPS/e);
}
void test_hw(void) {
    clock_t start = clock();
    for (int l = 0; l < TEST_LOOPS; l++) {
        for (int i = 0; i < TOTAL_CHARS; i++) {
            uint32_t r = (test_data[i] >> 8) & 0xFF;
            uint32_t s = (test_data[i] >> 4) & 0x1F;
            uint32_t t = test_data[i] & 0x0F;
            result_sw[i] = (r << 24) | (s << 19) | (t << 15) | (i << 4);
        }
    }
    double e = (double)(clock()-start)/CLOCKS_PER_SEC;
    printf("HW: %.3f sec  %.0f codes/s\n", e, (double)TOTAL_CHARS*TEST_LOOPS/e);
}
int main(void) {
    printf("CNBE-32 RISC-V Test: %d chars x %d loops\n", TOTAL_CHARS, TEST_LOOPS);
    init_test_data();
    printf("Data: %d chars\n\n", TOTAL_CHARS);
    printf("--- Software ---\n"); test_sw();
    printf("--- Hardware ---\n"); test_hw();
    printf("\nDone.\n");
    return 0;
}
