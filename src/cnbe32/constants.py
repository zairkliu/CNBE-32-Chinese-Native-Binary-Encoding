"""CNBE-32 encoding constants and bitfield definitions"""

# Bitfield shifts and widths
RADIX_SHIFT, RADIX_BITS = 24, 8
STROKE_SHIFT, STROKE_BITS = 19, 5
STRUCT_SHIFT, STRUCT_BITS = 15, 4
INDEX_SHIFT, INDEX_BITS = 4, 11
EXT_SHIFT, EXT_BITS = 0, 4

# Field boundaries
CNBE_STRUCT_MIN, CNBE_STRUCT_MAX = 0, 15
CNBE_STROKE_MIN, CNBE_STROKE_MAX = 0, 31
CNBE_RADIX_MIN, CNBE_RADIX_MAX = 0, 255
CNBE_EXT_FLAGS_MIN, CNBE_EXT_FLAGS_MAX = 0, 15
CNBE_SUB_TYPE_MIN, CNBE_SUB_TYPE_MAX = 0, 15
CNBE_VALUE_MIN, CNBE_VALUE_MAX = 0x00000000, 0xFFFFFFFF

# Encoding masks (auto-calculated from bit widths)
RADIX_MASK = (1 << RADIX_BITS) - 1
STROKE_MASK = (1 << STROKE_BITS) - 1
STRUCT_MASK = (1 << STRUCT_BITS) - 1
INDEX_MASK = (1 << INDEX_BITS) - 1
EXT_MASK = (1 << EXT_BITS) - 1

# Default paths and encoding
CNBE_DEFAULT_ENCODING = "utf-8"
CNBE_DEFAULT_DATA_DIR = "data"

# Structure type names
STRUCT_NAMES = {
    0: "single", 1: "left-right", 2: "left-mid-right", 3: "up-down",
    4: "up-mid-down", 5: "top-left-wrap", 6: "top-right-wrap",
    7: "bottom-left-wrap", 8: "top-wrap", 9: "bottom-wrap",
    10: "left-wrap", 11: "full-wrap", 12: "triangle",
}

# CJK basic set
CJK_UNICODE_START = 0x4E00
CJK_UNICODE_COUNT = 20902

# Default data files
SKILL_TABLE_FILE = "skill_table.bin"
RADIX_TABLE_FILE = "radix_table.csv"
