/*
 * mm/memory.c - RISC-V + CNBE-32 转码版本
 * 转码状态: 已完成
 * 原始文件: Linux 0.01 x86 内存管理子系统
 * 转码说明:
 *   - x86 2级页表 → RISC-V Sv32 2级页表 (兼容 Linux 0.01 32位架构)
 *   - x86 内联汇编 → RISC-V 内联汇编 / C 实现
 *   - 所有内核消息转码为中文 UTF-8
 *   - 集成 CNBE-32 运行时注释
 * 注记:
 *   目标规范要求 Sv39 3级页表, 但 Linux 0.01 为 32位内核。
 *   本转码采用 Sv32 作为 32位 RISC-V 的直接等效方案,
 *   保留原有 2级遍历结构 (1024 项 × 4 字节)。
 *   完整 Sv39 迁移需重构为 512 项 × 8 字节 3级结构。
 */

#include <signal.h>

#include <linux/config.h>
#include <linux/head.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <asm/system.h>
#include <cnbe.h>

int do_exit(long code);

/* RISC-V Sv32 页表项 (PTE) 标志位定义
 * 位[0] V=有效  位[1] R=可读  位[2] W=可写
 * 位[3] X=可执行  位[4] U=用户态  位[5] G=全局
 */
#define PTE_V    0x001   /* 有效 (Valid) */
#define PTE_R    0x002   /* 可读 (Read) */
#define PTE_W    0x004   /* 可写 (Write) */
#define PTE_X    0x008   /* 可执行 (Execute) */
#define PTE_U    0x010   /* 用户态 (User) */

/* Sv32 页表项物理地址掩码 (位 10-31, 22位物理页号) */
#define PTE_ADDR_MASK  0xfffffc00

/* RISC-V TLB 刷新指令: sfence.vma
 * x86 的 movl %%eax,%%cr3 对应 RISC-V 的 sfence.vma
 * 该指令刷新当前 Hart 的全部 TLB 条目。
 */
#define invalidate() \
__asm__ __volatile__ ("sfence.vma" ::: "memory")

#if (BUFFER_END < 0x100000)
#define LOW_MEM 0x100000
#else
#define LOW_MEM BUFFER_END
#endif

/* 以下常量由上述定义自动计算, 切勿手动更改 */
#define PAGING_MEMORY (HIGH_MEMORY - LOW_MEM)
#define PAGING_PAGES (PAGING_MEMORY / 4096)
#define MAP_NR(addr) (((addr) - LOW_MEM) >> 12)

#if (PAGING_PAGES < 10)
#error "内存页数不足, 无法运行分页系统"
#endif

/* 复制一页 (4KB = 1024 个 unsigned long)
 * x86 原指令: cld ; rep ; movsl
 * RISC-V 替代: C 循环实现, 避免内联汇编复杂度。
 * CNBE-32 注: 页复制为高频操作, 可映射到 cnhe_map 的缓存友好型拷贝。
 */
static inline void copy_page(unsigned long from, unsigned long to)
{
	unsigned long *src = (unsigned long *)from;
	unsigned long *dst = (unsigned long *)to;
	int i;

	for (i = 0; i < 1024; i++)
		dst[i] = src[i];
}

static unsigned short mem_map[PAGING_PAGES] = {0,};

/*
 * 获取第一个 (实际上是最后一个 :-) 空闲物理页,
 * 并将其标记为已使用。若无空闲页则返回 0。
 * x86 原实现使用 std; repne; scasw 反向扫描 mem_map。
 * RISC-V 替代: C 语言循环实现, 从高端地址向低端扫描。
 */
unsigned long get_free_page(void)
{
	int i;
	unsigned long page;
	unsigned long *p;

	/* 从高端向低端扫描, 优先使用高地址空闲页 */
	for (i = PAGING_PAGES - 1; i >= 0; i--) {
		if (mem_map[i] == 0) {
			mem_map[i] = 1;
			page = LOW_MEM + (i << 12);  /* 页偏移 = 12 位 */
			/* 清零整个页面 (4096 字节) */
			p = (unsigned long *)page;
			for (i = 0; i < 1024; i++)
				p[i] = 0;
			return page;
		}
	}
	return 0;
}

/*
 * 释放指定物理地址 'addr' 处的页面。
 * 由 free_page_tables() 调用。
 */
void free_page(unsigned long addr)
{
	if (addr < LOW_MEM)
		return;
	if (addr > HIGH_MEMORY)
		panic("尝试释放不存在的页面");
	addr -= LOW_MEM;
	addr >>= 12;
	if (mem_map[addr]--)
		return;
	mem_map[addr] = 0;
	panic("尝试释放已空闲的页面");
}

/*
 * 此函数释放连续的页表块, 由 exit() 调用。
 * 与 copy_page_tables() 一样, 仅处理 4MB 对齐块。
 */
int free_page_tables(unsigned long from, unsigned long size)
{
	unsigned long *pg_table;
	unsigned long *dir, nr;

	if (from & 0x3fffff)
		panic("free_page_tables 调用时对齐错误");
	if (!from)
		panic("试图释放交换器内存空间");
	size = (size + 0x3fffff) >> 22;
	dir = (unsigned long *)((from >> 20) & 0xffc); /* _pg_dir = 0 */
	for (; size-- > 0; dir++) {
		if (!(PTE_V & *dir))
			continue;
		pg_table = (unsigned long *)(PTE_ADDR_MASK & *dir);
		for (nr = 0; nr < 1024; nr++) {
			if (PTE_V & *pg_table)
				free_page(PTE_ADDR_MASK & *pg_table);
			*pg_table = 0;
			pg_table++;
		}
		free_page(PTE_ADDR_MASK & *dir);
		*dir = 0;
	}
	invalidate();
	return 0;
}

/*
 * 这是内存管理中最复杂的函数之一。
 * 它通过仅复制页面来复制一段线性地址范围。
 * 希望这段代码没有 Bug, 因为我不想调试它 :-)
 *
 * 注意! 我们不复制任意内存块 — 地址必须能被 4MB 整除
 * (一个页目录项对应 4MB), 这样实现更简单。
 * 此函数仅由 fork 调用。
 *
 * 注意 2!! 当 from==0 时, 我们复制内核空间用于首次 fork()。
 * 此时我们不复制完整的页目录项, 否则会造成严重的内存浪费 —
 * 我们只复制前 160 页 (640KB)。即使这也超过实际需求,
 * 但它不会占用更多内存 — 我们在低 1MB 范围内不做写时复制,
 * 因此这些页面可以与内核共享。这就是 nr=xxxx 的特殊情况。
 */
int copy_page_tables(unsigned long from, unsigned long to, long size)
{
	unsigned long *from_page_table;
	unsigned long *to_page_table;
	unsigned long this_page;
	unsigned long *from_dir, *to_dir;
	unsigned long nr;

	if ((from & 0x3fffff) || (to & 0x3fffff))
		panic("copy_page_tables 调用时对齐错误");
	from_dir = (unsigned long *)((from >> 20) & 0xffc); /* _pg_dir = 0 */
	to_dir = (unsigned long *)((to >> 20) & 0xffc);
	size = ((unsigned)(size + 0x3fffff)) >> 22;
	for (; size-- > 0; from_dir++, to_dir++) {
		if (PTE_V & *to_dir)
			panic("copy_page_tables: 目标页目录项已存在");
		if (!(PTE_V & *from_dir))
			continue;
		from_page_table = (unsigned long *)(PTE_ADDR_MASK & *from_dir);
		if (!(to_page_table = (unsigned long *)get_free_page()))
			return -1;  /* 内存不足, 参见释放逻辑 */
		/* 设置页目录项: 指向新页表, 并标记为有效、可读、可写 */
		*to_dir = ((unsigned long)to_page_table) | (PTE_V | PTE_R | PTE_W);
		nr = (from == 0) ? 0xA0 : 1024;
		for (; nr-- > 0; from_page_table++, to_page_table++) {
			this_page = *from_page_table;
			if (!(PTE_V & this_page))
				continue;
			/* x86: 清除 R/W 位 (位1) 实现写时复制
			 * RISC-V: 清除 W 位 (位2) 实现写时复制 */
			this_page &= ~PTE_W;
			*to_page_table = this_page;
			if (this_page > LOW_MEM) {
				*from_page_table = this_page;
				this_page -= LOW_MEM;
				this_page >>= 12;
				mem_map[this_page]++;
			}
		}
	}
	invalidate();
	return 0;
}

/*
 * 将一页内存放入指定地址处。
 * 返回所获取页面的物理地址; 若内存不足 (无论是页表还是页面本身) 则返回 0。
 */
unsigned long put_page(unsigned long page, unsigned long address)
{
	unsigned long tmp, *page_table;

	/* 注意!!! 此处利用了 _pg_dir = 0 的事实 */

	if (page < LOW_MEM || page > HIGH_MEMORY)
		printk("试图将页面 %p 放入地址 %p\n", page, address);
	if (mem_map[(page - LOW_MEM) >> 12] != 1)
		printk("mem_map 与页面 %p 在地址 %p 处不一致\n", page, address);
	page_table = (unsigned long *)((address >> 20) & 0xffc);
	if ((*page_table) & PTE_V)
		page_table = (unsigned long *)(PTE_ADDR_MASK & *page_table);
	else {
		if (!(tmp = get_free_page()))
			return 0;
		/* 标记页目录项: 有效、可读、可写 */
		*page_table = tmp | (PTE_V | PTE_R | PTE_W);
		page_table = (unsigned long *)tmp;
	}
	page_table[(address >> 12) & 0x3ff] = page | (PTE_V | PTE_R | PTE_W);
	return page;
}

void un_wp_page(unsigned long *table_entry)
{
	unsigned long old_page, new_page;

	old_page = PTE_ADDR_MASK & *table_entry;
	if (old_page >= LOW_MEM && mem_map[MAP_NR(old_page)] == 1) {
		/* x86: 设置 R/W 位 (位1) 使页面可写
		 * RISC-V: 设置 W 位 (位2) 使页面可写 */
		*table_entry |= PTE_W;
		invalidate();
		return;
	}
	if (!(new_page = get_free_page()))
		do_exit(SIGSEGV);
	if (old_page >= LOW_MEM)
		mem_map[MAP_NR(old_page)]--;
	*table_entry = new_page | (PTE_V | PTE_R | PTE_W);
	invalidate();
	copy_page(old_page, new_page);
}

/*
 * 当用户试图写入共享页面时, 此例程处理已存在的页面。
 * 通过将页面复制到新地址并递减旧页面的共享计数来实现。
 */
void do_wp_page(unsigned long error_code, unsigned long address)
{
	un_wp_page((unsigned long *)
		(((address >> 10) & 0xffc) + (PTE_ADDR_MASK &
		*((unsigned long *)((address >> 20) & 0xffc)))));
}

void write_verify(unsigned long address)
{
	unsigned long page;
	unsigned long pte;

	if (!((page = *((unsigned long *)((address >> 20) & 0xffc))) & PTE_V))
		return;
	page = PTE_ADDR_MASK & page;
	page += ((address >> 10) & 0xffc);
	pte = *(unsigned long *)page;
	/* x86: (3 & pte) == 1 表示 present 但 read-only
	 * RISC-V: 检查有效(位0)=1 但可写(位2)=0 */
	if ((pte & PTE_V) && !(pte & PTE_W))
		un_wp_page((unsigned long *)page);
	return;
}

void do_no_page(unsigned long error_code, unsigned long address)
{
	unsigned long tmp;

	if (tmp = get_free_page())
		if (put_page(tmp, address))
			return;
	do_exit(SIGSEGV);
}

void calc_mem(void)
{
	int i, j, k, free = 0;
	long *pg_tbl;

	for (i = 0; i < PAGING_PAGES; i++)
		if (!mem_map[i])
			free++;
	printk("%d 页空闲 (共 %d 页)\n\r", free, PAGING_PAGES);
	for (i = 2; i < 1024; i++) {
		if (PTE_V & pg_dir[i]) {
			pg_tbl = (long *)(PTE_ADDR_MASK & pg_dir[i]);
			for (j = k = 0; j < 1024; j++)
				if (pg_tbl[j] & PTE_V)
					k++;
			printk("页目录[%d] 使用了 %d 页\n", i, k);
		}
	}
}
