#include "cnbe_ref.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int cnbe_table_load(CnbeSkillTable *table, const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        fprintf(stderr, "cannot open %s\n", path);
        return -1;
    }
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    if (size <= 0 || size % 8 != 0) {
        fclose(fp);
        return -1;
    }
    table->n = (size_t)(size / 8);
    table->unicode = (uint32_t *)malloc(table->n * sizeof(uint32_t));
    table->cnbe = (uint32_t *)malloc(table->n * sizeof(uint32_t));
    if (!table->unicode || !table->cnbe) {
        fclose(fp);
        return -1;
    }
    unsigned char buf[8];
    for (size_t i = 0; i < table->n; i++) {
        if (fread(buf, 1, 8, fp) != 8) {
            fclose(fp);
            return -1;
        }
        table->unicode[i] = (uint32_t)buf[0] | ((uint32_t)buf[1] << 8) |
                            ((uint32_t)buf[2] << 16) | ((uint32_t)buf[3] << 24);
        table->cnbe[i] = (uint32_t)buf[4] | ((uint32_t)buf[5] << 8) |
                         ((uint32_t)buf[6] << 16) | ((uint32_t)buf[7] << 24);
    }
    fclose(fp);
    return 0;
}

void cnbe_table_free(CnbeSkillTable *table) {
    free(table->unicode);
    free(table->cnbe);
    table->unicode = NULL;
    table->cnbe = NULL;
    table->n = 0;
}

uint32_t cnbe_lookup(const CnbeSkillTable *table, uint32_t unicode) {
    size_t lo = 0, hi = table->n;
    while (lo < hi) {
        size_t mid = (lo + hi) / 2;
        uint32_t value = table->unicode[mid];
        if (value == unicode) {
            return table->cnbe[mid];
        }
        if (value < unicode) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return 0;
}

uint32_t cnbe_extract(uint32_t code, uint32_t selector) {
    switch (selector) {
        case 0:
            return (code >> 24) & 0xFF;
        case 1:
            return (code >> 19) & 0x1F;
        case 2:
            return (code >> 15) & 0x0F;
        case 3:
            return (code >> 4) & 0x7FF;
        case 4:
            return code & 0xF;
        default:
            return 0;
    }
}

uint32_t cnbe_cmp(uint32_t a, uint32_t b) {
    uint32_t ra = (a >> 24) & 0xFF, rb = (b >> 24) & 0xFF;
    uint32_t sa = (a >> 19) & 0x1F, sb = (b >> 19) & 0x1F;
    uint32_t ta = (a >> 15) & 0x0F, tb = (b >> 15) & 0x0F;
    uint32_t dr = ra > rb ? ra - rb : rb - ra;
    uint32_t ds = sa > sb ? sa - sb : sb - sa;
    uint32_t dt = ta > tb ? ta - tb : tb - ta;
    return dr * 8 + ds * 5 + dt * 4;
}

uint32_t cnbe_skill(const CnbeSkillTable *table, uint32_t code) {
    for (size_t i = 0; i < table->n; i++) {
        if (table->cnbe[i] == code) {
            return table->unicode[i];
        }
    }
    return 0;
}
