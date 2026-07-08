.text
.globl main
main:

# hello_test
hello_test:
    li t1, 42
    addi sp, sp, -16
    sw t1, 0(sp)
    li a7, 64
    li a0, 1
    mv a1, sp
    li a2, 4
    ecall
    addi sp, sp, 16
    li t2, 0
    mv a0, t2
    li a7, 93
    ecall

# CNBE runtime stubs
cnhe_map: ret
cnhe_extract: ret
cnhe_cmp: ret