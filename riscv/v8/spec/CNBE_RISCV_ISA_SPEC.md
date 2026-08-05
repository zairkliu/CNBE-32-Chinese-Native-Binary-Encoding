# CNBE-32 RISC-V ISA Specification (v8)

**Version**: 0.1  
**Date**: 2026-08-05  
**Status**: local engineering baseline, subject to external review

## 1. Scope

This specification defines the CNBE-32 custom instructions for a RV32 base processor and the behavior expected from every simulator and hardware model in the v8 layer.

The custom instructions are placed in the **Custom-0** encoding space:

```text
opcode = 0x0B
```

All custom instructions use R-type encoding:

```text
31        25 24      20 19      15 14      12 11       7 6        0
------------------------------------------------------------------------
|  funct7  |   rs2    |   rs1    |  funct3  |    rd    |  opcode   |
------------------------------------------------------------------------
```

For the CNBE instructions, `funct7 = 0` and the operation is selected by `funct3`.

## 2. Instructions

| Mnemonic | funct3 | MATCH | MASK | Semantics |
|---|---|---|---|---|
| `cnbe.map rd, rs1` | 0 | `0x0000000B` | `0xFE00707F` | `rd = skill_lookup(rs1)` |
| `cnbe.extract rd, rs1, rs2` | 1 | `0x0000100B` | `0xFE00707F` | `rd = field_extract(rs1, rs2)` |
| `cnbe.cmp rd, rs1, rs2` | 2 | `0x0000200B` | `0xFE00707F` | `rd = field_distance(rs1, rs2)` |
| `cnbe.skill rd, rs1` | 3 | `0x0000300B` | `0xFE00707F` | `rd = reverse_skill(rs1)` |

### 2.1 `cnbe.map`

Input:

- `rs1`: Unicode code point

Output:

- `rd`: 32-bit CNBE code, or `0` if the Unicode code point is not in the skill table

The lookup uses the generated skill table from `data/cnbe32.db`. The table is sorted by Unicode. A conforming implementation may use direct lookup, CAM, hash, or binary search; the v8 simulator models a fixed 2-cycle latency.

### 2.2 `cnbe.extract`

Input:

- `rs1`: 32-bit CNBE code
- `rs2`: field selector

Output:

- `rd`: field value

| rs2 | Field | Bits | Width |
|---:|---|---|---:|
| 0 | radix | 31:24 | 8 |
| 1 | stroke | 23:19 | 5 |
| 2 | struct | 18:15 | 4 |
| 3 | idx | 14:4 | 11 |
| 4 | ext | 3:0 | 4 |

Invalid selectors return `0`. Modeled latency: 1 cycle.

### 2.3 `cnbe.cmp`

Input:

- `rs1`, `rs2`: CNBE codes

Output:

- `rd`: field-weighted distance

```text
rd = |rad1-rad2| * 8 + |stroke1-stroke2| * 5 + |struct1-struct2| * 4
```

This matches the SDK `field_weighted_distance` implementation. `idx` and `ext` are intentionally excluded. Modeled latency: 3 cycles.

### 2.4 `cnbe.skill`

Input:

- `rs1`: 32-bit CNBE code

Output:

- `rd`: Unicode code point for the first matching skill-table entry, or `0` if not found

This is the reverse lookup of `cnbe.map` and is used for round-trip verification. The skill table may contain duplicate CNBE codes (currently 4 rows in the runtime database); reverse lookup always returns the first match in Unicode order. Modeled latency: 2 cycles.

## 3. Registers and Memory

The v8 Python simulator implements a RV32I subset:

- 32 integer registers, `x0` always zero;
- byte-addressable memory;
- little-endian loads/stores;
- `pc` and cycle counter.

Implemented base instructions:

```text
lui auipc jal jalr
beq bne blt bge bltu bgeu
lb lh lw lbu lhu sb sh sw
addi slti sltiu xori ori andi slli srli srai
add sub sll slt sltu xor srl sra or and
ecall ebreak
```

Unimplemented instructions raise `CNBESimError`.

## 4. Cycle Model

| Instruction | Modeled cycles |
|---|---:|
| base RV32I | 1 |
| `cnbe.map` | 2 |
| `cnbe.extract` | 1 |
| `cnbe.cmp` | 3 |
| `cnbe.skill` | 2 |

Cycle counts are deterministic and are used for trace comparison across implementations. They are a modeling contract, not a silicon performance claim.

## 5. Skill Table

The generated binary format is a sequence of little-endian pairs:

```text
uint32 unicode
uint32 cnbe
```

Generated files:

| File | Content |
|---|---|
| `generated/skill_table.bin` | all 21,178 runtime rows |
| `generated/skill_table_8105.bin` | 7,602 standard-track rows |
| `generated/unicode_table.hex` | Unicode words for Verilog |
| `generated/cnbe_table.hex` | CNBE words for Verilog |
| `generated/cnbe_skill_table.cc` | C array for Spike integration |

## 6. Conformance

A v8 implementation is conforming when it passes the shared golden vectors:

- `cnbe.map` returns the expected CNBE code for each sample Unicode;
- `cnbe.extract` returns the expected fields;
- `cnbe.cmp` returns the SDK field-weighted distance;
- `cnbe.skill` returns the expected Unicode on round-trip;
- unsupported Unicode/codes return `0`.

## 7. Boundaries

- v8 is a research and engineering baseline, not a ratified ISA extension;
- the opcode space `0x0B` is experimental and must be reserved through proper vendor channels before silicon;
- cycle counts are modeled values, not measured silicon results;
- `idx` is a compatibility field and must not be used as an addressing key;
- radix numbering is project-internal until GF 0011-2009 anchoring is complete.
