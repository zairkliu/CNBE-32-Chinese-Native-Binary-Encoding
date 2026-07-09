const RADIX_SHIFT: u32 = 24;
const STROKE_SHIFT: u32 = 19;
const STRUCT_SHIFT: u32 = 15;
const INDEX_SHIFT: u32 = 4;
const EXT_SHIFT: u32 = 0;

const RADIX_MAX: u32 = 255;
const STROKE_MAX: u32 = 31;
const STRUCT_MAX: u32 = 15;
const INDEX_MAX: u32 = 2047;
const EXT_MAX: u32 = 15;

struct ValidVector {
    name: &'static str,
    radix: u32,
    stroke: u32,
    structure: u32,
    index: u32,
    ext: u32,
    code: u32,
}

struct InvalidVector {
    name: &'static str,
    radix: i32,
    stroke: i32,
    structure: i32,
    index: i32,
    ext: i32,
}

fn validate_field(value: i32, max_value: u32) -> bool {
    value >= 0 && (value as u32) <= max_value
}

fn validate_fields(radix: i32, stroke: i32, structure: i32, index: i32, ext: i32) -> bool {
    validate_field(radix, RADIX_MAX)
        && validate_field(stroke, STROKE_MAX)
        && validate_field(structure, STRUCT_MAX)
        && validate_field(index, INDEX_MAX)
        && validate_field(ext, EXT_MAX)
}

fn encode_cnbe32(radix: u32, stroke: u32, structure: u32, index: u32, ext: u32) -> u32 {
    (radix << RADIX_SHIFT)
        | (stroke << STROKE_SHIFT)
        | (structure << STRUCT_SHIFT)
        | (index << INDEX_SHIFT)
        | ext
}

fn decode_radix(code: u32) -> u32    { (code >> RADIX_SHIFT) & 0xFF }
fn decode_stroke(code: u32) -> u32   { (code >> STROKE_SHIFT) & 0x1F }
fn decode_structure(code: u32) -> u32 { (code >> STRUCT_SHIFT) & 0x0F }
fn decode_index(code: u32) -> u32    { (code >> INDEX_SHIFT) & 0x7FF }
fn decode_ext(code: u32) -> u32      { code & 0x0F }

fn valid_vectors() -> Vec<ValidVector> {
    vec![
        ValidVector { name: "all_zero",             radix:   0, stroke:  0, structure:  0, index:    0, ext:  0, code: 0x00000000 },
        ValidVector { name: "all_max",              radix: 255, stroke: 31, structure: 15, index: 2047, ext: 15, code: 0xFFFFFFFF },
        ValidVector { name: "radix_only",           radix:   1, stroke:  0, structure:  0, index:    0, ext:  0, code: 0x01000000 },
        ValidVector { name: "stroke_only",          radix:   0, stroke:  1, structure:  0, index:    0, ext:  0, code: 0x00080000 },
        ValidVector { name: "struct_only",          radix:   0, stroke:  0, structure:  1, index:    0, ext:  0, code: 0x00008000 },
        ValidVector { name: "index_only",           radix:   0, stroke:  0, structure:  0, index:    1, ext:  0, code: 0x00000010 },
        ValidVector { name: "ext_only",             radix:   0, stroke:  0, structure:  0, index:    0, ext:  1, code: 0x00000001 },
        ValidVector { name: "sample_ming_like",     radix:  72, stroke:  8, structure:  1, index:  123, ext:  0, code: 0x484087B0 },
        ValidVector { name: "sample_middle_values", radix: 128, stroke: 16, structure:  8, index: 1024, ext:  8, code: 0x80844008 },
        ValidVector { name: "sample_mixed_low",     radix:   7, stroke:  3, structure:  2, index:   45, ext:  9, code: 0x071902D9 },
        ValidVector { name: "sample_mixed_high",    radix: 201, stroke: 27, structure: 14, index: 1777, ext:  6, code: 0xC9DF6F16 },
    ]
}

fn invalid_vectors() -> Vec<InvalidVector> {
    vec![
        InvalidVector { name: "radix_negative",  radix:  -1, stroke:  0, structure:  0, index:    0, ext:  0 },
        InvalidVector { name: "radix_overflow",  radix: 256, stroke:  0, structure:  0, index:    0, ext:  0 },
        InvalidVector { name: "stroke_overflow", radix:   0, stroke: 32, structure:  0, index:    0, ext:  0 },
        InvalidVector { name: "struct_overflow", radix:   0, stroke:  0, structure: 16, index:    0, ext:  0 },
        InvalidVector { name: "index_overflow",  radix:   0, stroke:  0, structure:  0, index: 2048, ext:  0 },
        InvalidVector { name: "ext_overflow",    radix:   0, stroke:  0, structure:  0, index:    0, ext: 16 },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encode_matches_golden_vectors() {
        for v in valid_vectors() {
            let code = encode_cnbe32(v.radix, v.stroke, v.structure, v.index, v.ext);
            assert_eq!(code, v.code, "{}", v.name);
        }
    }

    #[test]
    fn decode_matches_golden_vectors() {
        for v in valid_vectors() {
            assert_eq!(decode_radix(v.code), v.radix, "{}", v.name);
            assert_eq!(decode_stroke(v.code), v.stroke, "{}", v.name);
            assert_eq!(decode_structure(v.code), v.structure, "{}", v.name);
            assert_eq!(decode_index(v.code), v.index, "{}", v.name);
            assert_eq!(decode_ext(v.code), v.ext, "{}", v.name);
        }
    }

    #[test]
    fn invalid_vectors_fail_validation() {
        for v in invalid_vectors() {
            assert!(!validate_fields(v.radix, v.stroke, v.structure, v.index, v.ext), "{}", v.name);
        }
    }
}
