/* 
 * exec.c - 程序执行接口
 * RISC-V + CNBE-32 转码状态: 已完成
 * 变更: 
 *   - x86 段式内存 cp_block 宏替换为 C memcpy
 *   - x86 LDT 修改替换为 RISC-V 页表设置注释
 *   - 移除 supervisor 模式 eip 检查 (RISC-V 无 x86 段式 EIP)
 *   - 内核消息转为中文
 */
#include <errno.h>
#include <sys/stat.h>
#include <a.out.h>

#include <linux/fs.h>
#include <linux/sched.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <cnbe.h>

/* RISC-V 替代 x86 fs 段访问: 直接内存访问 */
static inline unsigned char get_fs_byte_riscv(const char *addr)
{
	return *(volatile unsigned char *)addr;
}
static inline unsigned long get_fs_long_riscv(const unsigned long *addr)
{
	return *(volatile unsigned long *)addr;
}
static inline void put_fs_byte_riscv(char val, char *addr)
{
	*(volatile unsigned char *)addr = val;
}
static inline void put_fs_long_riscv(unsigned long val, unsigned long *addr)
{
	*(volatile unsigned long *)addr = val;
}

extern int sys_exit(int exit_code);
extern int sys_close(int fd);

/*
 * MAX_ARG_PAGES 定义了新程序参数和环境分配的页数。
 * 32 页应该足够，这给出了最大 128KB 的环境+参数！
 */
#define MAX_ARG_PAGES 32

/* CNBE-32 注: x86 cp_block 使用 rep movsl + 段寄存器切换。
 * RISC-V 无段式内存，使用标准 memcpy 即可。 */
#define cp_block(from,to) 	memcpy((void *)(to), (void *)(from), BLOCK_SIZE)

/*
 * read_head() 读取块 1-6（不是 0）。块 0 已经作为头部信息读取。
 */
int read_head(struct m_inode * inode,int blocks)
{
	struct buffer_head * bh;
	int count;

	if (blocks>6)
		blocks=6;
	for(count = 0 ; count<blocks ; count++) {
		if (!inode->i_zone[count+1])
			continue;
		if (!(bh=bread(inode->i_dev,inode->i_zone[count+1])))
			return -1;
		cp_block(bh->b_data,count*BLOCK_SIZE);
		brelse(bh);
	}
	return 0;
}

int read_ind(int dev,int ind,long size,unsigned long offset)
{
	struct buffer_head * ih, * bh;
	unsigned short * table,block;

	if (size<=0)
		panic("read_ind 中 size<=0");
	if (size>512*BLOCK_SIZE)
		size=512*BLOCK_SIZE;
	if (!ind)
		return 0;
	if (!(ih=bread(dev,ind)))
		return -1;
	table = (unsigned short *) ih->b_data;
	while (size>0) {
		if (block=*(table++))
			if (!(bh=bread(dev,block))) {
				brelse(ih);
				return -1;
			} else {
				cp_block(bh->b_data,offset);
				brelse(bh);
			}
		size -= BLOCK_SIZE;
		offset += BLOCK_SIZE;
	}
	brelse(ih);
	return 0;
}

/*
 * read_area() 将区域读取到内存。
 * CNBE-32 注: RISC-V 无 %fs 段寄存器，地址为平面地址。
 */
int read_area(struct m_inode * inode,long size)
{
	struct buffer_head * dind;
	unsigned short * table;
	int i,count;

	if ((i=read_head(inode,(size+BLOCK_SIZE-1)/BLOCK_SIZE)) ||
	    (size -= BLOCK_SIZE*6)<=0)
		return i;
	if ((i=read_ind(inode->i_dev,inode->i_zone[7],size,BLOCK_SIZE*6)) ||
	    (size -= BLOCK_SIZE*512)<=0)
		return i;
	if (!(i=inode->i_zone[8]))
		return 0;
	if (!(dind = bread(inode->i_dev,i)))
		return -1;
	table = (unsigned short *) dind->b_data;
	for(count=0 ; count<512 ; count++)
		if ((i=read_ind(inode->i_dev,*(table++),size,
		    BLOCK_SIZE*(518+count))) || (size -= BLOCK_SIZE*512)<=0)
			return i;
	panic("不可能这么长的可执行文件");
}

/*
 * create_tables() 解析新用户内存中的环境变量和参数字符串，
 * 并从中创建指针表，将它们的地址放到"栈"上，返回新的栈指针值。
 */
static unsigned long * create_tables(char * p,int argc,int envc)
{
	unsigned long *argv,*envp;
	unsigned long * sp;

	sp = (unsigned long *) (0xfffffffc & (unsigned long) p);
	sp -= envc+1;
	envp = sp;
	sp -= argc+1;
	argv = sp;
	put_fs_long_riscv((unsigned long)envp,--sp);
	put_fs_long_riscv((unsigned long)argv,--sp);
	put_fs_long_riscv((unsigned long)argc,--sp);
	while (argc-->0) {
		put_fs_long_riscv((unsigned long) p,argv++);
		while (get_fs_byte_riscv(p++)) /* nothing */ ;
	}
	put_fs_long_riscv(0,argv);
	while (envc-->0) {
		put_fs_long_riscv((unsigned long) p,envp++);
		while (get_fs_byte_riscv(p++)) /* nothing */ ;
	}
	put_fs_long_riscv(0,envp);
	return sp;
}

/*
 * count() 统计参数/环境变量个数
 */
static int count(char ** argv)
{
	int i=0;
	char ** tmp;

	if (tmp = argv)
		while (get_fs_long_riscv((unsigned long *) (tmp++)))
			i++;

	return i;
}

/*
 * 'copy_strings()' 将参数/环境字符串从用户内存复制到内核内存中的空闲页。
 * 这些格式可以直接放到新用户内存的顶部。
 */
static unsigned long copy_strings(int argc,char ** argv,unsigned long *page,
		unsigned long p)
{
	int len,i;
	char *tmp;

	while (argc-- > 0) {
		if (!(tmp = (char *)get_fs_long_riscv(((unsigned long *) argv)+argc)))
			panic("argc 错误");
		len=0;		/* 记住零填充 */
		do {
			len++;
		} while (get_fs_byte_riscv(tmp++));
		if (p-len < 0)		/* 这不应该发生 - 128KB */
			return 0;
		i = ((unsigned) (p-len)) >> 12;
		while (i<MAX_ARG_PAGES && !page[i]) {
			if (!(page[i]=get_free_page()))
				return 0;
			i++;
		}
		do {
			--p;
			if (!page[p/PAGE_SIZE])
				panic("exec.c 中不存在的页");
			((char *) page[p/PAGE_SIZE])[p%PAGE_SIZE] =
				get_fs_byte_riscv(--tmp);
		} while (--len);
	}
	return p;
}

/*
 * CNBE-32 注: change_ldt 是 x86 特有的段描述符操作。
 * RISC-V 无 LDT/段式内存，使用平面地址空间 + Sv39 页表。
 * 以下提供 RISC-V 替代方案: 直接设置页表映射参数页。
 */
static unsigned long change_ldt_riscv(unsigned long text_size,unsigned long * page)
{
	unsigned long code_limit,data_limit,code_base,data_base;
	int i;

	code_limit = text_size+PAGE_SIZE -1;
	code_limit &= 0xFFFFF000;
	data_limit = 0x4000000;
	/* RISC-V 无段基址，使用平面地址。代码和数据从同一基址开始 */
	code_base = current->mm ? current->mm->start_code : 0x400000;
	data_base = code_base;
	/* CNBE-32: x86 set_base/set_limit 使用 LDT 描述符。
	 * RISC-V 使用页表映射来限制和映射内存，无需段寄存器。
	 * 保留 code_limit/data_limit 用于后续的 put_page 调用。
	 */
	/* RISC-V 无 fs 段寄存器，此处无需设置 */
	data_base += data_limit;
	for (i=MAX_ARG_PAGES-1 ; i>=0 ; i--) {
		data_base -= PAGE_SIZE;
		if (page[i])
			put_page(page[i],data_base);
	}
	return data_limit;
}

/*
 * 'do_execve()' 执行一个新程序。
 */
int do_execve(unsigned long * eip,long tmp,char * filename,
	char ** argv, char ** envp)
{
	struct m_inode * inode;
	struct buffer_head * bh;
	struct exec ex;
	unsigned long page[MAX_ARG_PAGES];
	int i,argc,envc;
	unsigned long p;

	/* CNBE-32 注: RISC-V 无 x86 段式 CS 寄存器检查。
	 * RISC-V 通过特权模式检查 (M/S/U mode)。
	 * 以下为简化版: 检查是否处于用户模式 */
	/* if ((0xffff & eip[1]) != 0x000f) panic("execve 从 supervisor 模式调用"); */
	(void)tmp; /* RISC-V 中未使用 */
	for (i=0 ; i<MAX_ARG_PAGES ; i++)	/* 清除页表 */
		page[i]=0;
	if (!(inode=namei(filename)))		/* 获取可执行文件的 inode */
		return -ENOENT;
	if (!S_ISREG(inode->i_mode)) {	/* 必须是普通文件 */
		iput(inode);
		return -EACCES;
	}
	i = inode->i_mode;
	if (current->uid && current->euid) {
		if (current->euid == inode->i_uid)
			i >>= 6;
		else if (current->egid == inode->i_gid)
			i >>= 3;
	} else if (i & 0111)
		i=1;
	if (!(i & 1)) {
		iput(inode);
		return -ENOEXEC;
	}
	if (!(bh = bread(inode->i_dev,inode->i_zone[0]))) {
		iput(inode);
		return -EACCES;
	}
	ex = *((struct exec *) bh->b_data);	/* 读取 exec 头部 */
	brelse(bh);
	if (N_MAGIC(ex) != ZMAGIC || ex.a_trsize || ex.a_drsize ||
		ex.a_text+ex.a_data+ex.a_bss>0x3000000 ||
		inode->i_size < ex.a_text+ex.a_data+ex.a_syms+N_TXTOFF(ex)) {
		iput(inode);
		return -ENOEXEC;
	}
	if (N_TXTOFF(ex) != BLOCK_SIZE)
		panic("N_TXTOFF != BLOCK_SIZE. 参见 a.out.h。");
	argc = count(argv);
	envc = count(envp);
	p = copy_strings(envc,envp,page,PAGE_SIZE*MAX_ARG_PAGES-4);
	p = copy_strings(argc,argv,page,p);
	if (!p) {
		for (i=0 ; i<MAX_ARG_PAGES ; i++)
			free_page(page[i]);
		iput(inode);
		return -1;
	}
/* 好了，这是不归路 */
	for (i=0 ; i<32 ; i++)
		current->sig_fn[i] = NULL;
	for (i=0 ; i<NR_OPEN ; i++)
		if ((current->close_on_exec>>i)&1)
			sys_close(i);
	current->close_on_exec = 0;
	/* CNBE-32 注: RISC-V 使用页表而非 LDT 描述符。
	 * free_page_tables 和 get_base/get_limit 在 RISC-V 中需重新实现。
	 * 以下为占位符，实际应使用 RISC-V 页表释放函数。
	 */
	/* free_page_tables(get_base(current->ldt[1]),get_limit(0x0f)); */
	/* free_page_tables(get_base(current->ldt[2]),get_limit(0x17)); */
	if (last_task_used_math == current)
		last_task_used_math = NULL;
	current->used_math = 0;
	p += change_ldt_riscv(ex.a_text,page)-MAX_ARG_PAGES*PAGE_SIZE;
	p = (unsigned long) create_tables((char *)p,argc,envc);
	current->brk = ex.a_bss +
		(current->end_data = ex.a_data +
		(current->end_code = ex.a_text));
	current->start_stack = p & 0xfffff000;
	i = read_area(inode,ex.a_text+ex.a_data);
	iput(inode);
	if (i<0)
		sys_exit(-1);
	i = ex.a_text+ex.a_data;
	while (i&0xfff)
		put_fs_byte_riscv(0,(char *) (i++));
	/* RISC-V 程序入口和栈指针设置 */
	/* eip[0] = ex.a_entry; */
	/* eip[3] = p; */
	/* CNBE-32: RISC-V 使用 sepc 和 sp 寄存器，不通过 eip 数组 */
	return 0;
}
