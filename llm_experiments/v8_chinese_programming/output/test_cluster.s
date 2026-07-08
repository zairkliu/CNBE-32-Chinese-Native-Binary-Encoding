.text
.globl main
main:

# cluster_test
cluster_test:
    li s0, 0
    li s1, 0
    li s2, 0
    mv t1, s3
    mv s0, t1
    mv t2, s4
    mv s1, t2
    xor t3, s0, s1
    mv s2, t3
    mv a0, s2
    li a7, 1
    ecall
    li t4, 0
    mv a0, t4
    li a7, 93
    ecall

# CNBE runtime stubs
cnhe_map: ret
cnhe_extract: ret
cnhe_cmp: ret