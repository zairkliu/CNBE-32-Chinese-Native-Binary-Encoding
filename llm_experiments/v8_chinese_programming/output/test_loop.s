.text
.globl main
main:

# loop_sum
loop_sum:
    li t1, 0
    mv s0, t1
    li t2, 0
    mv s1, t2
    li t3, 10
    li t4, 0
.L1:
    bge t4, t3, .L2
    add t5, s0, s1
    mv s0, t5
    li t0, 1
    add t1, s1, t0
    mv s1, t1
    addi t4, t4, 1
    j .L1
.L2:
    mv a0, s0
    li a7, 1
    ecall
    li t2, 0
    mv a0, t2
    li a7, 93
    ecall

# CNBE runtime stubs
cnhe_map: ret
cnhe_extract: ret
cnhe_cmp: ret