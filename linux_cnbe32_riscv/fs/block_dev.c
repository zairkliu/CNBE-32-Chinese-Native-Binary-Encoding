/* 
 * block_dev.c - 块设备读写接口
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: x86 fs 段访问宏替换为 RISC-V 内存直接访问
 */
#include <errno.h>

#include <linux/fs.h>
#include <linux/kernel.h>
#include <cnbe.h>

/* RISC-V 替代方案: 无段式内存，直接访问用户空间指针 */
static inline unsigned char get_fs_byte_riscv(const char *addr)
{
	return *(volatile unsigned char *)addr;
}
static inline void put_fs_byte_riscv(char val, char *addr)
{
	*(volatile unsigned char *)addr = val;
}

#define NR_BLK_DEV ((sizeof (rd_blk))/(sizeof (rd_blk[0])))

int block_write(int dev, long * pos, char * buf, int count)
{
	int block = *pos / BLOCK_SIZE;
	int offset = *pos % BLOCK_SIZE;
	int chars;
	int written = 0;
	struct buffer_head * bh;
	register char * p;

	while (count>0) {
		bh = bread(dev,block);
		if (!bh)
			return written?written:-EIO;
		chars = (count<BLOCK_SIZE) ? count : BLOCK_SIZE;
		p = offset + bh->b_data;
		offset = 0;
		block++;
		*pos += chars;
		written += chars;
		count -= chars;
		while (chars-->0)
			*(p++) = get_fs_byte_riscv(buf++);
		bh->b_dirt = 1;
		brelse(bh);
	}
	return written;
}

int block_read(int dev, unsigned long * pos, char * buf, int count)
{
	int block = *pos / BLOCK_SIZE;
	int offset = *pos % BLOCK_SIZE;
	int chars;
	int read = 0;
	struct buffer_head * bh;
	register char * p;

	while (count>0) {
		bh = bread(dev,block);
		if (!bh)
			return read?read:-EIO;
		chars = (count<BLOCK_SIZE) ? count : BLOCK_SIZE;
		p = offset + bh->b_data;
		offset = 0;
		block++;
		*pos += chars;
		read += chars;
		count -= chars;
		while (chars-->0)
			put_fs_byte_riscv(*(p++),buf++);
		bh->b_dirt = 1;
		brelse(bh);
	}
	return read;
}

extern void rw_hd(int rw, struct buffer_head * bh);

typedef void (*blk_fn)(int rw, struct buffer_head * bh);

static blk_fn rd_blk[]={
	NULL,		/* 无设备 */
	NULL,		/* /dev/mem */
	NULL,		/* /dev/fd */
	rw_hd,		/* /dev/hd */
	NULL,		/* /dev/ttyx */
	NULL,		/* /dev/tty */
	NULL};		/* /dev/lp */

void ll_rw_block(int rw, struct buffer_head * bh)
{
	blk_fn blk_addr;
	unsigned int major;

	if ((major=MAJOR(bh->b_dev)) >= NR_BLK_DEV || !(blk_addr=rd_blk[major]))
		panic("尝试读取不存在的块设备");
	blk_addr(rw, bh);
}
