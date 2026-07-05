# CNBE-32 Spike Custom Instruction Integration (v7.1.1)

This directory contains the three CNBE-32 RISC-V custom instructions
integrated into the Spike ISA simulator:

## Instructions

| Instruction | funct3 | MATCH | MASK | Function |
|-------------|:------:|:-----:|:----:|----------|
| `cnhe.map` | 0 | 0x0000000B | 0xFE00707F | Unicode -> CNBE encoding lookup |
| `cnhe.extract` | 1 | 0x0000100B | 0xFE00707F | Extract field from CNBE code |
| `cnhe.cmp` | 2 | 0x0000200B | 0xFE00707F | Compare two CNBE codes |

## Files

- `cnhe_map.h` - cnhe.map instruction behavior (direct array lookup)
- `cnhe_extract.h` - cnhe.extract instruction behavior (bitfield extraction)
- `cnhe_cmp.h` - cnhe.cmp instruction behavior (weighted distance)
- `cnhe_skill_table.h` - Skill table header (constants and declarations)
- `cnhe_skill_table.cc` - Skill table data (83.6KB, embedded in Spike)

## Spike Integration

To integrate into Spike:

1. Copy `cnhe_map.h`, `cnhe_extract.h`, `cnhe_cmp.h` to `riscv/insns/`
2. Copy `cnhe_skill_table.h`, `cnhe_skill_table.cc` to `riscv/`
3. Add MATCH/MASK definitions to `riscv/encoding.h` (see encoding_additions.h)
4. Add instruction files to `riscv/riscv.mk.in`

## Encoding Format

All three instructions use the **Custom-0** encoding space (opcode=0x0B)
with R-type format and funct3 field for opcode selection:

```
31  27 26  25 24  20 19  15 14  12 11  7 6    0
+------+-----+------+------+------+------+-------+
| rs2  | rs1 | funct3|  rd  | opcode |  [31:0]  |
+------+-----+------+------+------+-------+
```

See `encoding_changes.md` for the full MATCH/MASK definitions.
