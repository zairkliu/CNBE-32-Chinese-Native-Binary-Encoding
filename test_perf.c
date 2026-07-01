#include <stdio.h>
#include <stdint.h>
extern const uint32_t cnbe_table[8105];
extern const uint32_t unicode_table[8105];

static inline uint64_t rdcycle(void) {
    uint64_t c; asm volatile("rdcycle %0" : "=r"(c)); return c;
}

// Software baseline
uint32_t sw_enc(uint32_t u) {
    for (int i = 0; i < 8105; i++) if (unicode_table[i] == u) return cnbe_table[i];
    return 0;
}
uint32_t sw_rad(uint32_t c) { return (c >> 24) & 0xFF; }

void sw_test_enc(void) {
    for (int i = 0; i < 8105; i++) { volatile uint32_t r = sw_enc(unicode_table[i]); (void)r; }
}
void sw_test_rad(void) {
    for (int i = 0; i < 8105; i++) { volatile uint32_t r = sw_rad(cnbe_table[i]); (void)r; }
}

// Hardware instruction
void hw_test_enc(void) {
    for (int i = 0; i < 8105; i++) {
        uint32_t r; asm volatile("cnbe.enc %0, %1" : "=r"(r) : "r"(unicode_table[i])); (void)r;
    }
}
void hw_test_rad(void) {
    for (int i = 0; i < 8105; i++) {
        uint32_t r; asm volatile("cnbe.rad %0, %1" : "=r"(r) : "r"(cnbe_table[i])); (void)r;
    }
}

int main(void) {
    const int ITER = 5;
    uint64_t sw_enc_total = 0, hw_enc_total = 0;
    uint64_t sw_rad_total = 0, hw_rad_total = 0;

    printf("CNBE-32 RISC-V Performance Benchmark\n");
    printf("======================================\n\n");

    for (int t = 0; t < ITER; t++) {
        uint64_t s, e;
        s = rdcycle(); sw_test_enc(); e = rdcycle(); sw_enc_total += e - s;
        s = rdcycle(); hw_test_enc(); e = rdcycle(); hw_enc_total += e - s;
        s = rdcycle(); sw_test_rad(); e = rdcycle(); sw_rad_total += e - s;
        s = rdcycle(); hw_test_rad(); e = rdcycle(); hw_rad_total += e - s;
    }

    sw_enc_total /= ITER; hw_enc_total /= ITER;
    sw_rad_total /= ITER; hw_rad_total /= ITER;

    printf("+---------------------------+-------------+-------------+----------+\n");
    printf("| Operation                 | Software     | Hardware     | Speedup  |\n");
    printf("+---------------------------+-------------+-------------+----------+\n");
    printf("| Encode (8105 chars)       | %11llu | %11llu | %8.2fx |\n",
           sw_enc_total, hw_enc_total, (double)sw_enc_total / hw_enc_total);
    printf("| Per char                  | %11llu | %11llu |          |\n",
           sw_enc_total/8105, hw_enc_total/8105);
    printf("| Radical extract (8105)    | %11llu | %11llu | %8.2fx |\n",
           sw_rad_total, hw_rad_total, (double)sw_rad_total / hw_rad_total);
    printf("+---------------------------+-------------+-------------+----------+\n");
    return 0;
}
