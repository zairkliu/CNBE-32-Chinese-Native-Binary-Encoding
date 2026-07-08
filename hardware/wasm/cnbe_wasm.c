#include <emscripten/emscripten.h>
#include <stdint.h>

/* CNBE-32 bit layout (aligned with cnbe32.h v0.4.0) */
#define RADIX_SHIFT  24
#define STROKE_SHIFT 19
#define STRUCT_SHIFT 15
#define INDEX_SHIFT  4

/* Structure type names */
const char* struct_names[] = {
    "single","left-right","left-mid-right","up-down",
    "up-mid-down","top-left-wrap","top-right-wrap","bottom-left-wrap",
    "top-wrap","bottom-wrap","left-wrap","full-wrap","triangle"
};

/* Encode fields into 32-bit CNBE code */
EMSCRIPTEN_KEEPALIVE
uint32_t cnbe_encode(int radix, int stroke, int struct_type, int index_val, int ext) {
    return ((uint32_t)(radix & 0xFF) << RADIX_SHIFT) |
           ((uint32_t)(stroke & 0x1F) << STROKE_SHIFT) |
           ((uint32_t)(struct_type & 0xF) << STRUCT_SHIFT) |
           ((uint32_t)(index_val & 0x7FF) << INDEX_SHIFT) |
           (ext & 0xF);
}

/* Decode individual fields */
EMSCRIPTEN_KEEPALIVE int cnbe_radix(uint32_t code) { return (code >> RADIX_SHIFT) & 0xFF; }
EMSCRIPTEN_KEEPALIVE int cnbe_stroke(uint32_t code) { return (code >> STROKE_SHIFT) & 0x1F; }
EMSCRIPTEN_KEEPALIVE int cnbe_struct_type(uint32_t code) { return (code >> STRUCT_SHIFT) & 0xF; }
EMSCRIPTEN_KEEPALIVE int cnbe_index(uint32_t code) { return (code >> INDEX_SHIFT) & 0x7FF; }
EMSCRIPTEN_KEEPALIVE int cnbe_extension(uint32_t code) { return code & 0xF; }

/* Hamming distance between two CNBE codes */
EMSCRIPTEN_KEEPALIVE int cnbe_distance(uint32_t a, uint32_t b) {
    int ra = (a >> RADIX_SHIFT) & 0xFF, rb = (b >> RADIX_SHIFT) & 0xFF;
    int sa = (a >> STROKE_SHIFT) & 0x1F, sb = (b >> STROKE_SHIFT) & 0x1F;
    int ta = (a >> STRUCT_SHIFT) & 0xF, tb = (b >> STRUCT_SHIFT) & 0xF;
    int ia = (a >> INDEX_SHIFT) & 0x7FF, ib = (b >> INDEX_SHIFT) & 0x7FF;
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4 + abs(ia - ib);
}

/* Get struct name by index (returns pointer to static string) */
EMSCRIPTEN_KEEPALIVE const char* cnbe_struct_name(int type) {
    if (type >= 0 && type <= 12) return struct_names[type];
    return "unknown";
}
