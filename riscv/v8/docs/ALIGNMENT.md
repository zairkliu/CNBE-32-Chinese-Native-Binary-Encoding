# v8 Alignment Map

**Date**: 2026-08-05  
**Goal**: make the new RISC-V layer align with the existing CNBE-32 project instead of living as a separate demo.

## 1. SDK Alignment (`src/cnbe32`)

| Item | SDK | v8 RISC-V |
|---|---|---|
| Field encoding | `radix(8) stroke(5) struct(4) idx(11) ext(4)` | same bit layout |
| Field distance | D(c₁, c₂) = 8·|Δrad| + 5·|Δstroke| + 4·|Δstruct| | `cnbe.cmp` uses same weights |
| Decode source | code bitfields | same, including the `中` metadata-column discrepancy note |
| Golden vectors | `spec/golden_vectors.json` | `golden/golden_vectors.json` generated from DB |
| Naming | `CNBE-32` | `cnbe.*` instructions, no `CNHE` |

## 2. Data Alignment (`data/cnbe32.db`)

- Skill tables are generated from the same 21,178-row runtime database;
- 8105 standard-track subset is kept separately (`skill_table_8105.bin`);
- `unicode` and `cnbe` are the authoritative identity/code pair;
- field columns in the DB are metadata and may lag the code (example: `中` `struct_type=12` while code bitfield `struct=0`); canonical behavior follows the code bitfield, matching the SDK.

## 3. RISC-V v7 Alignment

- v7 remains as the historical proof-of-concept;
- v8 keeps the Custom-0 encoding space (opcode `0x0B`);
- v8 renames `cnhe.*` to `cnbe.*`;
- v8 adds `cnbe.skill` (reverse lookup) as the fourth instruction;
- v8 uses real DB skill tables instead of the synthetic 20,902-row table.

## 4. Hardware Alignment (`hardware/`)

- v8 provides the clean reference semantics that the existing Verilog CAM and Spike patches should converge to;
- `hardware/` legacy files are kept for history;
- v8 Verilog testbench reads the same `generated/*.hex` and `golden/qemu_expected.txt` used by Python/C/QEMU.

## 5. OS / Mini-Kernel Alignment (`linux_cnbe32_riscv/`)

- v8 defines the instruction semantics that the CNBE shell should use;
- kernel-level integration is a later milestone and must not redefine `cnbe.cmp` weights or field extraction;
- any future CNBE syscall should call the same C reference functions or the same generated table.

## 6. Experiment Alignment

- 8105 standard track: v8 `skill_table_8105.bin` is the hardware-facing version of the 7,602-row standard track;
- GF 0017 structure labels: v8 `struct` field follows the SDK 13-label numbering;
- MoE/OCR experiments do not depend on RISC-V, but any future edge inference should use the same CNBE code semantics.

## 7. Boundary Rules

- v8 is not a ratified ISA extension;
- no silicon performance claims are made from modeled cycle counts;
- `idx` is compatibility-only and not an addressing key;
- radix is project-internal until GF 0011-2009 anchoring is complete;
- all new code uses `cnbe` naming; legacy `CNHE` is retained only for historical files.
