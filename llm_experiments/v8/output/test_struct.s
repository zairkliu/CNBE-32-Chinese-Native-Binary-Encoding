.text
.globl main
main:

# struct_compare
struct_compare:
    li t2, 26862
    mv t1, t2
    mv s0, t1
    li t4, 26576
    mv t3, t4
    mv s1, t3
    srli t5, s0, 24
    andi t5, t5, 0xFF
    mv s2, t5
    srli t0, s1, 24
    andi t0, t0, 0xFF
    mv s3, t0
    li t1, 0
    mv s4, t1
    bne s2, s3, .L3
    li t2, 1
    j .L4
.L3: li t2, 0
.L4:
    beqz t2, .L1
    li t3, 1
    mv s4, t3
    j .L2
.L1:
    li t4, 0
    mv s4, t4
.L2:
    mv a0, s4
    li a7, 1
    ecall
    li t5, 0
    mv a0, t5
    li a7, 93
    ecall

# CNBE runtime stubs
cnhe_map: ret
cnhe_extract: ret
cnhe_cmp: ret