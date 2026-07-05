.text
.globl main
main:

# hello_test
hello_test:
    li t1, 42
    mv a0, t1
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