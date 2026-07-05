#include <stdio.h>
#include <stdint.h>
#define N 20902
static uint32_t tbl[N];
uint32_t lu(uint32_t u) {
    if (u >= 0x4E00 && u <= 0x9FA5) return tbl[u - 0x4E00];
    return 0;
}
int main() {
    uint32_t r = 0;
    for (int i = 0; i < 10; i++)
        for (uint32_t u = 0x4E00; u < 0x4E0A; u++)
            r ^= lu(u);
    printf("%u\n", r);
    return 0;
}
