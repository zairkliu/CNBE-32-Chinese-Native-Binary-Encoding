.text
.globl main
main:

# struct_compare
struct_compare:
    li s0, 0
    li s1, 0
    li s2, 0
    li s3, 0
    li s4, 0
    li s5, 0
    mv t1, s0
    mv s2, t1
    mv t2, s1
    mv s3, t2
    srli t3, s2, 24
    andi t3, t3, 0xFF
    mv s4, t3
    srli t4, s3, 24
    andi t4, t4, 0xFF
    mv s5, t4
    bne s4, s5, .L3
    li t5, 1
    j .L4
.L3: li t5, 0
.L4:
    beqz t5, .L1
    li t0, 1
    mv a0, t0
    li a7, 1
    ecall
    j .L2
.L1:
    li t1, 0
    mv a0, t1
    li a7, 1
    ecall
.L2:
    li t2, 0
    mv a0, t2
    li a7, 93
    ecall

# CNBE runtime stubs
cnhe_map: ret
cnhe_extract: ret
cnhe_cmp: ret