.section .text._start
.globl _start
_start:
    la sp, _stack_top
    call main
    wfi
    j .