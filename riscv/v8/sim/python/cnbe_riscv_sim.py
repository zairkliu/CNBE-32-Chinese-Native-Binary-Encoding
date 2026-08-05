#!/usr/bin/env python3
"""Deterministic RV32I-subset + CNBE-32 custom instruction simulator (v8)."""

from __future__ import annotations

import os
import struct
from typing import Optional


class CNBESimError(RuntimeError):
    pass


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def r_type(funct7: int, rs2: int, rs1: int, funct3: int, rd: int, opcode: int) -> int:
    return (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )


def i_type(imm: int, rs1: int, funct3: int, rd: int, opcode: int) -> int:
    imm &= 0xFFF
    return (imm << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def s_type(imm: int, rs2: int, rs1: int, funct3: int, opcode: int) -> int:
    imm &= 0xFFF
    imm11_5 = (imm >> 5) & 0x7F
    imm4_0 = imm & 0x1F
    return (
        (imm11_5 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (imm4_0 << 7)
        | opcode
    )


def b_type(imm: int, rs2: int, rs1: int, funct3: int, opcode: int) -> int:
    imm &= 0x1FFF
    return (
        ((imm >> 12) & 0x1) << 31
        | ((imm >> 5) & 0x3F) << 25
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | ((imm >> 1) & 0xF) << 8
        | ((imm >> 11) & 0x1) << 7
        | opcode
    )


def u_type(imm: int, rd: int, opcode: int) -> int:
    return ((imm & 0xFFFFF) << 12) | (rd << 7) | opcode


def j_type(imm: int, rd: int, opcode: int) -> int:
    imm &= 0x1FFFFF
    return (
        ((imm >> 20) & 0x1) << 31
        | ((imm >> 1) & 0x3FF) << 21
        | ((imm >> 11) & 0x1) << 20
        | ((imm >> 12) & 0xFF) << 12
        | (rd << 7)
        | opcode
    )


CNBE_OPCODE = 0x0B


def cnbe_map(rd: int, rs1: int) -> int:
    return r_type(0, 0, rs1, 0, rd, CNBE_OPCODE)


def cnbe_extract(rd: int, rs1: int, rs2: int) -> int:
    return r_type(0, rs2, rs1, 1, rd, CNBE_OPCODE)


def cnbe_cmp(rd: int, rs1: int, rs2: int) -> int:
    return r_type(0, rs2, rs1, 2, rd, CNBE_OPCODE)


def cnbe_skill(rd: int, rs1: int) -> int:
    return r_type(0, 0, rs1, 3, rd, CNBE_OPCODE)


class SkillTable:
    def __init__(self, unicode_table: list[int], cnbe_table: list[int]):
        self.unicode_table = unicode_table
        self.cnbe_table = cnbe_table
        self.reverse: dict[int, int] = {}
        for u, c in zip(unicode_table, cnbe_table):
            if c not in self.reverse:
                self.reverse[c] = u

    @classmethod
    def load(cls, path: str) -> "SkillTable":
        unicode_table: list[int] = []
        cnbe_table: list[int] = []
        with open(path, "rb") as fh:
            data = fh.read()
        for i in range(0, len(data), 8):
            u, c = struct.unpack_from("<II", data, i)
            unicode_table.append(u)
            cnbe_table.append(c)
        return cls(unicode_table, cnbe_table)

    def lookup(self, unicode_cp: int) -> int:
        lo, hi = 0, len(self.unicode_table) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            value = self.unicode_table[mid]
            if value == unicode_cp:
                return self.cnbe_table[mid]
            if value < unicode_cp:
                lo = mid + 1
            else:
                hi = mid - 1
        return 0

    def reverse_lookup(self, code: int) -> int:
        return self.reverse.get(code, 0)


class CNBERiscvSim:
    CUSTOM_CYCLES = {0: 1, 1: 0, 2: 2, 3: 1}

    def __init__(
        self,
        skill_table: SkillTable,
        memory_size: int = 1 << 20,
        base: int = 0x80000000,
    ):
        self.skill = skill_table
        self.memory = bytearray(memory_size)
        self.base = base
        self.regs = [0] * 32
        self.pc = base
        self.cycles = 0
        self.halted = False
        self.exit_code = 0
        self.trace: list[dict] = []

    def reset(self) -> None:
        self.regs = [0] * 32
        self.pc = self.base
        self.cycles = 0
        self.halted = False
        self.exit_code = 0
        self.trace = []

    def load_program(self, words: list[int]) -> None:
        if len(words) * 4 > len(self.memory):
            raise CNBESimError("program does not fit in memory")
        for i, word in enumerate(words):
            self.write_u32(self.base + i * 4, word)
        self.pc = self.base

    def load_data(self, address: int, data: bytes) -> None:
        offset = address - self.base
        if offset < 0 or offset + len(data) > len(self.memory):
            raise CNBESimError("data does not fit in memory")
        self.memory[offset : offset + len(data)] = data

    def read_u8(self, address: int) -> int:
        return self.memory[self._offset(address)]

    def read_u16(self, address: int) -> int:
        off = self._offset(address)
        return int.from_bytes(self.memory[off : off + 2], "little")

    def read_u32(self, address: int) -> int:
        off = self._offset(address)
        return int.from_bytes(self.memory[off : off + 4], "little")

    def write_u8(self, address: int, value: int) -> None:
        self.memory[self._offset(address)] = value & 0xFF

    def write_u16(self, address: int, value: int) -> None:
        off = self._offset(address)
        self.memory[off : off + 2] = (value & 0xFFFF).to_bytes(2, "little")

    def write_u32(self, address: int, value: int) -> None:
        off = self._offset(address)
        self.memory[off : off + 4] = u32(value).to_bytes(4, "little")

    def _offset(self, address: int) -> int:
        off = address - self.base
        if off < 0 or off + 4 > len(self.memory):
            raise CNBESimError(f"memory access out of range: 0x{address:08X}")
        return off

    def step(self) -> int:
        if self.halted:
            raise CNBESimError("simulator is halted")
        insn = self.read_u32(self.pc)
        self._exec_instruction(insn)
        return insn

    def step_instruction(self, insn: int) -> int:
        if self.halted:
            raise CNBESimError("simulator is halted")
        self._exec_instruction(insn)
        return insn

    def _exec_instruction(self, insn: int) -> None:
        self.cycles += 1
        self.trace.append({"pc": f"0x{self.pc:08X}", "insn": f"0x{insn:08X}"})
        opcode = insn & 0x7F
        rd = (insn >> 7) & 0x1F
        funct3 = (insn >> 12) & 0x7
        rs1 = (insn >> 15) & 0x1F
        rs2 = (insn >> 20) & 0x1F
        funct7 = (insn >> 25) & 0x7F

        if opcode == CNBE_OPCODE:
            self._exec_cnbe(insn, rd, funct3, rs1, rs2)
        elif opcode == 0x37:  # lui
            self._write_rd(rd, (insn & 0xFFFFF000))
            self.pc += 4
        elif opcode == 0x17:  # auipc
            self._write_rd(rd, u32(self.pc + (insn & 0xFFFFF000)))
            self.pc += 4
        elif opcode == 0x6F:  # jal
            self._write_rd(rd, self.pc + 4)
            self.pc = u32(self.pc + self._jal_imm(insn))
        elif opcode == 0x67:  # jalr
            imm = sign_extend((insn >> 20) & 0xFFF, 12)
            target = u32((self.regs[rs1] + imm) & ~1)
            self._write_rd(rd, self.pc + 4)
            self.pc = target
        elif opcode == 0x63:  # branches
            imm = self._b_imm(insn)
            cond = self._branch_cond(funct3, rs1, rs2)
            self.pc = u32(self.pc + imm) if cond else self.pc + 4
        elif opcode == 0x03:  # loads
            imm = sign_extend((insn >> 20) & 0xFFF, 12)
            addr = u32(self.regs[rs1] + imm)
            self._exec_load(funct3, rd, addr)
            self.pc += 4
        elif opcode == 0x23:  # stores
            imm = self._s_imm(insn)
            addr = u32(self.regs[rs1] + imm)
            self._exec_store(funct3, rs2, addr)
            self.pc += 4
        elif opcode == 0x13:  # op-imm
            imm = sign_extend((insn >> 20) & 0xFFF, 12)
            self._exec_op_imm(funct3, funct7, rs1, rd, imm)
            self.pc += 4
        elif opcode == 0x33:  # op
            self._exec_op(funct3, funct7, rs1, rs2, rd)
            self.pc += 4
        elif opcode == 0x73:  # system
            if insn == 0x00000073:  # ecall
                self.exit_code = self.regs[10] & 0xFF
                self.halted = True
            elif insn == 0x00100073:  # ebreak
                self.halted = True
            else:
                raise CNBESimError(f"unsupported system instruction 0x{insn:08X}")
        else:
            raise CNBESimError(f"unsupported opcode 0x{opcode:02X} at 0x{self.pc:08X}")

    def run(self, max_steps: int = 100000) -> int:
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
        return steps

    def _exec_cnbe(self, insn: int, rd: int, funct3: int, rs1: int, rs2: int) -> None:
        if funct3 == 0:  # cnbe.map
            self._write_rd(rd, self.skill.lookup(self.regs[rs1]))
        elif funct3 == 1:  # cnbe.extract
            code = u32(self.regs[rs1])
            sel = self.regs[rs2] & 0xFF
            value = self._extract_field(code, sel)
            self._write_rd(rd, value)
        elif funct3 == 2:  # cnbe.cmp
            a, b = u32(self.regs[rs1]), u32(self.regs[rs2])
            self._write_rd(rd, self._field_distance(a, b))
        elif funct3 == 3:  # cnbe.skill
            self._write_rd(rd, self.skill.reverse_lookup(u32(self.regs[rs1])))
        else:
            raise CNBESimError(f"invalid CNBE funct3 {funct3}")
        self.cycles += self.CUSTOM_CYCLES.get(funct3, 0)
        self.pc += 4

    @staticmethod
    def _extract_field(code: int, sel: int) -> int:
        if sel == 0:
            return (code >> 24) & 0xFF
        if sel == 1:
            return (code >> 19) & 0x1F
        if sel == 2:
            return (code >> 15) & 0x0F
        if sel == 3:
            return (code >> 4) & 0x7FF
        if sel == 4:
            return code & 0xF
        return 0

    @staticmethod
    def _field_distance(a: int, b: int) -> int:
        return (
            abs(((a >> 24) & 0xFF) - ((b >> 24) & 0xFF)) * 8
            + abs(((a >> 19) & 0x1F) - ((b >> 19) & 0x1F)) * 5
            + abs(((a >> 15) & 0x0F) - ((b >> 15) & 0x0F)) * 4
        )

    def _write_rd(self, rd: int, value: int) -> None:
        if rd != 0:
            self.regs[rd] = u32(value)

    def _exec_load(self, funct3: int, rd: int, addr: int) -> None:
        if funct3 == 0:
            value = sign_extend(self.read_u8(addr), 8)
        elif funct3 == 1:
            value = sign_extend(self.read_u16(addr), 16)
        elif funct3 == 2:
            value = sign_extend(self.read_u32(addr), 32)
        elif funct3 == 4:
            value = self.read_u8(addr)
        elif funct3 == 5:
            value = self.read_u16(addr)
        else:
            raise CNBESimError(f"invalid load funct3 {funct3}")
        self._write_rd(rd, value)

    def _exec_store(self, funct3: int, rs2: int, addr: int) -> None:
        value = self.regs[rs2]
        if funct3 == 0:
            self.write_u8(addr, value)
        elif funct3 == 1:
            self.write_u16(addr, value)
        elif funct3 == 2:
            self.write_u32(addr, value)
        else:
            raise CNBESimError(f"invalid store funct3 {funct3}")

    def _exec_op_imm(self, funct3: int, funct7: int, rs1: int, rd: int, imm: int) -> None:
        src = self.regs[rs1]
        if funct3 == 0:
            result = src + imm
        elif funct3 == 2:
            result = 1 if sign_extend(src, 32) < imm else 0
        elif funct3 == 3:
            result = 1 if src < (imm & 0xFFFFFFFF) else 0
        elif funct3 == 4:
            result = src ^ imm
        elif funct3 == 6:
            result = src | imm
        elif funct3 == 7:
            result = src & imm
        elif funct3 == 1:
            result = src << (imm & 0x1F)
        elif funct3 == 5:
            shamt = imm & 0x1F
            result = (src >> shamt) if (funct7 & 0x20) == 0 else sign_extend(src, 32) >> shamt
        else:
            raise CNBESimError(f"invalid op-imm funct3 {funct3}")
        self._write_rd(rd, result)

    def _exec_op(self, funct3: int, funct7: int, rs1: int, rs2: int, rd: int) -> None:
        a, b = self.regs[rs1], self.regs[rs2]
        sa, sb = sign_extend(a, 32), sign_extend(b, 32)
        if funct3 == 0:
            result = a + b if funct7 == 0 else a - b
        elif funct3 == 1:
            result = a << (b & 0x1F)
        elif funct3 == 2:
            result = 1 if sa < sb else 0
        elif funct3 == 3:
            result = 1 if a < b else 0
        elif funct3 == 4:
            result = a ^ b
        elif funct3 == 5:
            result = (a >> (b & 0x1F)) if funct7 == 0 else (sa >> (b & 0x1F))
        elif funct3 == 6:
            result = a | b
        elif funct3 == 7:
            result = a & b
        else:
            raise CNBESimError(f"invalid op funct3 {funct3}")
        self._write_rd(rd, result)

    def _branch_cond(self, funct3: int, rs1: int, rs2: int) -> bool:
        a, b = self.regs[rs1], self.regs[rs2]
        sa, sb = sign_extend(a, 32), sign_extend(b, 32)
        if funct3 == 0:
            return a == b
        if funct3 == 1:
            return a != b
        if funct3 == 4:
            return sa < sb
        if funct3 == 5:
            return sa >= sb
        if funct3 == 6:
            return a < b
        if funct3 == 7:
            return a >= b
        raise CNBESimError(f"invalid branch funct3 {funct3}")

    @staticmethod
    def _b_imm(insn: int) -> int:
        imm = (
            ((insn >> 31) & 0x1) << 12
            | ((insn >> 7) & 0x1) << 11
            | ((insn >> 25) & 0x3F) << 5
            | ((insn >> 8) & 0xF) << 1
        )
        return sign_extend(imm, 13)

    @staticmethod
    def _s_imm(insn: int) -> int:
        imm = ((insn >> 25) << 5) | ((insn >> 7) & 0x1F)
        return sign_extend(imm, 12)

    @staticmethod
    def _jal_imm(insn: int) -> int:
        imm = (
            ((insn >> 31) & 0x1) << 20
            | ((insn >> 12) & 0xFF) << 12
            | ((insn >> 20) & 0x1) << 11
            | ((insn >> 21) & 0x3FF) << 1
        )
        return sign_extend(imm, 21)


def default_skill_table_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "..", "generated", "skill_table.bin")
