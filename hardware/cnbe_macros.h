#ifndef CNBE_MACROS_H
#define CNBE_MACROS_H
#include <stdint.h>
// cnhe.extract rd, rs1, imm - extract bit-field
#define CNHE_EXTRACT(rd, rs1, imm) __asm__ volatile(".insn r 0x0B, 0x0, %0, %1, zero, %2" : "=r"(rd) : "r"(rs1), "i"(imm))
// cnhe.cmp rd, rs1, rs2 - compare two CNBE codes
#define CNHE_CMP(rd, rs1, rs2) __asm__ volatile(".insn r 0x0B, 0x1, %0, %1, %2, 0" : "=r"(rd) : "r"(rs1), "r"(rs2))
// cnhe.map rd, rs1 - Unicode to CNBE lookup
#define CNHE_MAP(rd, rs1) __asm__ volatile(".insn r 0x0B, 0x2, %0, %1, zero, 0" : "=r"(rd) : "r"(rs1))
// cnhe.mv rd, rs1 - move CNBE code
#define CNHE_MV(rd, rs1) __asm__ volatile(".insn r 0x0B, 0x3, %0, %1, zero, 0" : "=r"(rd) : "r"(rs1))
// cnhe.enc rd, rs1, imm - encode into CNBE format
#define CNHE_ENC(rd, rs1, imm) __asm__ volatile(".insn r 0x0B, 0x4, %0, %1, zero, %2" : "=r"(rd) : "r"(rs1), "i"(imm))
static inline uint32_t cnbe_sw_encode(uint32_t r, uint32_t s, uint32_t t, uint32_t i) {
    return (r << 24) | (s << 19) | (t << 15) | (i << 4);
}
static inline uint32_t cnbe_sw_extract_radical(uint32_t c) { return (c >> 24) & 0xFF; }
static inline uint32_t cnbe_sw_extract_stroke(uint32_t c)  { return (c >> 19) & 0x1F; }
static inline uint32_t cnbe_sw_extract_structure(uint32_t c) { return (c >> 15) & 0x0F; }
static inline uint32_t cnbe_sw_extract_index(uint32_t c)  { return (c >> 4) & 0x7FF; }
static inline uint32_t cnbe_sw_distance(uint32_t a, uint32_t b) {
    return abs((int)((a>>24)&0xFF)-(int)((b>>24)&0xFF))*8+abs((int)((a>>19)&0x1F)-(int)((b>>19)&0x1F))*5+abs((int)((a>>15)&0x0F)-(int)((b>>15)&0x0F))*4+abs((int)((a>>4)&0x7FF)-(int)((b>>4)&0x7FF))*11;
}
#endif
