CC = riscv64-linux-gnu-gcc
CFLAGS = -march=rv64im_zicsr -mabi=lp64 -static -O2 -nostdlib -ffreestanding -Iinclude
LDFLAGS = -T src/kernel/linker.ld -nostdlib

OBJS = src/boot/start.o src/kernel/main.o 
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
	qemu-system-riscv64 -machine virt -kernel $(TARGET) -nographic

clean:
	rm -f $(OBJS) $(TARGET) output/kernel.bin
