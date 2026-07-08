#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
"""Generate CNBE-32 binary mapping table from CJK Unicode range"""
import numpy as np, os, json

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
TABLE_SIZE = 20902

def generate_skill_table(output_format="bin"):
    """Generate 81.6KB skill table (using heuristic encoding)"""
    table = np.zeros(TABLE_SIZE, dtype=np.uint32)
    for i in range(TABLE_SIZE):
        unicode_cp = 0x4E00 + i
        radix = (i % 214) + 1
        stroke = (i % 31) + 1
        struct = i % 13
        table[i] = (radix << 24) | (stroke << 19) | (struct << 15) | (i & 0xF)
    os.makedirs(os.path.dirname(OUT) if os.path.dirname(OUT) else ".", exist_ok=True)
    if output_format == "npy":
        np.save(os.path.join(OUT, "skill_table.npy"), table)
    else:
        open(os.path.join(OUT, "skill_table.bin"), "wb").write(table.tobytes())
    print(f"Generated {TABLE_SIZE} entries -> {OUT}")

if __name__ == "__main__":
    generate_skill_table()


