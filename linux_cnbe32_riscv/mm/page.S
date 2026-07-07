/*
 * mm/page.S - RISC-V + CNBE-32 转码版本
 * 转码状态: 已完成
 * 原始文件: Linux 0.01 x86 页面异常底层处理
 * 转码说明:
 *   - x86 汇编 → RISC-V 汇编
 *   - 移除 x86 段寄存器保存/恢复 (RISC-V 无段式内存管理)
 *   - x86 CR2 故障地址 → RISC-V stval CSR
 *   - x86 错误码格式 → RISC-V scause 异常码
 *   - x86 iret → RISC-V sret
 *   - 所有注释转码为中文
 * CNBE-32 注: 页面异常为内核关键路径, 此处禁用 CNBE 转换以保持性能。
 */

.globl page_fault

.text
.align 2

/*
 * page_fault —— RISC-V 页面异常处理入口
 *
 * RISC-V 发生页面异常时, 硬件自动将以下信息存入 CSR:
 *   sepc  = 发生异常的指令地址
 *   scause= 异常原因 (12=取指页缺失, 13=读页缺失, 15=写/AMO 页缺失)
 *   stval = 引发异常的虚拟地址
 *   sstatus.SPP = 异常前的特权级 (0=用户态, 1=内核态)
 *
 * 本处理程序保存必要的调用者保存寄存器, 构造与 x86 兼容的 error_code,
 * 调用 C 语言处理函数 do_no_page() 或 do_wp_page(), 然后恢复寄存器并返回。
 */
page_fault:
	/* 保存调用者保存寄存器到栈中
	 * RISC-V ABI: a0-a7, t0-t6, ra 为调用者保存寄存器
	 */
	addi	sp, sp, -48
	sw	ra, 44(sp)
	sw	t0, 40(sp)
	sw	t1, 36(sp)
	sw	t2, 32(sp)
	sw	a0, 28(sp)
	sw	a1, 24(sp)
	sw	a2, 20(sp)
	sw	a3, 16(sp)
	sw	a4, 12(sp)
	sw	a5, 8(sp)
	sw	a6, 4(sp)
	sw	a7, 0(sp)

	/* 读取 scause CSR 判断异常类型 */
	csrr	t0, scause

	/* scause = 15 (store/AMO page fault) → 写保护异常
	 * 对应 x86 错误码 bit0 = 1 (protection violation)
	 * 跳转至 do_wp_page 处理
	 */
	li	t1, 15
	beq	t0, t1, 1f

	/* scause = 12 (instruction page fault) 或 13 (load page fault)
	 * → 页面不存在
	 * 构造 error_code = 0 (not present), 与 x86 兼容
	 * 从 stval CSR 读取故障虚拟地址
	 */
	li	a0, 0
	csrr	a1, stval
	call	do_no_page
	j	2f

1:
	/* 写保护异常: 构造 error_code = 1 (protection violation)
	 * 从 stval CSR 读取故障虚拟地址
	 */
	li	a0, 1
	csrr	a1, stval
	call	do_wp_page

2:
	/* 恢复保存的寄存器 */
	lw	a7, 0(sp)
	lw	a6, 4(sp)
	lw	a5, 8(sp)
	lw	a4, 12(sp)
	lw	a3, 16(sp)
	lw	a2, 20(sp)
	lw	a1, 24(sp)
	lw	a0, 28(sp)
	lw	t2, 32(sp)
	lw	t1, 36(sp)
	lw	t0, 40(sp)
	lw	ra, 44(sp)
	addi	sp, sp, 48

	/* 返回异常发生点: sret 使用 sepc 作为返回地址,
	 * 并使用 sstatus.SPP 恢复特权级。
	 * 对应 x86 的 iret 指令。
	 */
	sret
