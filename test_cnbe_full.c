#include <stdio.h>
#include <stdint.h>
extern const uint32_t cnbe_table[8105];
extern const uint32_t unicode_table[8105];

static inline uint32_t cnbe_enc(uint32_t ucp) {
    uint32_t r; asm volatile("cnbe.enc %0, %1" : "=r"(r) : "r"(ucp)); return r;
}
static inline uint32_t cnbe_dec(uint32_t c) {
    uint32_t r; asm volatile("cnbe.dec %0, %1" : "=r"(r) : "r"(c)); return r;
}
static inline uint32_t cnbe_rad(uint32_t c) {
    uint32_t r; asm volatile("cnbe.rad %0, %1" : "=r"(r) : "r"(c)); return r;
}
static inline uint32_t cnbe_str(uint32_t c) {
    uint32_t r; asm volatile("cnbe.str %0, %1" : "=r"(r) : "r"(c)); return r;
}
static inline uint32_t cnbe_struct(uint32_t c) {
    uint32_t r; asm volatile("cnbe.struct %0, %1" : "=r"(r) : "r"(c)); return r;
}
static inline uint32_t cnbe_dist(uint32_t c1, uint32_t c2) {
    uint32_t r; asm volatile("cnbe.dist %0, %1, %2" : "=r"(r) : "r"(c1), "r"(c2)); return r;
}

int test_enc(void) {
    int e = 0;
    printf("  CNBE.ENC (8105 chars)...\n");
    for (int i = 0; i < 8105; i++) {
        uint32_t r = cnbe_enc(unicode_table[i]);
        if (r != cnbe_table[i]) { if (e < 5) printf("    FAIL[%d]\n", i); e++; }
    }
    return e;
}
int test_dec(void) {
    int e = 0;
    printf("  CNBE.DEC (8105 chars)...\n");
    for (int i = 0; i < 8105; i++) {
        uint32_t r = cnbe_dec(cnbe_table[i]);
        if (r != unicode_table[i]) { if (e < 5) printf("    FAIL[%d]\n", i); e++; }
    }
    return e;
}
int test_extract(void) {
    int e = 0;
    printf("  CNBE.RAD/STR/STRUCT (8105 chars)...\n");
    for (int i = 0; i < 8105; i++) {
        uint32_t c = cnbe_table[i];
        if (cnbe_rad(c) != ((c>>24)&0xFF)) e++;
        if (cnbe_str(c) != ((c>>19)&0x1F)) e++;
        if (cnbe_struct(c) != ((c>>15)&0xF)) e++;
    }
    return e;
}
int test_dist(void) {
    printf("  CNBE.DIST sampling...\n");
    uint32_t c0 = cnbe_table[0], c1 = cnbe_table[200];
    uint32_t d = cnbe_dist(c0, c1);
    printf("    dist(chr[0], chr[200]) = %u\n", d);
    return 0;
}
int main(void) {
    int total = 0;
    printf("CNBE-32 RISC-V Full Test Suite\n");
    printf("================================\n\n");
    total += test_enc();
    total += test_dec();
    total += test_extract();
    test_dist();
    printf("\n");
    if (total == 0) printf("✓ ALL 8105 TESTS PASSED\n");
    else printf("✗ FAILED: %d errors\n", total);
    return total;
}
