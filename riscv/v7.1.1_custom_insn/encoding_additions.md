# Spike encoding.h Additions

Add the following to `riscv/encoding.h` after the existing DECLARE_INSN lines:

```c
// CNBE-32 v7.1 Custom Instructions (Custom-0, opcode=0x0b)
#define MATCH_CNHE_MAP     0x0000000b
#define MASK_CNHE_MAP      0xfe00707f
#define MATCH_CNHE_EXTRACT 0x0000100b
#define MASK_CNHE_EXTRACT  0xfe00707f
#define MATCH_CNHE_CMP     0x0000200b
#define MASK_CNHE_CMP      0xfe00707f

DECLARE_INSN(cnhe_map, MATCH_CNHE_MAP, MASK_CNHE_MAP)
DECLARE_INSN(cnhe_extract, MATCH_CNHE_EXTRACT, MASK_CNHE_EXTRACT)
DECLARE_INSN(cnhe_cmp, MATCH_CNHE_CMP, MASK_CNHE_CMP)
```

## riscv.mk.in Addition

Add to `riscv/riscv.mk.in`:

```makefile
riscv_insn_ext_cnhe = \
	cnhe_map \
	cnhe_extract \
	cnhe_cmp
```

## processor.cc Addition

Add state variables for CNBE cycle counters:

```cpp
// In processor_t constructor
cnbe_cycle_counter = 0;
cnbe_inst_map_count = 0;
cnbe_inst_extract_count = 0;
cnbe_inst_cmp_count = 0;
```

## Instruction Encoding Format

All instructions use R-type Custom-0 encoding:

| Bit field | Description |
|:---------:|-------------|
| [6:0] | opcode = 0x0B (Custom-0) |
| [14:12] | funct3: 0=map, 1=extract, 2=cmp |
| [19:15] | rs1 (source register 1) |
| [24:20] | rs2 (source register 2, for extract/cmp) |
| [11:7] | rd (destination register) |
| [31:25] | funct7 = 0 (for map, extended funct for others) |

## Compatibility Note

These v7.1 instructions replace the previous v2 instruction set:
- `cnhe.map` replaces `cnbe_enc` (same funct3=0)
- `cnhe.extract` replaces `cnbe_dec` (same funct3=1)
- `cnhe.cmp` replaces `cnbe_rad` (same funct3=2)

The new design uses direct array lookup (O(1)) instead of binary search,
and weighted absolute difference distance instead of popcount-based distance.
