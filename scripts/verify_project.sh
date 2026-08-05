#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/outputs/verification"
LOG="$LOG_DIR/VERIFY_2026-08-05.log"
mkdir -p "$LOG_DIR"

# Local user-space tools used on this WSL machine.
TOOLS_ROOT=/home/zairk/tools/root/usr
if [ -d "$TOOLS_ROOT/bin" ]; then
    export PATH="$TOOLS_ROOT/bin:$PATH"
    export LD_LIBRARY_PATH="$TOOLS_ROOT/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="$TOOLS_ROOT/lib/x86_64-linux-gnu/pkgconfig:$TOOLS_ROOT/share/pkgconfig:${PKG_CONFIG_PATH:-}"
    export IVERILOG="$TOOLS_ROOT/bin/iverilog"
    export VVP="$TOOLS_ROOT/bin/vvp"
fi

exec > >(tee "$LOG") 2>&1

echo "===== CNBE-32 project verification $(date -u +%FT%TZ) ====="

step() {
    echo ""
    echo ">>> $1"
    shift
    "$@"
}

step "v8: generate + Python + C + QEMU" make -C "$ROOT/riscv/v8" all
step "v8: Verilog" make -C "$ROOT/riscv/v8" verilog
step "v8: Spike" make -C "$ROOT/riscv/v8" spike

step "Linux 0.01: build" make -C "$ROOT/linux_cnbe32_riscv" all
step "Linux 0.01: runtime alignment" make -C "$ROOT/linux_cnbe32_riscv" verify
step "Linux 0.01: QEMU boot smoke" make -C "$ROOT/linux_cnbe32_riscv" boot-smoke

step "Math: five directions + deep analysis" make -C "$ROOT/experiments/2026-08-05_cnbe_math" verify

echo ""
echo "ALL LOCAL VERIFICATION PASSED"
echo "LOG: $LOG"
