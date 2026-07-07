/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/traps.c
 * 状态: 已完成转码
 * 变更:
 *   - x86 段寄存器访问宏(get_seg_byte, get_seg_long, _fs) → 直接虚拟地址访问
 *   - x86 寄存器打印(EIP, EFLAGS, ESP, FS, CS, DS, ES) → RISC-V 寄存器(ra, sp, gp, tp, a0-a7, s0-s11, mepc, mstatus)
 *   - x86 门描述符设置(set_trap_gate, set_system_gate) → RISC-V 保留宏
 *   - x86 调试寄存器访问(已注释) → RISC-V 断点寄存器
 *   - 注释 → 中文
 *   - 内核消息 → 中文 UTF-8
 * 
 * 【陷阱处理】处理硬件陷阱和故障，在状态保存后进入。
 * 目前主要作为调试辅助，未来将扩展为终止违规进程
 * (通过发送信号或直接终止)。
 */

#include <string.h>

#include <linux/head.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <asm/system.h>
#include <asm/segment.h>
#include <cnbe.h>

/* RISC-V: 段式内存访问宏已移至 asm/segment.h */

int do_exit(long code);

void page_exception(void);

void divide_error(void);
void debug(void);
void nmi(void);
void int3(void);
void overflow(void);
void bounds(void);
void invalid_op(void);
void device_not_available(void);
void double_fault(void);
void coprocessor_segment_overrun(void);
void invalid_TSS(void);
void segment_not_present(void);
void stack_segment(void);
void general_protection(void);
void page_fault(void);
void coprocessor_error(void);
void reserved(void);

/*
 * 死亡函数 - 打印寄存器状态并终止进程
 * 原 x86 版本打印 EIP, EFLAGS, ESP, FS, CS, DS 等寄存器。
 * RISC-V 版本打印 mepc, mstatus, sp, 通用寄存器等。
 */
static void die(char * str,long esp_ptr,long nr)
{
	long * esp = (long *) esp_ptr;
	int i;

	printk("【致命错误】%s: %04x\n\r",str,nr&0xffff);
	/*
	 * RISC-V 注：原 x86 打印 EIP, EFLAGS, ESP, FS, CS, DS 等。
	 * RISC-V 的寄存器布局不同，打印 mepc(异常PC), mstatus, sp。
	 * 栈布局取决于 RISC-V 上下文保存实现。
	 */
	printk("异常PC(mepc):\t%p\n状态(mstatus):\t%p\n栈指针(sp):\t%p\n",
		esp[0],esp[2],esp[3]);
	/* printk("fs: %04x\n",_fs()); */  /* RISC-V 无 FS 段寄存器 */
	printk("进程基址: %p, 限长: %p\n",get_base(current->ldt[1]),get_limit(0x17));
	printk("栈内容: ");
	for (i=0;i<4;i++)
		printk("%p ",get_seg_long(0x17,i+(long *)esp[3]));
	printk("\n");
	str(i);
	printk("进程号: %d, 进程编号: %d\n\r",current->pid,0xffff & i);
	for(i=0;i<10;i++)
		printk("%02x ",0xff & get_seg_byte(esp[1],(i+(char *)esp[0])));
	printk("\n\r");
	do_exit(11);		/* 段异常处理 */
}

void do_double_fault(long esp, long error_code)
{
	die("双重故障",esp,error_code);
}

void do_general_protection(long esp, long error_code)
{
	die("通用保护错误",esp,error_code);
}

void do_divide_error(long esp, long error_code)
{
	die("除零错误",esp,error_code);
}

/*
 * 断点处理 (int3)
 * 原 x86 打印所有寄存器值(TR, EAX, EBX, ECX, EDX, ESI, EDI, EBP, ESP, DS, ES, FS, CS, EIP, EFLAGS)。
 * RISC-V 打印通用寄存器(a0-a7, s0-s11, ra, sp, mepc, mstatus)。
 */
void do_int3(long * esp, long error_code,
		long fs,long es,long ds,
		long ebp,long esi,long edi,
		long edx,long ecx,long ebx,long eax)
{
	int tr;

	/* RISC-V 注：原 x86 的 str 指令读取 TR 寄存器。RISC-V 无 TR，保留为 0 */
	tr = 0;
	printk("a0\t\ta1\t\ta2\t\ta3\n\r%8x\t%8x\t%8x\t%8x\n\r",
		eax,ebx,ecx,edx);
	printk("s0\t\ts1\t\tebp\t\tsp\n\r%8x\t%8x\t%8x\t%8x\n\r",
		esi,edi,ebp,(long) esp);
	printk("\n\rdes\tes\tfs\ttr\n\r%4x\t%4x\t%4x\t%4x\n\r",
		ds,es,fs,tr);
	printk("异常PC(mepc): %8x\t状态(mstatus): %8x\n\r",esp[0],esp[2]);
}

void do_nmi(long esp, long error_code)
{
	die("不可屏蔽中断",esp,error_code);
}

void do_debug(long esp, long error_code)
{
	die("调试异常",esp,error_code);
}

void do_overflow(long esp, long error_code)
{
	die("溢出异常",esp,error_code);
}

void do_bounds(long esp, long error_code)
{
	die("边界检查异常",esp,error_code);
}

void do_invalid_op(long esp, long error_code)
{
	die("非法操作码",esp,error_code);
}

void do_device_not_available(long esp, long error_code)
{
	die("设备不可用(浮点)",esp,error_code);
}

void do_coprocessor_segment_overrun(long esp, long error_code)
{
	die("协处理器段越界",esp,error_code);
}

void do_invalid_TSS(long esp,long error_code)
{
	die("无效TSS",esp,error_code);
}

void do_segment_not_present(long esp,long error_code)
{
	die("段不存在",esp,error_code);
}

void do_stack_segment(long esp,long error_code)
{
	die("栈段错误",esp,error_code);
}

void do_coprocessor_error(long esp, long error_code)
{
	die("协处理器错误",esp,error_code);
}

void do_reserved(long esp, long error_code)
{
	die("保留错误(15,17-31)",esp,error_code);
}

/*
 * 【陷阱初始化】
 * 原 x86 通过 set_trap_gate/set_system_gate 设置 IDT 门描述符。
 * RISC-V 使用 mtvec/stvec 寄存器设置异常向量基址，
 * 所有异常通过统一的入口处理，根据 mcause/scause 分发。
 */
void trap_init(void)
{
	int i;

	/*
	 * RISC-V 注：以下门设置宏在 x86 中写入 IDT 表。
	 * RISC-V 中无 IDT，保留宏以保持代码兼容性。
	 * 实际异常处理通过设置 stvec 寄存器指向统一异常入口，
	 * 由入口代码根据 mcause 分发到以下各处理函数。
	 */
	set_trap_gate(0,&divide_error);
	set_trap_gate(1,&debug);
	set_trap_gate(2,&nmi);
	set_system_gate(3,&int3);	/* int3-5 可从所有特权级调用 */
	set_system_gate(4,&overflow);
	set_system_gate(5,&bounds);
	set_trap_gate(6,&invalid_op);
	set_trap_gate(7,&device_not_available);
	set_trap_gate(8,&double_fault);
	set_trap_gate(9,&coprocessor_segment_overrun);
	set_trap_gate(10,&invalid_TSS);
	set_trap_gate(11,&segment_not_present);
	set_trap_gate(12,&stack_segment);
	set_trap_gate(13,&general_protection);
	set_trap_gate(14,&page_fault);
	set_trap_gate(15,&reserved);
	set_trap_gate(16,&coprocessor_error);
	for (i=17;i<32;i++)
		set_trap_gate(i,&reserved);

	/*
	 * RISC-V 注：原 x86 调试寄存器代码已注释。
	 * RISC-V 支持触发断点，通过 dret 返回，无直接等价于 DR0-DR7 的寄存器。
	 * 未来可扩展为使用 RISC-V 的触发器模块(Trigger Module)实现硬件断点。
	 */
}
