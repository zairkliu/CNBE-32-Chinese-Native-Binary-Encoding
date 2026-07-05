CC = riscv64-linux-gnu-gcc
CFLAGS = -march=rv64im_zicsr -mabi=lp64 -static -O2 -nostdlib -ffreestanding -Iinclude
LDFLAGS = -T src/kernel/linker.ld -nostdlib
OBJS = src/boot/start.o src/kernel/main.o src/shell/shell.o src/basic/basic.o src/basic/cnbe.o
TARGET = output/kernel.elf
.PHONY: all run clean
all: $(TARGET)
$(TARGET): $(OBJS) src/kernel/linker.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $(TARGET)
	riscv64-linux-gnu-objcopy -O binary $(TARGET) output/kernel.bin
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@
run: $(TARGET)
	qemu-system-riscv64 -M virt -bios none -device loader,file=output/kernel.bin,addr=0x80000000 -nographic
clean:
	rm -f $(OBJS) $(TARGET) output/kernel.bin