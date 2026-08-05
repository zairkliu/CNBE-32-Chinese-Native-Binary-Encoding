#!/usr/bin/env python3
"""Generate v8 golden vectors from data/cnbe32.db."""

import json
import os
import sqlite3

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
V8_DIR = os.path.dirname(TOOLS_DIR)
REPO_DIR = os.path.dirname(os.path.dirname(V8_DIR))
DB_PATH = os.path.join(REPO_DIR, "data", "cnbe32.db")
GOLDEN_DIR = os.path.join(V8_DIR, "golden")

SAMPLES = [
    (0x4E2D, "中"),
    (0x5B66, "学"),
    (0x6C34, "水"),
    (0x570B, "國"),
    (0x9F8D, "龍"),
    (0x9AD4, "體"),
    (0x3447, "㑇"),
]


def main() -> None:
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "select unicode, char, cnbe, radix, strokes, struct_type, idx from cnbe32 order by unicode, rowid"
    ).fetchall()
    con.close()

    by_unicode = {r[0]: r for r in rows}
    reverse_first = {}
    for u, _, c, _, _, _, _ in rows:
        if c not in reverse_first:
            reverse_first[c] = u

    vectors = []
    for u, name in SAMPLES:
        row = by_unicode.get(u)
        if row is None:
            continue
        _, char, code, _, _, _, _ = row
        radix = (code >> 24) & 0xFF
        strokes = (code >> 19) & 0x1F
        struct_type = (code >> 15) & 0x0F
        idx = (code >> 4) & 0x7FF
        ext = code & 0xF
        vectors.append(
            {
                "name": f"map_{char}",
                "unicode": u,
                "char": char,
                "code": code,
                "code_hex": f"0x{code:08X}",
                "radix": radix,
                "stroke": strokes,
                "struct": struct_type,
                "idx": idx,
                "ext": ext,
                "reverse_unicode": reverse_first[code],
            }
        )

    def distance(a: int, b: int) -> int:
        def fields(code: int):
            return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F

        ar, as_, at = fields(a)
        br, bs, bt = fields(b)
        return (
            abs(ar - br) * 8
            + abs(as_ - bs) * 5
            + abs(at - bt) * 4
        )

    cmp_vectors = []
    for i in range(len(vectors) - 1):
        va, vb = vectors[i], vectors[i + 1]
        cmp_vectors.append(
            {
                "name": f"cmp_{va['char']}_{vb['char']}",
                "a": va["code"],
                "b": vb["code"],
                "distance": distance(va["code"], vb["code"]),
            }
        )

    golden = {
        "version": "v8.0.0",
        "encoding": "CNBE-32",
        "description": "Golden vectors for the v8 RISC-V simulator and hardware models. Fields are decoded from the CNBE code, matching the SDK; a few database metadata columns may lag the code.",
        "instructions": ["cnbe.map", "cnbe.extract", "cnbe.cmp", "cnbe.skill"],
        "cycle_model": {"map": 2, "extract": 1, "cmp": 3, "skill": 2},
        "map_vectors": vectors,
        "cmp_vectors": cmp_vectors,
        "not_found_unicode": 0xFFFF,
        "not_found_code": 0,
    }
    out = os.path.join(GOLDEN_DIR, "golden_vectors.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(golden, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out}")

    qemu_lines = []
    prev = None
    for v in vectors:
        dist = distance(prev["code"], v["code"]) if prev is not None else 0
        qemu_lines.append(
            f"{v['name']} {v['unicode']:04X} {v['code']:08X} "
            f"{v['radix']} {v['stroke']} {v['struct']} {v['idx']} {v['ext']} "
            f"{v['reverse_unicode']:04X} {dist}"
        )
        prev = v
    qemu_path = os.path.join(GOLDEN_DIR, "qemu_expected.txt")
    with open(qemu_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(qemu_lines) + "\n")
    print(f"wrote {qemu_path}")


if __name__ == "__main__":
    main()
