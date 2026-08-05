#!/usr/bin/env python3
"""v8 simulator tests: CNBE custom instructions and RV32I subset."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cnbe_riscv_sim import (  # noqa: E402
    CNBERiscvSim,
    SkillTable,
    b_type,
    cnbe_cmp,
    cnbe_extract,
    cnbe_map,
    cnbe_skill,
    i_type,
    j_type,
    s_type,
    u_type,
)

V8_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN_PATH = os.path.join(V8_DIR, "golden", "golden_vectors.json")
TABLE_PATH = os.path.join(V8_DIR, "generated", "skill_table.bin")


def test_cnbe_custom_instructions() -> None:
    with open(GOLDEN_PATH, "r", encoding="utf-8") as fh:
        golden = json.load(fh)
    table = SkillTable.load(TABLE_PATH)

    for v in golden["map_vectors"]:
        sim = CNBERiscvSim(table)
        sim.regs[10] = v["unicode"]
        sim.step_instruction(cnbe_map(11, 10))
        assert sim.regs[11] == v["code"], f"map failed for {v['char']}"
        assert sim.cycles == 2, f"map cycle mismatch for {v['char']}"

        for sel, expected in [
            (0, v["radix"]),
            (1, v["stroke"]),
            (2, v["struct"]),
            (3, v["idx"]),
            (4, v["ext"]),
        ]:
            sim.reset()
            sim.regs[11] = v["code"]
            sim.regs[12] = sel
            sim.step_instruction(cnbe_extract(13, 11, 12))
            assert sim.regs[13] == expected, f"extract sel={sel} failed for {v['char']}"

        sim.regs[11] = v["code"]
        sim.step_instruction(cnbe_skill(14, 11))
        assert sim.regs[14] == v["reverse_unicode"], f"skill failed for {v['char']}"

    for v in golden["cmp_vectors"]:
        sim = CNBERiscvSim(table)
        sim.regs[10] = v["a"]
        sim.regs[11] = v["b"]
        sim.step_instruction(cnbe_cmp(12, 10, 11))
        assert sim.regs[12] == v["distance"], f"cmp failed for {v['name']}"

    sim = CNBERiscvSim(table)
    sim.regs[10] = golden["not_found_unicode"]
    sim.step_instruction(cnbe_map(11, 10))
    assert sim.regs[11] == golden["not_found_code"]
    print("PASS test_cnbe_custom_instructions")


def test_rv32i_subset() -> None:
    table = SkillTable.load(TABLE_PATH)
    sim = CNBERiscvSim(table)
    words: list[int] = []

    def w(insn: int) -> int:
        words.append(insn)
        return (len(words) - 1) * 4

    w(u_type(0x12345, 5, 0x37))          # lui t0, 0x12345000
    w(i_type(0x678, 5, 0, 5, 0x13))      # addi t0, t0, 0x678
    w(u_type(0x800FF, 2, 0x37))          # lui sp, 0x800FF000
    w(s_type(0, 5, 2, 2, 0x23))          # sw t0, 0(sp)
    w(i_type(0, 2, 2, 6, 0x03))          # lw t1, 0(sp)
    w(b_type(8, 5, 6, 0, 0x63))          # beq t0, t1, +8
    w(i_type(1, 0, 0, 7, 0x13))          # addi t2, zero, 1
    w(i_type(5, 7, 0, 28, 0x13))         # addi t3, t2, 5
    jal_idx = len(words)
    w(0)                                 # placeholder jal ra, func
    w(0x00100073)                        # ebreak
    func_addr = len(words) * 4
    w(i_type(42, 0, 0, 10, 0x13))        # addi a0, zero, 42
    w(i_type(0, 1, 0, 0, 0x67))          # jalr zero, ra, 0
    words[jal_idx] = j_type(func_addr - jal_idx * 4, 1, 0x6F)

    sim.load_program(words)
    steps = sim.run()
    assert sim.halted, "program did not halt"
    assert sim.regs[5] == 0x12345678, "lui/addi failed"
    assert sim.regs[6] == 0x12345678, "load/store failed"
    assert sim.regs[7] == 0, "branch failed"
    assert sim.regs[28] == 5, "addi chain failed"
    assert sim.regs[10] == 42, "jal/jalr failed"
    assert steps == len(words) - 1, f"unexpected step count {steps}"
    print("PASS test_rv32i_subset")


if __name__ == "__main__":
    test_cnbe_custom_instructions()
    test_rv32i_subset()
    print("ALL SIMULATOR TESTS PASSED")
