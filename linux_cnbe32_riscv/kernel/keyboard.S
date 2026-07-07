/*
 * 【RISC-V 转码状态】kernel/keyboard.S
 * 原始文件: Linux 0.01 kernel/keyboard.s
 * 转码目标: RISC-V 64/32 + CNBE-32 中文环境
 * 转码变更:
 *   - x86 32位汇编 → RISC-V 64/32 汇编
 *   - 移除 x86 段寄存器操作 (push %ds, push %es, mov %ax, %ds)
 *   - 移除 inb/outb 指令 (x86 I/O 端口) → 内存映射 I/O 加载/存储
 *   - x86 调用约定 (eax, ebx, ecx, edx) → RISC-V 调用约定 (a0-a7, ra)
 *   - x86 栈操作 (pushl/popl) → RISC-V 栈操作 (addi sp, sd/ld)
 *   - iret → RISC-V mret (从中断返回)
 *   - 键盘中断号: x86 0x21 → RISC-V 外部中断 via PLIC/CLINT
 *   - 保留键盘扫描码处理逻辑和键码表
 *   - 添加中文注释
 *   - 集成 CNBE-32 头文件
 *
 * 【RISC-V 说明】
 * RISC-V 无段式内存，使用扁平虚拟地址空间。
 * 键盘控制器在 x86 中通过 I/O 端口 0x60/0x61/0x64 访问。
 * RISC-V 平台通常使用内存映射的键盘控制器或 virtio-input。
 * 本文件保留 PS/2 键盘逻辑框架，但使用 MMIO 地址访问。
 * 实际平台需根据设备树调整 MMIO 基址。
 */

#include <asm/system.h>        /* RISC-V CSR 定义 */

/* 文本段 */
	.text
	.globl keyboard_interrupt

/*
 * 键盘读取队列常量定义
 * 这些必须与 tty_io.c 中的定义一致！
 */
	.equ SIZE, 1024         /* 必须是 2 的幂！ */
	.equ HEAD, 4
	.equ TAIL, 8
	.equ PROC_LIST, 12
	.equ BUF, 16

/*
 * 键盘状态变量
 * 由于 RISC-V 汇编中 .byte 和 .space 的使用方式与 x86 相同，
 * 这里保留原始布局，但使用 RISC-V 汇编语法。
 */
	.bss
	.align 2
mode:
	.byte 0                 /* 大写、alt、ctrl 和 shift 模式 */
leds:
	.byte 0                 /* 数字锁、大写、滚动锁模式 (数字锁开启) */
e0:
	.byte 0

	.text
/*
 * keyboard_interrupt 是实际的中断处理程序，
 * 读取键盘扫描码并转换为相应的 ASCII 字符。
 *
 * 【RISC-V 中断栈帧】
 * 进入中断时，硬件已保存:
 *   - mepc (返回地址)
 *   - mcause (中断原因)
 *   - mstatus (处理器状态)
 * 软件需保存:
 *   - 所有被调用者保存的寄存器 (s0-s11)
 *   - 参数寄存器 (a0-a7)
 *   - 返回地址 (ra)
 *
 * 注意：实际的 RISC-V 中断入口通常由 trap_entry.S 处理，
 * 此函数作为 C 可调用函数，由通用中断分发器调用。
 */
keyboard_interrupt:
	/* 保存寄存器到栈 */
	addi	sp, sp, -80
	sd	ra, 0(sp)
	sd	a0, 8(sp)
	sd	a1, 16(sp)
	sd	a2, 24(sp)
	sd	a3, 32(sp)
	sd	a4, 40(sp)
	sd	a5, 48(sp)
	sd	s0, 56(sp)
	sd	s1, 64(sp)

	/* 【RISC-V 替换】xorl %al, %al → 清零 a0 (扫描码寄存器) */
	li	a0, 0

	/*
	 * 【RISC-V 替换】inb $0x60, %al → 从 MMIO 键盘数据端口读取
	 * 键盘数据端口 MMIO 地址 (占位符，需按平台调整)
	 */
	li	s0, 0x10011000          /* 键盘数据端口 MMIO 基址 */
	lbu	a0, 0(s0)               /* a0 = 扫描码 */

	/* 【RISC-V 替换】cmpb $0xe0, %al → 比较 a0 */
	li	t0, 0xE0
	beq	a0, t0, set_e0
	li	t0, 0xE1
	beq	a0, t0, set_e1

	/*
	 * 【RISC-V 替换】call key_table(,%eax,4) → 汇编查表跳转
	 * x86 使用 4 字节索引的跳转表，RISC-V 64位使用 8 字节索引。
	 * a0 保存扫描码，从 key_table 加载对应的函数指针并调用。
	 */
	la	t0, key_table
	slli	t1, a0, 3              /* t1 = scan_code * 8 (64-bit pointer) */
	add	t0, t0, t1
	ld	t1, 0(t0)               /* t1 = key_table[scan_code] */
	jalr	ra, t1, 0              /* 调用处理函数 */

	/* 【RISC-V 替换】movb $0, e0 → 清零 e0 标志 */
	la	t0, e0
	sb	zero, 0(t0)
	e0_e1:

	/*
	 * 【RISC-V 替换】x86 键盘控制器 EOI 序列 → RISC-V 简化
	 * 原始 x86 代码:
	 *   inb $0x61, %al
	 *   orb $0x80, %al
	 *   outb %al, $0x61
	 *   andb $0x7F, %al
	 *   outb %al, $0x61
	 *   movb $0x20, %al
	 *   outb %al, $0x20
	 * RISC-V 无 8259A PIC，EOI 通过 PLIC 完成。
	 * 此处仅设置键盘 ACK（如果平台支持），
	 * 并调用 do_tty_interrupt(0)。
	 */
	li	a0, 0
	call	do_tty_interrupt

	/* 恢复寄存器 */
	ld	ra, 0(sp)
	ld	a0, 8(sp)
	ld	a1, 16(sp)
	ld	a2, 24(sp)
	ld	a3, 32(sp)
	ld	a4, 40(sp)
	ld	a5, 48(sp)
	ld	s0, 56(sp)
	ld	s1, 64(sp)
	addi	sp, sp, 80

	/* 返回调用者 (mret 由中断入口处理) */
	ret

set_e0:
	la	t0, e0
	li	t1, 1
	sb	t1, 0(t0)
	j	e0_e1

set_e1:
	la	t0, e0
	li	t1, 2
	sb	t1, 0(t0)
	j	e0_e1


/*
 * ============================================================
 * 以下为保留的键盘处理数据表和处理函数。
 * 这些函数在 RISC-V 中更适合用 C 实现，
 * 但为保持与原始代码的对应关系，此处保留汇编版本。
 * ============================================================
 */

	.text
/*
 * put_queue - 将最多 8 字节的数据填入缓冲区
 * 参数: a0 = 低字节, a1 = 高字节 (扩展的 64 位)
 * 原始 x86 使用 ebx:eax，RISC-V 使用 a1:a0。
 * 字节写入顺序: a0[7:0], a0[15:8], a0[23:16], a0[31:24]...
 */
	.globl put_queue
put_queue:
	addi	sp, sp, -32
	sd	s0, 0(sp)
	sd	s1, 8(sp)
	sd	s2, 16(sp)
	sd	s3, 24(sp)

	/* s0 = table_list[0] (控制台读取队列) */
	la	s0, table_list
	ld	s0, 0(s0)               /* s0 = &tty_table[0].read_q */

	/* s1 = head */
	lw	s1, HEAD(s0)

1:
	/* buf[s0 + s1] = a0[7:0] */
	andi	s2, a0, 0xFF
	add	s3, s0, s1
	sb	s2, BUF(s3)

	/* head++ */
	addi	s1, s1, 1
	andi	s1, s1, SIZE - 1

	/* 检查缓冲区是否满 */
	lw	s2, TAIL(s0)
	beq	s1, s2, 3f             /* 如果满，丢弃 */

	/* 右移 8 位，检查是否为零 */
	srli	a0, a0, 8
	beq	a0, zero, 2f
	j	1b

2:
	/* 保存 head */
	sw	s1, HEAD(s0)

	/* 唤醒等待进程 */
	lw	s2, PROC_LIST(s0)
	beq	s2, zero, 3f
	sw	zero, 0(s2)

3:
	ld	s0, 0(sp)
	ld	s1, 8(sp)
	ld	s2, 16(sp)
	ld	s3, 24(sp)
	addi	sp, sp, 32
	ret


/*
 * ctrl / alt 处理
 */
	.globl ctrl
ctrl:
	li	a0, 0x04
	j	1f

	.globl alt
alt:
	li	a0, 0x10

1:
	la	t0, e0
	lbu	t1, 0(t0)
	beq	t1, zero, 2f
	slli	a0, a0, 1

2:
	la	t0, mode
	lbu	t1, 0(t0)
	or	t1, t1, a0
	sb	t1, 0(t0)
	ret

	.globl unctrl
unctrl:
	li	a0, 0x04
	j	1f

	.globl unalt
unalt:
	li	a0, 0x10

1:
	la	t0, e0
	lbu	t1, 0(t0)
	beq	t1, zero, 2f
	slli	a0, a0, 1

2:
	la	t0, mode
	lbu	t1, 0(t0)
	not	a0, a0
	and	t1, t1, a0
	sb	t1, 0(t0)
	ret


/*
 * shift 处理
 */
	.globl lshift
lshift:
	la	t0, mode
	lbu	t1, 0(t0)
	ori	t1, t1, 0x01
	sb	t1, 0(t0)
	ret

	.globl unlshift
unlshift:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t1, t1, 0xFE
	sb	t1, 0(t0)
	ret

	.globl rshift
rshift:
	la	t0, mode
	lbu	t1, 0(t0)
	ori	t1, t1, 0x02
	sb	t1, 0(t0)
	ret

	.globl unrshift
unrshift:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t1, t1, 0xFD
	sb	t1, 0(t0)
	ret


/*
 * caps / scroll / num 处理
 */
	.globl caps
caps:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x80
	bnez	t2, 1f
	la	t0, leds
	lbu	t1, 0(t0)
	xori	t1, t1, 0x04
	sb	t1, 0(t0)
	la	t0, mode
	lbu	t1, 0(t0)
	xori	t1, t1, 0x40
	ori	t1, t1, 0x80
	sb	t1, 0(t0)
	j	set_leds

1:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t1, t1, 0x7F
	sb	t1, 0(t0)
	ret

	.globl uncaps
uncaps:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t1, t1, 0x7F
	sb	t1, 0(t0)
	ret

	.globl scroll
scroll:
	la	t0, leds
	lbu	t1, 0(t0)
	xori	t1, t1, 0x01
	sb	t1, 0(t0)
	j	set_leds

	.globl num
num:
	la	t0, leds
	lbu	t1, 0(t0)
	xori	t1, t1, 0x02
	sb	t1, 0(t0)
	j	set_leds

set_leds:
	/* 【RISC-V 注释】键盘 LED 设置需要平台特定的控制器支持 */
	/* x86 代码使用 kb_wait + outb 0x60 发送命令 */
	/* RISC-V 平台若有 PS/2 控制器，使用 MMIO 发送 */
	ret


/*
 * cursor - 光标键/数字键盘处理
 */
	.globl cursor
cursor:
	addi	a0, a0, -0x47
	bltz	a0, 1f
	li	t0, 12
	bgt	a0, t0, 1f

	/* 检查 Ctrl-Alt-Del */
	bne	a0, zero, cur2
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x0C
	beq	t2, zero, cur2
	andi	t2, t1, 0x30
	bnez	t2, reboot

cur2:
	la	t0, e0
	lbu	t1, 0(t0)
	li	t2, 1
	beq	t1, t2, cur          /* e0 强制光标移动 */

	la	t0, leds
	lbu	t1, 0(t0)
	andi	t2, t1, 0x02
	beq	t2, zero, cur       /* 非数字锁强制光标 */

	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x03
	bnez	t2, cur             /* shift 强制光标 */

	li	a1, 0
	la	t0, num_table
	add	t0, t0, a0
	lbu	a0, 0(t0)
	j	put_queue

1:
	ret

cur:
	la	t0, cur_table
	add	t0, t0, a0
	lbu	a0, 0(t0)
	li	t0, '9'
	bgt	a0, t0, ok_cur
	li	t1, '~'
	slli	t1, t1, 8
	or	a0, a0, t1
ok_cur:
	slli	a0, a0, 16
	li	t0, 0x5B1B
	or	a0, a0, t0
	li	a1, 0
	j	put_queue


/*
 * func - 功能键处理
 */
	.globl func
func:
	addi	a0, a0, -0x3B
	bltz	a0, end_func
	li	t0, 9
	ble	a0, t0, ok_func
	addi	a0, a0, -18
	bltz	a0, end_func
	li	t0, 10
	ble	a0, t0, ok_func
	li	t0, 11
	bgt	a0, t0, end_func
ok_func:
	li	t0, 4
	blt	a2, t0, end_func
	/* func_table 查找 - 64位版本，每项 8 字节 */
	la	t0, func_table
	slli	a0, a0, 3
	add	t0, t0, a0
	ld	a0, 0(t0)
	li	a1, 0
	j	put_queue
end_func:
	ret


/*
 * do_self - 处理普通按键
 */
	.globl do_self
do_self:
	la	s0, alt_map
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x20
	bnez	t2, 1f

	la	s0, shift_map
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x03
	bnez	t2, 1f

	la	s0, key_map

1:
	add	s0, s0, a0
	lbu	a0, 0(s0)
	beq	a0, zero, none

	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x4C
	beq	t2, zero, 2f

	li	t0, 'a'
	blt	a0, t0, 2f
	li	t0, 'z'
	bgt	a0, t0, 2f
	addi	a0, a0, -32

2:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x0C
	beq	t2, zero, 3f

	li	t0, 64
	blt	a0, t0, 3f
	li	t0, 96
	bge	a0, t0, 3f
	addi	a0, a0, -64

3:
	la	t0, mode
	lbu	t1, 0(t0)
	andi	t2, t1, 0x10
	beq	t2, zero, 4f
	ori	a0, a0, 0x80

4:
	andi	a0, a0, 0xFF
	li	a1, 0
	call	put_queue
none:
	ret


/*
 * minus - 处理减号/小键盘斜杠
 */
	.globl minus
minus:
	la	t0, e0
	lbu	t1, 0(t0)
	li	t2, 1
	bne	t1, t2, do_self
	li	a0, '/'
	li	a1, 0
	j	put_queue


/*
 * kb_wait - 等待键盘控制器缓冲区为空
 * 无超时 - 如果缓冲区不清空，系统挂起。
 */
	.globl kb_wait
kb_wait:
	li	s0, 0x10011004          /* 键盘状态端口 MMIO */
1:
	lbu	t0, 0(s0)
	andi	t0, t0, 0x02
	bnez	t0, 1b
	ret


/*
 * reboot - 重启机器
 * 通过向键盘控制器发送复位脉冲请求。
 * 【RISC-V 说明】RISC-V 通常通过 sbi_system_reset() 或
 * 看门狗定时器复位，而非键盘控制器。
 */
	.globl reboot
reboot:
	call	kb_wait
	/* x86: movw $0x1234, 0x472 (跳过内存检查) */
	/* RISC-V: 通过 SBI 调用或 MMIO 复位 */
	li	a0, 0
	li	a1, 0
	li	a7, 0x53525354          /* SBI SRST extension */
	ecall

die:
	j	die


/*
 * ============================================================
 * 数据表 (key_map, shift_map, alt_map, key_table, etc.)
 * 保留原始键码映射，字节序和布局不变。
 * ============================================================
 */

	.data
	.align 3

num_table:
	.ascii "789 456 1230,"
	.align 3
cur_table:
	.ascii "HA5 DGC YB623"

	.align 3
func_table:
	/* 功能键发送 F1:'esc [ [ A' F2:'esc [ [ B' 等 */
	.dword	0x415b5b1b, 0x425b5b1b, 0x435b5b1b, 0x445b5b1b
	.dword	0x455b5b1b, 0x465b5b1b, 0x475b5b1b, 0x485b5b1b
	.dword	0x495b5b1b, 0x4a5b5b1b, 0x4b5b5b1b, 0x4c5b5b1b

	.align 3
key_map:
	.byte 0, 27
	.ascii "1234567890+'"
	.byte 127, 9
	.ascii "qwertyuiop}"
	.byte 0, 10, 0
	.ascii "asdfghjkl|{"
	.byte 0, 0
	.ascii "'zxcvbnm,.-"
	.byte 0, '*', 0, 32          /* 36-39 */
	.fill 16, 1, 0               /* 3A-49 */
	.byte '-, 0, 0, 0, '+        /* 4A-4E */
	.byte 0, 0, 0, 0, 0, 0, 0    /* 4F-55 */
	.byte '<
	.fill 10, 1, 0

	.align 3
shift_map:
	.byte 0, 27
	.ascii "!\"#$%&/()=?`"
	.byte 127, 9
	.ascii "QWERTYUIOP]^"
	.byte 10, 0
	.ascii "ASDFGHJKL\\["
	.byte 0, 0
	.ascii "*ZXCVBNM;:_"
	.byte 0, '*', 0, 32          /* 36-39 */
	.fill 16, 1, 0               /* 3A-49 */
	.byte '-, 0, 0, 0, '+        /* 4A-4E */
	.byte 0, 0, 0, 0, 0, 0, 0    /* 4F-55 */
	.byte '>
	.fill 10, 1, 0

	.align 3
alt_map:
	.byte 0, 0
	.ascii "\0@\0$\0\0{[]}\\0"
	.byte 0, 0
	.byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	.byte '~, 10, 0
	.byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	.byte 0, 0
	.byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	.byte 0, 0, 0, 0             /* 36-39 */
	.fill 16, 1, 0               /* 3A-49 */
	.byte 0, 0, 0, 0, 0          /* 4A-4E */
	.byte 0, 0, 0, 0, 0, 0, 0    /* 4F-55 */
	.byte '|
	.fill 10, 1, 0

	.align 3
/*
 * key_table - 扫描码分发表
 * 决定收到扫描码后调用哪个处理程序。
 * 64位版本：每项 8 字节 (.dword)
 */
key_table:
	.dword none, do_self, do_self, do_self    /* 00-03 s0 esc 1 2 */
	.dword do_self, do_self, do_self, do_self /* 04-07 3 4 5 6 */
	.dword do_self, do_self, do_self, do_self /* 08-0B 7 8 9 0 */
	.dword do_self, do_self, do_self, do_self /* 0C-0F + ' bs tab */
	.dword do_self, do_self, do_self, do_self /* 10-13 q w e r */
	.dword do_self, do_self, do_self, do_self /* 14-17 t y u i */
	.dword do_self, do_self, do_self, do_self /* 18-1B o p } ^ */
	.dword do_self, ctrl, do_self, do_self    /* 1C-1F enter ctrl a s */
	.dword do_self, do_self, do_self, do_self /* 20-23 d f g h */
	.dword do_self, do_self, do_self, do_self /* 24-27 j k l | */
	.dword do_self, do_self, lshift, do_self  /* 28-2B { para lshift , */
	.dword do_self, do_self, do_self, do_self /* 2C-2F z x c v */
	.dword do_self, do_self, do_self, do_self /* 30-33 b n m , */
	.dword do_self, minus, rshift, do_self    /* 34-37 . - rshift * */
	.dword alt, do_self, caps, func            /* 38-3B alt sp caps f1 */
	.dword func, func, func, func              /* 3C-3F f2 f3 f4 f5 */
	.dword func, func, func, func              /* 40-43 f6 f7 f8 f9 */
	.dword func, num, scroll, cursor           /* 44-47 f10 num scr home */
	.dword cursor, cursor, do_self, cursor     /* 48-4B up pgup - left */
	.dword cursor, cursor, do_self, cursor     /* 4C-4F n5 right + end */
	.dword cursor, cursor, cursor, cursor       /* 50-53 dn pgdn ins del */
	.dword none, none, do_self, func           /* 54-57 sysreq ? < f11 */
	.dword func, none, none, none               /* 58-5B f12 ? ? ? */
	.dword none, none, none, none               /* 5C-5F ? ? ? ? */
	.dword none, none, none, none               /* 60-63 ? ? ? ? */
	.dword none, none, none, none               /* 64-67 ? ? ? ? */
	.dword none, none, none, none               /* 68-6B ? ? ? ? */
	.dword none, none, none, none               /* 6C-6F ? ? ? ? */
	.dword none, none, none, none               /* 70-73 ? ? ? ? */
	.dword none, none, none, none               /* 74-77 ? ? ? ? */
	.dword none, none, none, none               /* 78-7B ? ? ? ? */
	.dword none, none, none, none               /* 7C-7F ? ? ? ? */
	.dword none, none, none, none               /* 80-83 ? br br br */
	.dword none, none, none, none               /* 84-87 br br br br */
	.dword none, none, none, none               /* 88-8B br br br br */
	.dword none, none, none, none               /* 8C-8F br br br br */
	.dword none, none, none, none               /* 90-93 br br br br */
	.dword none, none, none, none               /* 94-97 br br br br */
	.dword none, none, none, none               /* 98-9B br br br br */
	.dword none, unctrl, none, none             /* 9C-9F br unctrl br br */
	.dword none, none, none, none               /* A0-A3 br br br br */
	.dword none, none, none, none               /* A4-A7 br br br br */
	.dword none, none, unlshift, none           /* A8-AB br br unlshift br */
	.dword none, none, none, none               /* AC-AF br br br br */
	.dword none, none, none, none               /* B0-B3 br br br br */
	.dword none, none, unrshift, none           /* B4-B7 br br unrshift br */
	.dword unalt, none, uncaps, none            /* B8-BB unalt br uncaps br */
	.dword none, none, none, none               /* BC-BF br br br br */
	.dword none, none, none, none               /* C0-C3 br br br br */
	.dword none, none, none, none               /* C4-C7 br br br br */
	.dword none, none, none, none               /* C8-CB br br br br */
	.dword none, none, none, none               /* CC-CF br br br br */
	.dword none, none, none, none               /* D0-D3 br br br br */
	.dword none, none, none, none               /* D4-D7 br br br br */
	.dword none, none, none, none               /* D8-DB br ? ? ? */
	.dword none, none, none, none               /* DC-DF ? ? ? ? */
	.dword none, none, none, none               /* E0-E3 e0 e1 ? ? */
	.dword none, none, none, none               /* E4-E7 ? ? ? ? */
	.dword none, none, none, none               /* E8-EB ? ? ? ? */
	.dword none, none, none, none               /* EC-EF ? ? ? ? */
	.dword none, none, none, none               /* F0-F3 ? ? ? ? */
	.dword none, none, none, none               /* F4-F7 ? ? ? ? */
	.dword none, none, none, none               /* F8-FB ? ? ? ? */
	.dword none, none, none, none               /* FC-FF ? ? ? ? */
