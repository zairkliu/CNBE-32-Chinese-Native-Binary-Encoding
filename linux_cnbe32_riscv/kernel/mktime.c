/*
 * 【RISC-V CNBE-32 转码状态】
 * 文件: kernel/mktime.c
 * 状态: 已完成转码
 * 变更:
 *   - 英文注释 → 中文注释
 *   - 保留核心算法不变(纯C计算，与架构无关)
 *   - 添加 CNBE-32 注释
 *   - 内核消息 → 中文 UTF-8
 * 
 * 【内核时间计算】将 struct tm 转换为自1970年1月1日以来的秒数。
 * 这不是库函数，仅在内核中使用。
 * 因此我们忽略年份<1970等问题，假设一切正常。
 * 同样，时区等被忽略。我们尽可能简单地处理。
 */

#include <time.h>

#define MINUTE 60
#define HOUR (60*MINUTE)
#define DAY (24*HOUR)
#define YEAR (365*DAY)

/* 闰年假设 */
static int month[12] = {
	0,
	DAY*(31),
	DAY*(31+29),
	DAY*(31+29+31),
	DAY*(31+29+31+30),
	DAY*(31+29+31+30+31),
	DAY*(31+29+31+30+31+30),
	DAY*(31+29+31+30+31+30+31),
	DAY*(31+29+31+30+31+30+31+31),
	DAY*(31+29+31+30+31+30+31+31+30),
	DAY*(31+29+31+30+31+30+31+31+30+31),
	DAY*(31+29+31+30+31+30+31+31+30+31+30)
};

/*
 * 将 tm 结构转换为内核时间(秒数)
 * 参数: tm - 包含年/月/日/时/分/秒的时间结构
 * 返回: 自1970年1月1日00:00:00以来的秒数
 * 
 * 注：此函数为纯C计算，与架构无关，RISC-V 可直接使用。
 * 唯一需要注意的是 RISC-V 32位系统上 long 为 32位，
 * 时间范围约到 2038 年(Y2K38 问题)，与 x86 32位一致。
 */
long kernel_mktime(struct tm * tm)
{
	long res;
	int year;

	/* 计算自1970年起的年数 */
	year = tm->tm_year - 70;
	/* 神奇偏移 (y+1) 用于正确计算闰年 */
	res = YEAR*year + DAY*((year+1)/4);
	res += month[tm->tm_mon];
	/* 这里使用 (y+2)。如果不是闰年，需要调整 */
	if (tm->tm_mon>1 && ((year+2)%4))
		res -= DAY;
	res += DAY*(tm->tm_mday-1);
	res += HOUR*tm->tm_hour;
	res += MINUTE*tm->tm_min;
	res += tm->tm_sec;
	return res;
}
