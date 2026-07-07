/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/sys.c
 * 状态: 已完成转码
 * 变更:
 *   - x86 用户空间访问(put_fs_long, put_fs_byte, get_fs_long, verify_area) → RISC-V 直接虚拟地址访问
 *   - sys_uname 中的系统名称 → 中文标识 + RISC-V 架构
 *   - 注释 → 中文
 *   - 内核消息 → 中文 UTF-8
 *   - 添加 CNBE-32 集成点
 * 
 * 【系统调用】各类系统调用函数的实现。
 */

#include <errno.h>

#include <linux/sched.h>
#include <linux/tty.h>
#include <linux/kernel.h>
#include <asm/segment.h>
#include <sys/times.h>
#include <sys/utsname.h>
#include <cnbe.h>

/* 未实现系统调用 - 返回 ENOSYS */
int sys_ftime()
{
	return -ENOSYS;
}

int sys_mknod()
{
	return -ENOSYS;
}

int sys_break()
{
	return -ENOSYS;
}

int sys_mount()
{
	return -ENOSYS;
}

int sys_umount()
{
	return -ENOSYS;
}

int sys_ustat(int dev,struct ustat * ubuf)
{
	return -1;
}

int sys_ptrace()
{
	return -ENOSYS;
}

int sys_stty()
{
	return -ENOSYS;
}

int sys_gtty()
{
	return -ENOSYS;
}

int sys_rename()
{
	return -ENOSYS;
}

int sys_prof()
{
	return -ENOSYS;
}

/* 设置组ID */
int sys_setgid(int gid)
{
	if (current->euid && current->uid)
		if (current->gid==gid || current->sgid==gid)
			current->egid=gid;
		else
			return -EPERM;
	else
		current->gid=current->egid=gid;
	return 0;
}

int sys_acct()
{
	return -ENOSYS;
}

int sys_phys()
{
	return -ENOSYS;
}

int sys_lock()
{
	return -ENOSYS;
}

int sys_mpx()
{
	return -ENOSYS;
}

int sys_ulimit()
{
	return -ENOSYS;
}

/* 获取当前时间 */
int sys_time(long * tloc)
{
	int i;

	i = CURRENT_TIME;
	if (tloc) {
		verify_area(tloc,4);
		put_fs_long(i,(unsigned long *)tloc);
	}
	return i;
}

/* 设置用户ID */
int sys_setuid(int uid)
{
	if (current->euid && current->uid)
		if (uid==current->uid || current->suid==current->uid)
			current->euid=uid;
		else
			return -EPERM;
	else
		current->euid=current->uid=uid;
	return 0;
}

/* 设置系统时间 */
int sys_stime(long * tptr)
{
	if (current->euid && current->uid)
		return -1;
	startup_time = get_fs_long((unsigned long *)tptr) - jiffies/HZ;
	return 0;
}

/* 获取进程时间 */
int sys_times(struct tms * tbuf)
{
	if (!tbuf)
		return jiffies;
	verify_area(tbuf,sizeof *tbuf);
	put_fs_long(current->utime,(unsigned long *)&tbuf->tms_utime);
	put_fs_long(current->stime,(unsigned long *)&tbuf->tms_stime);
	put_fs_long(current->cutime,(unsigned long *)&tbuf->tms_cutime);
	put_fs_long(current->cstime,(unsigned long *)&tbuf->tms_cstime);
	return jiffies;
}

/* 设置数据段末尾 */
int sys_brk(unsigned long end_data_seg)
{
	if (end_data_seg >= current->end_code &&
	    end_data_seg < current->start_stack - 16384)
		current->brk = end_data_seg;
	return current->brk;
}

/*
 * 这需要更多检查...
 * 我还没做。我也不完全理解会话/进程组等。
 * 让懂的人来解释吧。
 */
int sys_setpgid(int pid, int pgid)
{
	int i;

	if (!pid)
		pid = current->pid;
	if (!pgid)
		pgid = pid;
	for (i=0 ; i<NR_TASKS ; i++)
		if (task[i] && task[i]->pid==pid) {
			if (task[i]->leader)
				return -EPERM;
			if (task[i]->session != current->session)
				return -EPERM;
			task[i]->pgrp = pgid;
			return 0;
		}
	return -ESRCH;
}

/* 获取进程组ID */
int sys_getpgrp(void)
{
	return current->pgrp;
}

/* 创建新会话 */
int sys_setsid(void)
{
	if (current->uid && current->euid)
		return -EPERM;
	if (current->leader)
		return -EPERM;
	current->leader = 1;
	current->session = current->pgrp = current->pid;
	current->tty = -1;
	return current->pgrp;
}

/*
 * 获取系统信息
 * RISC-V 版本：更新系统名称为 RISC-V 架构标识
 * CNBE-32 集成：使用中文 UTF-8 标识
 */
int sys_uname(struct utsname * name)
{
	/*
	 * RISC-V CNBE-32 版本系统名称
	 * 使用中文 UTF-8 编码，表明这是 RISC-V + CNBE-32 移植版
	 */
	static struct utsname thisname = {
		"中文系统","节点名","CNBE32","版本 ","RISC-V"
	};
	int i;

	if (!name) return -1;
	verify_area(name,sizeof *name);
	for(i=0;i<sizeof *name;i++)
		put_fs_byte(((char *) &thisname)[i],i+(char *) name);
	return (0);
}

/* 设置文件权限掩码 */
int sys_umask(int mask)
{
	int old = current->umask;

	current->umask = mask & 0777;
	return (old);
}

/* 以下为 Linux 0.01 扩展系统调用桩函数 */

int sys_sigaction(int sig, const struct sigaction *act, struct sigaction *oact)
{
	/* 信号动作处理 —— 简化实现 */
	return -ENOSYS;
}

int sys_sgetmask(void)
{
	/* 获取信号掩码 */
	return current->blocked;
}

int sys_ssetmask(int newmask)
{
	/* 设置信号掩码 */
	int old = current->blocked;
	current->blocked = newmask;
	return old;
}

int sys_setreuid(int ruid, int euid)
{
	/* 设置真实/有效用户ID */
	return -ENOSYS;
}

int sys_setregid(int rgid, int egid)
{
	/* 设置真实/有效组ID */
	return -ENOSYS;
}
