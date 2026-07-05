.section .text
.globl main
main:
    li a1, 0x5B66
    .word 0x0001D00B
    beqz a0, fail
    mv a1, a0
    li a2, 0
    .word 0x0107850B
    li t0, 39
    bne a0, t0, fail
    li a1, 0xFFFFFFFF
    li a2, 0
    .word 0x0107A50B
    li t0, 32
    bne a0, t0, fail
    li a0, 0
    ret
fail:
    li a0, 1
    ret
