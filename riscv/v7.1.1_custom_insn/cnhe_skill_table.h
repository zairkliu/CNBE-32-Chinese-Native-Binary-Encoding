#ifndef __CNBE_SKILL_TABLE_H
#define __CNBE_SKILL_TABLE_H

#include <stdint.h>

// Table maps Unicode (U+4E00~U+9FA5) to 32-bit CNBE encoding
#define CNBE_TABLE_SIZE 20902

extern const uint32_t cnbe_skill_table[CNBE_TABLE_SIZE];

// Bitfield constants for CNBE 32-bit code
#define CNBE_RADICAL_MASK   0xFF000000
#define CNBE_RADICAL_SHIFT  24
#define CNBE_STROKE_MASK    0x00F80000
#define CNBE_STROKE_SHIFT   19
#define CNBE_STRUCT_MASK    0x00078000
#define CNBE_STRUCT_SHIFT   15

#endif // __CNBE_SKILL_TABLE_H
