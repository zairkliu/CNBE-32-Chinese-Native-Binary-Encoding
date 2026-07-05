CC = riscv64-linux-gnu-gcc
CFLAGS = -march=rv64im_zicsr -mabi=lp64 -static -O2 -nostdlib -ffreestanding -Iinclude
LDFLAGS = -T src/kernel/linker.ld -nostdlib
OBJS = src/boot/start.o src/kernel/main.o src/shell/shell.o src/basic/basic.o src/basic/cnbe.o
TARGET = output/kernel.elf
.PHONY: all run clean
all: 
:  src/kernel/linker.ld
	   -o 
	riscv64-linux-gnu-objcopy -O binary  output/kernel.bin
%.o: %.c
	  -c $< -o 
%.o: %.S
	  -c $< -o 
run: 
	qemu-system-riscv64 -machine virt -bios default -kernel  -nographic
clean:
	rm -f   output/kernel.bin
