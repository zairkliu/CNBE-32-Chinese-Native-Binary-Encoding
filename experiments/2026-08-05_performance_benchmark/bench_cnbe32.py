#!/usr/bin/env python3
"""CNBE-32 production benchmark: encode/decode, distance, lookup, load, memory, storage.

Target environment: Ubuntu 26.04 (WSL or native), gcc available. The script writes
`results.json` and generates a C table header under `build/`, then compiles and runs
the C microbenchmark for a cross-language baseline.

Usage:
    PYTHONPATH=repo/src python3 bench_cnbe32.py --db repo/data/cnbe32.db --out results.json
"""

from __future__ import annotations

import argparse
import json
import platform
import resource
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import cnbe32  # noqa: E402
from cnbe32 import (  # noqa: E402
    batch,
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
    lookup,
)

TABLE_SIZE = 8105


def median_ns_per_op(fn, n, repeat=7, warmup=3):
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeat):
        start = time.perf_counter_ns()
        fn()
        end = time.perf_counter_ns()
        samples.append((end - start) / n)
    samples.sort()
    return samples[len(samples) // 2]


def write_c_table(rows, header_path: Path) -> None:
    rows = sorted(rows, key=lambda r: r["unicode"])[:TABLE_SIZE]
    unicode_vals = ", ".join(str(r["unicode"]) for r in rows)
    cnbe_vals = ", ".join(str(r["cnbe"]) for r in rows)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(
        "#pragma once\n"
        "#include <stdint.h>\n"
        f"static const uint32_t bench_unicode[{len(rows)}] = {{{unicode_vals}}};\n"
        f"static const uint32_t bench_cnbe[{len(rows)}] = {{{cnbe_vals}}};\n",
        encoding="utf-8",
    )


def run_c_benchmark(workdir: Path, header_path: Path) -> dict[str, float]:
    src = Path(__file__).with_name("bench_cnbe32.c")
    bin_path = workdir / "bench_cnbe32"
    compile_result = subprocess.run(
        ["gcc", "-O2", "-std=c99", "-I", str(workdir), "-o", str(bin_path), str(src)],
        check=True,
        capture_output=True,
        text=True,
    )
    if compile_result.returncode != 0:
        raise RuntimeError(f"C compile failed:\n{compile_result.stderr}")
    proc = subprocess.run([str(bin_path)], check=True, capture_output=True, text=True)
    results: dict[str, float] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "RESULT":
            results[parts[1]] = float(parts[2])
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    args = parser.parse_args()

    db_path = args.db.resolve()
    workdir = Path(__file__).resolve().parent / "build"
    workdir.mkdir(parents=True, exist_ok=True)
    header_path = workdir / "cnbe_bench_table.h"

    uname = platform.uname()
    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": uname.machine,
        "processor": uname.processor,
        "db": str(db_path),
        "db_bytes": db_path.stat().st_size,
        "table_rows": TABLE_SIZE,
    }

    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM cnbe32 ORDER BY unicode")]
    con.close()

    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    memory_kb = max(after - before, 0)

    chars = [r["char"] for r in rows]
    samples = rows[: max(1, len(rows) // 32)]
    pair_count = len(samples) - 1

    def enc_loop() -> None:
        acc = 0
        for i in range(len(samples)):
            r = samples[i]
            acc ^= encode_cnbe(r["radix"], r["strokes"], r["struct_type"], r["idx"], 0).code
        if acc == 0xDEADBEEF:
            print(acc)

    def dec_loop() -> None:
        acc = 0
        for i in range(len(samples)):
            acc ^= decode_cnbe(samples[i]["cnbe"])["stroke"]
        if acc == 0xDEADBEEF:
            print(acc)

    def cmp_loop() -> None:
        acc = 0
        for i in range(pair_count):
            a = encode_cnbe(samples[i]["radix"], samples[i]["strokes"], samples[i]["struct_type"], samples[i]["idx"], 0)
            b = encode_cnbe(samples[i + 1]["radix"], samples[i + 1]["strokes"], samples[i + 1]["struct_type"], samples[i + 1]["idx"], 0)
            acc += field_weighted_distance(a, b)
        if acc == 0xDEADBEEF:
            print(acc)

    def bitcmp_loop() -> None:
        acc = 0
        for i in range(pair_count):
            a = encode_cnbe(samples[i]["radix"], samples[i]["strokes"], samples[i]["struct_type"], samples[i]["idx"], 0)
            b = encode_cnbe(samples[i + 1]["radix"], samples[i + 1]["strokes"], samples[i + 1]["struct_type"], samples[i + 1]["idx"], 0)
            acc += bit_hamming_distance(a, b)
        if acc == 0xDEADBEEF:
            print(acc)

    lookup_char = chars[0]

    def lookup_loop() -> None:
        for _ in range(500):
            lookup(lookup_char)

    def batch_loop() -> None:
        batch(chars[:1000])

    def ord_loop() -> None:
        acc = 0
        for i in range(200000):
            acc ^= ord(chars[i % len(chars)])
        if acc == 0xDEADBEEF:
            print(acc)

    py_ops = {
        "python_encode_ns_per_op": median_ns_per_op(enc_loop, len(samples)),
        "python_decode_ns_per_op": median_ns_per_op(dec_loop, len(samples)),
        "python_field_distance_ns_per_pair": median_ns_per_op(cmp_loop, pair_count),
        "python_bit_hamming_ns_per_pair": median_ns_per_op(bitcmp_loop, pair_count),
        "python_lookup_ns_per_op": median_ns_per_op(lookup_loop, 500),
        "python_batch_ns_per_char": median_ns_per_op(batch_loop, 1000),
        "python_ord_ns_per_op": median_ns_per_op(ord_loop, 200000),
    }

    def db_load() -> None:
        c = sqlite3.connect(str(db_path))
        c.execute("SELECT COUNT(*) FROM cnbe32").fetchone()
        c.close()

    db_metrics = {
        "db_connect_count_ms": median_ns_per_op(db_load, 1, repeat=15) / 1e6,
    }

    binary_size = len(rows) * 4
    utf8_size = sum(len(c.encode("utf-8")) for c in chars)
    json_size = len(json.dumps(rows[:5000], ensure_ascii=False).encode("utf-8"))
    storage = {
        "db_file_bytes": db_path.stat().st_size,
        "cnbe_binary_bytes": binary_size,
        "cnbe_binary_bytes_per_char": 4,
        "utf8_chars_bytes": utf8_size,
        "utf8_bytes_per_char": round(utf8_size / len(rows), 3),
        "json_rows_bytes": json_size,
        "rows_measured": len(rows),
    }

    write_c_table(rows, header_path)
    c_results = run_c_benchmark(workdir, header_path)

    result = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "environment": env,
        "python_operations": py_ops,
        "database": db_metrics,
        "memory": {"maxrss_delta_kb": memory_kb},
        "storage": storage,
        "c_operations": c_results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
