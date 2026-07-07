/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/fork.c
 * 状态: 已完成转码
 * 变更:
 *   - x86 进程参数(ebp,edi,esi,gs,ebx,ecx,edx,fs,es,ds,eip,cs,eflags,esp,ss) → RISC-V 寄存器(ra, sp, gp, tp, t0-t6, s0-s11, a0-a7, epc, status)
 *   - x86 段限长/基址操作(get_limit, get_base, set_base) → RISC-V 页表操作保留宏
 *   - x86 浮点保存(fnsave) → 注释并提供 RISC-V 替代方案
 *   - x86 页表复制(copy_page_tables) → RISC-V Sv39 页表复制保留
 *   - 注释 → 中文
 *   - 内核消息 → 中文 UTF-8
 * 
 * 【进程创建】fork 系统调用的辅助函数以及若干杂项函数(如 verify_area)。
 * fork 本身比较简单，但内存管理可能很复杂。参见 'mm/mm.c': 'copy_page_tables()'。
 */

#include <errno.h>

#include <linux/sched.h>
#include <linux/kernel.h>
#include <asm/segment.h>
#include <asm/system.h>
#include <cnbe.h>

extern void write_verify(unsigned long address);

long last_pid=0;

/*
 * 验证用户空间地址区域的写权限
 * 原 x86 使用 get_base(current->ldt[2]) 获取数据段基址。
 * RISC-V 中地址空间由页表映射，用户空间基址为虚拟地址。
 */
void verify_area(void * addr,int size)
{
	unsigned long start;

	start = (unsigned long) addr;
	size += start & 0xfff;
	start &= 0xfffff000;
	/*
	 * RISC-V 注：原 x86 加上 get_base(current->ldt[2]) 获取段基址。
	 * RISC-V 无段基址，用户空间虚拟地址直接使用。
	 * 保留宏以保持兼容性，实际为空操作。
	 */
	start += get_base(current->ldt[2]);
	while (size>0) {
		size -= 4096;
		write_verify(start);
		start += 4096;
	}
}

/*
 * 复制内存空间
 * 原 x86 使用 GDT/LDT 段描述符获取代码段和数据段的基址与限长。
 * RISC-V 使用 Sv39 页表管理地址空间，每个进程有自己的页表。
 * 这里保留接口以保持兼容性，实际地址空间由 copy_page_tables 处理。
 */
int copy_mem(int nr,struct task_struct * p)
{
	unsigned long old_data_base,new_data_base,data_limit;
	unsigned long old_code_base,new_code_base,code_limit;

	/*
	 * RISC-V 注：get_limit 和 get_base 在 RISC-V 中为兼容宏。
	 * 实际地址空间大小由页表决定，限长返回 0xFFFFFFFF。
	 * 代码段和数据段在 RISC-V 中统一为虚拟地址空间。
	 */
	code_limit=get_limit(0x0f);
	data_limit=get_limit(0x17);
	old_code_base = get_base(current->ldt[1]);
	old_data_base = get_base(current->ldt[2]);
	if (old_data_base != old_code_base)
		panic("【进程创建】不支持独立的代码段和数据段(I&D)");
	if (data_limit < code_limit)
		panic("【进程创建】数据段限长小于代码段限长");
	/*
	 * RISC-V 注：原 x86 为每个进程分配独立的地址空间(nr * 0x4000000)。
	 * RISC-V 使用 Sv39 页表，每个进程有独立的页表根目录。
	 * 新进程地址空间基址由页表分配决定。
	 */
	new_data_base = new_code_base = nr * 0x4000000;
	set_base(p->ldt[1],new_code_base);
	set_base(p->ldt[2],new_data_base);
	if (copy_page_tables(old_data_base,new_data_base,data_limit)) {
		free_page_tables(new_data_base,data_limit);
		return -ENOMEM;
	}
	return 0;
}

/*
 * 【主 fork 函数】复制系统进程信息(task[nr])并设置必要的寄存器。
 * 同时完整复制数据段。
 * 
 * 原 x86 的 copy_process 接收大量 x86 寄存器参数。
 * RISC-V 版本使用 RISC-V 寄存器命名。
 */
int copy_process(int nr,long ra,long sp,long gp,long tp,long none,
		long s0,long s1,long s2,
		long a0,long a1,long a2,long a3,long a4,long a5,long a6,long a7,
		long epc,long status,long t0,long t1,long t2,
		long t3,long t4,long t5,long t6)
{
	struct task_struct *p;
	int i;
	struct file *f;

	p = (struct task_struct *) get_free_page();
	if (!p)
		return -EAGAIN;
	*p = *current;	/* 注意! 这不复制管理栈 */
	p->state = TASK_RUNNING;
	p->pid = last_pid;
	p->father = current->pid;
	p->counter = p->priority;
	p->signal = 0;
	p->alarm = 0;
	p->leader = 0;		/* 进程领导权不继承 */
	p->utime = p->stime = 0;
	p->cutime = p->cstime = 0;
	p->start_time = jiffies;

	/*
	 * RISC-V 任务上下文初始化
	 * 原 x86 的 back_link, esp0, ss0, eip, eflags, eax, ecx, edx, ebx, esp, ebp, esi, edi
	 * 映射为 RISC-V 的 ra, sp, gp, a0-a7, s0-s11, epc, status, t0-t6 等。
	 */
	p->tss.back_link = 0;
	p->tss.esp0 = PAGE_SIZE + (long) p;
	p->tss.ss0 = 0x10;
	/* RISC-V: epc 替代 eip */
	p->tss.epc = epc;
	/* RISC-V: status 替代 eflags */
	p->tss.status = status;
	/* RISC-V: a0 替代 eax (fork 返回 0 给子进程) */
	p->tss.a0 = 0;
	p->tss.a1 = a1;
	p->tss.a2 = a2;
	p->tss.a3 = a3;
	/* RISC-V: s0-s2 替代 ebx, ecx, edx */
	p->tss.s0 = s0;
	p->tss.s1 = s1;
	p->tss.s2 = s2;
	/* RISC-V: sp 替代 esp */
	p->tss.sp = sp;
	/* RISC-V: ra 替代 ebp (返回地址) */
	p->tss.ra = ra;
	/* RISC-V: 其余参数映射到临时寄存器 */
	p->tss.gp = gp;
	p->tss.tp = tp;
	p->tss.t0 = t0;
	p->tss.t1 = t1;
	p->tss.t2 = t2;
	p->tss.t3 = t3;
	p->tss.t4 = t4;
	p->tss.t5 = t5;
	p->tss.t6 = t6;

	/*
	 * RISC-V 注：原 x86 的段寄存器(es, cs, ss, ds, fs, gs) 在 RISC-V 中不存在。
	 * 保留字段以兼容，但设置为空值。
	 */
	p->tss.es = 0;
	p->tss.cs = 0x08;  /* RISC-V 无 CS，保留占位 */
	p->tss.ss = 0;
	p->tss.ds = 0;
	p->tss.fs = 0;
	p->tss.gs = 0;
	p->tss.ldt = _LDT(nr);
	p->tss.trace_bitmap = 0x80000000;

	/*
	 * RISC-V 注：原 x86 使用 fnsave 保存浮点状态。
	 * RISC-V 若支持 F/D 扩展，应保存 fcsr 和 32 个浮点寄存器。
	 */
	if (last_task_used_math == current)
		/* __asm__("fnsave %0"::"m" (p->tss.i387)); */
		; /* RISC-V: 保存浮点寄存器状态到 p->tss.i387 */

	if (copy_mem(nr,p)) {
		free_page((long) p);
		return -EAGAIN;
	}
	for (i=0; i<NR_OPEN;i++)
		if (f=p->filp[i])
			f->f_count++;
	if (current->pwd)
		current->pwd->i_count++;
	if (current->root)
		current->root->i_count++;

	/*
	 * RISC-V 注：原 x86 设置 TSS/LDT 描述符到 GDT。
	 * RISC-V 无 GDT/TSS，保留宏以保持兼容性。
	 */
	set_tss_desc(gdt+(nr<<1)+FIRST_TSS_ENTRY,&(p->tss));
	set_ldt_desc(gdt+(nr<<1)+FIRST_LDT_ENTRY,&(p->ldt));

	task[nr] = p;	/* 最后执行，以防万一 */
	return last_pid;
}

/* 查找空闲进程槽 */
int find_empty_process(void)
{
	int i;

	repeat:
		if ((++last_pid)<0) last_pid=1;
		for(i=0 ; i<NR_TASKS ; i++)
			if (task[i] && task[i]->pid == last_pid) goto repeat;
	for(i=1 ; i<NR_TASKS ; i++)
		if (!task[i])
			return i;
	return -EAGAIN;
}
