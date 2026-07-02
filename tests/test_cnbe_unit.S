.section .text
.globl _start
_start:
    # Test 1: CNBE.ENC - encode '中' (U+4E2D)
    li a0, 0x4E2D
    cnbe.enc a1, a0
    # Test 2: CNBE.DEC - decode back to Unicode
    cnbe.dec a2, a1
    # Verify: a2 should equal 0x4E2D
    li t0, 0x4E2D
    bne a2, t0, fail
    # Test 3: CNBE.RAD - extract radical
    cnbe.rad a3, a1
    # Test 4: CNBE.STR - extract strokes
    cnbe.str a4, a1
    # Test 5: CNBE.STRUCT - extract structure
    cnbe.struct a5, a1
    # Test 6: CNBE.DIST - compare '中' and '文'
    li a6, 0x6587
    cnbe.enc a7, a6
    cnbe.dist t0, a1, a7
    # Signal pass
    li a0, 0
    ecall
fail:
    li a0, 1
    ecall
loop: j loop
