# Linux 0.01 CNBE-32 for RISC-V Makefile
# 基于仓库 v84_riscv_os_full/Makefile 扩展
# 编译器: riscv64-linux-gnu-gcc
# 目标硬件: 1GHz RISC-V | 32MB L3 Cache | 1GB RAM | 1GB Storage

CC      = riscv64-linux-gnu-gcc
LD      = riscv64-linux-gnu-ld
OBJCOPY = riscv64-linux-gnu-objcopy
OBJDUMP = riscv64-linux-gnu-objdump

# RISC-V 架构: RV64I + M + Zicsr (CSR 支持)
# -static -nostdlib -ffreestanding: 独立内核，不依赖 libc
# -O2: 优化级别 (1GHz 主频下平衡性能与代码体积)
# -mcmodel=medany: 适合 1GB 地址空间的代码模型
CFLAGS  = -march=rv64im_zicsr -mabi=lp64 -mcmodel=medany \
          -static -O2 -nostdlib -ffreestanding -fno-pic \
          -Wall -Wextra -Wno-unused-parameter \
          -Iinclude -fno-exceptions -fno-rtti -fno-threadsafe-statics

# 链接器脚本: 定义 1GB 内存布局
LDFLAGS = -T kernel/linker.ld -nostdlib -nostartfiles

# 启动代码 (RISC-V 汇编)
BOOT_OBJS = boot/start.o

# 初始化
INIT_OBJS = init/main.o

# 内核核心
KERNEL_OBJS = kernel/sched.o kernel/traps.o kernel/fork.o \
              kernel/exit.o kernel/panic.o kernel/printk.o \
              kernel/vsprintf.o kernel/console.o kernel/tty_io.o \
              kernel/keyboard.o kernel/serial.o kernel/hd.o \
              kernel/mktime.o kernel/sys.o kernel/asm.o \
              kernel/system_call.o kernel/rs_io.o \
              kernel/cnbe_basic.o kernel/cnbe_shell.o kernel/cnbe_compiler.o

# 内存管理
MM_OBJS = mm/memory.o mm/page.o

# 文件系统
FS_OBJS = fs/bitmap.o fs/block_dev.o fs/buffer.o fs/char_dev.o \
          fs/exec.o fs/fcntl.o fs/file_dev.o fs/file_table.o \
          fs/inode.o fs/ioctl.o fs/namei.o fs/open.o fs/pipe.o \
          fs/read_write.o fs/stat.o fs/super.o fs/truncate.o fs/tty_ioctl.o

# 内核库
LIB_OBJS = lib/_exit.o lib/close.o lib/ctype.o lib/dup.o \
           lib/errno.o lib/execve.o lib/open.o lib/read.o lib/setsid.o \
           lib/string.o lib/wait.o lib/write.o

# CNBE-32 运行时
CNBE_OBJS = cnbe/cnbe.o

ALL_OBJS = $(BOOT_OBJS) $(INIT_OBJS) $(KERNEL_OBJS) $(MM_OBJS) \
           $(FS_OBJS) $(LIB_OBJS) $(CNBE_OBJS)

TARGET_ELF = output/kernel.elf
TARGET_BIN = output/kernel.bin
TARGET_MAP = output/kernel.map

.PHONY: all run qemu clean disasm

all: $(TARGET_BIN)

$(TARGET_ELF): $(ALL_OBJS) kernel/linker.ld
	$(LD) $(LDFLAGS) $(ALL_OBJS) -o $(TARGET_ELF)
	$(OBJDUMP) -d $(TARGET_ELF) > $(TARGET_MAP)

$(TARGET_BIN): $(TARGET_ELF)
	$(OBJCOPY) -O binary $(TARGET_ELF) $(TARGET_BIN)

# 模式规则
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	$(CC) $(CFLAGS) -D__ASSEMBLY__ -c $< -o $@

# QEMU 运行 (RISC-V virt 平台, 1GB 内存)
run: $(TARGET_BIN)
	qemu-system-riscv64 \
		-M virt \
		-m 1024M \
		-smp 1 \
		-bios none \
		-kernel $(TARGET_BIN) \
		-nographic \
		-serial stdio

qemu: run

# 反汇编查看
disasm: $(TARGET_ELF)
	$(OBJDUMP) -d $(TARGET_ELF) | less

# 清理
clean:
	rm -f $(ALL_OBJS) $(TARGET_ELF) $(TARGET_BIN) $(TARGET_MAP)

# 生成 CNBE-32 Skill 表 (需要 Python 运行时)
gen-table:
	python3 tools/gen_cnbe_table.py
