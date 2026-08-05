.section .text
.globl main
main:
    # cnbe.map a0, a1   (a1 = U+4E2D 中)
    li a1, 0x4E2D
    .word 0x0005850B
    li t0, 0x022002D0
    bne a0, t0, fail

    # cnbe.extract a0, a0, a2   (a2 = 1 -> stroke)
    li a2, 1
    .word 0xC5950B
    li t0, 4
    bne a0, t0, fail

    # cnbe.cmp a0, a1, a2       (a1 = 中 code, a2 = 学 code)
    li a1, 0x022002D0
    li a2, 0x27415660
    .word 0xC5A50B
    li t0, 324
    bne a0, t0, fail

    # cnbe.skill a0, a1         (round-trip to U+4E2D)
    li a1, 0x022002D0
    .word 0x0005B50B
    li t0, 0x4E2D
    bne a0, t0, fail

    li a0, 0
    ret
fail:
    li a0, 1
    ret
