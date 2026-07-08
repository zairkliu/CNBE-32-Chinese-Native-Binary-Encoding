#!/bin/bash
set -e
echo "========================================"
echo " CNBE-32 v8.2 Spike End-to-End Validation"
echo "========================================"
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR/.."

echo "[1] Compiling 5 test programs..."
for test in test_loop test_struct test_cluster test_array test_hello; do
    echo "  $test"
    python3 src/compiler.py "tests/${test}.cnbe" -o "output/${test}.s"
done

echo "[2] Cross-compiling to ELF..."
for test in test_loop test_struct test_cluster test_array test_hello; do
    echo "  $test"
    riscv64-linux-gnu-gcc -march=rv64im -static -O2 \
        "output/${test}.s" src/runtime/cnbe_runtime.c \
        -o "output/${test}.elf"
done

echo ""
echo "[3] Running on Spike..."
mkdir -p results
RESULTS="results/v82_spike_log.txt"
echo "CNBE-32 v8.2 Spike Run Log" > "$RESULTS"
date >> "$RESULTS"
echo "========================================" >> "$RESULTS"

for test in test_loop test_struct test_cluster test_array test_hello; do
    echo "  spike pk output/${test}.elf"
    echo "=== $test ===" >> "$RESULTS"
    spike pk "output/${test}.elf" >> "$RESULTS" 2>&1
    echo "" >> "$RESULTS"
done

echo ""
echo "[4] Results:"
cat "$RESULTS"
echo ""
echo "Complete! Log: $RESULTS"