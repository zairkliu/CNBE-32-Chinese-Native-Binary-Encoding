OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x80200000, LENGTH = 256M }
SECTIONS {
    .text : { *(.text._start) *(.text*) } > RAM
    .rodata : { *(.rodata*) } > RAM
    .data : { *(.data*) } > RAM
    .bss : { __bss_start = .; *(.bss*); __bss_end = .; } > RAM
    _stack_top = 0x81000000;
}