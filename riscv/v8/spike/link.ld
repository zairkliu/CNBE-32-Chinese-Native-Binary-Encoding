OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
  . = 0x80000000;
  .text : { *(.text) }
  . = ALIGN(4);
  .data : { *(.data) }
  .bss  : { *(.bss) }
}

tohost = 0x80010000;
fromhost = 0x80010008;
