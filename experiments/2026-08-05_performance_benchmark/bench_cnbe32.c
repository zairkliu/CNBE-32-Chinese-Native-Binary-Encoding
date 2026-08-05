#define _POSIX_C_SOURCE 199309L

#include <stdint.h>
#include <stdio.h>
#include <time.h>

#include "cnbe_bench_table.h"

#define NS 1000000000.0

static double now_s(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / NS;
}

static inline uint32_t bench_encode(uint8_t radix, uint8_t stroke, uint8_t struct_type,
                                    uint16_t index, uint16_t ext) {
    return ((uint32_t)radix << 24) | ((uint32_t)stroke << 19) |
           ((uint32_t)struct_type << 15) | ((uint32_t)(index & 0x7FFu) << 4) | (ext & 0xFu);
}

static inline uint8_t bench_decode_radix(uint32_t code) { return (uint8_t)((code >> 24) & 0xFFu); }
static inline uint8_t bench_decode_stroke(uint32_t code) { return (uint8_t)((code >> 19) & 0x1Fu); }
static inline uint8_t bench_decode_struct(uint32_t code) { return (uint8_t)((code >> 15) & 0x0Fu); }
static inline uint16_t bench_decode_index(uint32_t code) { return (uint16_t)((code >> 4) & 0x7FFu); }
static inline uint8_t bench_decode_ext(uint32_t code) { return (uint8_t)(code & 0xFu); }

static inline uint32_t bench_bit_cmp(uint32_t a, uint32_t b) { return (uint32_t)__builtin_popcount(a ^ b); }

static inline uint32_t bench_lookup(uint32_t target) {
    size_t lo = 0, hi = sizeof(bench_unicode) / sizeof(bench_unicode[0]);
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (bench_unicode[mid] == target) return bench_cnbe[mid];
        if (bench_unicode[mid] < target) lo = mid + 1; else hi = mid;
    }
    return 0;
}

static void report(const char *name, double ns_per_op) {
    printf("RESULT %s %.3f\n", name, ns_per_op);
}

int main(void) {
    const int N = 1000000;
    const int LOOKUP_N = 200000;
    const size_t TABLE_LEN = sizeof(bench_unicode) / sizeof(bench_unicode[0]);
    volatile uint32_t sink = 0;
    double t0, t1;
    int i;

    t0 = now_s();
    for (i = 0; i < N; i++) {
        sink ^= bench_encode((uint8_t)(i & 255u), (uint8_t)(i & 31u),
                             (uint8_t)(i & 15u), (uint16_t)(i & 2047u), (uint8_t)(i & 15u));
    }
    t1 = now_s();
    report("c_encode_ns_per_op", (t1 - t0) / N * NS);

    t0 = now_s();
    for (i = 0; i < N; i++) {
        uint32_t c = bench_cnbe[i % TABLE_LEN];
        sink ^= bench_decode_radix(c) + bench_decode_stroke(c) + bench_decode_struct(c) +
                bench_decode_index(c) + bench_decode_ext(c);
    }
    t1 = now_s();
    report("c_decode_ns_per_op", (t1 - t0) / N * NS);

    t0 = now_s();
    for (i = 0; i < N; i++) {
        sink ^= bench_bit_cmp(bench_cnbe[i % TABLE_LEN], bench_cnbe[(i + 1) % TABLE_LEN]);
    }
    t1 = now_s();
    report("c_bit_hamming_ns_per_pair", (t1 - t0) / N * NS);

    t0 = now_s();
    for (i = 0; i < LOOKUP_N; i++) {
        sink ^= bench_lookup(bench_unicode[i % TABLE_LEN]);
    }
    t1 = now_s();
    report("c_binary_lookup_ns_per_op", (t1 - t0) / LOOKUP_N * NS);

    (void)sink;
    return 0;
}
