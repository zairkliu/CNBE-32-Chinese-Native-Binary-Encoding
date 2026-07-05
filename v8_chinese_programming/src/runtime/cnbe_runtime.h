#ifndef CNBE_RUNTIME_H
#define CNBE_RUNTIME_H
#include <stdint.h>
uint32_t cnhe_map(uint32_t unicode);
uint32_t cnhe_extract(uint32_t code, uint32_t field);
uint32_t cnhe_cmp(uint32_t a, uint32_t b);
int cnhe_compare_chars(uint32_t a, uint32_t b);
#endif
