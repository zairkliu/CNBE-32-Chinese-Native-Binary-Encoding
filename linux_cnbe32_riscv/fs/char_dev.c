/* 
 * char_dev.c - 字符设备读写接口
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: 无 x86 特定代码，仅更新注释为中文
 */
#include <errno.h>

#include <linux/sched.h>
#include <linux/kernel.h>
#include <cnbe.h>

extern int tty_read(unsigned minor,char * buf,int count);
extern int tty_write(unsigned minor,char * buf,int count);

static int rw_ttyx(int rw,unsigned minor,char * buf,int count);
static int rw_tty(int rw,unsigned minor,char * buf,int count);

typedef (*crw_ptr)(int rw,unsigned minor,char * buf,int count);

#define NRDEVS ((sizeof (crw_table))/(sizeof (crw_ptr)))

static crw_ptr crw_table[]={
	NULL,		/* 无设备 */
	NULL,		/* /dev/mem */
	NULL,		/* /dev/fd */
	NULL,		/* /dev/hd */
	rw_ttyx,	/* /dev/ttyx */
	rw_tty,		/* /dev/tty */
	NULL,		/* /dev/lp */
	NULL};		/* 未命名管道 */

static int rw_ttyx(int rw,unsigned minor,char * buf,int count)
{
	return ((rw==READ)?tty_read(minor,buf,count):
		tty_write(minor,buf,count));
}

static int rw_tty(int rw,unsigned minor,char * buf,int count)
{
	if (current->tty<0)
		return -EPERM;
	return rw_ttyx(rw,current->tty,buf,count);
}

int rw_char(int rw,int dev, char * buf, int count)
{
	crw_ptr call_addr;

	if (MAJOR(dev)>=NRDEVS)
		panic("rw_char: 设备号超出范围");
	if (!(call_addr=crw_table[MAJOR(dev)])) {
		printk("设备: %04x\n",dev);
		panic("尝试从不存在的字符设备读写");
	}
	return call_addr(rw,MINOR(dev),buf,count);
}
