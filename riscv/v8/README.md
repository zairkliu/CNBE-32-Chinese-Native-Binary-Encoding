# CNBE-32 RISC-V v8 Layer

**Status**: local engineering foundation (not cloud-dependent)  
**Date**: 2026-08-05  
**Goal**: rebuild the CNBE-32 RISC-V work around a deterministic simulator as the single source of truth.

## Why v8

The v7 series proved the idea: CNBE fields can be encoded, extracted, compared, and verified with RISC-V custom instructions. v8 turns that proof into a reproducible foundation:

- ISA behavior is defined by one spec;
- Golden vectors are generated from `data/cnbe32.db` (21,178 rows);
- Python simulator, C reference, Spike, QEMU, and Verilog all align to the same vectors;
- Skill tables come from the real runtime database, not synthetic data;
- Everything runs locally in WSL; no GPU or cloud is required.

## Directory Layout

```text
v8/
  README.md
  Makefile
  spec/CNBE_RISCV_ISA_SPEC.md
  golden/golden_vectors.json
  tools/gen_skill_table.py
  tools/gen_golden_vectors.py
  generated/                # generated skill tables and headers
  sim/python/cnbe_riscv_sim.py
  sim/python/test_sim.py
  sim/c/cnbe_ref.c
  sim/c/cnbe_ref.h
  qemu/test_cnbe_qemu.c
  spike/                    # Spike patch files and build script
  verilog/                  # CNBE execution unit and testbench
  docs/ALIGNMENT.md
```

## Quick Start

```bash
cd repo/riscv/v8
make generate      # create skill tables and golden vectors from cnbe32.db
make python-sim    # run the Python cycle simulator tests
make c-ref         # run the C reference on host
make qemu          # cross-compile and run under qemu-riscv64
make verilog       # run Verilog testbench if iverilog is available
make spike         # build patched Spike and run assembly test
```

## Ubuntu 26.04 Verified (2026-08-05)

All local experiments were run in WSL `Ubuntu-26.04`:

```text
make generate  -> 21,178 rows, 7,602 standard, 4 duplicate codes
make python-sim -> PASS
make c-ref      -> 7 passed, 0 failed
make qemu       -> 7 passed, 0 failed
make verilog    -> 55 passed, 0 failed (iverilog 12.0)
make spike      -> PASS (patched Spike, bare-metal tohost exit)
```

The user-space toolchain used by the local run:

```text
/home/zairk/tools/root/usr/bin/iverilog
/home/zairk/tools/root/usr/bin/vvp
/home/zairk/tools/root/usr/bin/pkg-config
```

For Verilog:

```bash
make verilog IVERILOG=/home/zairk/tools/root/usr/bin/iverilog \
             VVP=/home/zairk/tools/root/usr/bin/vvp
```

For Spike, the build script expects `pkg-config`, `libfdt-dev`, the RISC-V
toolchain, and a writable home prefix. It downloads riscv-isa-sim to
`$HOME/tools` and installs the patched binary to `$HOME/tools/spike-prefix`.

## Alignment

See [docs/ALIGNMENT.md](docs/ALIGNMENT.md) for how v8 maps to the `cnbe32` SDK, v7 RISC-V work, hardware prototypes, the Linux mini-kernel, and the experiment reports.

The full verification process is publicized in
[docs/VERIFICATION_REPORT_2026-08-05.md](docs/VERIFICATION_REPORT_2026-08-05.md).
