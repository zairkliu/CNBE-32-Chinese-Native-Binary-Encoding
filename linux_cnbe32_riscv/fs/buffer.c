/* 
 * buffer.c - 实现缓冲区缓存功能
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: x86 cli/sti 替换为 RISC-V CSR 操作，移除 x86 内存布局检查
 * 
 * 竞态条件通过不允许中断改变缓冲区来避免（数据除外），
 * 而是让调用者来做。注意！由于中断可以唤醒调用者，
 * 在睡眠调用检查时需要一些关中断/开中断序列。
 */

#include <linux/config.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <cnbe.h>

/* RISC-V 替代 x86 cli/sti: 使用 mstatus.MIE 位 */
#define cli_riscv() __asm__ __volatile__ ("csrci mstatus, 8" ::: "memory")
#define sti_riscv() __asm__ __volatile__ ("csrsi mstatus, 8" ::: "memory")

/* CNBE-32 注: RISC-V 无 x86 640KB 内存布局限制，以下检查已移除 */
/* #if (BUFFER_END & 0xfff) ... 已移除，RISC-V 使用 Sv39 页表 */
/* #if (BUFFER_END > 0xA0000 && BUFFER_END <= 0x100000) ... 已移除 */

extern int end;
struct buffer_head * start_buffer = (struct buffer_head *) &end;
struct buffer_head * hash_table[NR_HASH];
static struct buffer_head * free_list;
static struct task_struct * buffer_wait = NULL;
int NR_BUFFERS = 0;

static inline void wait_on_buffer(struct buffer_head * bh)
{
	cli_riscv();
	while (bh->b_lock)
		sleep_on(&bh->b_wait);
	sti_riscv();
}

int sys_sync(void)
{
	int i;
	struct buffer_head * bh;

	sync_inodes();		/* 将 inode 写入缓冲区 */
	bh = start_buffer;
	for (i=0 ; i<NR_BUFFERS ; i++,bh++) {
		wait_on_buffer(bh);
		if (bh->b_dirt)
			ll_rw_block(WRITE,bh);
	}
	return 0;
}

static int sync_dev(int dev)
{
	int i;
	struct buffer_head * bh;

	bh = start_buffer;
	for (i=0 ; i<NR_BUFFERS ; i++,bh++) {
		if (bh->b_dev != dev)
			continue;
		wait_on_buffer(bh);
		if (bh->b_dirt)
			ll_rw_block(WRITE,bh);
	}
	return 0;
}

#define _hashfn(dev,block) (((unsigned)(dev^block))%NR_HASH)
#define hash(dev,block) hash_table[_hashfn(dev,block)]

static inline void remove_from_queues(struct buffer_head * bh)
{
/* 从哈希队列中移除 */
	if (bh->b_next)
		bh->b_next->b_prev = bh->b_prev;
	if (bh->b_prev)
		bh->b_prev->b_next = bh->b_next;
	if (hash(bh->b_dev,bh->b_blocknr) == bh)
		hash(bh->b_dev,bh->b_blocknr) = bh->b_next;
/* 从空闲链表中移除 */
	if (!(bh->b_prev_free) || !(bh->b_next_free))
		panic("空闲链表已损坏");
	bh->b_prev_free->b_next_free = bh->b_next_free;
	bh->b_next_free->b_prev_free = bh->b_prev_free;
	if (free_list == bh)
		free_list = bh->b_next_free;
}

static inline void insert_into_queues(struct buffer_head * bh)
{
/* 放到空闲链表末尾 */
	bh->b_next_free = free_list;
	bh->b_prev_free = free_list->b_prev_free;
	free_list->b_prev_free->b_next_free = bh;
	free_list->b_prev_free = bh;
/* 如果有设备，放到新的哈希队列 */
	bh->b_prev = NULL;
	bh->b_next = NULL;
	if (!bh->b_dev)
		return;
	bh->b_next = hash(bh->b_dev,bh->b_blocknr);
	hash(bh->b_dev,bh->b_blocknr) = bh;
	bh->b_next->b_prev = bh;
}

static struct buffer_head * find_buffer(int dev, int block)
{		
	struct buffer_head * tmp;

	for (tmp = hash(dev,block) ; tmp != NULL ; tmp = tmp->b_next)
		if (tmp->b_dev==dev && tmp->b_blocknr==block)
			return tmp;
	return NULL;
}

/*
 * 你可能会问为什么要这样写... 原因是竞态条件。
 * 由于我们只在读取时锁定缓冲区，
 * 在我们睡眠时可能会发生一些事（比如读错误导致缓冲区失效）。
 * 目前不应该发生，但代码已经准备好了。
 */
struct buffer_head * get_hash_table(int dev, int block)
{
	struct buffer_head * bh;

repeat:
	if (!(bh=find_buffer(dev,block)))
		return NULL;
	bh->b_count++;
	wait_on_buffer(bh);
	if (bh->b_dev != dev || bh->b_blocknr != block) {
		brelse(bh);
		goto repeat;
	}
	return bh;
}

/*
 * 这是 getblk，同样写得不太清晰，也是为了竞态条件。
 * 大部分代码很少使用（重复），所以实际效率比看起来要高。
 */
struct buffer_head * getblk(int dev,int block)
{
	struct buffer_head * tmp;

repeat:
	if (tmp=get_hash_table(dev,block))
		return tmp;
	tmp = free_list;
	do {
		if (!tmp->b_count) {
			wait_on_buffer(tmp);	/* 仍然需要等待 */
			if (!tmp->b_count)	/* 在等的时候，它可能变脏了 */
				break;
		}
		tmp = tmp->b_next_free;
	} while (tmp != free_list || (tmp=NULL));
	/* 孩子们，不要在家里尝试这个 ^^^^^。魔法 */
	if (!tmp) {
		printk("正在空闲缓冲区上睡眠 ..");
		sleep_on(&buffer_wait);
		printk("完成\n");
		goto repeat;
	}
	tmp->b_count++;
	remove_from_queues(tmp);
/*
 * 现在，我们知道没有人能访问这个节点（因为它已从空闲链表移除），
 * 我们把它写出去。在这里睡觉不用担心竞态条件。
 */
	if (tmp->b_dirt)
		sync_dev(tmp->b_dev);
/* 更新缓冲区内容 */
	tmp->b_dev=dev;
	tmp->b_blocknr=block;
	tmp->b_dirt=0;
	tmp->b_uptodate=0;
/* 注意!! 在 sync_dev() 中可能睡眠时，其他人可能已经添加了这个块，
 * 所以检查一下。感谢上帝有 goto。
 */
	if (find_buffer(dev,block)) {
		tmp->b_dev=0;		/* 好的，有人抢先了 */
		tmp->b_blocknr=0;	/* 释放这个块并重试 */
		tmp->b_count=0;
		insert_into_queues(tmp);
		goto repeat;
	}
/* 然后插入到正确位置 */
	insert_into_queues(tmp);
	return tmp;
}

void brelse(struct buffer_head * buf)
{
	if (!buf)
		return;
	wait_on_buffer(buf);
	if (!(buf->b_count--))
		panic("尝试释放已释放的缓冲区");
	wake_up(&buffer_wait);
}

/*
 * bread() 读取指定的块并返回包含它的缓冲区。
 * 如果块不可读则返回 NULL。
 */
struct buffer_head * bread(int dev,int block)
{
	struct buffer_head * bh;

	if (!(bh=getblk(dev,block)))
		panic("bread: getblk 返回 NULL\n");
	if (bh->b_uptodate)
		return bh;
	ll_rw_block(READ,bh);
	if (bh->b_uptodate)
		return bh;
	brelse(bh);
	return (NULL);
}

void buffer_init(void)
{
	struct buffer_head * h = start_buffer;
	void * b = (void *) BUFFER_END;
	int i;

	while ( (b -= BLOCK_SIZE) >= ((void *) (h+1)) ) {
		h->b_dev = 0;
		h->b_dirt = 0;
		h->b_count = 0;
		h->b_lock = 0;
		h->b_uptodate = 0;
		h->b_wait = NULL;
		h->b_next = NULL;
		h->b_prev = NULL;
		h->b_data = (char *) b;
		h->b_prev_free = h-1;
		h->b_next_free = h+1;
		h++;
		NR_BUFFERS++;
		/* CNBE-32 注: RISC-V 无 x86 640KB/1MB 内存空洞，以下检查已移除 */
		/* if (b == (void *) 0x100000) b = (void *) 0xA0000; */
	}
	h--;
	free_list = start_buffer;
	free_list->b_prev_free = h;
	h->b_next_free = free_list;
	for (i=0;i<NR_HASH;i++)
		hash_table[i]=NULL;
}	
