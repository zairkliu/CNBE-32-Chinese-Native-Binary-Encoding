#ifndef CNBE32_H
#define CNBE32_H
#include <stdint.h>

/* Canonical CJK bit layout */
#define CNBE_RADIX_SHIFT   24
#define CNBE_STROKE_SHIFT  19
#define CNBE_STRUCT_SHIFT  15
#define CNBE_EXT_SHIFT     0
#define CNBE_INDEX_SHIFT   4
#define CNBE_INDEX_BITS    11

#define CNBE_RADIX_MASK    0xFF000000
#define CNBE_STROKE_MASK   0x00F80000
#define CNBE_STRUCT_MASK   0x00078000
#define CNBE_EXT_MASK      0x0000000F
#define CNBE_INDEX_MASK    0x00000FF0

/* Structure types */
#define CNBE_SINGLE       0
#define CNBE_LEFT_RIGHT   1
#define CNBE_LMR          2
#define CNBE_UP_DOWN      3
#define CNBE_UMD          4
#define CNBE_TOP_LEFT     5
#define CNBE_TOP_RIGHT    6
#define CNBE_BOTTOM_LEFT  7
#define CNBE_TOP_WRAP     8
#define CNBE_BOTTOM_WRAP  9
#define CNBE_LEFT_WRAP    10
#define CNBE_FULL_WRAP    11
#define CNBE_TRIANGLE     12

/* Core operations */
uint32_t cnhe_map(uint32_t unicode);
uint32_t cnhe_extract(uint32_t code, uint32_t field);
uint32_t cnhe_cmp(uint32_t a, uint32_t b);

static inline uint32_t cnbe_encode(uint8_t radix, uint8_t stroke, uint8_t struct_type, uint16_t ext, uint16_t index) {
    return ((uint32_t)radix << 24) | ((uint32_t)stroke << 19) | ((uint32_t)struct_type << 15) | ((uint32_t)(index & 0x7FF) << 4) | (ext & 0xF);
}
#endif

