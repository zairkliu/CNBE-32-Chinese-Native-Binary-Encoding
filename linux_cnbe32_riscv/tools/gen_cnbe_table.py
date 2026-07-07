#!/usr/bin/env python3
#!/usr/bin/env python3
"""
CNBE-32 Skill Table Generator for Linux 0.01 RISC-V
=====================================================
Generates a C header file with a const uint32_t array of 20902 CNBE-32
encoding entries covering Unicode range U+4E00 .. U+9FA5.

CNBE-32 Bit Layout (32 bits):
    [31:24] 部首 ID   (8 bits, 1-214)
    [23:19] 笔画数   (5 bits, 1-31)
    [18:15] 结构类型 (4 bits, 0-12)
    [14:4]  字库索引 (11 bits)
    [3:0]   扩展标志 (4 bits)

Data Sources (CSV, UTF-8):
    - radix_table.csv : radical_id, unicode, hanzi, stroke_count
    - stroke_db.csv   : unicode, hanzi, stroke_count
    - struct_db.csv   : unicode, hanzi, struct_id, struct_name

Characters not present in the CSV files fall back to deterministic
heuristics so the table is fully populated for all 20902 codepoints.
"""

import csv
import os
import sys

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR),
                        "..", "2.github CNBE-32-Chinese-Native-Binary-Encoding-main", "data")
# Try alternative path if the above doesn't exist
if not os.path.isdir(DATA_DIR):
    # Fallback: look relative to Desktop
    DATA_DIR = "/Users/liuzhaoqi/Desktop/2.github CNBE-32-Chinese-Native-Binary-Encoding-main/data"

RADIX_CSV   = os.path.join(DATA_DIR, "radix_table.csv")
STROKE_CSV  = os.path.join(DATA_DIR, "stroke_db.csv")
STRUCT_CSV  = os.path.join(DATA_DIR, "struct_db.csv")

OUTPUT_HEADER = os.path.join(os.path.dirname(SCRIPT_DIR), "include", "cnbe_table_data.h")

# ── Constants ────────────────────────────────────────────────────────────
CJK_START = 0x4E00
CJK_END   = 0x9FA5
TABLE_SIZE = CJK_END - CJK_START + 1  # 20902

# CNBE-32 bit shifts and masks (must match cnbe.h)
RADIX_SHIFT  = 24
STROKE_SHIFT = 19
STRUCT_SHIFT = 15
INDEX_SHIFT  = 4

# ── Data loaders ─────────────────────────────────────────────────────────

def parse_unicode(s):
    """Parse a Unicode codepoint string like 'U+4E00' or '0x4E00' to int."""
    s = s.strip()
    if s.startswith("U+") or s.startswith("u+"):
        return int(s[2:], 16)
    if s.startswith("0x") or s.startswith("0X"):
        return int(s[2:], 16)
    return int(s, 16)


def load_radix_table(path):
    """Load radix_table.csv → {unicode_codepoint: (radix_id, stroke_count)}"""
    table = {}
    if not os.path.isfile(path):
        sys.stderr.write(f"Warning: {path} not found, using heuristics only\n")
        return table
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                radix_id = int(row["radix_id"])
                cp = parse_unicode(row["unicode"])
                stroke = int(row["stroke_count"]) if row.get("stroke_count") else None
                table[cp] = (radix_id, stroke)
            except (ValueError, KeyError):
                continue
    return table


def load_stroke_table(path):
    """Load stroke_db.csv → {unicode_codepoint: stroke_count}"""
    table = {}
    if not os.path.isfile(path):
        sys.stderr.write(f"Warning: {path} not found, using heuristics only\n")
        return table
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cp = parse_unicode(row["unicode"])
                stroke = int(row["stroke_count"])
                table[cp] = stroke
            except (ValueError, KeyError):
                continue
    return table


def load_struct_table(path):
    """Load struct_db.csv → {unicode_codepoint: struct_id}"""
    table = {}
    if not os.path.isfile(path):
        sys.stderr.write(f"Warning: {path} not found, using heuristics only\n")
        return table
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cp = parse_unicode(row["unicode"])
                struct_id = int(row["struct_id"])
                table[cp] = struct_id
            except (ValueError, KeyError):
                continue
    return table


# ── CNBE-32 packing ─────────────────────────────────────────────────────

def pack_cnbe(radix_id, stroke, struct_type, index, ext=0):
    """Pack fields into a 32-bit CNBE code."""
    # Clamp to valid ranges
    radix_id  = max(1, min(214, radix_id))    # 1-214 → 8 bits
    stroke    = max(1, min(31, stroke))        # 1-31 → 5 bits
    struct_type = max(0, min(12, struct_type)) # 0-12 → 4 bits
    index     = max(0, min(0x7FF, index))      # 0-2047 → 11 bits
    ext       = max(0, min(0xF, ext))          # 0-15 → 4 bits

    return ((radix_id   & 0xFF)  << RADIX_SHIFT)  | \
           ((stroke     & 0x1F)  << STROKE_SHIFT) | \
           ((struct_type & 0x0F) << STRUCT_SHIFT) | \
           ((index      & 0x7FF) << INDEX_SHIFT)  | \
           (ext         & 0x0F)


# ── Main generation ─────────────────────────────────────────────────────

def generate_table():
    """Generate the 20902-entry CNBE-32 skill table."""
    radix_data  = load_radix_table(RADIX_CSV)
    stroke_data = load_stroke_table(STROKE_CSV)
    struct_data = load_struct_table(STRUCT_CSV)

    sys.stderr.write(f"Loaded: {len(radix_data)} radix, "
                     f"{len(stroke_data)} stroke, "
                     f"{len(struct_data)} struct entries\n")

    table = []
    for i in range(TABLE_SIZE):
        cp = CJK_START + i

        # Radical ID: from CSV, else heuristic (deterministic distribution
        # across all 214 radicals)
        if cp in radix_data:
            radix_id = radix_data[cp][0]
        else:
            radix_id = (i % 214) + 1  # 1-214

        # Stroke count: from radix table, then stroke db, else heuristic
        if cp in radix_data and radix_data[cp][1] is not None:
            stroke = radix_data[cp][1]
        elif cp in stroke_data:
            stroke = stroke_data[cp]
        else:
            stroke = (i % 31) + 1  # 1-31

        # Structure type: from CSV, else heuristic
        if cp in struct_data:
            struct_type = struct_data[cp]
        else:
            struct_type = i % 13  # 0-12

        # Library index: sequential position within the CJK block (0-based)
        index = i & 0x7FF  # 11 bits → wraps at 2048

        # Extension flags: 0 for base table
        ext = 0

        code = pack_cnbe(radix_id, stroke, struct_type, index, ext)
        table.append(code)

    return table


def write_header(table, output_path):
    """Write the table as a C header file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = []
    lines.append("/*")
    lines.append(" * CNBE-32 Skill Table — Auto-generated, DO NOT EDIT")
    lines.append(" * Generated by: tools/gen_cnbe_table.py")
    lines.append(f" * Table size: {len(table)} entries (U+4E00 .. U+9FA5)")
    lines.append(" * Layout: [31:24]radix | [23:19]stroke | [18:15]struct | [14:4]index | [3:0]ext")
    lines.append(" */")
    lines.append("")
    lines.append("#ifndef _CNBE_TABLE_DATA_H")
    lines.append("#define _CNBE_TABLE_DATA_H")
    lines.append("")
    lines.append("#include <stdint.h>")
    lines.append("")
    lines.append(f"const uint32_t cnbe_skill_table_data[{len(table)}] = {{")

    # 4 entries per line for readability
    for i in range(0, len(table), 4):
        chunk = table[i:i+4]
        hex_vals = ", ".join(f"0x{v:08X}" for v in chunk)
        if i + 4 < len(table):
            lines.append(f"    {hex_vals},")
        else:
            lines.append(f"    {hex_vals}")

    lines.append("};")
    lines.append("")
    lines.append("#endif /* _CNBE_TABLE_DATA_H */")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    sys.stderr.write(f"Written: {output_path} ({len(table)} entries)\n")


def main():
    table = generate_table()
    write_header(table, OUTPUT_HEADER)


if __name__ == "__main__":
    main()
