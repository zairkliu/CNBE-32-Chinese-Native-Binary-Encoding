#include <stdio.h>
#include <stdint.h>
extern const uint32_t cnbe_table[8105];
extern const uint32_t unicode_table[8105];

static inline uint32_t cnbe_enc(uint32_t u) {
    uint32_t r; asm volatile("cnbe.enc %0, %1" : "=r"(r) : "r"(u)); return r;
}
static inline uint32_t cnbe_dist(uint32_t a, uint32_t b) {
    uint32_t r; asm volatile("cnbe.dist %0, %1, %2" : "=r"(r) : "r"(a), "r"(b)); return r;
}

int main(void) {
    printf("CNBE-32 Clustering Verification\n");
    printf("================================\n\n");
    // 氵部字 (radical=85): 江 U+6C5F, 河 U+6CB3, 海 U+6D77, 汗 U+6C57, 池 U+6C60
    uint32_t water[] = {0x6C5F, 0x6CB3, 0x6D77, 0x6C57, 0x6C60};
    // 木部字 (radical=75): 林 U+6797, 村 U+6751, 树 U+6811, 杆 U+6746, 根 U+6839
    uint32_t wood[]  = {0x6797, 0x6751, 0x6811, 0x6746, 0x6839};
    // 口部字 (radical=30): 吃 U+5403, 喝 U+559D, 唱 U+5531, 喊 U+558A, 叫 U+53EB
    uint32_t mouth[] = {0x5403, 0x559D, 0x5531, 0x558A, 0x53EB};

    uint32_t wc[5], mc[5], oc[5];
    for (int i = 0; i < 5; i++) {
        wc[i] = cnbe_enc(water[i]);
        mc[i] = cnbe_enc(wood[i]);
        oc[i] = cnbe_enc(mouth[i]);
    }

    // Within-group distances
    uint32_t wd = cnbe_dist(wc[0], wc[1]);  // 氵-氵
    uint32_t md = cnbe_dist(mc[0], mc[1]);  // 木-木
    uint32_t od = cnbe_dist(oc[0], oc[1]);  // 口-口

    // Cross-group distances
    uint32_t wm = cnbe_dist(wc[0], mc[0]);  // 氵-木
    uint32_t wo = cnbe_dist(wc[0], oc[0]);  // 氵-口
    uint32_t mo = cnbe_dist(mc[0], oc[0]);  // 木-口

    printf("同部首距离:\n");
    printf("  氵-氵: %u\n", wd);
    printf("  木-木: %u\n", md);
    printf("  口-口: %u\n", od);
    printf("\n跨部首距离:\n");
    printf("  氵-木: %u\n", wm);
    printf("  氵-口: %u\n", wo);
    printf("  木-口: %u\n", mo);
    printf("\n分离度:\n");
    printf("  氵vs木: %.1fx\n", (float)wm / (wd ? wd : 1));
    printf("  氵vs口: %.1fx\n", (float)wo / (wd ? wd : 1));

    int pass = (wm > wd && wo > wd && mo > md);
    printf("\n%s\n", pass ? "✓ 聚类验证通过" : "✗ 聚类验证失败");
    return pass ? 0 : 1;
}
