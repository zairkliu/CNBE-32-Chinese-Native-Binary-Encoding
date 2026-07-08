#!/bin/bash
cd "/mnt/c/Users/zairk/Documents/Codex/2026-07-02/codex-dangerously-bypass-approvals-and-sandbox/github-upload/v83_riscv_os"
make clean 2>/dev/null
make all 2>&1
echo ""
echo "=== QEMU ==="
qemu-system-riscv64 -machine virt -kernel output/kernel.elf -nographic
