/* 
 * super.c - 超级块处理代码
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: x86 内联汇编 set_bit 替换为纯 C 实现
 */
/*
 * super.c 包含处理超级块表的代码。
 */
#include <linux/config.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <cnbe.h>

/* CNBE-32 注: x86 原代码使用 bt/setb 指令。
 * RISC-V 无直接位测试指令，使用 C 实现。 */
#define set_bit(bitnr,addr) ({ 	int __res = ((unsigned long *)(addr))[(bitnr) >> 5] & (1 << ((bitnr) & 31)); 	((unsigned long *)(addr))[(bitnr) >> 5] |= (1 << ((bitnr) & 31)); 	__res; })

struct super_block super_block[NR_SUPER];

struct super_block * do_mount(int dev)
{
	struct super_block * p;
	struct buffer_head * bh;
	int i,block;

	for(p = &super_block[0] ; p < &super_block[NR_SUPER] ; p++ )
		if (!(p->s_dev))
			break;
	p->s_dev = -1;		/* 标记为使用中 */
	if (p >= &super_block[NR_SUPER])
		return NULL;
	if (!(bh = bread(dev,1)))
		return NULL;
	*p = *((struct super_block *) bh->b_data);
	brelse(bh);
	if (p->s_magic != SUPER_MAGIC) {
		p->s_dev = 0;
		return NULL;
	}
	for (i=0;i<I_MAP_SLOTS;i++)
		p->s_imap[i] = NULL;
	for (i=0;i<Z_MAP_SLOTS;i++)
		p->s_zmap[i] = NULL;
	block=2;
	for (i=0 ; i < p->s_imap_blocks ; i++)
		if (p->s_imap[i]=bread(dev,block))
			block++;
		else
			break;
	for (i=0 ; i < p->s_zmap_blocks ; i++)
		if (p->s_zmap[i]=bread(dev,block))
			block++;
		else
			break;
	if (block != 2+p->s_imap_blocks+p->s_zmap_blocks) {
		for(i=0;i<I_MAP_SLOTS;i++)
			brelse(p->s_imap[i]);
		for(i=0;i<Z_MAP_SLOTS;i++)
			brelse(p->s_zmap[i]);
		p->s_dev=0;
		return NULL;
	}
	p->s_imap[0]->b_data[0] |= 1;
	p->s_zmap[0]->b_data[0] |= 1;
	p->s_dev = dev;
	p->s_isup = NULL;
	p->s_imount = NULL;
	p->s_time = 0;
	p->s_rd_only = 0;
	p->s_dirt = 0;
	return p;
}

void mount_root(void)
{
	int i,free;
	struct super_block * p;
	struct m_inode * mi;

	if (32 != sizeof (struct d_inode))
		panic("错误的 inode 大小");
	for(i=0;i<NR_FILE;i++)
		file_table[i].f_count=0;
	for(p = &super_block[0] ; p < &super_block[NR_SUPER] ; p++)
		p->s_dev = 0;
	if (!(p=do_mount(ROOT_DEV)))
		panic("无法挂载根文件系统");
	if (!(mi=iget(ROOT_DEV,1)))
		panic("无法读取根 inode");
	mi->i_count += 3 ;	/* 注意! 逻辑上使用了 4 次，不是 1 次 */
	p->s_isup = p->s_imount = mi;
	current->pwd = mi;
	current->root = mi;
	free=0;
	i=p->s_nzones;
	while (-- i >= 0)
		if (!set_bit(i&8191,p->s_zmap[i>>13]->b_data))
			free++;
	printk("%d/%d 空闲块\n\r",free,p->s_nzones);
	free=0;
	i=p->s_ninodes+1;
	while (-- i >= 0)
		if (!set_bit(i&8191,p->s_imap[i>>13]->b_data))
			free++;
	printk("%d/%d 空闲 inode\n\r",free,p->s_ninodes);
}
