#!/bin/bash
P="/mnt/c/Users/zairk/Documents/Codex/2026-07-02/codex-dangerously-bypass-approvals-and-sandbox/github-upload/v8_chinese_programming"

# Compile all to ELF
echo "=== Compiling to ELF ==="
for t in test_hello test_loop test_struct test_cluster test_array; do
    echo -n "$t: "
    riscv64-linux-gnu-gcc -static -O2 "$P/output/$t.s" "$P/src/runtime/cnbe_runtime.c" -o "$P/output/$t.elf" 2>&1 | grep -c Warning
done

# Run all with QEMU
echo ""
echo "=== QEMU Results ==="
L="$P/results/v82_qemu_log.txt"
mkdir -p "$P/results"
echo "CNBE-32 v8.2 QEMU Run Log" > "$L"
date >> "$L"
echo "==========================" >> "$L"

for t in test_hello test_loop test_struct test_cluster test_array; do
    echo "=== $t ===" >> "$L"
    qemu-riscv64 "$P/output/$t.elf" >> "$L" 2>&1
    echo "exit: $?" >> "$L"
    echo "" >> "$L"
done

echo ""
cat "$L"
echo ""
echo "Log saved: $L"