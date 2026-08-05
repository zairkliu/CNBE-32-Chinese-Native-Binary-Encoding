#!/usr/bin/env python3
"""Generate the CNBE kernel table from data/cnbe32.db (v8-aligned)."""

import os
import sqlite3

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
KERNEL_DIR = os.path.dirname(TOOLS_DIR)
REPO_DIR = os.path.dirname(KERNEL_DIR)
DB_PATH = os.path.join(REPO_DIR, "data", "cnbe32.db")
OUT_PATH = os.path.join(KERNEL_DIR, "include", "cnbe_table_data.h")


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "select unicode, cnbe from cnbe32 order by unicode, rowid"
    ).fetchall()
    con.close()

    unicode_values = [u for u, _ in rows]
    cnbe_values = [c for _, c in rows]

    with open(OUT_PATH, "w", encoding="ascii") as fh:
        fh.write("/* CNBE-32 Kernel Skill Table - generated from data/cnbe32.db */\n")
        fh.write("/* v8-aligned: sorted Unicode pairs, binary-search lookup */\n")
        fh.write("#ifndef _CNBE_TABLE_DATA_H\n#define _CNBE_TABLE_DATA_H\n\n")
        fh.write("#include <stdint.h>\n\n")
        fh.write(f"#define CNBE_KERNEL_TABLE_SIZE {len(rows)}u\n\n")

        fh.write("const uint32_t cnbe_kernel_unicode_table[CNBE_KERNEL_TABLE_SIZE] = {\n")
        for i in range(0, len(unicode_values), 8):
            chunk = [str(v) for v in unicode_values[i : i + 8]]
            fh.write("    " + ", ".join(chunk) + ",\n")
        fh.write("};\n\n")

        fh.write("const uint32_t cnbe_kernel_skill_table[CNBE_KERNEL_TABLE_SIZE] = {\n")
        for i in range(0, len(cnbe_values), 8):
            chunk = [str(v) for v in cnbe_values[i : i + 8]]
            fh.write("    " + ", ".join(chunk) + ",\n")
        fh.write("};\n\n")

        fh.write("#endif\n")

    print(f"wrote {OUT_PATH} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
