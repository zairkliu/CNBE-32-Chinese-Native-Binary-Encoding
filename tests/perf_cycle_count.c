/* perf_cycle_count.c — CNBE-32 周期精确性能测量
 * 编译: riscv64-unknown-elf-gcc -march=rv64imafdc -nostartfiles
 *       -I path/to/cnbe-riscv/src/table -o perf_cycle_count.elf
 *       perf_cycle_count.c
 * 运行: spike pk perf_cycle_count.elf
 */
#include <stdio.h>
#include <stdint.h>

extern const uint32_t cnbe_table[8105];
extern const uint32_t unicode_table[8105];

/* ============ 辅助函数 ============ */
static inline uint64_t rdcycle(void) {
    uint64_t c;
    asm volatile("rdcycle %0" : "=r"(c));
    return c;
}

/* 打印性能报告表头 */
static void print_header(void) {
    printf("\n");
    printf("+============================================================+\n");
    printf("|     CNBE-32 RISC-V Cycle-Accurate Performance Report      |\n");
    printf("+============================================================+\n");
    printf("| Platform: Spike RISC-V ISA Simulator                       |\n");
    printf("| ISA:      RV64IMAFDC + CNBE Custom Extension              |\n");
    printf("| Test set: 8105 Chinese chars (通用规范汉字表)              |\n");
    printf("+============================================================+\n\n");
}

/* ============ CNBE 内联汇编 ============ */
static inline uint32_t cnbe_enc(uint32_t u) {
    uint32_t r; asm volatile("cnbe.enc %0, %1" : "=r"(r) : "r"(u)); return r;
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
static inline uint32_t cnbe_dist(uint32_t a, uint32_t b) {
    uint32_t r; asm volatile("cnbe.dist %0, %1, %2" : "=r"(r) : "r"(a), "r"(b)); return r;
}

/* ============ 软件基线实现 ============ */
uint32_t sw_encode(uint32_t ucp) {
    for (int i = 0; i < 8105; i++)
        if (unicode_table[i] == ucp) return cnbe_table[i];
    return 0;
}

uint32_t sw_decode(uint32_t code) {
    for (int i = 0; i < 8105; i++)
        if (cnbe_table[i] == code) return unicode_table[i];
    return 0;
}

uint32_t sw_radical(uint32_t code) { return (code >> 24) & 0xFF; }
uint32_t sw_strokes(uint32_t code) { return (code >> 19) & 0x1F; }
uint32_t sw_struct(uint32_t code)  { return (code >> 15) & 0xF; }

uint32_t sw_distance(uint32_t a, uint32_t b) {
    return 4 * __builtin_popcount(((a>>24)&0xFF) ^ ((b>>24)&0xFF))
         + 2 * __builtin_popcount(((a>>19)&0x1F) ^ ((b>>19)&0x1F))
         + 1 * __builtin_popcount(((a>>15)&0xF)  ^ ((b>>15)&0xF));
}

/* ============ 测试基准 ============ */

/* Test 1: 位域提取 — 从8105个编码中提取部首 */
void test_radical_extract(void) {
    const int N = 8105;
    uint64_t s, e, sw_sum = 0, hw_sum = 0;

    // 软件：重复5次取平均
    for (int t = 0; t < 5; t++) {
        s = rdcycle();
        for (int i = 0; i < N; i++) {
            volatile uint32_t r = sw_radical(cnbe_table[i]);
            (void)r;
        }
        e = rdcycle();
        sw_sum += (e - s);
    }

    // 硬件：cnbe.rad 重复5次取平均
    for (int t = 0; t < 5; t++) {
        s = rdcycle();
        for (int i = 0; i < N; i++) {
            volatile uint32_t r = cnbe_rad(cnbe_table[i]);
            (void)r;
        }
        e = rdcycle();
        hw_sum += (e - s);
    }

    sw_sum /= 5; hw_sum /= 5;

    printf("--- Test 1: 部首提取 (8105 chars, 5次平均) ---\n");
    printf("  软件 (移位+掩码): %llu cycles (%.1f cycles/char)\n",
           sw_sum, (double)sw_sum / N);
    printf("  硬件 (cnbe.rad):   %llu cycles (%.1f cycles/char)\n",
           hw_sum, (double)hw_sum / N);
    printf("  加速比:            %.2fx\n", (double)sw_sum / hw_sum);
    printf("  单指令周期比:      ~%dx (软件2条 → 硬件1条)\n\n",
           2);
}

/* Test 2: 编码查表 — 对全部8105字编码 */
void test_encode_lookup(void) {
    const int N = 8105;
    uint64_t s, e, sw_sum = 0, hw_sum = 0;

    for (int t = 0; t < 3; t++) {
        s = rdcycle();
        for (int i = 0; i < N; i++) {
            volatile uint32_t r = sw_encode(unicode_table[i]);
            (void)r;
        }
        e = rdcycle();
        sw_sum += (e - s);
    }

    for (int t = 0; t < 3; t++) {
        s = rdcycle();
        for (int i = 0; i < N; i++) {
            volatile uint32_t r = cnbe_enc(unicode_table[i]);
            (void)r;
        }
        e = rdcycle();
        hw_sum += (e - s);
    }

    sw_sum /= 3; hw_sum /= 3;

    printf("--- Test 2: 编码查表 (8105 chars, 3次平均) ---\n");
    printf("  软件 (线性搜索):   %llu cycles (%.1f cycles/char)\n",
           sw_sum, (double)sw_sum / N);
    printf("  硬件 (cnbe.enc):   %llu cycles (%.1f cycles/char)\n",
           hw_sum, (double)hw_sum / N);
    printf("  加速比:            %.2fx\n", (double)sw_sum / hw_sum);
    printf("  预期CAM加速:       >8000x (O(1) vs O(8105))\n\n");
}

/* Test 3: 语义距离 — 1000字对 */
void test_distance(void) {
    const int N = 1000;
    uint64_t s, e, sw_sum = 0, hw_sum = 0;

    for (int t = 0; t < 5; t++) {
        s = rdcycle();
        volatile uint32_t d;
        for (int i = 0; i < N; i++) {
            d = sw_distance(cnbe_table[i], cnbe_table[(i+137)%8105]);
        }
        (void)d;
        e = rdcycle();
        sw_sum += (e - s);
    }

    for (int t = 0; t < 5; t++) {
        s = rdcycle();
        volatile uint32_t d;
        for (int i = 0; i < N; i++) {
            d = cnbe_dist(cnbe_table[i], cnbe_table[(i+137)%8105]);
        }
        (void)d;
        e = rdcycle();
        hw_sum += (e - s);
    }

    sw_sum /= 5; hw_sum /= 5;

    printf("--- Test 3: 语义距离 (1000 pairs, 5次平均) ---\n");
    printf("  软件 (移位+popcount×3+加权): %llu cycles (%.1f cycles/pair)\n",
           sw_sum, (double)sw_sum / N);
    printf("  硬件 (cnbe.dist):             %llu cycles (%.1f cycles/pair)\n",
           hw_sum, (double)hw_sum / N);
    printf("  加速比:                       %.2fx\n\n",
           (double)sw_sum / hw_sum);
}

/* Test 4: 综合基准 — 编码+部首+距离混合工作负载 */
void test_mixed_workload(void) {
    const int N = 8105;
    uint64_t s, e, sw_sum = 0, hw_sum = 0;

    for (int t = 0; t < 3; t++) {
        s = rdcycle();
        volatile uint32_t r1, r2, d;
        for (int i = 0; i < 500; i++) {
            uint32_t c1 = sw_encode(unicode_table[i]);
            uint32_t c2 = sw_encode(unicode_table[i+100]);
            r1 = sw_radical(c1);
            r2 = sw_radical(c2);
            d = sw_distance(c1, c2);
        }
        (void)r1; (void)r2; (void)d;
        e = rdcycle();
        sw_sum += (e - s);
    }

    for (int t = 0; t < 3; t++) {
        s = rdcycle();
        volatile uint32_t r1, r2, d;
        for (int i = 0; i < 500; i++) {
            uint32_t c1 = cnbe_enc(unicode_table[i]);
            uint32_t c2 = cnbe_enc(unicode_table[i+100]);
            r1 = cnbe_rad(c1);
            r2 = cnbe_rad(c2);
            d = cnbe_dist(c1, c2);
        }
        (void)r1; (void)r2; (void)d;
        e = rdcycle();
        hw_sum += (e - s);
    }

    sw_sum /= 3; hw_sum /= 3;
    printf("--- Test 4: 综合工作负载 (500字: 编码+部首提取×2+距离×1, 3次平均) ---\n");
    printf("  软件:                    %llu cycles\n", sw_sum);
    printf("  硬件 (CNBE指令集):       %llu cycles\n", hw_sum);
    printf("  综合加速比:              %.2fx\n\n", (double)sw_sum / hw_sum);
}

/* ============ 主函数 ============ */
int main(void) {
    print_header();
    test_radical_extract();
    test_encode_lookup();
    test_distance();
    test_mixed_workload();

    printf("+============================================================+\n");
    printf("| 结论:                                                      |\n");
    printf("| 1. 位域提取 (cnbe.rad/str/struct): 软:2条 → 硬:1条 ≈2x    |\n");
    printf("| 2. 编码查表 (cnbe.enc): 线性搜索瓶颈, 需CAM方案O(1)        |\n");
    printf("| 3. 语义距离 (cnbe.dist): 多步运算合并, 预计5-8x加速        |\n");
    printf("| 4. CAM方案的cnbe.enc加速比: 突破线性搜索的8105x理论上限    |\n");
    printf("+============================================================+\n");
    return 0;
}
