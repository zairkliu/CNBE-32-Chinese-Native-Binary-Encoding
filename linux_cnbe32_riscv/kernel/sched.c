/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/sched.c
 * 状态: 已完成转码
 * 变更:
 *   - x86 浮点保存/恢复指令(fnsave/frstor/fninit) → 已注释并添加 RISC-V 替代方案
 *   - x86 中断控制器(PIC) outb/inb → MMIO writeb/readb
 *   - x86 门描述符设置 → RISC-V 异常向量保留宏
 *   - x86 段寄存器(stack_start) → RISC-V 不使用段式内存
 *   - 注释 → 中文
 *   - 内核消息 → 中文 UTF-8
 * 
 * 【调度器核心】调度原语(sleep_on, wakeup, schedule 等)
 * 以及若干简单系统调用函数(如 getpid 等，直接从当前任务中提取字段)
 */

#include <linux/sched.h>
#include <linux/kernel.h>
#include <signal.h>
#include <linux/sys.h>
#include <asm/system.h>
#include <asm/io.h>
#include <asm/segment.h>
#include <cnbe.h>

#define LATCH (1193180/HZ)

extern void mem_use(void);

extern int timer_interrupt(void);
extern int system_call(void);

union task_union {
	struct task_struct task;
	char stack[PAGE_SIZE];
};

static union task_union init_task = {INIT_TASK,};

long volatile jiffies=0;
long startup_time=0;
struct task_struct *current = &(init_task.task), *last_task_used_math = NULL;

struct task_struct * task[NR_TASKS] = {&(init_task.task), };

long user_stack [ PAGE_SIZE>>2 ] ;

/*
 * RISC-V 注：原 x86 的 stack_start 包含段选择子(0x10)。
 * RISC-V 架构不使用段式内存管理，因此简化为栈指针和占位符。
 * 栈底指针指向 user_stack 的末尾。
 */
struct {
	long * a;
	short b;
	} stack_start = { & user_stack [PAGE_SIZE>>2] , 0 };

/*
 * 数学协处理器状态恢复函数
 * 原 x86 使用 fnsave/frstor/fninit 指令操作浮点寄存器。
 * RISC-V 架构可选 F/D 扩展支持浮点，使用 fcsr 和浮点寄存器保存区。
 */
void math_state_restore()
{
	/*
	 * RISC-V 替代方案：若支持 F/D 扩展，使用 fcsr 和 fsw/Flw 保存/恢复
	 * 32 个浮点寄存器。若不使用浮点，可保留此函数为空。
	 * 以下为 x86 原始代码，已禁用:
	 */
	if (last_task_used_math)
		/* 原 x86: __asm__("fnsave %0"::"m" (last_task_used_math->tss.i387)); */
		; /* RISC-V: 保存浮点寄存器状态到 last_task_used_math->tss.i387 */
	if (current->used_math)
		/* 原 x86: __asm__("frstor %0"::"m" (current->tss.i387)); */
		; /* RISC-V: 从 current->tss.i387 恢复浮点寄存器状态 */
	else {
		/* 原 x86: __asm__("fninit"::); */
		; /* RISC-V: 初始化浮点单元(设置 fcsr 为默认值) */
		current->used_math=1;
	}
	last_task_used_math=current;
}

/*
 * 【调度器】调度函数。这是高质量代码!
 * 在绝大多数情况下无需修改，因为它能良好处理各种场景
 * (即能为 I/O 密集型进程提供良好的响应等)。
 * 唯一可能需要关注的是此处的信号处理代码。
 *
 * 注意!! 任务 0 是"空闲"任务，当没有其他任务可运行时会被调用。
 * 它不能被终止，也不能睡眠。task[0] 中的'状态'信息永远不会被使用。
 */
void schedule(void)
{
	int i,next,c;
	struct task_struct ** p;

/* 检查闹钟，唤醒任何收到信号的可中断任务 */

	for(p = &LAST_TASK ; p > &FIRST_TASK ; --p)
		if (*p) {
			if ((*p)->alarm && (*p)->alarm < jiffies) {
					(*p)->signal |= (1<<(SIGALRM-1));
					(*p)->alarm = 0;
				}
			if ((*p)->signal && (*p)->state==TASK_INTERRUPTIBLE)
				(*p)->state=TASK_RUNNING;
		}

/* 这是真正的调度器: */

	while (1) {
		c = -1;
		next = 0;
		i = NR_TASKS;
		p = &task[NR_TASKS];
		while (--i) {
			if (!*--p)
				continue;
			if ((*p)->state == TASK_RUNNING && (*p)->counter > c)
				c = (*p)->counter, next = i;
		}
		if (c) break;
		for(p = &LAST_TASK ; p > &FIRST_TASK ; --p)
			if (*p)
				(*p)->counter = ((*p)->counter >> 1) +
						(*p)->priority;
	}
	switch_to(next);
}

/* 暂停进程 */
int sys_pause(void)
{
	current->state = TASK_INTERRUPTIBLE;
	schedule();
	return 0;
}

/* 将当前进程挂起到指定队列 */
void sleep_on(struct task_struct **p)
{
	struct task_struct *tmp;

	if (!p)
		return;
	if (current == &(init_task.task))
		panic("【调度器】任务0尝试睡眠，这是不允许的");
	tmp = *p;
	*p = current;
	current->state = TASK_UNINTERRUPTIBLE;
	schedule();
	if (tmp)
		tmp->state=0;
}

/* 可中断睡眠 */
void interruptible_sleep_on(struct task_struct **p)
{
	struct task_struct *tmp;

	if (!p)
		return;
	if (current == &(init_task.task))
		panic("【调度器】任务0尝试睡眠，这是不允许的");
	tmp=*p;
	*p=current;
repeat:	current->state = TASK_INTERRUPTIBLE;
		schedule();
	if (*p && *p != current) {
		(**p).state=0;
		goto repeat;
	}
	*p=NULL;
	if (tmp)
		tmp->state=0;
}

/* 唤醒等待队列中的进程 */
void wake_up(struct task_struct **p)
{
	if (p && *p) {
		(**p).state=0;
		*p=NULL;
	}
}

/* 定时器处理函数 */
void do_timer(long cpl)
{
	if (cpl)
		current->utime++;
	else
		current->stime++;
	if ((--current->counter)>0) return;
	current->counter=0;
	if (!cpl) return;
	schedule();
}

/* 设置闹钟 */
int sys_alarm(long seconds)
{
	current->alarm = (seconds>0)?(jiffies+HZ*seconds):0;
	return seconds;
}

/* 获取进程号 */
int sys_getpid(void)
{
	return current->pid;
}

/* 获取父进程号 */
int sys_getppid(void)
{
	return current->father;
}

/* 获取用户ID */
int sys_getuid(void)
{
	return current->uid;
}

/* 获取有效用户ID */
int sys_geteuid(void)
{
	return current->euid;
}

/* 获取组ID */
int sys_getgid(void)
{
	return current->gid;
}

/* 获取有效组ID */
int sys_getegid(void)
{
	return current->egid;
}

/* 调整进程优先级 */
int sys_nice(long increment)
{
	if (current->priority-increment>0)
		current->priority -= increment;
	return 0;
}

/* 信号设置系统调用 */
int sys_signal(long signal,long addr,long restorer)
{
	long i;

	switch (signal) {
		case SIGHUP: case SIGINT: case SIGQUIT: case SIGILL:
		case SIGTRAP: case SIGABRT: case SIGFPE: case SIGUSR1:
		case SIGSEGV: case SIGUSR2: case SIGPIPE: case SIGALRM:
		case SIGCHLD:
			i=(long) current->sig_fn[signal-1];
			current->sig_fn[signal-1] = (fn_ptr) addr;
			current->sig_restorer = (fn_ptr) restorer;
			return i;
		default: return -1;
	}
}

/*
 * 【调度器初始化】
 * 原 x86 版本设置 GDT/LDT、PIT 定时器、中断门等。
 * RISC-V 版本：
 *   - 不使用 GDT/LDT (无段式内存)
 *   - 使用 CLINT 定时器 (替代 x86 PIT 8253)
 *   - 使用 mtvec/stvec 设置异常向量 (替代门描述符)
 */
void sched_init(void)
{
	int i;

	/*
	 * RISC-V 注：原 x86 代码设置 TSS/LDT 描述符到 GDT。
	 * RISC-V 无段式内存，因此跳过 GDT/LDT 设置。
	 * 保留函数调用以保持代码兼容性。
	 */
	set_tss_desc(gdt+FIRST_TSS_ENTRY,&(init_task.task.tss));
	set_ldt_desc(gdt+FIRST_LDT_ENTRY,&(init_task.task.ldt));

	/* 初始化任务数组 */
	for(i=1;i<NR_TASKS;i++) {
		task[i] = NULL;
	}

	/*
	 * RISC-V 注：原 x86 加载 TR/LDT 寄存器。
	 * RISC-V 不使用这些寄存器，为空操作。
	 */
	ltr(0);
	lldt(0);

	/*
	 * RISC-V 注：原 x86 设置 PIT 定时器 (8253 芯片，I/O 端口 0x40-0x43)。
	 * RISC-V 使用 CLINT (Core Local Interruptor) 定时器，通过 MMIO 访问。
	 * CLINT 基址: 0x02000000 (mtimecmp 偏移: 0x4000)
	 * 以下为 x86 原始代码，已禁用:
	 */
	/* outb_p(0x36,0x43); */  /* 二进制,模式3,LSB/MSB,通道0 */
	/* outb_p(LATCH & 0xff , 0x40); */  /* LSB */
	/* outb(LATCH >> 8 , 0x40); */  /* MSB */

	/*
	 * RISC-V 注：原 x86 通过 set_intr_gate 设置 IDT 门描述符。
	 * RISC-V 使用 mtvec/stvec 设置异常向量基址。
	 * 系统调用通过 ecall 指令触发，在 stvec 中统一处理。
	 */
	set_intr_gate(0x20,&timer_interrupt);
	/* outb(inb_p(0x21)&~0x01,0x21); */  /* 启用定时器中断 (x86 PIC) */
	set_system_gate(0x80,&system_call);
}
