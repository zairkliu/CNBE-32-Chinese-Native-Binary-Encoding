#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define RADIX_SHIFT 24
#define STROKE_SHIFT 19
#define STRUCT_SHIFT 15
#define INDEX_SHIFT 4
#define EXT_SHIFT 0

#define RADIX_MAX 255u
#define STROKE_MAX 31u
#define STRUCT_MAX 15u
#define INDEX_MAX 2047u
#define EXT_MAX 15u

/* Golden vector consistency test — validated against spec/golden_vectors.json */
/* This file should not be modified independently of the spec. */
/* See spec/IMPLEMENTATION_CONSISTENCY.md for CI and cross-language test instructions. */

typedef struct {
    const char *name;
    unsigned radix;
    unsigned stroke;
    unsigned structure;
    unsigned index;
    unsigned ext;
    unsigned code;
} ValidVector;

typedef struct {
    const char *name;
    int radix;
    int stroke;
    int structure;
    int index;
    int ext;
} InvalidVector;

static int validate_field(int value, unsigned max_value) {
    return value >= 0 && (unsigned)value <= max_value;
}

static int validate_fields(int radix, int stroke, int structure, int index, int ext) {
    return validate_field(radix, RADIX_MAX)
        && validate_field(stroke, STROKE_MAX)
        && validate_field(structure, STRUCT_MAX)
        && validate_field(index, INDEX_MAX)
        && validate_field(ext, EXT_MAX);
}

static unsigned encode_cnbe32(unsigned radix, unsigned stroke, unsigned structure, unsigned index, unsigned ext) {
    return (radix << RADIX_SHIFT)
        | (stroke << STROKE_SHIFT)
        | (structure << STRUCT_SHIFT)
        | (index << INDEX_SHIFT)
        | ext;
}

static unsigned decode_radix(unsigned code)    { return (code >> RADIX_SHIFT) & 0xFFu; }
static unsigned decode_stroke(unsigned code)   { return (code >> STROKE_SHIFT) & 0x1Fu; }
static unsigned decode_structure(unsigned code) { return (code >> STRUCT_SHIFT) & 0x0Fu; }
static unsigned decode_index(unsigned code)    { return (code >> INDEX_SHIFT) & 0x7FFu; }
static unsigned decode_ext(unsigned code)      { return code & 0x0Fu; }

static void fail(const char *name, const char *message) {
    fprintf(stderr, "FAIL [%s]: %s\n", name, message);
    exit(1);
}

int main(void) {
    const ValidVector valid_vectors[] = {
        {"all_zero",            0u, 0u, 0u,    0u, 0u, 0x00000000u},
        {"all_max",           255u, 31u, 15u, 2047u, 15u, 0xFFFFFFFFu},
        {"radix_only",          1u, 0u, 0u,    0u, 0u, 0x01000000u},
        {"stroke_only",         0u, 1u, 0u,    0u, 0u, 0x00080000u},
        {"struct_only",         0u, 0u, 1u,    0u, 0u, 0x00008000u},
        {"index_only",          0u, 0u, 0u,    1u, 0u, 0x00000010u},
        {"ext_only",            0u, 0u, 0u,    0u, 1u, 0x00000001u},
        {"sample_ming_like",   72u, 8u, 1u,  123u, 0u, 0x484087B0u},
        {"sample_middle_values",128u,16u, 8u, 1024u, 8u, 0x80844008u},
        {"sample_mixed_low",    7u, 3u, 2u,   45u, 9u, 0x071902D9u},
        {"sample_mixed_high", 201u,27u,14u, 1777u, 6u, 0xC9DF6F16u},
    };

    const InvalidVector invalid_vectors[] = {
        {"radix_negative",  -1,  0,  0,    0, 0},
        {"radix_overflow", 256,  0,  0,    0, 0},
        {"stroke_overflow",  0, 32,  0,    0, 0},
        {"struct_overflow",  0,  0, 16,    0, 0},
        {"index_overflow",   0,  0,  0, 2048, 0},
        {"ext_overflow",     0,  0,  0,    0, 16},
    };

    const size_t vcount = sizeof(valid_vectors) / sizeof(valid_vectors[0]);
    const size_t icount = sizeof(invalid_vectors) / sizeof(invalid_vectors[0]);

    for (size_t i = 0; i < vcount; i++) {
        const ValidVector v = valid_vectors[i];
        unsigned code = encode_cnbe32(v.radix, v.stroke, v.structure, v.index, v.ext);
        if (code != v.code) {
            char msg[64];
            snprintf(msg, sizeof(msg), "expected 0x%08X, got 0x%08X", v.code, code);
            fail(v.name, msg);
        }
        if (decode_radix(v.code) != v.radix)         fail(v.name, "radix mismatch");
        if (decode_stroke(v.code) != v.stroke)       fail(v.name, "stroke mismatch");
        if (decode_structure(v.code) != v.structure) fail(v.name, "structure mismatch");
        if (decode_index(v.code) != v.index)         fail(v.name, "index mismatch");
        if (decode_ext(v.code) != v.ext)             fail(v.name, "ext mismatch");
    }

    for (size_t i = 0; i < icount; i++) {
        const InvalidVector v = invalid_vectors[i];
        if (validate_fields(v.radix, v.stroke, v.structure, v.index, v.ext))
            fail(v.name, "invalid vector passed validation");
    }

    printf("C golden vector consistency PASS: %zu valid, %zu invalid\n", vcount, icount);
    return 0;
}
/* integrity check: 1783623667 */
