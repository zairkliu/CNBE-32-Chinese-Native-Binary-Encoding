#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
V8_DIR="$ROOT/riscv/v8"
SPIKE_SRC="${SPIKE_SRC:-$HOME/tools/riscv-isa-sim}"
PREFIX="${PREFIX:-$HOME/tools/spike-prefix}"
TARBALL="$HOME/tools/riscv-isa-sim.tar.gz"
NPROC="$(nproc)"

if [ ! -d "$SPIKE_SRC" ]; then
    mkdir -p "$HOME/tools" "$(dirname "$SPIKE_SRC")"
    curl -L --max-time 120 -o "$TARBALL" \
        https://github.com/riscv-software-src/riscv-isa-sim/archive/refs/heads/master.tar.gz
    tar -xzf "$TARBALL" -C "$(dirname "$SPIKE_SRC")"
    mv "$(dirname "$SPIKE_SRC")/riscv-isa-sim-master" "$SPIKE_SRC"
fi

cp "$V8_DIR"/spike/cnbe_*.h "$SPIKE_SRC/riscv/insns/"
cp "$V8_DIR/generated/cnbe_skill_table.h" "$SPIKE_SRC/riscv/cnbe_skill_table.h"
cp "$V8_DIR/generated/cnbe_skill_table.cc" "$SPIKE_SRC/riscv/cnbe_skill_table.cc"

# Append encoding declarations if not already present.
if ! grep -q "MATCH_CNBE_MAP" "$SPIKE_SRC/riscv/encoding.h"; then
    cat "$V8_DIR/spike/encoding_additions.h" >> "$SPIKE_SRC/riscv/encoding.h"
fi

# Insert DECLARE_INSN lines inside the #ifdef DECLARE_INSN block.
if ! grep -q "DECLARE_INSN(cnbe_map" "$SPIKE_SRC/riscv/encoding.h"; then
    python3 - "$SPIKE_SRC/riscv/encoding.h" "$V8_DIR/spike/cnbe_declare_insn.h" <<'PY'
import sys

path, decl_path = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
decl = open(decl_path, encoding="utf-8").read().strip()
lines = text.splitlines()
last_decl = max(i for i, line in enumerate(lines) if line.startswith("DECLARE_INSN("))
for j in range(last_decl + 1, len(lines)):
    if lines[j].strip() == "#endif":
        lines[j:j] = decl.splitlines()
        break
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
fi

# Add the generated skill table source to the riscv library.
if ! grep -q "cnbe_skill_table.cc" "$SPIKE_SRC/riscv/riscv.mk.in"; then
    python3 - "$SPIKE_SRC/riscv/riscv.mk.in" <<'PY'
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
target = next(i for i, line in enumerate(lines) if line.strip() == "$(riscv_gen_srcs) \\")
lines.insert(target + 1, "\tcnbe_skill_table.cc \\")
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
fi

# Ensure the CNBE instruction-list variable is defined before riscv_gen_srcs.
if ! grep -q "^riscv_insn_ext_cnbe =" "$SPIKE_SRC/riscv/riscv.mk.in"; then
    python3 - "$SPIKE_SRC/riscv/riscv.mk.in" "$V8_DIR/spike/riscv_mk_additions.mk" <<'PY'
import sys

path, add_path = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().splitlines()
block = open(add_path, encoding="utf-8").read().splitlines()
target = next(i for i, line in enumerate(lines) if line.startswith("riscv_gen_srcs ="))
lines[target:target] = block
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
fi

# Reference the CNBE instruction list inside riscv_insn_list.
if ! grep -q "riscv_insn_ext_cnbe) \\\\" "$SPIKE_SRC/riscv/riscv.mk.in"; then
    python3 - "$SPIKE_SRC/riscv/riscv.mk.in" <<'PY'
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
target = next(i for i, line in enumerate(lines) if line.startswith("riscv_gen_srcs ="))
insert_at = target
while insert_at > 0 and lines[insert_at - 1].strip() == "":
    insert_at -= 1
lines.insert(insert_at, "\t$(riscv_insn_ext_cnbe) \\")
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
fi

BUILD_DIR="$SPIKE_SRC/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
../configure --prefix="$PREFIX"
if ! grep -q "DEFINE_INSN(cnbe_map" "$BUILD_DIR/insn_list.h" 2>/dev/null; then
    rm -f "$BUILD_DIR/insn_list.h"
fi
make -j"$NPROC"
make install

cd "$V8_DIR"
mkdir -p "$V8_DIR/work"
riscv64-unknown-elf-as \
    -o "$V8_DIR/work/test_cnbe_v8_bare.o" \
    "$V8_DIR/spike/test_cnbe_v8_bare.S"
riscv64-unknown-elf-ld \
    -T "$V8_DIR/spike/link.ld" \
    -o "$V8_DIR/work/test_cnbe_v8_bare.elf" \
    "$V8_DIR/work/test_cnbe_v8_bare.o"
if timeout 10 "$PREFIX/bin/spike" --isa=rv64imac_zicsr_zifencei \
    "$V8_DIR/work/test_cnbe_v8_bare.elf"; then
    echo "Spike CNBE v8 test PASS"
else
    echo "Spike CNBE v8 test FAIL"
    exit 1
fi
echo "Spike build complete: $PREFIX/bin/spike"
