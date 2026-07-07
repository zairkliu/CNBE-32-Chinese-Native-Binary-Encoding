#ifndef _SYS_TIMES_H
#define _SYS_TIMES_H

struct tms {
	long tms_utime;
	long tms_stime;
	long tms_cutime;
	long tms_cstime;
};

#endif
