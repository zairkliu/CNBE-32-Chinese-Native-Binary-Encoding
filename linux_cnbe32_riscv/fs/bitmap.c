/* 
 * bitmap.c - 处理 inode 和块位图的代码
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: x86 内联汇编替换为纯 C 实现，内核消息转为中文
 */
#include <string.h>

#include <linux/sched.h>
#include <linux/kernel.h>
#include <cnbe.h>

/* CNBE-32 注: 以下宏替代 x86 汇编，使用纯 C 实现以保证 RISC-V 可移植性 */

#define clear_block(addr) 	memset((addr), 0, BLOCK_SIZE)

#define set_bit(nr,addr) ({ 	int __res = ((unsigned long *)(addr))[(nr) >> 5] & (1 << ((nr) & 31)); 	((unsigned long *)(addr))[(nr) >> 5] |= (1 << ((nr) & 31)); 	__res; })

#define clear_bit(nr,addr) ({ 	int __res = ((unsigned long *)(addr))[(nr) >> 5] & (1 << ((nr) & 31)); 	((unsigned long *)(addr))[(nr) >> 5] &= ~(1 << ((nr) & 31)); 	__res; })

#define find_first_zero(addr) ({ 	unsigned long *__ap = (unsigned long *)(addr); 	int __res = 8192; 	int __i; 	for (__i = 0; __i < (8192/32); __i++) { 		unsigned long __w = ~(__ap[__i]); 		if (__w) { 			int __b = 0; 			while (!(__w & (1 << __b))) __b++; 			__res = __i * 32 + __b; 			break; 		} 	} 	__res; })

void free_block(int dev, int block)
{
	struct super_block * sb;
	struct buffer_head * bh;

	if (!(sb = get_super(dev)))
		panic("尝试释放不存在的设备上的块");
	if (block < sb->s_firstdatazone || block >= sb->s_nzones)
		panic("尝试释放数据区之外的块");
	bh = get_hash_table(dev,block);
	if (bh) {
		if (bh->b_count != 1) {
			printk("尝试释放块 (%04x:%d)，计数=%d\n",
				dev,block,bh->b_count);
			return;
		}
		bh->b_dirt=0;
		bh->b_uptodate=0;
		brelse(bh);
	}
	block -= sb->s_firstdatazone - 1 ;
	if (clear_bit(block&8191,sb->s_zmap[block/8192]->b_data)) {
		printk("块 (%04x:%d) ",dev,block+sb->s_firstdatazone-1);
		panic("free_block: 位图已清除");
	}
	sb->s_zmap[block/8192]->b_dirt = 1;
}

int new_block(int dev)
{
	struct buffer_head * bh;
	struct super_block * sb;
	int i,j;

	if (!(sb = get_super(dev)))
		panic("尝试从不存在的设备获取新块");
	j = 8192;
	for (i=0 ; i<8 ; i++)
		if (bh=sb->s_zmap[i])
			if ((j=find_first_zero(bh->b_data))<8192)
				break;
	if (i>=8 || !bh || j>=8192)
		return 0;
	if (set_bit(j,bh->b_data))
		panic("new_block: 位图已设置");
	bh->b_dirt = 1;
	j += i*8192 + sb->s_firstdatazone-1;
	if (j >= sb->s_nzones)
		return 0;
	if (!(bh=getblk(dev,j)))
		panic("new_block: 无法获取块");
	if (bh->b_count != 1)
		panic("new_block: 计数不为 1");
	clear_block(bh->b_data);
	bh->b_uptodate = 1;
	bh->b_dirt = 1;
	brelse(bh);
	return j;
}

void free_inode(struct m_inode * inode)
{
	struct super_block * sb;
	struct buffer_head * bh;

	if (!inode)
		return;
	if (!inode->i_dev) {
		memset(inode,0,sizeof(*inode));
		return;
	}
	if (inode->i_count>1) {
		printk("尝试释放计数=%d 的 inode\n",inode->i_count);
		panic("free_inode");
	}
	if (inode->i_nlinks)
		panic("尝试释放有链接的 inode");
	if (!(sb = get_super(inode->i_dev)))
		panic("尝试释放不存在的设备上的 inode");
	if (inode->i_num < 1 || inode->i_num > sb->s_ninodes)
		panic("尝试释放 inode 0 或不存在的 inode");
	if (!(bh=sb->s_imap[inode->i_num>>13]))
		panic("超级块中不存在 imap");
	if (clear_bit(inode->i_num&8191,bh->b_data))
		panic("free_inode: 位图已清除");
	bh->b_dirt = 1;
	memset(inode,0,sizeof(*inode));
}

struct m_inode * new_inode(int dev)
{
	struct m_inode * inode;
	struct super_block * sb;
	struct buffer_head * bh;
	int i,j;

	if (!(inode=get_empty_inode()))
		return NULL;
	if (!(sb = get_super(dev)))
		panic("new_inode: 未知设备");
	j = 8192;
	for (i=0 ; i<8 ; i++)
		if (bh=sb->s_imap[i])
			if ((j=find_first_zero(bh->b_data))<8192)
				break;
	if (!bh || j >= 8192 || j+i*8192 > sb->s_ninodes) {
		iput(inode);
		return NULL;
	}
	if (set_bit(j,bh->b_data))
		panic("new_inode: 位图已设置");
	bh->b_dirt = 1;
	inode->i_count=1;
	inode->i_nlinks=1;
	inode->i_dev=dev;
	inode->i_dirt=1;
	inode->i_num = j + i*8192;
	inode->i_mtime = inode->i_atime = inode->i_ctime = CURRENT_TIME;
	return inode;
}
