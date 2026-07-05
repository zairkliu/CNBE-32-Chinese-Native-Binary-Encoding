# RISCV Hardware Implementation (v7 Series)

This directory documents the CNBE-32 RISC-V hardware implementation,
from software emulation through FPGA prototype.

## Directory Structure

| Directory | Version | Content |
|-----------|:-------:|---------|
| `v7.0_c_impl/` | v7.0 | C language skill table implementation |
| `v7.0.1_qemu/` | v7.0.1 | RISC-V cross compilation + QEMU verification |
| `v7.1_spike/` | v7.1 | RISC-V custom instruction encoding verification |
| `v7.1.1_custom_insn/` | v7.1.1 | Spike integrated custom instruction source |
| `v7.2_fpga/` | v7.2 | Verilog RTL and FPGA synthesis |
| `src/` | - | Verilog modules, C tests, assembly tests |
| `skill_table/` | - | CNBE skill table (.hex, .npy, .bin) |

## White Papers

| File | Experiment |
|------|------------|
| `CNBE-32_v7.0_*.md` | C implementation baseline (0.8ns lookup) |
| `CNBE-32_v7.0.1_*.md` | QEMU/Spike toolchain verification (2.5ns) |
| `CNBE-32_v7.1_*.md` | Custom instruction encoding (.insn -> SIGILL) |
| `CNBE-32_v7.1.1_*.md` | Spike integrated cnhe.map/extract/cmp |
| `CNBE-32_v7.2_*.md` | Verilog RTL + FPGA synthesis (81.6KB BRAM) |

## Key Results

| Metric | Value |
|--------|-------|
| Skill table size | 81.6KB (fits in L2 cache) |
| x86 single lookup | 0.8 ns |
| QEMU RISC-V lookup | 2.5 ns (simulated) |
| Spike instruction type | Custom-0 (opcode=0x0B) |
| FPGA BRAM | 81.6KB, single-cycle access |
| Min verification | QEMU RISC-V user-mode, 3 instructions |

## See Also

The `hardware/spike-patches/` directory in the repo root contains
the original v2 Spike patches for reference.
