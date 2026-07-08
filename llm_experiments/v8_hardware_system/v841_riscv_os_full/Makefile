CC = riscv64-linux-gnu-gcc
CFLAGS = -march=rv64im_zicsr -mabi=lp64 -static -O2 -nostdlib -ffreestanding -Iinclude -Isrc
LDFLAGS = -T src/kernel/linker.ld -nostdlib

SRCS_BOOT = src/boot/start.S
SRCS_KERNEL = src/kernel/main.c
SRCS_SHELL = src/shell/shell.c
SRCS_BASIC = src/basic/basic.c src/basic/cnbe.c
SRCS_EDITOR = src/editor/reader.c

OBJS = src/boot/start.o src/kernel/main.o src/shell/shell.o src/basic/basic.o src/basic/cnbe.o src/editor/reader.o
TARGET = output/kernel.elf
BIN = output/kernel.bin

.PHONY: all run clean clean-all

all: $(TARGET)

$(TARGET): $(OBJS) src/kernel/linker.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $(TARGET)
	riscv64-linux-gnu-objcopy -O binary $(TARGET) $(BIN)
	@echo "Build complete: $(BIN)"
	@ls -la $(BIN)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

run: $(TARGET)
	qemu-system-riscv64 -machine virt -bios none \
		-device loader,file=$(BIN),addr=0x80200000 \
		-nographic

run-simple: $(TARGET)
	qemu-system-riscv64 -machine virt -kernel $(TARGET) -nographic

clean:
	rm -f $(OBJS) $(TARGET) $(BIN)

clean-all: clean
	rm -f output/*.o output/*.elf output/*.bin
