#ifndef CNBE_REF_H
#define CNBE_REF_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t *unicode;
    uint32_t *cnbe;
    size_t n;
} CnbeSkillTable;

int cnbe_table_load(CnbeSkillTable *table, const char *path);
void cnbe_table_free(CnbeSkillTable *table);

uint32_t cnbe_lookup(const CnbeSkillTable *table, uint32_t unicode);
uint32_t cnbe_extract(uint32_t code, uint32_t selector);
uint32_t cnbe_cmp(uint32_t a, uint32_t b);
uint32_t cnbe_skill(const CnbeSkillTable *table, uint32_t code);

#ifdef __cplusplus
}
#endif

#endif
