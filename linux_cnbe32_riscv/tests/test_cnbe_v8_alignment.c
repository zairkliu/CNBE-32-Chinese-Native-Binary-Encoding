#include <stdio.h>
#include <stdint.h>

#include "cnbe.h"

struct vector {
    const char *name;
    uint32_t unicode;
    uint32_t code;
    uint32_t radix, stroke, structure, index, ext;
    uint32_t reverse;
};

static const struct vector vectors[] = {
    {"中", 0x4E2D, 0x022002D0, 2, 4, 0, 45, 0, 0x4E2D},
    {"学", 0x5B66, 0x27415660, 39, 8, 2, 1382, 0, 0x5B66},
    {"水", 0x6C34, 0x55206340, 85, 4, 0, 1588, 0, 0x6C34},
    {"國", 0x570B, 0xB0B090B0, 176, 22, 1, 267, 0, 0x570B},
    {"龍", 0x9F8D, 0x787E18D0, 120, 15, 12, 397, 0, 0x9F8D},
    {"體", 0x9AD4, 0xC37E4D40, 195, 15, 12, 1236, 0, 0x9AD4},
    {"㑇", 0x3447, 0x0939E470, 9, 7, 3, 1607, 0, 0x3447},
};

static const uint32_t expected_distances[] = {324, 396, 822, 527, 600, 1564};

static int check(const char *what, uint32_t got, uint32_t want)
{
    if (got != want) {
        printf("FAIL %s: got 0x%08X expected 0x%08X\n", what, got, want);
        return 0;
    }
    return 1;
}

int main(void)
{
    cnbe_init();
    int pass = 0, fail = 0;
    size_t n = sizeof(vectors) / sizeof(vectors[0]);
    size_t i;

    for (i = 0; i < n; i++) {
        const struct vector *v = &vectors[i];
        if (!check(v->name, cnbe_map(v->unicode), v->code)) fail++;
        else pass++;
        if (!check("radix", cnbe_extract(v->code, 0), v->radix)) fail++;
        else pass++;
        if (!check("stroke", cnbe_extract(v->code, 1), v->stroke)) fail++;
        else pass++;
        if (!check("struct", cnbe_extract(v->code, 2), v->structure)) fail++;
        else pass++;
        if (!check("index", cnbe_extract(v->code, 3), v->index)) fail++;
        else pass++;
        if (!check("ext", cnbe_extract(v->code, 4), v->ext)) fail++;
        else pass++;
        if (!check("skill", cnbe_skill(v->code), v->reverse)) fail++;
        else pass++;
    }

    for (i = 0; i + 1 < n; i++) {
        if (!check("cmp", cnbe_cmp(vectors[i].code, vectors[i + 1].code),
                   expected_distances[i]))
            fail++;
        else
            pass++;
    }

    printf("CNBE kernel v8 alignment test: %d passed, %d failed\n", pass, fail);
    return fail == 0 ? 0 : 1;
}
